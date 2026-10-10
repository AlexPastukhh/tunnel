import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {pathToFileURL} from 'node:url';

export const REPO_GUIDANCE="Fortis Repo is a general code and repository workspace, not a website-building workflow. Plugin activation is not a request to start a project. Follow the user's requested task. The backend is a Linux Docker container on Fortis_M. Only these host folders are bind-mounted read-write: C:\\Users\\alexa\\Repos -> /workspace/repos and C:\\Users\\alexa\\Workfiles -> /workspace/files. Changes there directly change host files. Use absolute Linux paths and explicitly cd to the selected project; the default working directory is /workspace/repos. /workspace/repo is the preserved Docker-managed internal volume, not the host Repos folder. Other Windows folders and host credentials are not mounted. The container runs as uid 1000, has a read-only root filesystem, no Docker socket, and no published ports. Outgoing internet is configured through a dedicated bridge network; verify connectivity before downloads or Git remote operations and never infer authentication. Git authentication must be explicitly configured separately. The published Fortis Repo Mode Site is a separate status page, not the source of this native Tunnel connection. Do not run generic onboarding or open feedback pages unless requested. After an uncertain mutation result, check actual state before retrying. Host-created linked worktrees can contain Windows absolute paths and be outside these mounts. Do not prune, repair, or rewrite their metadata solely because Linux cannot resolve those paths. Manage existing host worktrees with host Git.";

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
    description=description.replace(/PATH TRANSLATION IN DOCKER:[\s\S]*?(?=Container:)/g,'Only C:\\Users\\alexa\\Repos and C:\\Users\\alexa\\Workfiles are mounted, at /workspace/repos and /workspace/files. Use Linux paths.\n');
    return {...stripLegacyUi(tool),description:description+"\nFortis Repo: general code workspace; plugin activation does not request a website. Host Repos = /workspace/repos; host Workfiles = /workspace/files, both read-write. /workspace/repo is the internal Docker volume. Outgoing internet is configured; verify connectivity and Git authentication."};
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
