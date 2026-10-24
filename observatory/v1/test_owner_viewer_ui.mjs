import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import vm from "node:vm";

const source=readFileSync(new URL("./owner_viewer.py",import.meta.url),"utf8");
const page=source.match(/PAGE = r'''([\s\S]*?)'''/)[1];
const js=page.match(/<script nonce="__NONCE__">([\s\S]*?)<\/script>/)[1];
const ids=[...page.matchAll(/\bid="([^"]+)"/g)].map(match=>match[1]);
assert.equal(new Set(ids).size,ids.length,"duplicate element id");
for(const id of ["registerPanel","instructionPanel","pairPanel"]){
 assert.match(page,new RegExp('id="'+id+'"[^>]+ hidden'));
}
assert.ok(page.indexOf('<main id="workspaceGrid" class="grid">')>page.indexOf('class="action-area"'));
assert.match(page,/class="sticky-top"/);
assert.match(page,/<nav id="sessionTabBar" class="session-tab-bar"[^>]+ hidden>/);
assert.match(page,/<div id="sessions" role="tablist" aria-label="Подключённые сессии">/);
assert.ok(page.indexOf('id="sessionTabBar"')>page.indexOf('id="toolbar"'),
  "session tabs are under actions in the header");
assert.ok(page.indexOf('id="sessionTabBar"')<page.indexOf('<section id="app"'),
  "session tabs are in the sticky header, not in the columns");
assert.ok(page.indexOf('id="sessions"')<page.indexOf('class="workspace-viewport"'));
assert.doesNotMatch(page,/class="sessions-column"[\s\S]*?<div id="sessions"/,
  "side column must not keep a duplicate session list");
assert.ok(page.indexOf('id="composeArea"')>page.indexOf('<section id="app"'),
  "full-width composer is outside sticky header");
assert.ok(page.indexOf('id="composeArea"')<page.indexOf('class="workspace-viewport"'),
  "composer is above the four columns");
assert.equal((page.match(/id="toggleCompose"/g)||[]).length,1);
assert.match(page,/id="composeFile"[^>]*>Файл<\/button>/);
assert.match(page,/id="composeInsert"[^>]*>Вставить<\/button>/);
assert.match(page,/id="composeSend"[^>]*>Файл \+ Send<\/button>/);
assert.match(page,/id="composeSendPrepared"[^>]*>Нажать Send<\/button>/);
assert.match(page,/id="composeEvents" role="log"/);
assert.ok(page.indexOf('id="composeEvents"')>page.indexOf('id="composeFile"'));
assert.match(page,/class="compose-command-row"/);
assert.match(page,/id="toggleComposeModules"/);
assert.match(page,/class="column-resizer"/);
assert.equal((page.match(/role="separator"/g)||[]).length,3);

class Element {
 constructor(tag="div"){
  this.tagName=tag;this.children=[];this.textContent="";this.value="";
  this.hidden=false;this.listeners={};this.attributes={};this.className="";
  this.clientWidth=1200;this.style={};this.dataset={};
  this.classList={add(){},remove(){},contains(){return false}};
 }
 setPointerCapture(id){this.pointerId=id}
 hasPointerCapture(id){return this.pointerId===id}
 releasePointerCapture(){this.pointerId=null}
 replaceChildren(...children){this.children=children}
 append(...children){this.children.push(...children)}
 addEventListener(name,fn){this.listeners[name]=fn}
 setAttribute(name,value){this.attributes[name]=value}
 removeAttribute(name){delete this.attributes[name]}
 focus(){}
 select(){}
}

const elements=new Map(ids.map(id=>[id,new Element()]));
for(const id of ["registerPanel","instructionPanel","pairPanel","composePanel","app"]){
 elements.get(id).hidden=true
}
const document={
 getElementById(id){assert.ok(elements.has(id),"unknown id: "+id);return elements.get(id)},
 createElement(tag){return new Element(tag)}
};
const intervals=[];
const savedStorage=new Map();
const localStorage={getItem:key=>savedStorage.has(key)?savedStorage.get(key):null,
 setItem:(key,value)=>savedStorage.set(key,String(value)),removeItem:key=>savedStorage.delete(key)};
const window={localStorage,addEventListener(){},setInterval(callback,delay){intervals.push({callback,delay})}};
const session1="rs_"+"a".repeat(32), session2="rs_"+"b".repeat(32);
const task1="task_"+"c".repeat(32), task2="task_"+"d".repeat(32);
const requests=[],postRequests=[],approvalRequests=[];
let holdPair=false,releasePair=null,holdState=false,releaseState=null;
const responses={
 "/api/notifier/discovered":{ok:true,chats:[]},
 "/api/notifier/connect":{ok:true,created:false,approved:true,session:session1,
   conversation_id:"discovered-chat-12345678",task_intents:false},
 "/api/state":{sessions:[
  {reporting_session_id:session1,conversation_id:"abcdefgh-01234567",title:"Первый чат",state:"active",events:[
   {task_id:task1,event:"started",event_id:"start-1",sequence:0,stage:"planning",
    summary:"Планирование проверки",has_detail:true,
    accepted_at:"2026-10-19T06:00:01Z"},
   {task_id:task1,event:"progress",event_id:"progress-1",sequence:1,stage:"editing",
    summary:"Правка интерфейса",accepted_at:"2026-10-19T06:00:03Z"}
  ]},
  {reporting_session_id:session2,conversation_id:"abcdefgh-22222222",title:"Второй чат",state:"active"}
 ]},
 ["/api/tasks?session="+session1]:{tasks:[
  {task_id:task1,first_seen_at:"2026-10-19T06:00:00Z",original_received:true,original_preview:"Точный исходный текст"}
 ]},
 ["/api/tasks?session="+session2]:{tasks:[
  {task_id:task2,first_seen_at:"2026-10-19T06:05:00Z",original_received:false}
 ]},
 ["/api/history?session="+session1+"&task="+task1]:{
  session:session1,task_id:task1,original_text:"<script>do not run</script>",
  assistant_messages:[
   {message_id:"msg_1",kind:"interim",body:"Промежуточный полный отчёт",
    accepted_at:"2026-10-19T06:00:02Z"},
   {message_id:"msg_2",kind:"final",body:"Полный ответ\n\n<script>не исполнять</script>",
    accepted_at:"2026-10-19T06:00:05Z"}
  ],events:[{event:"started",sequence:0,detail:"Полное объяснение шага с Unicode 🌍"},{event:"progress",sequence:1}]
 },
 ["/api/history?session="+session2+"&task="+task2]:{
  session:session2,task_id:task2,original_text:null,assistant_messages:[],events:[]
 },
 ["/api/instructions?session="+session1]:{session:session1,text:"Инструкция один"},
 ["/api/instructions?session="+session2]:{session:session2,text:"Инструкция два"},
 ["/api/notifier/pending?session="+session1]:{ok:true,approved:false,
   pending:[{fingerprint:"abcdef123456",chat:"abcdefgh-01234567"}]},
 ["/api/notifier/pending?session="+session2]:{ok:true,approved:false,pending:[]},
 "/api/notifier/approve":{ok:true,approved:true},
 "/api/notifier/revoke":{ok:true,revoked:true},
 ["/api/dispatch/status?session="+session1]:{ok:true,paired:true,
   ever_seen:true,available:true,last_seen_seconds_ago:2,dispatch:null,
   modules_synced:true,
   history:[{at:"2026-10-20T19:15:01Z",event:"queued",mode:"file",
             dispatch_id:"dispatch_"+"4".repeat(32)},
            {at:"2026-10-20T19:15:02Z",event:"claimed",mode:"file"},
            {at:"2026-10-20T19:15:03Z",event:"refused",mode:"file",
             reason:"prepared_missing"}],
   modules:[{id:"policy.verification",title:"Проверка результатов"},
            {id:"review.summary",title:"Резюме"}],
   default_module_ids:["policy.verification"],
   profiles_synced:true,active_profile_id:"repo",
   profiles:[{id:"default",name:"Обычный",module_ids:[]},
             {id:"repo",name:"Работа в Repo",module_ids:["policy.verification"]}]},
 ["/api/dispatch/status?session="+session2]:{ok:true,paired:false,
   ever_seen:false,available:false,last_seen_seconds_ago:null,dispatch:null},
 "/api/dispatch":{dispatch_id:"dispatch_"+("1".repeat(32)),status:"pending"},
 ["/api/notifier-pair?session="+session1]:{pairing:{
  reporting_session_id:session1,origin:"http://127.0.0.1:18755",observer_key:"mock-only"
 }}
};
const sandbox={
 document,window,console,Date,TextEncoder,
 setInterval(callback,delay){intervals.push({callback,delay})},
 alert(){throw Error("unexpected alert")},
 navigator:{clipboard:{async writeText(){}}},
 fetch:async(url,options={})=>{
  requests.push(url);assert.ok(responses[url],"unexpected request: "+url);
  if(holdState&&url==="/api/state"){
   return new Promise(resolve=>{releaseState=()=>resolve({ok:true,json:async()=>responses[url]})})
  }
  if(url==="/api/dispatch")postRequests.push(options);
  if(url==="/api/notifier/approve"||url==="/api/notifier/revoke")approvalRequests.push(options);
  if(holdPair&&url.includes("/api/notifier-pair?")){
   return new Promise(resolve=>{
    releasePair=()=>resolve({ok:true,json:async()=>responses[url]})
   })
  }
  return {ok:true,json:async()=>responses[url]}
 }
};
vm.createContext(sandbox);
vm.runInContext(js,sandbox);
const fire=async(id,kind="click")=>{
 const e=elements.get(id);
 assert.ok(e.listeners[kind],"missing "+kind+" handler for "+id);
 await e.listeners[kind]({preventDefault(){}});
};
const tick=()=>new Promise(resolve=>setImmediate(resolve));

assert.equal(elements.get("registerPanel").hidden,true);
assert.equal(elements.get("pairPanel").hidden,true);
assert.match(page,/<details id="sessionDiagnostics" class="session-diagnostics">/);
assert.doesNotMatch(page,/<details id="sessionDiagnostics"[^>]*\sopen(?:\s|>)/);
assert.match(page,/<summary id="sessionDetailsHeading">Подробности сессии<\/summary>/);
assert.match(page,/<input id="autoFollow" type="checkbox">/);
assert.equal(elements.get("autoFollow").checked,undefined,
 "default follow must be disabled so polling does not steal focus");
assert.deepEqual(intervals.map(x=>x.delay),[5000,5000]);
elements.get("autoFollow").checked=true;
const poll=()=>intervals.at(-1).callback();
assert.equal(elements.get("instructionPanel").hidden,true);
elements.get("secret").value="synthetic_viewer_token";
await fire("form","submit");
assert.equal(elements.get("app").hidden,false);
assert.equal(elements.get("sessions").children.length,2);
assert.equal(elements.get("sessionTabBar").hidden,false);
assert.equal(elements.get("sessions").children[0].attributes.role,"tab");
assert.equal(elements.get("sessions").children[0].attributes["aria-selected"],"true");
assert.equal(elements.get("sessions").children[1].attributes["aria-selected"],"false");
assert.equal(elements.get("sessions").children[0].attributes["aria-controls"],"workspaceGrid");
assert.equal(elements.get("tasks").children.length,1);
assert.equal(elements.get("records").children.length,5);
assert.equal(elements.get("recordCount").textContent,"5");
assert.equal(elements.get("history").children.length,5);
assert.equal(elements.get("records").children[0].className.includes("user"),true);
assert.equal(elements.get("records").children[1].className.includes("event"),true);
assert.equal(elements.get("records").children[2].className.includes("message"),true);
assert.equal(elements.get("records").children[4].className.includes("message"),true);
assert.equal(elements.get("history").children[4].textContent,"Полный ответ\n\n<script>не исполнять</script>");
assert.ok(elements.get("records").children.at(-1).className.includes("active"),
  "new session defaults to newest chronological record");
elements.get("records").scrollHeight=913;
await poll();
assert.equal(elements.get("records").scrollTop,913,"follow scrolls records to bottom on poll");
assert.match(elements.get("status").textContent,/обновлено/);
assert.equal(elements.get("toolbar").hidden,false);
assert.equal(elements.get("sessionChatLink").textContent,
  "https://chatgpt.com/c/abcdefgh-01234567");
assert.equal(elements.get("sessionChatLink").href,
  "https://chatgpt.com/c/abcdefgh-01234567");
assert.equal(elements.get("diagnosticChatId").textContent,"abcdefgh-01234567");
assert.equal(elements.get("diagnosticSessionId").textContent,session1);
assert.match(elements.get("notifierConnection").textContent,/ПОДКЛЮЧЁН/);
assert.match(elements.get("enrollmentStatus").textContent,/abcdef123456/);
assert.equal(elements.get("approveNotifier").hidden,false);
assert.equal(elements.get("revokeAutoNotifier").hidden,true);
assert.doesNotMatch(elements.get("notifierConnection").textContent,/mock-only/);
assert.equal(elements.get("checkNotifierConnection").disabled,false);
await fire("checkNotifierConnection");
assert.match(elements.get("notifierConnection").textContent,/2 сек/);
responses["/api/notifier/pending?session="+session1]={ok:true,approved:true,pending:[]};
await fire("approveNotifier");
const approval=approvalRequests.find(opt=>JSON.parse(opt.body??"{}").fingerprint==="abcdef123456");
assert.ok(approval,"one-time approved pending user script");
assert.equal(JSON.parse(approval.body).chat,"abcdefgh-01234567");
assert.equal(elements.get("approveNotifier").hidden,true);
assert.equal(elements.get("revokeAutoNotifier").hidden,false);
assert.match(elements.get("enrollmentStatus").textContent,/Постоянная привязка одобрена/);

assert.equal(elements.get("composePanel").hidden,true);
await fire("toggleCompose");
assert.equal(elements.get("composePanel").hidden,false);
assert.match(elements.get("composeTarget").textContent,/Первый чат/);
assert.match(elements.get("composeStatus").textContent,/подключена/);
assert.equal(elements.get("composeEvents").children.length,3);
assert.match(elements.get("composeEvents").children[0].textContent,/Команда поставлена в очередь/);
assert.match(elements.get("composeEvents").children[1].textContent,/Notifier принял/);
assert.match(elements.get("composeEvents").children[2].textContent,/нет готового черновика/);
const partialStatus=responses["/api/dispatch/status?session="+session1];
partialStatus.history.push({at:"2026-10-20T19:15:04Z",event:"attachment_unconfirmed",
 mode:"file",reason:"upload_unconfirmed"});
partialStatus.history.push({at:"2026-10-20T19:15:05Z",event:"attachment_only",
 mode:"file",reason:"context_mismatch"});
await vm.runInContext("checkComposeStatus()",sandbox);
assert.match(elements.get("composeEvents").children[3].textContent,
 /файл МОГ прикрепиться|Карточка не распознана/);
assert.match(elements.get("composeEvents").children[4].textContent,
 /Fortis-контекст НЕ подготовлен/);
const completeNotifierFailure="Файл прикреплён, но контекст не добавлен: "+
 "Вставка не совпала с исходником посимвольно. "+
 "Исходник сохранён; Send не нажимался. Не отправляй до ручной проверки.";
partialStatus.history.push({at:"2026-10-20T19:15:06Z",event:"attachment_only",
 mode:"file",reason:"context_mismatch",detail:completeNotifierFailure});
await vm.runInContext("checkComposeStatus()",sandbox);
assert.match(elements.get("composeEvents").children[5].textContent,
 /Полное сообщение Notifier: Файл прикреплён, но контекст не добавлен:/);
assert.ok(elements.get("composeEvents").children[5].textContent.includes(
 completeNotifierFailure),"the Owner journal must show the complete Notifier warning");
assert.doesNotMatch(elements.get("composeEvents").children[5].textContent,
 /undefined|\[object Object\]/);
partialStatus.dispatch={mode:"file",status:"attachment_unconfirmed"};
await vm.runInContext("checkComposeStatus()",sandbox);
assert.match(elements.get("composeStatus").textContent,/результат не подтверждён/);
assert.doesNotMatch(elements.get("composeStatus").textContent,/Notifier отказал/);
partialStatus.dispatch={mode:"file",status:"attachment_only"};
await vm.runInContext("checkComposeStatus()",sandbox);
assert.match(elements.get("composeStatus").textContent,/не подтверждены/);
partialStatus.dispatch=null;
assert.equal(elements.get("composeProfileSelect").children.length,2,
 "Same native profile IDs and names as Notifier");
assert.equal(elements.get("composeProfileSelect").value,"repo");
assert.equal(elements.get("composeProfileSelect").children[1].textContent,
 "Работа в Repo · активный");
assert.equal(elements.get("composeModulesList").children.length,2,
 "module selector shows only real Notifier catalog IDs");
assert.equal(elements.get("composeModulesList").children[0].children[0].checked,true);
await fire("toggleComposeModules");
assert.equal(elements.get("composeModulesPanel").open,true);
const module2=elements.get("composeModulesList").children[1].children[0];
module2.checked=true;await module2.listeners.change();
elements.get("composeText").value="Привет 🪐 — тест выбранного чата";
await fire("composeText","input");
await fire("composeInsert");
assert.equal(postRequests.length,1);
const sent=JSON.parse(postRequests[0].body);
assert.equal(sent.session,session1);
assert.equal(sent.chat,"abcdefgh-01234567");
assert.equal(sent.mode,"insert");
assert.equal(sent.text,"Привет 🪐 — тест выбранного чата");
assert.deepEqual(sent.module_ids,["policy.verification","review.summary"]);
assert.equal(sent.profile_id,"repo");
assert.equal(elements.get("composeText").value,sent.text,"retain original until explicit action");
await fire("composeFile");
const sentFile=JSON.parse(postRequests.at(-1).body);
assert.equal(sentFile.mode,"file");
assert.equal(sentFile.chat,sent.chat);
assert.equal(sentFile.text,sent.text);
assert.deepEqual(sentFile.module_ids,sent.module_ids);
await fire("composeSend");
const sentSend=JSON.parse(postRequests.at(-1).body);
assert.equal(sentSend.mode,"send");
assert.deepEqual(sentSend.module_ids,sent.module_ids);
await fire("composeSendPrepared");
const preparedPayload=JSON.parse(postRequests.at(-1).body);
assert.deepEqual(preparedPayload,{session:session1,chat:sent.chat,
 mode:"send_prepared",text:"",module_ids:null,profile_id:null});
assert.equal(elements.get("composeText").value,sent.text,
 "separate prepared Send must not mutate Observatory original prompt");
assert.equal(elements.get("composeText").value,sent.text,
 "neither file nor send clears original before Notifier acknowledgement");
elements.get("composeProfileSelect").value="default";
await fire("composeProfileSelect","change");
assert.equal(elements.get("composeProfileSelect").value,"default");
assert.equal(elements.get("composeModulesList").children.length,2);
assert.equal(elements.get("composeModulesList").children[0].children[0].checked,false);
assert.equal(elements.get("composeModulesList").children[1].children[0].checked,false);
await fire("composeInsert");
const defaultPayload=JSON.parse(postRequests.at(-1).body);
assert.equal(defaultPayload.profile_id,"default");
assert.equal(defaultPayload.module_ids,null,
 "Notifier resolves saved default profile modules and behaviors by profile ID");
elements.get("composeProfileSelect").value="repo";
await fire("composeProfileSelect","change");
assert.equal(elements.get("composeModulesList").children[0].children[0].checked,true,
 "Repo profile restores its own native module set");
assert.equal(elements.get("composeModulesList").children[1].children[0].checked,false);

elements.get("composeModuleSearch").value="резюме";
await fire("composeModuleSearch","input");
assert.equal(elements.get("composeModulesList").children.length,1,
  "module catalog search filters without changing selected IDs");
assert.equal(elements.get("composeModulesList").children[0].children[0].checked,false,
 "returning to saved profile discards temporary unsaved module override");
elements.get("composeModuleSearch").value="";
await fire("composeModuleSearch","input");
assert.equal(elements.get("composeModulesList").children.length,2);
elements.get("composeText").value="Д".repeat(12000);
await fire("composeInsert");
assert.equal(JSON.parse(postRequests.at(-1).body).mode,"file",
  "oversized insert is prepared as File, not a dangerous huge native paste");
elements.get("composeText").value=sent.text;
await fire("composeText","input");
await fire("toggleCompose");
assert.equal(elements.get("composePanel").hidden,true);
await fire("toggleCompose");
assert.equal(elements.get("composePanel").hidden,false);
assert.equal(elements.get("sessionCount").textContent,"2");
assert.equal(elements.get("taskCount").textContent,"1");
const columnsBefore=elements.get("workspaceGrid").style.gridTemplateColumns;
const handle=elements.get("resize1");
handle.listeners.keydown({key:"ArrowRight",shiftKey:false,preventDefault(){}});
assert.notEqual(elements.get("workspaceGrid").style.gridTemplateColumns,columnsBefore);
const afterKey=elements.get("workspaceGrid").style.gridTemplateColumns;
handle.listeners.pointerdown({button:0,pointerId:2,clientX:500,preventDefault(){}});
handle.listeners.pointermove({pointerId:2,clientX:520});
handle.listeners.pointerup({pointerId:2});
assert.notEqual(elements.get("workspaceGrid").style.gridTemplateColumns,afterKey);
handle.listeners.dblclick();
assert.equal(elements.get("workspaceGrid").style.gridTemplateColumns,columnsBefore);
elements.get("records").children[1].onclick();
assert.equal(elements.get("history").children.some(item=>item.textContent==="Планирование проверки"),true);
assert.equal(elements.get("history").children.some(item=>item.textContent==="Полное объяснение шага с Unicode 🌍"),true);
elements.get("records").children[0].onclick();
assert.equal(elements.get("history").children.at(-1).textContent,"<script>do not run</script>");
elements.get("records").children[2].onclick();
assert.equal(elements.get("history").children.at(-1).textContent,"Промежуточный полный отчёт");
elements.get("autoFollow").checked=false;
await fire("autoFollow","change");
elements.get("records").scrollTop=23;
elements.get("history").scrollTop=15;
await poll();
assert.equal(elements.get("history").children.at(-1).textContent,"Промежуточный полный отчёт",
 "poll with auto follow off must preserve selected detailed record");
assert.equal(elements.get("records").scrollTop,23,"manual record scroll retained");
assert.equal(elements.get("history").scrollTop,15,"manual detail scroll retained");
await fire("refresh");
assert.equal(elements.get("history").children.at(-1).textContent,"Промежуточный полный отчёт",
 "manual refresh preserves selection when follow unchecked");
assert.equal(elements.get("records").scrollTop,23,"manual refresh must preserve scroll");
assert.equal(requests.filter(x=>x.includes("register")||x.includes("notifier-pair")).length,0);

await fire("toggleRegister");
assert.equal(elements.get("registerPanel").hidden,false);
assert.equal(elements.get("instructionPanel").hidden,true);
await fire("toggleRegister");
assert.equal(elements.get("registerPanel").hidden,true);
await fire("toggleInstructions");
assert.equal(elements.get("instructions").value,"Инструкция один");
assert.equal(elements.get("instructionPanel").hidden,false);
assert.equal(elements.get("registerPanel").hidden,true);
await fire("togglePair");
assert.equal(elements.get("pairPanel").hidden,false);
assert.equal(elements.get("instructionPanel").hidden,true);
await fire("makePair");
assert.ok(elements.get("pairValue").value.includes("mock-only"));
// A later task arrives while user is viewing the older task with follow OFF.
const taskNew="task_"+("e".repeat(32));
responses["/api/tasks?session="+session1].tasks.push({
 task_id:taskNew,first_seen_at:"2026-10-20T18:10:00Z",
 original_received:true,original_preview:"Новый запрос"
});
responses["/api/history?session="+session1+"&task="+taskNew]={
 session:session1,task_id:taskNew,original_text:"Новый запрос",
 assistant_messages:[{message_id:"msg_new",kind:"final",body:"Завершённый ответ",
   accepted_at:"2026-10-20T18:10:02Z"}],
 events:[{event:"completed",sequence:12,
  accepted_at:"2026-10-20T18:10:03Z",summary:"Завершено позже финала"}]
};
// Backend delivers the newly accepted event in session metadata, as in Repo.
responses["/api/state"].sessions[0].events.push({
 task_id:taskNew,event:"completed",event_id:"new-last",sequence:12,
 stage:"other",summary:"Завершено позже финала",
 accepted_at:"2026-10-20T18:10:03Z"
});
await poll();
assert.equal(elements.get("taskCount").textContent,"2");
assert.equal(elements.get("history").children.at(-1).textContent,"Промежуточный полный отчёт",
 "new task must NOT steal focus while auto follow is off");
elements.get("autoFollow").checked=true;
await fire("autoFollow","change");
await tick();
assert.equal(elements.get("tasks").children.at(-1).className.includes("active"),true,
 "enabling follow immediately selects freshest task");
assert.equal(elements.get("records").children.at(-1).className.includes("active"),true,
 "follow picks most recently accepted record, even completed event after final");
assert.equal(elements.get("history").children.some(e=>e.textContent.includes("Завершено позже финала")),true);
assert.equal(elements.get("records").scrollTop,913,"new task event list scrolls down");
const latestTask=vm.runInContext("newestTaskId",sandbox);
assert.equal(latestTask([...responses["/api/tasks?session="+session1].tasks].reverse()),taskNew,
 "most recent task must be selected by timestamp, not array position");
// A new event INSIDE the same task should be selected and scrolled into view.
responses["/api/history?session="+session1+"&task="+taskNew].events.push({
 event:"checkpoint",sequence:13,summary:"Новейшее событие"
});
responses["/api/state"].sessions[0].events.push({
 task_id:taskNew,event:"checkpoint",event_id:"new-checkpoint",sequence:13,
 stage:"testing",summary:"Новейшее событие",accepted_at:"2026-10-20T18:10:04Z"
});
await poll();
assert.equal(elements.get("recordCount").textContent,"4");
assert.equal(elements.get("records").children.at(-1).className.includes("active"),true);
assert.ok(elements.get("history").children.some(e=>e.textContent.includes("Новейшее событие")));
assert.equal(elements.get("records").scrollTop,913);
// With follow off, explicit session selection STILL jumps to newest task.
elements.get("autoFollow").checked=false;
await fire("autoFollow","change");
elements.get("tasks").children[0].onclick();
await tick();
assert.equal(elements.get("tasks").children[0].className.includes("active"),true);
holdPair=true;
const stalePair=fire("makePair");
await tick();
assert.equal(typeof releasePair,"function");
elements.get("sessions").children[1].onclick();
releasePair();
await stalePair;
holdPair=false;


await tick();
assert.equal(elements.get("pairPanel").hidden,true);
assert.equal(elements.get("pairValue").value,"","pairing code cleared on session switch");
assert.equal(elements.get("composeText").value,"","second session must have its own draft");
assert.match(elements.get("composeTarget").textContent,/Второй чат/);
assert.equal(elements.get("instructionPanel").hidden,true);
assert.equal(elements.get("tasks").children.length,1);
assert.equal(elements.get("records").children.length,1);
await fire("checkNotifierConnection");
assert.equal(elements.get("sessionChatLink").textContent,
  "https://chatgpt.com/c/abcdefgh-22222222");
assert.equal(elements.get("diagnosticChatId").textContent,"abcdefgh-22222222");
assert.equal(elements.get("diagnosticSessionId").textContent,session2);
assert.match(elements.get("notifierConnection").textContent,/код привязки ещё не создавался/);
assert.doesNotMatch(elements.get("notifierConnection").textContent,/mock-only/);
assert.equal(elements.get("history").children.at(-1).textContent.includes("не восстанавливается"),true);
elements.get("sessions").children[0].onclick();
await tick();
assert.ok(elements.get("tasks").children.at(-1).className.includes("active"),
 "opening a different session picks latest task even with follow unchecked");
assert.ok(elements.get("records").children.at(-1).className.includes("active"),
 "opening latest task picks last record even with follow unchecked");
elements.get("sessions").children[1].onclick();
await tick();
await fire("toggleInstructions");
assert.equal(elements.get("instructions").value,"Инструкция два");
await fire("refresh");
assert.equal(elements.get("sessions").children.length,2);
elements.get("sessions").scrollLeft=180;
await fire("refresh");
assert.equal(elements.get("sessions").scrollLeft,180,
  "five-second state refresh must preserve horizontally scrolled tabs");
assert.equal(elements.get("taskCount").textContent,"1");
assert.equal(elements.get("registerPanel").hidden,true);
// Slow state read cannot overlap another poll: one active request at a time.
const baseline=requests.filter(x=>x==="/api/state").length;
holdState=true;
const hanging=poll();
await tick();
assert.equal(typeof releaseState,"function");
await poll();
assert.equal(requests.filter(x=>x==="/api/state").length,baseline+1,
 "a second timer tick must not schedule a second /api/state request");
holdState=false;
releaseState();
await hanging;
assert.equal(requests.filter(x=>x==="/api/state").length,baseline+1);
console.log("Owner Viewer UI synthetic interaction: PASS");

// Step C: lifecycle presentation is independent from legacy event diagnostics.
const flat=e=>String(e.textContent||"")+e.children.map(flat).join(" ");
const fresh=Date.now()/1000;
const overview={version:2,basis:"latest_task",available:true,primary_state:"working",primary_color:"blue",primary_label:"AI в работе",
 checked_at_unix:fresh,working_count:1,pending_count:2,silent_count:1,draft_count:1,
 blocked_count:1,failed_count:1,completed_count:1,incomplete:false};
const states=[
 ["prepared",null,"Черновик сохранён"],["waiting_ai","yellow","Ожидает AI"],
 ["working","blue","AI в работе"],["silent","purple","Долгая тишина"],
 ["unknown","purple","Состояние неизвестно"],["completed","green","Завершено (сообщено AI)"],
 ["failed","red","Ошибка (сообщено AI)"],["blocked",null,"Приостановлено"]
];
const cards=states.map(([state,color,label],i)=>({task_id:"task_"+(i+1).toString(16).repeat(32),state,
 status_color:color,status_label:label,status_checked_at_unix:fresh,original_received:false,
 first_seen_at:new Date().toISOString(),send_label:state==="waiting_ai"?"Отправка инициирована; подтверждение неизвестно":null}));
sandbox.statusFixture={overview,cards,session:session1};
vm.runInContext(`state={sessions:[{reporting_session_id:statusFixture.session,conversation_id:"abcdefgh-01234567",
 title:"Смешанная сессия",state:"REPORTED_COMPLETED",task_overview:statusFixture.overview}]};
 chosenSession=statusFixture.session;chosenTask=statusFixture.cards[0].task_id;taskCards=statusFixture.cards;
 archiveStatusStale=false;taskStatusStale=false;renderSessions();`,sandbox);
let sessionButton=elements.get("sessions").children[0];
assert.equal(sessionButton.attributes["data-status"],"blue");
assert.doesNotMatch(flat(sessionButton),/Ожидают:|В работе:|Черновики:|Ошибки:|Завершено:|Тишина:/);



assert.match(sessionButton.title,/REPORTED_COMPLETED/);
assert.equal(elements.get("tasks").children.length,8);
for(const [i,record] of cards.entries()){
 assert.equal(elements.get("tasks").children[i].attributes["data-status"],record.status_color??undefined);
 assert.ok(flat(elements.get("tasks").children[i]).includes(record.status_label));
}
assert.equal(vm.runInContext('STATUS_COLORS.has("gray")',sandbox),false);
assert.equal(vm.runInContext('STATUS_COLORS.size',sandbox),5);
assert.doesNotMatch(page,/data-status=["']gray["']/);
const renderSession=vm.runInContext("renderSessionStatus",sandbox);
const renderTask=vm.runInContext("renderTaskStatus",sandbox);
const latestDone=new Element("button");
renderSession(latestDone,{...overview,primary_state:"completed",primary_color:"green",primary_label:"Завершено (сообщено AI)",silent_count:99,completed_count:100});
assert.equal(latestDone.attributes["data-status"],"green");
assert.doesNotMatch(flat(latestDone),/99|100|Тишина:|Завершено:/);
const legacySummary=new Element("button");renderSession(legacySummary,{...overview,version:1});
assert.equal(legacySummary.attributes["data-status"],undefined);

const stale=new Element("button");
renderSession(stale,{...overview,checked_at_unix:fresh-60});
assert.equal(stale.attributes["data-status"],undefined);assert.match(flat(stale),/данные устарели/);
assert.doesNotMatch(flat(stale),/Ожидают:|Ошибки:|Завершено:/);
const unavailable=new Element("button");renderSession(unavailable,{version:1,available:false});
assert.equal(unavailable.attributes["data-status"],undefined);assert.match(flat(unavailable),/недоступны/);
const injected=new Element("button");renderTask(injected,{status_label:'<img src=x onerror="boom()">',
 status_color:'red" onclick="boom()',status_checked_at_unix:fresh,send_label:"<script>boom()</script>"});
assert.equal(injected.attributes["data-status"],undefined);assert.match(flat(injected),/<img/);
assert.equal(injected.children.some(e=>e.tagName==="img"||e.tagName==="script"),false);
const chosen=vm.runInContext("chosenTask",sandbox),sentBefore=postRequests.length;
const savedFetch=sandbox.fetch;sandbox.fetch=async()=>{throw Error("synthetic offline")};
await fire("refresh");sandbox.fetch=savedFetch;
sessionButton=elements.get("sessions").children[0];
assert.equal(sessionButton.attributes["data-status"],undefined);assert.match(flat(sessionButton),/данные устарели/);
assert.equal(vm.runInContext("chosenTask",sandbox),chosen);assert.equal(elements.get("tasks").children.length,8);
assert.equal(postRequests.length,sentBefore,"status rendering/poll failure never dispatches Send");
console.log("Owner Viewer lifecycle colors, latest-task session, stale data and safe DOM: PASS");

// A hung read must not keep an old blue indicator looking current indefinitely.
overview.checked_at_unix=Date.now()/1000-60;
for(const record of cards)record.status_checked_at_unix=Date.now()/1000-60;
vm.runInContext('archiveStatusStale=false;taskStatusStale=false;archiveRefreshBusy=true',sandbox);
const beforeBusyTick=requests.length;
await poll();
assert.equal(requests.length,beforeBusyTick,"busy timer never starts overlapping reads");
sessionButton=elements.get("sessions").children[0];
assert.equal(sessionButton.attributes["data-status"],undefined);
assert.match(flat(sessionButton),/данные устарели/);
assert.doesNotMatch(flat(sessionButton),/Ожидают:|В работе:|Черновики:|Ошибки:|Завершено:|Тишина:/);
assert.equal(vm.runInContext("chosenTask",sandbox),chosen);
assert.equal(postRequests.length,sentBefore);
vm.runInContext('archiveRefreshBusy=false',sandbox);
console.log("Owner Viewer hung-read staleness and no overlapping requests: PASS");


// Discovery is owner-viewer-only, creates no command, and preserves selection.
const discoveryChat="discovered-chat-12345678";
const discoveryFp="abcde1234567";
responses["/api/notifier/discovered"]={ok:true,chats:[{
 chat:discoveryChat,fingerprints:[discoveryFp],last_seen_seconds_ago:2,blocked:false
}]};
// Restore the ordinary server fixture after the preceding synthetic stale snapshot.
elements.get("autoFollow").checked=false;
sandbox.discoveryStateFixture=responses["/api/state"];
sandbox.discoveryTaskFixture=responses["/api/tasks?session="+session1].tasks;
vm.runInContext("state=discoveryStateFixture;taskCards=discoveryTaskFixture;chosenTask=taskCards[0].task_id;renderSessions()",sandbox);
const selectedSessionBeforeDiscovery=vm.runInContext("chosenSession",sandbox);
const selectedTaskBeforeDiscovery=vm.runInContext("chosenTask",sandbox);
const commandsBeforeDiscovery=postRequests.length;
await vm.runInContext("refreshDiscoveredChats()",sandbox);
let discoveryRow=elements.get("discoveredChats").children[0];
assert.equal(discoveryRow.children[0].href,"https://chatgpt.com/c/"+discoveryChat);
assert.equal(discoveryRow.children[0].textContent,discoveryChat);
assert.equal(discoveryRow.children[2].disabled,false);
responses["/api/notifier/discovered"]={ok:true,chats:[]};
const discoveryRequestsBefore=requests.length;
await discoveryRow.children[2].onclick();
assert.ok(requests.slice(discoveryRequestsBefore).includes("/api/notifier/connect"));
assert.equal(vm.runInContext("chosenSession",sandbox),selectedSessionBeforeDiscovery);
assert.equal(vm.runInContext("chosenTask",sandbox),selectedTaskBeforeDiscovery);
assert.equal(postRequests.length,commandsBeforeDiscovery,"connecting a chat never sends text");
assert.equal(elements.get("discoveredChats").children.length,0);

responses["/api/notifier/discovered"]={ok:true,chats:[{
 chat:discoveryChat,fingerprints:[discoveryFp,"123456789abc"],last_seen_seconds_ago:1,blocked:false
}]};
await vm.runInContext("refreshDiscoveredChats()",sandbox);
discoveryRow=elements.get("discoveredChats").children[0];
assert.equal(discoveryRow.children[2].disabled,true);
assert.match(discoveryRow.children[1].textContent,/несколько Notifier/);
const beforeAmbiguous=requests.length;
await discoveryRow.children[2].onclick();
assert.equal(requests.length,beforeAmbiguous);
responses["/api/notifier/discovered"]={ok:true,chats:[{
 chat:"<script>bad</script>",fingerprints:[discoveryFp],last_seen_seconds_ago:1,blocked:false
}]};
await vm.runInContext("refreshDiscoveredChats()",sandbox);
assert.match(elements.get("discoveryStatus").textContent,/недоступен/);
assert.equal(elements.get("discoveredChats").children[0].children[2].disabled,true);
console.log("Owner Viewer discovered-chat connection, ambiguity and safe DOM: PASS");


// Human captions remain inert text and do not replace chat/session identities.
const humanTitle="Проект 🧪 <b>Альфа</b>";
responses["/api/notifier/discovered"]={ok:true,chats:[{
 chat:discoveryChat,title:humanTitle,fingerprints:[discoveryFp],last_seen_seconds_ago:1,blocked:false
}],session_titles:{[session1]:"Проект Альфа"}};
const taskBeforeTitle=vm.runInContext("chosenTask",sandbox);
await vm.runInContext("refreshDiscoveredChats()",sandbox);
discoveryRow=elements.get("discoveredChats").children[0];
assert.equal(discoveryRow.children[0].textContent,humanTitle);
assert.equal(discoveryRow.children[0].href,"https://chatgpt.com/c/"+discoveryChat);
assert.equal(discoveryRow.children[3].textContent,"ID: "+discoveryChat);
assert.equal(discoveryRow.children[0].children.length,0,"title markup is inert");
assert.equal(elements.get("sessions").children[0].textContent,"Проект Альфа");
assert.equal(vm.runInContext("chosenTask",sandbox),taskBeforeTitle);
responses["/api/notifier/discovered"].chats[0].title="Переименованный чат";
responses["/api/notifier/discovered"].session_titles[session1]="Обновлённый проект";
await vm.runInContext("refreshDiscoveredChats()",sandbox);
assert.equal(elements.get("discoveredChats").children[0].children[0].textContent,"Переименованный чат");
assert.equal(elements.get("sessions").children[0].textContent,"Обновлённый проект");
assert.equal(vm.runInContext("chosenTask",sandbox),taskBeforeTitle);
console.log("Owner Viewer private tab titles, live rename, safe DOM and stable task: PASS");

const beforeKeyboard=vm.runInContext("chosenSession",sandbox);
let tabSelectPrevented=false;
const buttonsBefore=elements.get("sessions").children;
const firstSelected=buttonsBefore.findIndex(b=>b.attributes["aria-selected"]==="true");
const keyboardFrom=buttonsBefore[firstSelected];
elements.get("sessions").listeners.keydown({
 key:"ArrowRight",target:keyboardFrom,preventDefault(){tabSelectPrevented=true}
});
assert.equal(tabSelectPrevented,true);
assert.notEqual(vm.runInContext("chosenSession",sandbox),beforeKeyboard,
 "right arrow must switch the active session");
await tick();
assert.equal(elements.get("sessions").children.filter(
 b=>b.attributes["aria-selected"]==="true").length,1);
const otherActive=elements.get("sessions").children.find(
 b=>b.attributes["aria-selected"]==="true");
elements.get("sessions").listeners.keydown({
 key:"ArrowLeft",target:otherActive,preventDefault(){}
});
assert.equal(vm.runInContext("chosenSession",sandbox),beforeKeyboard,
 "left arrow returns to the previous session");
await tick();
console.log("Owner Viewer sticky session tabs, keyboard and horizontal scroll: PASS");

assert.match(page,/id="composeSendDelay"/);
assert.match(page,/id="composeRestoreDraft"/);
assert.match(page,/Файл \+ Send/);
const durableSample="Точный черновик 🌙\nвторая строка";
assert.equal(vm.runInContext("safeDraftWrite("+JSON.stringify(session1)+","+JSON.stringify(durableSample)+")",sandbox),true);
assert.equal(vm.runInContext("safeDraftRead("+JSON.stringify(session1)+")",sandbox),durableSample);
assert.equal(vm.runInContext("markDraftSent("+JSON.stringify(session1)+","+JSON.stringify(durableSample)+")",sandbox),true);
assert.equal(vm.runInContext("safeDraftRead("+JSON.stringify(session1)+")",sandbox),"",
 "confirmed one-shot Send leaves the editor empty across page reload");
assert.equal(vm.runInContext("safeDraftRecovery("+JSON.stringify(session1)+").text",sandbox),durableSample,
 "sent original stays recoverable in the owner-only local browser profile");
const savedBefore=JSON.parse(savedStorage.get("fortis-owner-draft-v1-"+session1));
assert.equal(savedBefore.sent,true);
const existingOrder=elements.get("sessions").children.map(b=>b.dataset.sessionId);
assert.equal(existingOrder.length,2);
vm.runInContext("moveSessionTab("+JSON.stringify(existingOrder[1])+","+JSON.stringify(existingOrder[0])+")",sandbox);
assert.equal(elements.get("sessions").children[0].dataset.sessionId,existingOrder[1],
 "manual tab order must affect only tabs, not archive order");
assert.equal(JSON.parse(savedStorage.get("fortis-owner-session-tab-order-v1"))[0],existingOrder[1],
 "manual tab order must survive refresh");
assert.deepEqual(elements.get("sessions").children.filter(b=>b.attributes["aria-selected"]==="true").length,1);
console.log("Owner Viewer durable drafts, sent recovery, reorder: PASS");
