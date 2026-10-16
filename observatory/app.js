const $=s=>document.querySelector(s), history=[], events=[]; let current=null,previous=null,lastDiagnosisKey="",lastEventSeq=0;
const esc=v=>String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
function sec(v){if(v==null||!Number.isFinite(+v))return "-";let s=Math.max(0,+v);return s<60?s.toFixed(s<10?1:0)+"s":s<3600?Math.floor(s/60)+"m "+Math.floor(s%60)+"s":Math.floor(s/3600)+"h "+Math.floor((s%3600)/60)+"m"}
function ms(v){if(v==null||!Number.isFinite(+v))return "-";return +v>=1000?(+v/1000).toFixed(2)+"s":Math.round(+v)+"ms"}
function cmap(o){let a=Object.entries(o||{});return a.length?a.sort((x,y)=>x[0].localeCompare(y[0])).map(([k,v])=>k+":"+v).join(" | "):"-"}
function dot(id,s){let e=$(id);if(e)e.className="dot "+(s==="ok"?"green":s==="warn"?"amber":s==="bad"?"red":"gray")}
function comp(h,n){return (h.components||{})[n]||{}} function cstate(c){return !c?.status?"unknown":c.status==="ok"||c.status==="disabled"?"ok":c.status==="degraded"||c.status==="warn"?"warn":"bad"}
function add(level,title,text,time=null){let stamp=time?new Date(time).toLocaleTimeString("ru-RU",{hour12:false}):new Date().toLocaleTimeString("ru-RU",{hour12:false});events.unshift({time:stamp,level,title,text});events.length=Math.min(events.length,30);renderEvents()}
function renderEvents(){$("#eventList").innerHTML=events.length?events.map(e=>'<div class="event '+e.level+'"><time>'+e.time+'</time><i></i><div><b>'+esc(e.title)+'</b><p>'+esc(e.text)+'</p></div></div>').join(""):'<div class="muted">No local marks yet.</div>'}
function layers(h){let cp=comp(h,"control-plane"),mc=comp(h,"mcp"),q=comp(h,"queue"),d=comp(h,"dispatcher"),rd=comp(h,"response-delivery"),qd=q.details||{},dd=d.details||{},md=mc.details||{},rows=[["Tunnel process",h.live?"ok":"bad",h.ready?"live / ready":"live but not ready",sec(h.runtime?.uptime_seconds)],["Control plane",cstate(cp),(cp.state||"-")+" | failures "+(cp.details?.consecutive_failures||0),"poll age "+sec(cp.details?.current_poll_age_seconds)],["MCP target",cstate(mc),(md.child_state||"-")+" | "+(md.initialize?.ok?"initialized":"not initialized"),"epoch "+(md.initialize_epoch||"-")],["Local queue",qd.backpressure_seconds>0?"warn":"ok",(qd.depth||0)+"/"+(qd.capacity||"-")+" | active "+(dd.active||0),"oldest "+sec(dd.oldest_active_age_seconds||0)],["Response delivery",cstate(rd),(rd.state||"-")+" | terminal "+(rd.details?.terminal_failures||0),"retries "+(rd.details?.retries||0)]];$("#layers").innerHTML=rows.map(r=>'<div class="layer"><i class="dot '+(r[1]==="ok"?"green":r[1]==="warn"?"amber":"red")+'"></i><div><b>'+esc(r[0])+'</b><small>'+esc(r[2])+'</small></div><time>'+esc(r[3])+'</time></div>').join("")}
function davg(n,o){if(!n||!o)return null;let dc=+(n.count||0)-+(o.count||0),ds=+(n.sum_ms||0)-+(o.sum_ms||0);return dc>0&&ds>=0?ds/dc:null}
function latency(s){let m=s.metrics||{},e=m.tools_call_200||{},p=m.tools_call_poll_to_response_200||{},om=previous?.metrics||{},re=davg(e,om.tools_call_200),rp=davg(p,om.tools_call_poll_to_response_200);$("#recentLatency").textContent=ms(re);$("#cumulativeLatency").textContent=ms(e.avg_ms);$("#slowCalls").textContent=m.tools_call_over_10s_200??"-";if(re!=null||rp!=null){history.push({e2e:re==null?null:re/1000,poll:rp==null?null:rp/1000});if(history.length>720)history.shift()}chart()}
function chart(){let c=$("#latencyChart"),r=devicePixelRatio||1,w=Math.max(320,c.clientWidth||700),h=190;c.width=w*r;c.height=h*r;let x=c.getContext("2d");x.scale(r,r);x.clearRect(0,0,w,h);let vals=history.flatMap(p=>[p.e2e,p.poll]).filter(Number.isFinite),max=Math.max(10,...vals);x.strokeStyle="rgba(140,152,168,.18)";for(let i=1;i<=3;i++){let y=(h-20)*i/4;x.beginPath();x.moveTo(0,y);x.lineTo(w,y);x.stroke()}for(let [k,col] of [["e2e","#6ca8ff"],["poll","#63d8e8"]]){x.strokeStyle=col;x.lineWidth=2;x.beginPath();let st=false;history.forEach((p,i)=>{let v=p[k];if(!Number.isFinite(v))return;let xx=history.length<=1?0:i*(w-8)/(history.length-1),yy=(h-12)-Math.min(v/max,1)*(h-24);st?x.lineTo(xx,yy):(x.moveTo(xx,yy),st=true)});if(st)x.stroke()}}
function summary(s){let h=s.health||{},cp=comp(h,"control-plane"),mc=comp(h,"mcp"),q=comp(h,"queue"),d=comp(h,"dispatcher"),qd=q.details||{},dd=d.details||{},md=mc.details||{},cd=cp.details||{};$("#tunnelState").textContent=h.live&&h.ready?"live / ready":h.live?"live / not ready":"down";$("#uptime").textContent="uptime "+sec(h.runtime?.uptime_seconds);dot("#tunnelDot",h.live&&h.ready?"ok":h.live?"warn":"bad");$("#controlState").textContent=cp.state||"unknown";$("#controlMeta").textContent="poll age "+sec(cd.current_poll_age_seconds)+" | failures "+(cd.consecutive_failures||0);dot("#controlDot",cstate(cp));$("#mcpState").textContent=(md.child_state||"unknown")+" / "+(mc.state||"unknown");$("#mcpMeta").textContent="stdio | init epoch "+(md.initialize_epoch||"-");dot("#mcpDot",cstate(mc));$("#workState").textContent=dd.active?(dd.active+" active"):"idle";$("#workMeta").textContent="queue "+(qd.depth||0)+"/"+(qd.capacity||"-")+" | oldest "+sec(dd.oldest_active_age_seconds||0);dot("#workDot",qd.backpressure_seconds>0||dd.oldest_active_age_seconds>=20?"warn":"ok")}
function transport(s){let m=s.metrics||{},h=s.health||{},q=comp(h,"queue").details||{},d=comp(h,"dispatcher").details||{};$("#pollHttp").textContent=cmap(m.poll_http)+" | errs "+((m.poll_errors_timeout||0)+(m.poll_errors_other||0));$("#responseHttp").textContent=cmap(m.response_http);$("#tools200").textContent=(m.tools_call_200?.count||0);$("#tools409").textContent=(m.tools_call_409?.count||0);$("#queueStat").textContent=(q.depth||0)+"/"+(q.capacity||"-");$("#dispatcherStat").textContent=(d.active||0)+"/"+(d.pool_limit||"-")+" | failures "+(d.failures||0)}
function diagnosis(s){let d=s.diagnosis||{},sev=d.severity||"neutral";$("#riskPill").className="risk-pill "+sev;$("#riskPill").textContent=sev.toUpperCase();$("#diagnosisTitle").textContent=d.title||"No diagnosis";$("#evidenceList").innerHTML=(d.evidence||[]).map(x=>"<li>"+esc(x)+"</li>").join("");$("#hypothesis").textContent=d.hypothesis||"";let k=sev+"|"+(d.title||"");if(lastDiagnosisKey&&k!==lastDiagnosisKey)add(sev==="bad"?"error":sev,"Diagnosis changed",d.title||"");lastDiagnosisKey=k}
function ingest(s){for(let e of s.tunnel_events||[]){if(!e.seq||e.seq<=lastEventSeq)continue;let detail=[e.error_code,e.status_code?"HTTP "+e.status_code:"",e.error].filter(Boolean).join(" | ");add(e.level==="ERROR"?"error":"warn",e.message||"Tunnel event",detail||"see tunnel log",e.time);lastEventSeq=Math.max(lastEventSeq,e.seq)}}
function deltas(s){if(!previous)return;let n=+(s.metrics?.tools_call_409?.count||0),o=+(previous.metrics?.tools_call_409?.count||0);if(n>o)add("warn","tools/call 409 increased","+"+(n-o)+" | possible MCP initialization/session guard")}
function render(s){if(s.legacy_host_retired){
$("#collectorState").textContent="Old HOST intentionally retired (E43), not telemetry failure";
$("#modeBadge").className="mode-badge";$("#modeBadge").textContent="LEGACY HOST RETIRED";
for(const id of ["#tunnelState","#controlState","#mcpState","#workState"])$(id).textContent="not monitored";
for(const id of ["#tunnelDot","#controlDot","#mcpDot","#workDot"])dot(id,"unknown");
$("#diagnosisTitle").textContent="Old owner HOST stopped intentionally (E43)";
$("#riskPill").className="risk-pill neutral";$("#riskPill").textContent="NOT MONITORED";
$("#evidenceList").innerHTML="<li>G2 and Repo have separate routes.</li>";
$("#hypothesis").textContent="Repo health cannot prove ChatGPT routing. G2 requires a separate collector.";
$("#layers").innerHTML="<div class='muted'>Old HOST retired; no live telemetry.</div>";
return;}if(!s.ok){$("#collectorState").textContent="error | "+(s.error||"unknown");$("#modeBadge").className="mode-badge bad";$("#modeBadge").textContent="TELEMETRY DOWN";add("error","Collector failed",s.error||"unknown");return}$("#modeBadge").className="mode-badge live";$("#modeBadge").textContent="LIVE SHADOW";let c=s.collector||{};$("#collectorState").textContent="ok | "+s.collector_ms+"ms | samples "+(c.samples??"-")+" | failures "+(c.failures??"-")+" | consecutive "+(c.consecutive_failures??"-")+" | "+new Date(s.captured_at*1000).toLocaleTimeString("ru-RU",{hour12:false});summary(s);latency(s);layers(s.health||{});transport(s);diagnosis(s);ingest(s);deltas(s)}
async function refresh(){try{let r=await fetch("/api/snapshot",{cache:"no-store"}),s=await r.json();previous=current;current=s;render(s)}catch(e){render({ok:false,error:String(e)})}}
function historyDelta(n,o,prefix){let dc=+(n?.metrics?.[prefix+"_count"]||0)-+(o?.metrics?.[prefix+"_count"]||0),ds=+(n?.metrics?.[prefix+"_sum_ms"]||0)-+(o?.metrics?.[prefix+"_sum_ms"]||0);return dc>0&&ds>=0?ds/dc/1000:null}
async function loadHistory(){try{let r=await fetch("/api/history?minutes=60",{cache:"no-store"}),p=await r.json(),rows=p.history||[];history.length=0;for(let i=1;i<rows.length;i++){history.push({e2e:historyDelta(rows[i],rows[i-1],"tools_call_200"),poll:historyDelta(rows[i],rows[i-1],"tools_call_poll_200")})}if(history.length>720)history.splice(0,history.length-720);chart();add("info","History loaded",(p.samples||0)+" samples from rolling 60m window")}catch(e){add("warn","History unavailable",String(e))}}
let selectedIncidentId=null;
function when(ts){return ts?new Date(ts*1000).toLocaleString("ru-RU",{hour12:false}):"-"}
function incidentRows(items){if(!items.length)return '<div class="muted">No persisted incidents yet.</div>';return items.map(i=>{let wait=i.status==="collecting"&&i.post_capture_due_at?Math.max(0,Math.ceil(i.post_capture_due_at-Date.now()/1000)):null,meta=when(i.marked_at)+(wait!=null?" · post +"+wait+"s":" · post "+(i.history_after_samples||0));return '<button class="incident-row" data-incident-id="'+esc(i.incident_id)+'"><span class="status '+esc(i.status||"complete")+'">'+esc(i.status||"complete")+'</span><span><strong>'+esc(i.incident_id)+'</strong><small>'+esc(meta)+'</small></span><small>pre '+esc(i.history_before_samples||0)+'</small></button>'}).join("")}
async function loadIncidents(selectId=null){try{let r=await fetch("/api/incidents?limit=100",{cache:"no-store"}),p=await r.json();if(!r.ok||!p.ok)throw new Error(p.error||("HTTP "+r.status));$("#incidentList").innerHTML=incidentRows(p.incidents||[]);if(selectId)selectedIncidentId=selectId;if(selectedIncidentId&&((p.incidents||[]).some(i=>i.incident_id===selectedIncidentId)))await openIncident(selectedIncidentId)}catch(e){$("#incidentList").innerHTML='<div class="muted">Incident list unavailable: '+esc(e)+'</div>'}}
async function openIncident(id){selectedIncidentId=id;try{let r=await fetch("/api/incidents/"+encodeURIComponent(id),{cache:"no-store"}),p=await r.json();if(!r.ok||!p.ok)throw new Error(p.error||("HTTP "+r.status));let i=p.incident||{},s=i.snapshot||{},h=s.health||{},mcp=comp(h,"mcp").details||{},status=i.status||"complete",due=status==="collecting"?" · collecting until "+when(i.post_capture_due_at):"",pre=(i.history_before||[]).length,post=(i.history_after||[]).length,diag=s.diagnosis||{};$("#incidentDetail").innerHTML='<div><b>'+esc(i.incident_id)+'</b> <span class="muted">'+esc(status)+due+'</span></div><div class="incident-detail-grid"><div><span>Marked</span><b>'+esc(when(i.marked_at))+'</b></div><div><span>Tunnel</span><b>'+esc(String(h.live))+" / "+esc(String(h.ready))+'</b></div><div><span>MCP init</span><b>'+esc(String((mcp.initialize||{}).ok))+'</b></div><div><span>Pre samples</span><b>'+pre+'</b></div><div><span>Post samples</span><b>'+post+'</b></div><div><span>Diagnosis</span><b>'+esc(diag.title||"-")+'</b></div></div><p class="incident-note">'+esc(i.note||i.limitation||"")+'</p><div class="incident-actions"><a href="/api/incidents/'+encodeURIComponent(id)+'/export">Export redacted ZIP</a></div>'}catch(e){$("#incidentDetail").innerHTML='<div class="muted">Incident detail unavailable: '+esc(e)+'</div>'}}
async function mark(){let btn=$("#markTimeout");btn.disabled=true;try{let r=await fetch("/api/incidents",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({note:"Manual 25s timeout mark from GUI"})}),p=await r.json();if(!r.ok||!p.ok)throw new Error(p.error||("HTTP "+r.status));add("warn","25s timeout persisted",p.incident_id+" | pre samples "+p.history_samples+" | post window collecting");await refresh();await loadIncidents(p.incident_id)}catch(e){add("error","Incident save failed",String(e))}finally{btn.disabled=false}}
$("#refreshNow").addEventListener("click",refresh);$("#markTimeout").addEventListener("click",mark);$("#refreshIncidents").addEventListener("click",()=>loadIncidents());$("#incidentList").addEventListener("click",e=>{let b=e.target.closest("[data-incident-id]");if(b)openIncident(b.dataset.incidentId)});window.addEventListener("resize",chart);setInterval(()=>$("#clock").textContent=new Date().toLocaleTimeString("ru-RU",{hour12:false}),1000);$("#clock").textContent=new Date().toLocaleTimeString("ru-RU",{hour12:false});renderEvents();loadHistory().finally(refresh);loadIncidents();setInterval(refresh,5000);setInterval(()=>loadIncidents(),10000);


async function refreshRepo() {
  try {
    const response = await fetch("/api/repo-status", {cache: "no-store"});
    if (!response.ok) throw new Error("HTTP " + response.status);
    const value = await response.json();
    const state = ["UP","DOWN","UNKNOWN","STALE"].includes(value.state) ? value.state : "UNKNOWN";
    $("#repoStatus").textContent = state;
    $("#repoStatus").dataset.state = state;
    $("#repoReason").textContent = value.verified
      ? (value.mcp_state || "MCP unknown") + " · " + (value.listener || "verified") + " · local health only"
      : (value.reason || "No verified data");
  } catch(e) {
    $("#repoStatus").textContent = "UNKNOWN";
    $("#repoReason").textContent = "Collector request failed";
  }
}
const originalRender = render;
render = function(s) {
  originalRender(s);
  const h = s.health || {};
  const state = s.legacy_host_retired ? "RETIRED" : (!s.ok ? "UNKNOWN" : (h.live && h.ready ? "UP" : "DOWN"));
  $("#hostStatus").textContent = state;
  $("#hostStatus").dataset.state = state;
  $("#hostReason").textContent = s.legacy_host_retired ? "Stopped intentionally (E43); not G2" : s.ok ? ("MCP " + ((h.components || {}).mcp?.state || "unknown")) : "Collector unavailable";
};
refreshRepo();
setInterval(refreshRepo, 5000);

async function refreshRepoHistory() {
  try {
    const r = await fetch("/api/repo-history?minutes=60", {cache:"no-store"});
    if(!r.ok) throw new Error("HTTP " + r.status);
    const payload = await r.json();
    $("#repoHistoryCount").textContent = payload.samples ?? "—";
  } catch(e) {
    $("#repoHistoryCount").textContent = "недоступно";
  }
}
refreshRepoHistory();
setInterval(refreshRepoHistory, 15000);


// Optional read-only activity stream. Never interpolate command text: the
// server returns metadata ONLY, and HTML is escaped even for tool names.
async function refreshActivity() {
  const list = document.getElementById("activityList"), state = document.getElementById("activityCoverage");
  if (!list || !state) return;
  try {
    const res = await fetch("/api/activity?limit=40", {cache:"no-store"});
    if (!res.ok) throw new Error("HTTP " + res.status);
    const info = await res.json(), feeds = info.feeds || {};
    const details = ["repo","g2"].map(route => {
      const src = feeds[route] || {};
      return route.toUpperCase()+": "+(src.source_state || "unconfigured")+
        (src.source_recent_window_incomplete ? " · incomplete window" : "");
    });
    state.textContent = details.join(" | ") +
      " · Metadata only; no prompts, command text, arguments or outputs. History is rolling and incomplete.";
    const rows = info.events || [];
    list.innerHTML = rows.length ? rows.map(item =>
      '<div class="activity-row"><b>'+esc(item.route || "?")+'</b>'+
      '<span>'+esc(item.timestamp || "unknown")+'</span>'+
      '<strong>'+esc(item.tool || "unknown")+'</strong>'+
      '<small>'+esc(item.kind || "other")+
        ' · '+esc(item.duration_ms == null ? "?" : String(item.duration_ms))+
        'ms · '+esc(item.outcome || "unverified")+
        (item.command_present ? ' · command exists (local CLI only)' : '')+'</small></div>'
    ).join("") : '<p class="muted">No activity visible from configured sources.</p>';
  } catch (err) {
    state.textContent = "Activity feed unavailable; this is not evidence of zero tool calls.";
    list.textContent = String(err);
  }
}
document.getElementById("refreshActivity")?.addEventListener("click", refreshActivity);
refreshActivity();
setInterval(refreshActivity, 10000);

// Native G2 and Repo are independent routes. Never treat retired owner HOST
// telemetry as G2, or listener health as proof of a completed chat request.
function nativeMetricText(value) {
  return value == null || !Number.isFinite(+value) ? "—" : Math.round(+value).toLocaleString("ru-RU");
}
function nativeRoute(prefix, row) {
  const state = ["UP", "DOWN", "UNKNOWN", "STALE"].includes(row?.state) ? row.state : "UNKNOWN";
  const verified = row?.verified === true && state !== "STALE";
  const m = verified ? (row.metrics || {}) : {};
  const id = s => document.getElementById("native" + prefix + s);
  id("State").textContent = state;
  id("State").dataset.state = state;
  id("Reason").textContent = verified
    ? "Проверен локальный туннель " + (row.listener || "") + "; работа во всех чатах НЕ доказана"
    : (row?.reason || "Нет подтверждённых данных");
  id("Mcp").textContent = verified ? (row.mcp_state || "unknown") : "—";
  id("Polled").textContent = nativeMetricText(m.polled_total);
  id("Latency").textContent = m.command_latency_avg_ms == null ? "—" : ms(m.command_latency_avg_ms);
  id("Queue").textContent = m.queue_length == null ? "—" : nativeMetricText(m.queue_length) + " / " + nativeMetricText(m.queue_capacity);
  id("Dispatch").textContent = m.dispatcher_active == null ? "—" : nativeMetricText(m.dispatcher_active) + " / " + nativeMetricText(m.dispatcher_capacity);
  const age = m.poll_last_success_at == null ? null : Date.now()/1000 - m.poll_last_success_at;
  id("Poll").textContent = age != null && age >= 0 && age < 86400 ? sec(age) + " назад" : "—";
  id("Stamp").textContent = row?.sampled_at ? "Замер: " + new Date(row.sampled_at*1000).toLocaleTimeString("ru-RU") : "Нет замера";
}
async function refreshNative() {
  try {
    const response = await fetch("/api/tunnels", {cache:"no-store"});
    if (!response.ok) throw new Error("HTTP " + response.status);
    const p = await response.json();
    if (!p.ok) throw new Error("collector rejected response");
    nativeRoute("G2", p.g2);
    nativeRoute("Repo", p.repo);
  } catch (error) {
    nativeRoute("G2", {state:"UNKNOWN",reason:"API недоступно: " + error});
    nativeRoute("Repo", {state:"UNKNOWN",reason:"API недоступно: " + error});
  }
}
function nativeSeries(payload) {
  const rows = (payload.history || []).filter(x => Number.isFinite(+x.sampled_at) && Number.isFinite(+x.metrics?.polled_total));
  if (rows.length < 2) return [];
  const sorted = rows.slice().sort((a,b) => a.sampled_at-b.sampled_at);
  let baseline = +sorted[0].metrics.polled_total,prev=baseline,total=0;
  return sorted.map((row,i) => {
    const current = +row.metrics.polled_total;
    if (i) total += current >= prev ? current-prev : current; // counter reset
    prev = current;
    return {time:+row.sampled_at, count:total};
  });
}
let nativeSeriesRepo=[],nativeSeriesG2=[];
function renderNativeChart() {
  const canvas=document.getElementById("nativeHistoryChart");
  if (!canvas) return;
  const ratio=window.devicePixelRatio||1, w=Math.max(canvas.clientWidth||500,300),h=150;
  canvas.width=Math.round(w*ratio);canvas.height=Math.round(h*ratio);
  const ctx=canvas.getContext("2d");ctx.scale(ratio,ratio);ctx.clearRect(0,0,w,h);
  const lines=[nativeSeriesRepo,nativeSeriesG2];
  const full=lines.flat();
  if (!full.length) return;
  const minT=Math.min(...full.map(x=>x.time)),maxT=Math.max(...full.map(x=>x.time));
  const span=Math.max(1,maxT-minT);
  const maxCount=Math.max(1,...full.map(x=>x.count));
  ctx.strokeStyle="rgba(150,170,195,.2)";ctx.lineWidth=1;
  for(let i=1;i<=3;i++){const y=(h-14)*i/4;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
  for(let j=0;j<lines.length;j++){
    const points=lines[j];if(points.length<2)continue;
    ctx.strokeStyle=j===0?"#6ca8ff":"#63d8e8";ctx.lineWidth=2;ctx.beginPath();
    points.forEach((p,i)=>{const x=8+(p.time-minT)/span*(w-16),y=h-12-p.count/maxCount*(h-25); if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);});
    ctx.stroke();
  }
}
async function refreshNativeHistory() {
  try {
    const [repoResponse,g2Response] = await Promise.all([
      fetch("/api/repo-history?minutes=60",{cache:"no-store"}),
      fetch("/api/g2-history?minutes=60",{cache:"no-store"}),
    ]);
    if (!repoResponse.ok || !g2Response.ok) throw new Error("history API unavailable");
    const [repo,g2] = await Promise.all([repoResponse.json(),g2Response.json()]);
    nativeSeriesRepo=nativeSeries(repo);
    nativeSeriesG2=nativeSeries(g2);
    document.getElementById("nativeHistoryStatus").textContent =
      "Образцы за 60м · Repo: "+(repo.samples||0)+" · G2: "+(g2.samples||0);
    renderNativeChart();
  } catch(error) {
    document.getElementById("nativeHistoryStatus").textContent="История недоступна";
  }
}
document.getElementById("refreshTunnels").addEventListener("click",()=>{
  refreshNative();refreshNativeHistory();
});
window.addEventListener("resize",renderNativeChart);
refreshNative();refreshNativeHistory();
setInterval(refreshNative,10000);
setInterval(refreshNativeHistory,30000);
