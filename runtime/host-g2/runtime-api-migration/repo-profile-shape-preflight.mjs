import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const REPO_ID='tunnel_6ac9e4dc9e688191ae1838e858424e8d';
const EXPECTED_COMMAND='docker exec -i fortis-repo-test node /workspace/repo/.fortis/mcp-bridge.mjs';
const obj=v=>v && typeof v==='object' && !Array.isArray(v);
const active=v=>v!==undefined && v!==null && String(v).trim()!=='';
const ref=v=>!active(v)?'ABSENT':typeof v!=='string'?'INVALID':v.startsWith('file:')?'FILE_REFERENCE':v.startsWith('env:')?'ENV_REFERENCE':'LITERAL';
function publicOrigin(v){
 if(!active(v))return true;
 if(ref(v)!=='LITERAL')return null;
 try {const u=new URL(v);return u.origin==='https://api.openai.com' && !u.username && !u.password && !u.search && (!u.pathname || u.pathname==='/');}catch{return false;}
}
function defaultPrefix(v){return !active(v) || (ref(v)==='LITERAL' ? /^\/?$/.test(v):null);}
function loopback(v){
 if(!active(v))return true;
 if(ref(v)!=='LITERAL')return null;
 return /^(127\.0\.0\.1|localhost|\[::1\]):[0-9]{1,5}$/.test(v);
}
export function classifyProfile(c,env={}){
 if(!obj(c))return {Complete:false,Error:'INVALID_PROFILE_ROOT'};
 const cp=obj(c.control_plane)?c.control_plane:{},m=obj(c.mcp)?c.mcp:{};
 const h=obj(c.harpoon)?c.harpoon:{},health=obj(c.health)?c.health:{};
 const a=obj(c.admin_ui)?c.admin_ui:{},proxy=obj(c.proxy)?c.proxy:{};
 const log=obj(c.log)?c.log:{},cloud=obj(c.cloudflared)?c.cloudflared:{};
 const conflicts=[],review=[];
 const count=(v,name)=>{if(v===undefined || v===null)return 0;if(!Array.isArray(v)){review.push(name+'_SHAPE');return null;}return v.length;};
 const serverCount=count(m.server_urls,'MCP_HTTP_BINDINGS');
 const commandCount=count(m.commands,'MCP_COMMANDS');
 const targetCount=count(h.targets,'HARPOON_TARGETS');
 if(a.allow_remote===true)conflicts.push('ADMIN_ALLOW_REMOTE');
 if(a.open_browser===true)conflicts.push('ADMIN_OPEN_BROWSER');
 if(a.log_buffer_events!==undefined && a.log_buffer_events!==2000)conflicts.push('ADMIN_LOG_BUFFER_NONDEFAULT');
 if(h.capture_payloads===true)conflicts.push('HARPOON_CAPTURE_PAYLOADS');
 if(active(proxy.check_interval) && !['60s','1m','1m0s','60000ms'].includes(String(proxy.check_interval)))review.push('PROXY_INTERVAL_NATIVE_VALIDATION');
 if(active(cloud.token) || cloud.managed===true || active(cloud.path))review.push('CLOUDFLARED_CONFIGURATION');
 const cpOrigin=publicOrigin(cp.base_url),cpPrefix=defaultPrefix(cp.url_path);
 if(cpOrigin!==true)review.push('CONTROL_PLANE_ORIGIN_NONDEFAULT_OR_REFERENCE');
 if(cpPrefix!==true)review.push('CONTROL_PLANE_PREFIX_NONDEFAULT_OR_REFERENCE');
 if(serverCount!==0)review.push('ADDITIONAL_HTTP_BINDINGS');
 if(targetCount!==0)review.push('HARPOON_TARGET_LABELS');
 if(loopback(health.listen_addr)!==true || active(health.unix_socket))review.push('HEALTH_TRANSPORT_NONDEFAULT_OR_REFERENCE');
 if(log.http_raw_unsafe===true)review.push('RAW_HTTP_LOGGING_ENABLED');
 const knownTop=new Set(['config_version','ca_bundle','http_proxy','control_plane','log','health','admin_ui','process','cloudflared','mcp','harpoon','proxy']);
 const unknownTop=Object.keys(c).filter(k=>!knownTop.has(k)).length;
 if(unknownTop)review.push('UNKNOWN_TOP_LEVEL_FIELDS');
 const envNames=['TUNNEL_CLIENT_PROFILE_DIR','TUNNEL_CLIENT_CONFIG','TUNNEL_CLIENT_PROFILE_FILE','MCP_SERVER_URL','MCP_COMMAND','MCP_SERVER_MAIN_URL','CONTROL_PLANE_BASE_URL','CONTROL_PLANE_URL_PATH','HARPOON_TARGETS','HARPOON_ADDITIONAL_TRANSPORTS','OTEL_RESOURCE_ATTRIBUTES','OTEL_SERVICE_NAME','HEALTH_LISTEN_ADDR','HEALTH_UNIX_SOCKET'];
 const present={};for(const k of envNames)present[k]=active(env[k]);
 for(const k of ['MCP_SERVER_URL','MCP_SERVER_MAIN_URL','CONTROL_PLANE_BASE_URL','CONTROL_PLANE_URL_PATH','HARPOON_TARGETS','OTEL_RESOURCE_ATTRIBUTES','HEALTH_UNIX_SOCKET'])if(present[k])review.push('OBSERVER_ENV_'+k);
 if(present.TUNNEL_CLIENT_CONFIG || present.TUNNEL_CLIENT_PROFILE_FILE)review.push('CONFIG_SOURCE_ENV_CONFLICT_REQUIRES_NATIVE_PRECEDENCE_CHECK');
 const matches=cp.tunnel_id===REPO_ID;
 if(!matches)review.push('PROFILE_TUNNEL_ID_NOT_LITERAL_EXPECTED');
 return {
  Complete:true,ProfileTunnelIdMatches:matches,ConfigVersion:c.config_version??null,
  MainTransportForFixedCandidate:'STDIO_COMMAND_OVERRIDE',ProfileMcpHttpBindingCount:serverCount,
  ProfileCommandCount:commandCount,ProfileCommandMatchesFixed:commandCount===1 && m.commands[0]?.command===EXPECTED_COMMAND,
  HarpoonTargetCount:targetCount,ControlPlaneProductionOrigin:cpOrigin,ControlPlaneDefaultPrefix:cpPrefix,
  CredentialRepresentation:ref(cp.api_key),HealthLoopbackTcp:loopback(health.listen_addr),
  FullOnlyConflicts:conflicts,ReviewItems:review,UnknownTopLevelFieldCount:unknownTop,
  ObserverEnvironmentPresence:present,
  CandidateAdditionalHarpoonOverride:'EXPLICIT_EMPTY_REUSES_E08',
  NoShapeIssuesFound:conflicts.length===0 && review.length===0,
  NativeGoValidationExecuted:false
 };
}
export function summarizeText(text,yaml,env={}){
 try{return classifyProfile(yaml.load(text,{schema:yaml.JSON_SCHEMA}),env);}
 catch{return {Complete:false,Error:'PROFILE_PARSE_OR_CLASSIFICATION_FAILED_VALUES_WITHHELD'};}
}
function selectedProfile(env){
 const clean=v=>{
  const s=String(v).trim();
  if(s==='~' || s.startsWith('~/')){
   if(!active(env.HOME))throw Error('PROFILE_LOCATION');
   return path.win32.resolve(env.HOME,s==='~'?'':s.slice(2));
  }
  return path.win32.resolve(s);
 };
 let dir,kind;
 if(active(env.TUNNEL_CLIENT_PROFILE_DIR)){dir=clean(env.TUNNEL_CLIENT_PROFILE_DIR);kind='EXPLICIT_PROFILE_DIRECTORY_ENV';}
 else if(active(env.XDG_CONFIG_HOME)){dir=path.win32.join(clean(env.XDG_CONFIG_HOME),'tunnel-client');kind='XDG_CONFIG_HOME';}
 else if(active(env.HOME)){dir=path.win32.join(clean(env.HOME),'.config','tunnel-client');kind='HOME_CONFIG';}
 else if(active(env.APPDATA)){dir=path.win32.join(clean(env.APPDATA),'tunnel-client');kind='WINDOWS_USER_CONFIG';}
 else throw Error('PROFILE_LOCATION');
 return {file:path.win32.join(dir,'repo-mode.yaml'),kind};
}
function run(){
 if(process.platform!=='win32')throw Error('WINDOWS_REQUIRED');
 const p=selectedProfile(process.env);
 if(fs.statSync(p.file).size>131072)throw Error('PROFILE_SIZE');
 const bytes=fs.readFileSync(p.file);
 const require=createRequire(import.meta.url);
 const yaml=require('C:\\Tools\\desktop-commander\\node_modules\\js-yaml');
 const result=summarizeText(bytes.toString('utf8'),yaml,process.env);
 return {Check:'REPO_NAMED_PROFILE_SHAPE_PREFLIGHT',Utc:new Date().toISOString(),
  ProfileName:'repo-mode',ProfileLocationKind:p.kind,ProfileSHA256:crypto.createHash('sha256').update(bytes).digest('hex').toUpperCase(),
  Parser:'EXISTING_JS_YAML_JSON_SCHEMA',Result:result,
  Scope:'NAMED_PROFILE_AND_CURRENT_OWNER_OBSERVER_ENV_FOR_NEXT_LAUNCH',
  RunningProcessEnvironmentRead:false,ProfileParsedLocally:true,CredentialReferencesResolved:false,
  CredentialFilesOpened:0,ProfileOrEnvironmentValuesPrinted:false,
  NetworkRequests:0,FilesChanged:0,RuntimeRestarted:false,
  Limits:['Not the native Go config loader','Existing process environment not reconstructed','Does not prove actual runtime-only MCP compatibility']};
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href){
 try{console.log(JSON.stringify(run()));}catch{console.log(JSON.stringify({Check:'REPO_NAMED_PROFILE_SHAPE_PREFLIGHT',Complete:false,Error:'LOCAL_PREFLIGHT_FAILED_DETAILS_WITHHELD',FilesChanged:0,RuntimeRestarted:false}));process.exitCode=1;}
}
