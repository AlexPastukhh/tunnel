import {spawn,spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const settings=JSON.parse(readFileSync(new URL('./workspace-config.json',import.meta.url),'utf8'));
const container=settings.container;
function docker(args){const r=spawnSync('docker',args,{encoding:'utf8',timeout:45000});assert.equal(r.status,0,r.stderr||String(r.error));return r.stdout;}
const c=JSON.parse(docker(['inspect',container]))[0],h=c.HostConfig;
assert.equal(c.Id,settings.containerId,'Container identity changed');
assert.equal(c.Config.User,'1000:1000');assert.equal(h.Privileged,false);assert.equal(h.ReadonlyRootfs,true);
assert(h.CapDrop.includes('ALL'));assert(h.SecurityOpt.includes('no-new-privileges'));
assert.equal(Object.keys(h.PortBindings||{}).length,0);
assert.equal(h.Memory,1073741824);assert.equal(h.NanoCpus,2000000000);assert.equal(h.PidsLimit,256);
assert.deepEqual(Object.keys(h.Tmpfs||{}).sort(),['/home/node','/tmp']);
assert(!c.Config.Env.some(x=>/KEY=|TOKEN=|SECRET=/.test(x)));
const mounts=c.Mounts.filter(m=>m.Type!=='tmpfs');
assert.equal(mounts.length,3);
const volume=mounts.find(m=>m.Destination==='/workspace/repo');
assert.equal(volume.Type,'volume');assert.equal(volume.Name,'fortis-repo-workspace');assert.equal(volume.RW,true);
const normalize=s=>s.replaceAll('\\','/').toLowerCase().replace(/^\/run\/desktop\/mnt\/host\/([a-z])\//,'$1:/').replace(/\/$/,'');
for(const mapping of settings.folders){
 const m=mounts.find(m=>m.Destination===mapping.container);
 assert(m,'Missing mount '+mapping.container);assert.equal(m.Type,'bind');assert.equal(m.RW,true);
 assert.equal(normalize(m.Source),normalize(mapping.host));
}
const networks=Object.keys(c.NetworkSettings.Networks);
assert.deepEqual(networks,settings.internetEnabled?[settings.network]:[]);
if(!c.State.Running){
 assert(process.argv.includes('--start-if-stopped'),'Start the verified Repo container first');
 docker(['start',container]);
}
const roots=settings.allowedDirectories;
const checkCode=String.raw`const fs=require('fs'),crypto=require('crypto'),os=require('os');const roots=JSON.parse(process.argv[1]);const s=fs.readFileSync('/proc/self/status','utf8');let rootWrite=false;try{fs.writeFileSync('/repo-root-write-probe','x');rootWrite=true}catch{};for(const p of roots){const f=p+'/.fortis-access-check-'+crypto.randomUUID();fs.writeFileSync(f,'ok',{flag:'wx'});fs.unlinkSync(f);}console.log(JSON.stringify({uid:process.getuid(),workspaceWritable:true,rootWrite,capEff:s.match(/^CapEff:\s*(.+)$/m)?.[1],noNewPrivs:s.match(/^NoNewPrivs:\s*(.+)$/m)?.[1],dockerSocket:fs.existsSync('/var/run/docker.sock'),fullHostMount:fs.existsSync('/mnt/c/Users'),interfaces:Object.keys(os.networkInterfaces())}));`;
const isolation=JSON.parse(docker(['exec',container,'node','-e',checkCode,JSON.stringify(roots)]));
assert.equal(isolation.uid,1000);assert.equal(isolation.rootWrite,false);assert(/^0+$/.test(isolation.capEff));assert.equal(isolation.noNewPrivs,'1');assert.equal(isolation.dockerSocket,false);assert.equal(isolation.fullHostMount,false);
if(settings.internetEnabled)assert(isolation.interfaces.some(x=>x!=='lo'));else assert.deepEqual(isolation.interfaces,['lo']);
const gitSetup=String.raw`const fs=require('fs'),cp=require('child_process');function git(a){const r=cp.spawnSync('git',a,{encoding:'utf8'});if(r.status!==0)throw Error(r.stderr);}const prior=cp.spawnSync('git',['config','--global','--get-all','safe.directory'],{encoding:'utf8'}).stdout.trim().split('\n');for(const e of fs.readdirSync('/workspace/repos',{withFileTypes:true})){if(e.isDirectory()&&fs.existsSync('/workspace/repos/'+e.name+'/.git')){const p='/workspace/repos/'+e.name;if(!prior.includes(p))git(['config','--global','--add','safe.directory',p]);}}git(['config','--global','core.autocrlf',process.argv[1]]);`;
docker(['exec',container,'node','-e',gitSetup,settings.gitAutocrlf]);
const child=spawn('docker',['exec','-i',container,'node','/workspace/repo/.fortis/mcp-bridge.mjs'],{stdio:['pipe','pipe','pipe']});
let buffer='',next=0;const pending=new Map();
child.stderr.on('data',()=>{});
child.stdout.on('data',part=>{buffer+=part;let i;while((i=buffer.indexOf('\n'))>=0){let m;const line=buffer.slice(0,i);buffer=buffer.slice(i+1);try{m=JSON.parse(line)}catch{continue}const p=pending.get(m.id);if(p){pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(new Error('RPC error '+m.error.code)):p.resolve(m.result);}}});
const fail=()=>{for(const p of pending.values()){clearTimeout(p.timer);p.reject(new Error('MCP process stopped'));}pending.clear();};
child.on('error',fail);child.on('exit',fail);
function rpc(method,params={}){const id=++next;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{pending.delete(id);reject(new Error('Timeout '+method));},25000);pending.set(id,{resolve,reject,timer});child.stdin.write(JSON.stringify({jsonrpc:'2.0',id,method,params})+'\n');});}
async function call(name,args={}){const v=await rpc('tools/call',{name,arguments:args});assert.equal(v.isError||false,false,JSON.stringify(v));return v;}
try{
 const init=await rpc('initialize',{protocolVersion:'2025-03-26',capabilities:{},clientInfo:{name:'fortis-workspace-probe',version:'2'}});
 child.stdin.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/initialized'})+'\n');
 assert.equal(init.serverInfo.name,'fortis-repo');
 const listed=await rpc('tools/list',{});assert(listed.tools.some(t=>t.name==='start_process'));
 await call('set_config_value',{key:'allowedDirectories',value:roots});
 await call('set_config_value',{key:'defaultShell',value:'/bin/bash'});
 await call('set_config_value',{key:'telemetryEnabled',value:false});
 const cfg=await call('get_config');assert.deepEqual(cfg.structuredContent.config.allowedDirectories,roots);
 for(const p of roots)await call('list_directory',{path:p,depth:1});
 const blocked=await rpc('tools/call',{name:'read_file',arguments:{path:'/etc/passwd'}});assert.equal(blocked.isError,true);
 if(settings.internetEnabled && process.argv.includes('--check-internet')){
  const online=String.raw`const https=require('https');Promise.allSettled(['https://github.com','https://registry.npmjs.org'].map(url=>new Promise((resolve,reject)=>{const r=https.get(url,{timeout:15000},res=>{res.resume();if(res.statusCode>=200&&res.statusCode<400)resolve({url,status:res.statusCode});else reject(Error('HTTP '+res.statusCode));});r.on('timeout',()=>r.destroy(Error('Timeout')));r.on('error',reject);}))).then(x=>{console.log(JSON.stringify(x.map((r,i)=>({url:['https://github.com','https://registry.npmjs.org'][i],status:r.status==='fulfilled'?r.value.status:null,error:r.status==='rejected'?r.reason.message:null}))));if(!x.some(r=>r.status==='fulfilled'))process.exitCode=1}).catch(e=>{console.error(e.message);process.exitCode=1});`;
  console.log('NETWORK_CHECK '+docker(['exec',container,'node','-e',online]).trim());
 }
 writeFileSync(new URL('./linux-tools.json',import.meta.url),JSON.stringify(listed.tools,null,2));
 const report={checkedAt:new Date().toISOString(),container,containerId:c.Id,folders:settings.folders,allowedDirectories:roots,network:settings.network,internetEnabled:settings.internetEnabled,rootfsReadOnly:true,publishedPorts:0,hostBindMounts:2,isolation,toolCount:listed.tools.length};
 writeFileSync(new URL('./verification.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{child.stdin.end();child.kill();}
