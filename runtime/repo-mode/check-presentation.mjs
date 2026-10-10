import {spawn} from 'node:child_process';
import {writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';

function connect(entry) {
 const child=spawn('docker',['exec','-i','fortis-repo-test','node',entry],{stdio:['pipe','pipe','pipe']});
 let buffer='',next=0;const pending=new Map();
 child.stderr.on('data',()=>{});
 child.stdout.on('data',part=>{buffer+=part;let i;while((i=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,i);buffer=buffer.slice(i+1);let m;try{m=JSON.parse(line)}catch{continue}const p=pending.get(m.id);if(p){pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(new Error('MCP error '+m.error.code)):p.resolve(m.result);}}});
 const fail=()=>{for(const p of pending.values()){clearTimeout(p.timer);p.reject(new Error('MCP child stopped'));}pending.clear();};
 child.on('error',fail);child.on('exit',fail);
 const rpc=(method,params={})=>new Promise((resolve,reject)=>{const id=++next;const timer=setTimeout(()=>{pending.delete(id);reject(new Error('Timeout '+method));},25000);pending.set(id,{resolve,reject,timer});child.stdin.write(JSON.stringify({jsonrpc:'2.0',id,method,params})+'\n');});
 return {rpc,notify:()=>child.stdin.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/initialized'})+'\n'),close:()=>{child.stdin.end();child.kill();}};
}
const original=connect('/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js');
const bridge=connect('/workspace/repo/.fortis/mcp-bridge.mjs');
try {
 const params={protocolVersion:'2025-03-26',capabilities:{},clientInfo:{name:'fortis-presentation-check',version:'1'}};
 await original.rpc('initialize',params);original.notify();const upstream=await original.rpc('tools/list');
 const init=await bridge.rpc('initialize',params);bridge.notify();const listed=await bridge.rpc('tools/list');
 assert.equal(init.serverInfo.name,'fortis-repo');assert(init.instructions.includes('general code and repository workspace'));assert(init.instructions.includes('not a website-building workflow'));
 assert(!('resources' in init.capabilities));assert.deepEqual((await bridge.rpc('resources/list')).resources,[]);
 assert.deepEqual(listed.tools.map(t=>t.name),upstream.tools.map(t=>t.name));
 for(let i=0;i<listed.tools.length;i++){
  const t=listed.tools[i],u=upstream.tools[i];assert.deepEqual(t.inputSchema,u.inputSchema);assert.deepEqual(t.annotations,u.annotations);
  assert(!t._meta?.ui);assert(!t._meta?.['ui/resourceUri']);assert(!t._meta?.['openai/outputTemplate']);
  assert(t.description.includes('activation does not request a website'));assert(!t.description.includes('PATH TRANSLATION IN DOCKER:'));
 }
 const call=(name,args={})=>bridge.rpc('tools/call',{name,arguments:args});
 const config=await call('get_config');assert.equal(config.isError??false,false);assert.deepEqual(config.structuredContent.config.allowedDirectories,['/workspace/repos','/workspace/files','/workspace/repo']);
 assert.equal(config.structuredContent.config.systemInfo.platform,'linux');
 const path='/workspace/repo/.fortis/presentation-check.txt';
 assert.equal((await call('write_file',{path,content:'Fortis presentation bridge verified\n',mode:'rewrite'})).isError??false,false);
 assert(JSON.stringify(await call('read_file',{path})).includes('Fortis presentation bridge verified'));
 const process=await call('start_process',{command:'cd /workspace/repo && pwd && id -u',timeout_ms:10000});assert.equal(process.isError??false,false,JSON.stringify(process));let terminalOutput=JSON.stringify(process);const pid=process.structuredContent?.pid??Number(terminalOutput.match(/Process started with PID (\d+)/)?.[1]);if(!terminalOutput.includes('1000')&&pid){terminalOutput+=JSON.stringify(await call('read_process_output',{pid,timeout_ms:10000,length:100}));}assert(terminalOutput.includes('/workspace/repo'),terminalOutput);assert(terminalOutput.includes('1000'),terminalOutput);
 assert.equal((await call('read_file',{path:'/etc/passwd'})).isError,true);
 const report={verifiedAt:new Date().toISOString(),toolCount:listed.tools.length,instructionsVerified:true,legacyUiRemoved:true,pathMappingCorrected:true,schemasAndAnnotationsPreserved:true,fileWriteRead:true,terminal:true,outsideReadDenied:true,tunnelRestartRequired:true,chatPresentationVerified:false};
 writeFileSync(new URL('./presentation-verification.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
} finally {original.close();bridge.close();}
