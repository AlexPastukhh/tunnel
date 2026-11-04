import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {pathToFileURL} from 'node:url';

export const REPO_GUIDANCE="Fortis Repo is a general code and repository workspace, not a website-building workflow. Plugin activation is not a request to start a project. Follow the user's requested task. The backend is a Linux Docker container. Verified workspace layout in the current environment: /workspace/repo is the root of the persistent fortis-repo-workspace ext4 volume; /workspace/repos is its Repos subpath; /workspace/files is its Workfiles subpath. All three mounts are read-write. /workspace/repo/Repos and /workspace/repos resolve to the same directory; /workspace/repo/Workfiles and /workspace/files resolve to the same directory. These are not independent Windows bind mounts or separate security domains. Use absolute Linux paths and explicitly cd to the selected project; the default working directory is /workspace/repos. Files are shared by authorized processes with access to the workspace; do not assume agent isolation from MCP tool allowlists. Container hardening, Docker socket access, network membership and published ports are not inferred by this message; inspect the exact runtime before making claims or changing it. Verify connectivity and Git authentication before remote operations; never infer authentication from a configured helper or remote. Do not print credentials, place them in commands or logs, or expose private workspace paths. The published Fortis Repo Mode Site is a separate status page, not the source of this native Tunnel connection. Do not run generic onboarding or open feedback pages unless requested. After an uncertain mutation result, check actual state before retrying. Host-created linked worktrees can contain Windows absolute paths and be outside these mounts. Do not prune, repair, or rewrite their metadata solely because Linux cannot resolve those paths; manage them through their owning host Git workflow.";

function stripLegacyUi(value) {
  if(!value || typeof value!=='object' || !value._meta) return value;
  const out={...value}, meta={...value._meta};
  for(const key of Object.keys(meta)) if(key==='ui'||key.startsWith('ui/')||['openai/outputTemplate','openai/widgetAccessible'].includes(key)) delete meta[key];
  if(Object.keys(meta).length) out._meta=meta; else delete out._meta;
  return out;
}

export function presentResponse(message,request) {
  if(!message.result || !request) return message;
  let result=message.result;
  if(request.method==='initialize') {
    const capabilities={...result.capabilities}; delete capabilities.resources;
    result={...result,capabilities,serverInfo:{...result.serverInfo,name:'fortis-repo'},instructions:REPO_GUIDANCE};
  }
  if(request.method==='tools/list') result={...result,tools:result.tools.map(tool=>{
    let description=tool.description||'';
    description=description.replace(/PATH TRANSLATION IN DOCKER:[\s\S]*?(?=Container:)/g,'Verified workspace layout (2026-11-03): /workspace/repo is the root of the persistent fortis-repo-workspace ext4 volume; /workspace/repos is its Repos subpath; /workspace/files is its Workfiles subpath. All three mounts are read-write in this environment. These are not independent Windows bind mounts. Use absolute Linux paths.\n');
    return {...stripLegacyUi(tool),description:description+"\nFortis Repo: Linux Docker workspace. /workspace/repo is the root of the persistent fortis-repo-workspace ext4 volume; /workspace/repos (Repos) and /workspace/files (Workfiles) are read-write subpaths of that same volume in this environment, not independent Windows bind mounts. Files are shared by authorized processes with workspace access; tool allowlists are not OS isolation. Verify network connectivity and Git authentication per operation; never assume credentials."};
  })};
  // Keep operation results, false values, errors and structured content unchanged.
  return {...message,result};
}

export function runBridge() {
  const child=spawn(process.execPath,['/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'],{stdio:['pipe','pipe','pipe']});
  const requests=new Map();
  const send=message=>process.stdout.write(JSON.stringify(message)+'\n');
  const input=createInterface({input:process.stdin});
  const output=createInterface({input:child.stdout});
  child.stderr.on('data',()=>{}); // Upstream config diagnostics can contain call data.
  input.on('line',line=>{
    let request;try{request=JSON.parse(line);}catch{send({jsonrpc:'2.0',id:null,error:{code:-32700,message:'Parse error'}});return;}
    if(request.method==='resources/list'||request.method==='resources/templates/list') {
      if(request.id!==undefined)send({jsonrpc:'2.0',id:request.id,result:request.method==='resources/list'?{resources:[]}:{resourceTemplates:[]}});
      return;
    }
    if(request.method==='resources/read') {
      if(request.id!==undefined)send({jsonrpc:'2.0',id:request.id,error:{code:-32602,message:'Legacy UI resources are disabled in Fortis Repo'}});
      return;
    }
    if(request.id!==undefined) requests.set(request.id,request);
    // Forward once, preserving all original arguments and request metadata.
    child.stdin.write(line+'\n');
  });
  output.on('line',line=>{
    let message;try{message=JSON.parse(line);}catch{process.stderr.write('Fortis Repo: invalid upstream protocol output\n');return;}
    const request=requests.get(message.id);requests.delete(message.id);
    send(presentResponse(message,request));
  });
  input.on('close',()=>child.stdin.end());
  child.on('error',()=>{process.stderr.write('Fortis Repo: failed to start MCP backend\n');process.exitCode=1;input.close();process.stdin.destroy();});
  child.on('exit',code=>{process.exitCode=code??1;input.close();process.stdin.destroy();});
  for(const signal of ['SIGINT','SIGTERM']) process.on(signal,()=>{child.kill(signal);input.close();process.stdin.destroy();});
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) runBridge();
