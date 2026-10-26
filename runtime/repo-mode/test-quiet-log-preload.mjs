import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { createHash } from 'node:crypto';

const source = readFileSync(new URL('./quiet-log-preload.mjs', import.meta.url));
const option = '--import=data:text/javascript;base64,' + source.toString('base64');
const logPacket = {jsonrpc:'2.0', method:'notifications/message', params:{level:'info',data:'SYNTHETIC_ONLY'}};
const line = packet => JSON.stringify(packet) + '\n';

function run(script, {preload=true, options, args=[]} = {}) {
  const env = {...process.env};
  delete env.NODE_OPTIONS;
  if (preload) env.NODE_OPTIONS = option;
  if (options !== undefined) env.NODE_OPTIONS = options;
  const result = spawnSync(process.execPath, [...args, '--input-type=module', '-e', script], {
    env, encoding:'utf8', timeout:5000, maxBuffer:2*1024*1024,
  });
  assert.equal(result.error, undefined, result.error?.name);
  assert.equal(result.status, 0, result.stderr);
  return result.stdout;
}

test('only no-ID logging notifications are removed; replies and other notifications retain exact bytes', () => {
  const retained = [
    {jsonrpc:'2.0',id:0,result:{text:'notifications/message remains tool data'}},
    {jsonrpc:'2.0',id:'echo',error:{code:-32000,message:'SYNTHETIC_ERROR'}},
    ...['progress','tools/list_changed','resources/list_changed','resources/updated',
      'prompts/list_changed','cancelled'].map(name => ({jsonrpc:'2.0',method:'notifications/'+name,params:{}})),
    {...logPacket,id:0}, {...logPacket,id:null},
  ];
  const script = `const retained=${JSON.stringify(retained)};
    for (const level of ['debug','info','notice','warning','error','critical','alert','emergency']) {
      process.stdout.write(JSON.stringify({...${JSON.stringify(logPacket)},params:{level,data:'SYNTHETIC_ONLY'}})+'\\n');
    }
    for (const packet of retained) process.stdout.write(JSON.stringify(packet)+'\\n');`;
  assert.equal(run(script), retained.map(line).join(''));
});

test('a transport that captures and replaces stdout.write still cannot flood the tunnel', () => {
  const result = {jsonrpc:'2.0',id:7,result:{ok:true}};
  const progress = {jsonrpc:'2.0',method:'notifications/progress',params:{progressToken:'fixture',progress:1}};
  const script = `const saved=process.stdout.write;
    process.stdout.write=function(...args){ return Reflect.apply(saved,this,args); };
    for(let i=0;i<610;i++) saved.call(process.stdout,JSON.stringify(${JSON.stringify(logPacket)})+'\\n');
    saved.call(process.stdout,JSON.stringify(${JSON.stringify(progress)})+'\\n');
    process.stdout.write(JSON.stringify(${JSON.stringify(result)})+'\\n');`;
  assert.equal(run(script), line(progress)+line(result));
});

test('fragmented, batched, malformed and non-MCP output is byte-preserving', () => {
  const log = line(logPacket);
  const writes = [log.slice(0,17),log.slice(17), log+log, '{bad-json}\n',
    'plain stdout\n', JSON.stringify(logPacket), '\n',
    line({...logPacket,jsonrpc:'1.0'}), 'null\n', '[]\n'];
  const script = `for (const text of ${JSON.stringify(writes)}) process.stdout.write(text);`;
  assert.equal(run(script), writes.join(''));
});

test('Buffer logging is filtered and Unicode replies retain their bytes', () => {
  const reply = {jsonrpc:'2.0',id:9,result:{text:'тест 🧪'}};
  const script = `process.stdout.write(Buffer.from(${JSON.stringify(line(logPacket))},'utf8'));
    process.stdout.write(Buffer.from(${JSON.stringify(line(reply))},'utf8'));`;
  assert.equal(run(script),line(reply));
});

test('callbacks and return values remain usable for discarded writes', () => {
  const script = `let done=0;
    const packet=${JSON.stringify(line(logPacket))};
    const a=process.stdout.write(packet,()=>done++);
    const b=process.stdout.write(packet,'utf8',()=>done++);
    const c=process.stdout.write(Buffer.from(packet),()=>done++);
    await new Promise(resolve=>setImmediate(resolve));
    process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:10,result:{done,a,b,c}})+'\\n');`;
  const result=JSON.parse(run(script)).result;
  assert.deepEqual(result,{done:3,a:true,b:true,c:true});
});

test('invalid argument and encoding behaviour is delegated to Node', () => {
  const script = `const outcomes=[];
    for(const args of [[${JSON.stringify(line(logPacket))},'not-an-encoding'],
      [${JSON.stringify(line(logPacket))},'utf8',123],[123]]) {
      try { process.stdout.write(...args); outcomes.push('no-error'); }
      catch(error) { outcomes.push(error.code); }
    }
    process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:11,result:outcomes})+'\\n');`;
  assert.equal(run(script),run(script,{preload:false}));
});

test('the preload is removed from child environment and does not alter execArgv', () => {
  const script = `import {spawnSync} from 'node:child_process';
    const child=spawnSync(process.execPath,['-e',${JSON.stringify('process.stdout.write('+JSON.stringify(line(logPacket))+')')}],{encoding:'utf8'});
    process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:12,result:{
      nodeOptions:process.env.NODE_OPTIONS??null,
      inheritedImport:process.execArgv.some(x=>x.startsWith('--import')),
      childStatus:child.status,childLogs:child.stdout
    }})+'\\n');`;
  const r=JSON.parse(run(script)).result;
  assert.equal(r.nodeOptions,null);
  assert.equal(r.inheritedImport,false);
  assert.equal(r.childStatus,0);
  assert.equal(r.childLogs,line(logPacket));
});

test('an unrelated NODE_OPTIONS value is preserved when loaded via CLI', () => {
  const script = `process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:13,result:{options:process.env.NODE_OPTIONS}})+'\\n');`;
  const r=JSON.parse(run(script,{options:'--no-warnings',args:[option]})).result;
  assert.equal(r.options,'--no-warnings');
});

test('the Windows candidate embeds exactly the reviewed preload bytes', () => {
  const candidate = readFileSync(new URL('../host-g2/runtime-api-migration/repo-run-tunnel-quiet-logs.candidate.ps1',import.meta.url),'utf8');
  const encoded = candidate.match(/\$fortisQuietNodeOption = '--import=data:text\/javascript;base64,([A-Za-z0-9+/=]+)'/);
  const digest = candidate.match(/\$fortisQuietPreloadSha256 = '([a-f0-9]{64})'/);
  assert.ok(encoded && digest);
  assert.deepEqual(Buffer.from(encoded[1],'base64'),source);
  assert.equal(createHash('sha256').update(source).digest('hex'),digest[1]);
  assert.ok(candidate.startsWith("param([ValidateSet('Preview','Run')][string]$Mode='Preview', [switch]$RestartRepo1)"));
  assert.ok(candidate.includes("'--log.http-raw-unsafe=false'"));
  const preview = candidate.indexOf("if ($Mode -eq 'Preview')");
  const compatibility = candidate.indexOf('$fortisQuietRaw = &');
  const startup = candidate.indexOf('& $fortisRuntime run --profile');
  assert.ok(compatibility < preview && preview < startup);
  assert.ok(preview < candidate.indexOf('    Stop-RepoAccess'));
  assert.equal(candidate.match(/^    Stop-RepoAccess$/gm)?.length,1);
});

test('the candidate retains every prior confinement, identity and bootstrap guard', () => {
  const folder=new URL('../host-g2/runtime-api-migration/',import.meta.url);
  const original=readFileSync(new URL('repo-run-tunnel-two-profile-reboot.candidate.ps1',folder),'utf8').replaceAll('\r\n','\n');
  let candidate=readFileSync(new URL('repo-run-tunnel-quiet-logs.candidate.ps1',folder),'utf8').replaceAll('\r\n','\n');
  const start=candidate.indexOf('# PR-A-17: log-only preload');
  const end=candidate.indexOf('# The pinned controller is dot-sourced;',start);
  assert.ok(start>0 && end>start);
  candidate=candidate.slice(0,start)+candidate.slice(end);
  candidate=candidate.replace("param([ValidateSet('Preview','Run')][string]$Mode='Preview', [switch]$RestartRepo1)",
    "param([ValidateSet('Preview','Run')][string]$Mode='Run')");
  candidate=candidate.replace('# PR-A-17 CANDIDATE. Source only; NOT installed. Side-by-side Repo1 quiet-log canary.',
    '# PR-A-15 CANDIDATE. Source only; NOT installed. Owner-gated two-profile boot repair.');
  candidate=candidate.replace("        QuietPreloadProbe = 'PASS'; QuietPreloadSha256 = $fortisQuietPreloadSha256\n",'');
  candidate=candidate.replace(/# Canary is a warm-run logging change[\s\S]*?(?=# Never repair or launch a second runtime)/,'');
  candidate=candidate.replace("$mcpCommand = 'command=docker exec -i --env NODE_OPTIONS=' + $fortisQuietNodeOption + ' fortis-repo-test /usr/local/bin/node /opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'",
    "$mcpCommand = 'command=docker exec -i fortis-repo-test /usr/local/bin/node /opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'");
  candidate=candidate.replace(/\$fortisQuietRunId = \[Guid\]::NewGuid\(\)\.ToString\('N'\)\n[\s\S]*?Write-Host 'Starting pinned direct Desktop Commander with the quiet-log canary\.'/,
    "Write-Host 'Starting pinned direct Desktop Commander using existing repo-mode runtime.'");
  candidate=candidate.replace(" --log.level debug --log.format json --log.file $fortisQuietLogFile '--log.http-raw-unsafe=false'",'');
  assert.equal(candidate,original);
});
