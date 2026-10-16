'use strict';
// Synthetic-only fixture: no real tunnel, profile, key or command execution.
const fs=require('fs'),path=require('path'),http=require('http');
const cp=require('child_process'),rl=require('readline');
if(process.argv[2]==='stdio'){
 const input=rl.createInterface({input:process.stdin});
 input.on('line',line=>{
  let q;try{q=JSON.parse(line);}catch{return;}
  if(!Object.prototype.hasOwnProperty.call(q,'id'))return;
  let result,error;
  if(q.method==='initialize')result={protocolVersion:'2025-06-18',capabilities:{tools:{}},serverInfo:{name:'fortis-synthetic-echo',version:'1'}};
  else if(q.method==='tools/list')result={tools:[{name:'synthetic_echo',description:'Return a fixed synthetic marker',inputSchema:{type:'object',properties:{},additionalProperties:false}}]};
  else if(q.method==='tools/call'&&q.params.name==='synthetic_echo')result={content:[{type:'text',text:'FORTIS_G3_SYNTHETIC_OK'}],isError:false};
  else if(q.method==='ping')result={};
  else error={code:-32601,message:'Synthetic method unavailable'};
  process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:q.id,...(error?{error}:{result})})+'\n');
 });
 process.stdin.on('end',()=>process.exit(0));
}else{
 const dir=__dirname,exe=path.join(dir,'artifact','tunnel-client-runtime.exe');
 const key='FORTIS_G3_SYNTHETIC_ONLY',id='tunnel_00000000000000000000000000000003';
 const state={startedAt:new Date().toISOString(),fixturePID:process.pid,synthetic:true,controlRequests:[],responses:[],routes:[],status:'STARTING'};
 let child,ending=false,next=0,awaiting=null,session=null,stderr='';
 const messages=[
  {jsonrpc:'2.0',id:'init',method:'initialize',params:{protocolVersion:'2025-06-18',capabilities:{},clientInfo:{name:'fortis-fixture',version:'1'}}},
  {jsonrpc:'2.0',method:'notifications/initialized'},
  {jsonrpc:'2.0',id:'list',method:'tools/list',params:{}},
  {jsonrpc:'2.0',id:'echo',method:'tools/call',params:{name:'synthetic_echo',arguments:{}}}
 ];
 const save=()=>fs.writeFileSync(path.join(dir,'state.json'),JSON.stringify(state,null,2));
 const json=(res,code,value)=>{res.writeHead(code,{'Content-Type':'application/json'});res.end(JSON.stringify(value));};
 async function shutdown(reason){
  if(ending)return;ending=true;
  state.shutdownReason=reason;state.stoppedAt=new Date().toISOString();
  if(child&&child.exitCode===null)child.kill();
  state.status=state.status==='READY'?'STOPPED':state.status;save();
  server.close();setTimeout(()=>process.exit(0),1000);
 }
 const server=http.createServer((req,res)=>{
  if(req.url==='/fixture-stop'&&req.method==='POST'){json(res,200,{stopping:true});shutdown('owner synthetic stop');return;}
  const u=new URL(req.url,'http://127.0.0.1');
  state.controlRequests.push({method:req.method,path:u.pathname,syntheticAuth:req.headers.authorization==='Bearer '+key});
  if(req.headers.authorization!=='Bearer '+key){json(res,401,{error:'synthetic auth required'});return;}
  if(u.pathname==='/v1/tunnels/'+id+'/poll'&&req.method==='GET'){
   if(!awaiting&&next<messages.length){
    const n=next++,headers={'Content-Type':['application/json'],'Accept':['application/json']};
    if(session)headers['Mcp-Session-Id']=[session];
    awaiting='fixture-'+n;
    json(res,200,{commands:[{request_id:awaiting,shard_token:'synthetic-'+n,command_type:'jsonrpc',channel:'main',created_at:new Date().toISOString(),headers,jsonrpc:messages[n]}]});
   }else setTimeout(()=>{if(!res.destroyed)json(res,200,{commands:[]});},200);
   return;
  }
  if(u.pathname==='/v1/tunnels/'+id+'/response'&&req.method==='POST'){
   let body='';req.on('data',c=>body+=c);
   req.on('end',()=>{
    try{
     const p=JSON.parse(body);
     state.responses.push({requestID:p.request_id,code:p.resp_code,type:p.resp_type,result:p.resp_json});
     if(p.request_id===awaiting){awaiting=null;const h=p.resp_headers||{};for(const name of Object.keys(h))if(name.toLowerCase()==='mcp-session-id')session=h[name][0];}
     json(res,200,{});save();
    }catch(e){json(res,400,{error:'invalid synthetic response'});}
   });return;
  }
  json(res,404,{error:'synthetic fixture route unavailable'});
 });
 const request=(url,method='GET',body)=>new Promise((resolve,reject)=>{
  const req=http.request(url,{method,headers:body?{'Content-Type':'application/json'}:{}},res=>{let b='';res.on('data',c=>b+=c);res.on('end',()=>resolve({method,path:new URL(url).pathname,status:res.statusCode,body:b}));});
  req.on('error',reject);req.setTimeout(2000,()=>req.destroy(new Error('probe timeout')));
  req.end(body);
 });
 server.listen(0,'127.0.0.1',async()=>{
  const base='http://127.0.0.1:'+server.address().port;
  state.controlBase=base;
  const node=process.execPath.replaceAll('\\','/'),self=__filename.replaceAll('\\','/');
  const cmd='"'+node+'" "'+self+'" stdio';
  const yaml=['config_version: 1','control_plane:','  base_url: '+JSON.stringify(base),'  tunnel_id: '+id,'  api_key: env:FORTIS_G3_SYNTHETIC_KEY','  poll_channels: [main]','mcp:','  commands:','    - channel: main','      command: '+JSON.stringify(cmd),'health:','  listen_addr: 127.0.0.1:0','  url_file: '+JSON.stringify(path.join(dir,'health.url').replaceAll('\\','/')),'process:','  pid_file: '+JSON.stringify(path.join(dir,'runtime.pid').replaceAll('\\','/')),'admin_ui:','  open_browser: false','log:','  level: error','  format: struct-text',''].join('\n');
  fs.writeFileSync(path.join(dir,'synthetic.yaml'),yaml);
  const env={};
  for(const name of ['SystemRoot','WINDIR','COMSPEC','TEMP','TMP','PATH','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA'])if(process.env[name])env[name]=process.env[name];
  env.FORTIS_G3_SYNTHETIC_KEY=key;env.DESKTOP_COMMANDER_DISABLE_MCP_UI='1';env.HARPOON_ADDITIONAL_TRANSPORTS='http-streamable';
  state.transportOverride={inherited:'http-streamable',flag:'--harpoon.additional-transport='};
  child=cp.spawn(exe,['run','--config',path.join(dir,'synthetic.yaml'),'--harpoon.additional-transport='],{cwd:dir,env,windowsHide:true,stdio:['ignore','pipe','pipe']});
  state.runtimePID=child.pid;
  child.stderr.on('data',b=>{stderr=(stderr+b.toString()).slice(-6000);});
  child.stdout.on('data',()=>{});
  child.on('error',e=>{state.status='ERROR';state.error=e.message;save();shutdown('spawn error');});
  child.on('exit',(code,signal)=>{state.exit={code,signal};save();if(!ending){state.status='ERROR';state.error=stderr;save();shutdown('unexpected test runtime exit');}});
  save();
  try{
   const deadline=Date.now()+45000;
   while(Date.now()<deadline){
    if(ending)return;
    if(fs.existsSync(path.join(dir,'health.url'))&&state.responses.some(r=>r.requestID==='fixture-3')){
     const health=fs.readFileSync(path.join(dir,'health.url'),'utf8').trim();
     state.healthBase=health;
     for(const p of ['/healthz','/readyz','/health','/metrics','/','/ui','/api/status','/api/system','/api/oauth','/api/logs','/api/logs/export','/api/logs/stream','/api/log-level','/api/harpoon/status','/api/harpoon/targets','/api/harpoon/calls','/api/codex/status','/api/codex/events','/harpoon/mcp']){
      const r=await request(health+p);state.routes.push({method:r.method,path:r.path,status:r.status});
     }
     for(const p of ['/api/log-level','/api/codex/login/device','/api/codex/login/cancel','/api/codex/thread/start','/api/codex/turn/start']){
      const r=await request(health+p,p==='/api/log-level'?'PUT':'POST','{}');state.routes.push({method:r.method,path:r.path,status:r.status});
     }
     const echo=state.responses.find(r=>r.requestID==='fixture-3');
     if(echo.code!==200||echo.result?.result?.content?.[0]?.text!=='FORTIS_G3_SYNTHETIC_OK')throw new Error('Echo round trip failed');
     if(state.routes.some(r=>r.status!==(r.path.startsWith('/health')||r.path==='/readyz'||r.path==='/metrics'?200:404)))throw new Error('Unexpected test HTTP route');
     state.status='READY';save();console.log(JSON.stringify(state));return;
    }
    await new Promise(r=>setTimeout(r,250));
   }
   throw new Error('Synthetic runtime readiness timeout: '+stderr);
  }catch(e){state.status='ERROR';state.error=e.message;save();console.log(JSON.stringify(state));shutdown('test failure');}
 });
 setTimeout(()=>shutdown('synthetic fixture TTL'),480000);
}