'use strict';
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),cp=require('node:child_process'),crypto=require('node:crypto');
const root=process.argv[2],profile=path.join(root,'profile'),output=path.join(root,'worker-result.json');
if(!path.isAbsolute(root)||!/^g2-browser-functional-[a-f0-9]{32}$/.test(path.basename(root)))throw Error('Own fixture root required');
const nonce=crypto.randomUUID(),r={check:'G2_OWN_BROWSER_CDP',utc:new Date().toISOString(),sandbox:'default',ownerProfileUsed:false,externalPageUsed:false,pass:false};
let server=null,edge=null,ws=null,exitPromise=null,finished=false;
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function save(){fs.writeFileSync(output,JSON.stringify(r));}
const watchdog=setTimeout(()=>{r.error='WORKER_DEADLINE';save();process.exit(4);},40000);
async function run(){
 try{
  server=http.createServer((req,res)=>{
   if(req.url!=='/'+nonce){res.writeHead(404);res.end();return;}
   res.writeHead(200,{'Content-Type':'text/html','Cache-Control':'no-store'});
   res.end('<!doctype html><title>Fortis G2 synthetic</title><div id="g2-marker"></div><script>localStorage.setItem("G2_SYNTHETIC",'+JSON.stringify(nonce)+');document.querySelector("#g2-marker").textContent=localStorage.getItem("G2_SYNTHETIC");</script>');
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  r.httpPort=server.address().port;
  const url='http://127.0.0.1:'+r.httpPort+'/'+nonce;
  const args=['--headless=new','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-extensions','--disable-sync','--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--user-data-dir='+profile,url];
  r.browserFlagsDisableSandbox=args.includes('--no-sandbox');
  edge=cp.spawn('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',args,{stdio:'ignore',windowsHide:true});
  r.browserPid=edge.pid;
  let spawnError=null;
  edge.once('error',e=>{spawnError=e.code||e.name;});
  exitPromise=new Promise(resolve=>edge.once('exit',()=>{finished=true;resolve();}));
  const deadline=Date.now()+22000,portFile=path.join(profile,'DevToolsActivePort');
  while(!fs.existsSync(portFile)&&Date.now()<deadline){if(spawnError)throw Error('Edge spawn '+spawnError);if(finished)throw Error('Edge early exit');await pause(100);}
  if(!fs.existsSync(portFile))throw Error('Own DevTools port file deadline');
  const port=Number(fs.readFileSync(portFile,'utf8').split('\n')[0]);
  if(!Number.isInteger(port)||port<1||port>65535)throw Error('Invalid own CDP port');
  r.cdpPort=port;
  let page;
  while(Date.now()<deadline){
   const list=await fetch('http://127.0.0.1:'+port+'/json/list',{signal:AbortSignal.timeout(2500)}).then(response=>response.json());
   page=list.find(item=>item.type==='page'&&item.url===url);
   if(page)break;await pause(100);
  }
  if(!page||!page.webSocketDebuggerUrl.startsWith('ws://127.0.0.1:'+port+'/'))throw Error('Own synthetic target missing');
  ws=new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Own CDP open timeout')),3000);ws.onopen=()=>{clearTimeout(timer);resolve();};ws.onerror=()=>{clearTimeout(timer);reject(Error('Own CDP open error'));};});
  let next=1;const pending=new Map();
  ws.onmessage=event=>{const msg=JSON.parse(event.data);if(pending.has(msg.id)){const item=pending.get(msg.id);pending.delete(msg.id);clearTimeout(item.timer);msg.error?item.reject(Error('CDP '+msg.error.code)):item.resolve(msg.result);}};
  function call(method,params={}){return new Promise((resolve,reject)=>{const id=next++;const timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP method timeout '+method));},3000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));});}
  let loaded=false;
  for(let i=0;i<40;i++){
   const state=await call('Runtime.evaluate',{expression:'document.readyState==="complete"&&document.querySelector("#g2-marker")!==null',returnByValue:true});
   if(state.result.value===true){loaded=true;break;}await pause(100);
  }
  if(!loaded)throw Error('Own synthetic document readiness timeout');
  r.documentReadyBeforeDom=true;
  const doc=await call('DOM.getDocument',{depth:0});
  const element=await call('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'#g2-marker'});
  r.domQuery=element.nodeId>0;
  const expression='(() => {const n='+JSON.stringify(nonce)+';return document.querySelector("#g2-marker").textContent===n&&localStorage.getItem("G2_SYNTHETIC")===n;})()';
  const evaluated=await call('Runtime.evaluate',{expression,returnByValue:true});
  r.storageAndDomExact=evaluated.result.value===true&&!evaluated.exceptionDetails;
  const before=await call('Runtime.evaluate',{expression:'performance.timeOrigin',returnByValue:true});
  if(typeof before.result.value!=='number')throw Error('Own document identity missing');
  await call('Page.reload',{ignoreCache:true});
  let persisted=false;
  const afterExpression='performance.timeOrigin!=='+JSON.stringify(before.result.value)+'&&document.readyState==="complete"&&('+expression+')';
  for(let i=0;i<40;i++){
   try{
    const value=await call('Runtime.evaluate',{expression:afterExpression,returnByValue:true});
    if(value.result.value===true&&!value.exceptionDetails){persisted=true;break;}
   }catch(error){if(error.message!=='CDP -32000')throw error;}
   await pause(100);
  }
  r.newDocumentAfterReload=persisted;r.storageAfterReload=persisted;
  ws.send(JSON.stringify({id:10000,method:'Browser.close'}));
  r.browserCloseRequested=true;
  await Promise.race([exitPromise,pause(4000)]);
  r.browserExitedBeforeJobStop=finished;
  r.pass=r.domQuery&&r.storageAndDomExact&&r.storageAfterReload&&finished&&!r.browserFlagsDisableSandbox;
 }catch(error){r.error=error.message;r.pass=false;}
 finally{
  if(ws)ws.close();
  if(server){server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
  clearTimeout(watchdog);
  save();process.exitCode=r.pass?0:3;
 }
}
run();
