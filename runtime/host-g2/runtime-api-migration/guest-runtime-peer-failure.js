'use strict';
// Synthetic loopback-only MCP peer failure. Never loads real profiles or keys.
const fs=require('fs'),path=require('path'),http=require('http'),cp=require('child_process'),rl=require('readline');
const root=process.argv[2]==='stdio'?process.argv[3]:process.argv[2];
if(!root||!path.isAbsolute(root))throw new Error('Absolute synthetic root required');
const resultPath=path.join(root,'worker-result.json');
if(process.argv[2]==='stdio'){
 fs.writeFileSync(path.join(root,'mcp-child.json'),JSON.stringify({pid:process.pid,synthetic:true}),{flag:'wx'});
 process.on('exit',code=>fs.writeFileSync(path.join(root,'mcp-child-exit.json'),JSON.stringify({pid:process.pid,code})));
 const timer=setTimeout(()=>process.exit(88),25000);
 const input=rl.createInterface({input:process.stdin});
 input.on('line',line=>{
  let q;try{q=JSON.parse(line);}catch{return;}
  if(q.method==='tools/call'&&q.params?.name==='synthetic_crash'){
   clearTimeout(timer);process.exit(37);
  }
  if(!Object.prototype.hasOwnProperty.call(q,'id'))return;
  let result,error;
  if(q.method==='initialize')result={protocolVersion:'2025-06-18',capabilities:{tools:{}},serverInfo:{name:'fortis-synthetic-failure-peer',version:'1'}};
  else if(q.method==='tools/list')result={tools:[{name:'synthetic_echo',inputSchema:{type:'object',properties:{}}},{name:'synthetic_crash',inputSchema:{type:'object',properties:{}}}]};
  else if(q.method==='tools/call'&&q.params?.name==='synthetic_echo')result={content:[{type:'text',text:'FORTIS_SYNTHETIC_READY'}]};
  else error={code:-32601,message:'Synthetic method unavailable'};
  process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:q.id,...(error?{error}:{result})})+'\n');
 });
 process.stdin.on('end',()=>process.exit(0));
}else{
 (async()=>{
  const runtime='C:\\Tools\\tunnel-client\\runtime\\v0.0.15\\tunnel-client-runtime.exe';
  const tunnel='tunnel_00000000000000000000000000000029',key='FORTIS_SYNTHETIC_FAILURE_ONLY';
  const state={check:'G2_SYNTHETIC_MCP_PEER_FAILURE',startedUtc:new Date().toISOString(),fixturePid:process.pid,
   synthetic:true,externalControlPlaneUsed:false,realProfilesRead:false,realKeysUsed:false,pass:false};
  let server,child,timeout,done=false,index=0,awaiting=null,session=null;
  const sockets=new Set();
  const save=()=>fs.writeFileSync(resultPath,JSON.stringify(state,null,2));
  const messages=[
   {jsonrpc:'2.0',id:'init',method:'initialize',params:{protocolVersion:'2025-06-18',capabilities:{},clientInfo:{name:'fortis-synthetic-failure',version:'1'}}},
   {jsonrpc:'2.0',method:'notifications/initialized'},
   {jsonrpc:'2.0',id:'list',method:'tools/list',params:{}},
   {jsonrpc:'2.0',id:'echo',method:'tools/call',params:{name:'synthetic_echo',arguments:{}}},
   {jsonrpc:'2.0',id:'crash',method:'tools/call',params:{name:'synthetic_crash',arguments:{}}}
  ];
  function finish(error){
   if(done)return;done=true;clearTimeout(timeout);
   if(error)state.error=String(error);
   state.completedUtc=new Date().toISOString();save();
   if(server){server.close();for(const socket of sockets)socket.destroy();}
   // Parent Job is the bounded cleanup fallback. Never terminate unrelated PIDs.
   process.exit(state.pass?0:1);
  }
  const json=(res,code,v)=>{if(res.destroyed)return;res.writeHead(code,{'Content-Type':'application/json'});res.end(JSON.stringify(v));};
  try{
   server=http.createServer((req,res)=>{
    const u=new URL(req.url,'http://127.0.0.1');
    if(req.headers.authorization!=='Bearer '+key){json(res,401,{error:'synthetic auth required'});return;}
    if(u.pathname==='/v1/tunnels/'+tunnel+'/poll'&&req.method==='GET'){
     if(!awaiting&&index<messages.length){
      const n=index++,headers={'Content-Type':['application/json'],'Accept':['application/json']};
      if(session)headers['Mcp-Session-Id']=[session];
      awaiting='failure-fixture-'+n;
      if(n===4){state.crashIssuedUtc=new Date().toISOString();state.crashIssued=true;save();}
      json(res,200,{commands:[{request_id:awaiting,shard_token:'synthetic-'+n,command_type:'jsonrpc',channel:'main',created_at:new Date().toISOString(),headers,jsonrpc:messages[n]}]});
     }else setTimeout(()=>json(res,200,{commands:[]}),100);
     return;
    }
    if(u.pathname==='/v1/tunnels/'+tunnel+'/response'&&req.method==='POST'){
     let body='';req.on('data',b=>{body+=b;if(body.length>65536)req.destroy();});
     req.on('end',()=>{
      try{
       const p=JSON.parse(body);
       if(p.request_id===awaiting){
        awaiting=null;
        for(const [name,value] of Object.entries(p.resp_headers||{}))if(name.toLowerCase()==='mcp-session-id')session=value[0];
       }
       if(p.request_id==='failure-fixture-3')state.echoReady=p.resp_code===200&&p.resp_json?.result?.content?.[0]?.text==='FORTIS_SYNTHETIC_READY';
       json(res,200,{});save();
      }catch{json(res,400,{error:'invalid synthetic payload'});}
     });return;
    }
    json(res,404,{error:'synthetic route unavailable'});
   });
   server.on('connection',socket=>{sockets.add(socket);socket.on('close',()=>sockets.delete(socket));});
   await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
   state.controlPort=server.address().port;
   const cmd='"'+process.execPath.replaceAll('\\','/')+'" "'+__filename.replaceAll('\\','/')+'" stdio "'+root.replaceAll('\\','/')+'"';
   const yaml=['config_version: 1','control_plane:','  base_url: '+JSON.stringify('http://127.0.0.1:'+state.controlPort),
    '  tunnel_id: '+tunnel,'  api_key: env:FORTIS_SYNTHETIC_FAILURE_KEY','  poll_channels: [main]',
    'mcp:','  commands:','    - channel: main','      command: '+JSON.stringify(cmd),
    'health:','  listen_addr: 127.0.0.1:0','  url_file: '+JSON.stringify(path.join(root,'health.url').replaceAll('\\','/')),
    'process:','  pid_file: '+JSON.stringify(path.join(root,'runtime.pid').replaceAll('\\','/')),
    'admin_ui:','  open_browser: false','log:','  level: error','  format: struct-text',''].join('\n');
   const config=path.join(root,'synthetic.yaml');fs.writeFileSync(config,yaml,{flag:'wx'});
   const env={};
   for(const n of ['SystemRoot','WINDIR','COMSPEC','PATH','PATHEXT'])if(process.env[n])env[n]=process.env[n];
   for(const [n,folder] of Object.entries({USERPROFILE:'home',HOME:'home',LOCALAPPDATA:'local',APPDATA:'appdata',TEMP:'tmp',TMP:'tmp'})){
    env[n]=path.join(root,folder);fs.mkdirSync(env[n],{recursive:true});
   }
   env.FORTIS_SYNTHETIC_FAILURE_KEY=key;env.DESKTOP_COMMANDER_DISABLE_MCP_UI='1';
   timeout=setTimeout(()=>{state.timedOut=true;finish('Runtime did not complete synthetic peer failure within 35 seconds');},35000);
   child=cp.spawn(runtime,['run','--config',config,'--harpoon.additional-transport='],{cwd:root,env,windowsHide:true,stdio:['ignore','ignore','pipe']});
   state.runtimePid=child.pid;save();
   let stderrBytes=0;child.stderr.on('data',b=>{stderrBytes+=b.length;});
   child.once('error',e=>finish(e.message));
   child.once('exit',(code,signal)=>{
    state.runtimeExit={code,signal,utc:new Date().toISOString()};state.stderrBytes=stderrBytes;
    try{
     state.mcpChild=JSON.parse(fs.readFileSync(path.join(root,'mcp-child.json'),'utf8'));
     state.mcpChildExit=JSON.parse(fs.readFileSync(path.join(root,'mcp-child-exit.json'),'utf8'));
     const healthFile=path.join(root,'health.url');
     if(fs.existsSync(healthFile)){
      const u=new URL(fs.readFileSync(healthFile,'utf8').trim());
      if(u.protocol!=='http:'||u.hostname!=='127.0.0.1')throw new Error('Unexpected synthetic health address');
      state.healthPort=Number(u.port);
     }
     state.pass=state.echoReady===true&&state.crashIssued===true&&state.mcpChildExit.code===37&&state.mcpChildExit.pid===state.mcpChild.pid&&code!==null;
     finish(state.pass?null:'Synthetic crash prerequisites or peer exit not established');
    }catch(e){finish(e.message);}
   });
  }catch(e){finish(e.message);}
 })().catch(e=>{fs.writeFileSync(resultPath,JSON.stringify({pass:false,error:e.message}));process.exit(1);});
}
