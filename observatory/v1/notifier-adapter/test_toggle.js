"use strict";
const assert = require("node:assert/strict");
const path = require("node:path");
const root = process.argv[2];
if (!root) throw Error("Usage: node test_toggle.js <patched-notifier-root>");
const {createResponseMonitor} = require(path.resolve(root, "src/response-monitor.js"));
const {createCompletionModeSettings, createObservatoryCompletionBridge} =
  require(path.resolve(root, "src/observatory-completion.js"));
const {SYMBOLS} = require(path.resolve(root, "src/config.js"));
const {faviconSvg, cleanTitle} = require(path.resolve(root, "src/title-utils.js"));

let now = 1700000000000;
Date.now = () => now;
const storage = new Map(), alerts = [];
global.location = {href:"https://chatgpt.com/c/12345678-abcd"};
global.sessionStorage = {
  getItem(key) {return storage.get(key) ?? null;},
  setItem(key, value) {storage.set(key, value);}
};
const modes = createCompletionModeSettings({show: msg => alerts.push(msg)});
const check = (mode, dom, obs) => {
  assert.equal(modes.getMode(),mode);
  assert.equal(modes.domEnabled(),dom);
  assert.equal(modes.observatoryEnabled(),obs);
};
check("both",true,true);
modes.toggleDom();check("observatory",false,true);
assert.match(alerts.at(-1),/DOM Tab Notifier: ВЫКЛ/);
modes.toggleObservatory();check("off",false,false);
modes.toggleDom();check("dom",true,false);
modes.toggleObservatory();check("both",true,true);
modes.toggleDom();check("observatory",false,true);
assert.equal(createCompletionModeSettings({show:()=>{}}).getMode(),"observatory");
location.href="https://chatgpt.com/c/87654321-abcd";check("both",true,true);
location.href="https://chatgpt.com/c/12345678-abcd";check("observatory",false,true);
assert.equal(SYMBOLS["observatory-working"],"🔵");
assert.equal(cleanTitle("🔵 Synthetic chat"),"Synthetic chat");
assert.ok(decodeURIComponent(faviconSvg("observatory-working")).includes("#2563eb"));

let generating=false, queuedActions=0, uploadReset=0;
const notices=[], notifications={notifyFinished:(source="dom")=>notices.push(source)};
global.document = {
  hidden: true, hasFocus:()=>false,
  querySelector:()=>generating ? {} : null,
  querySelectorAll:()=>[]
};
const pending=new Map();
let timerId=0;
const originalTimeout=global.setTimeout, originalClear=global.clearTimeout;
global.setTimeout=(fn,delay)=>{const id=++timerId;pending.set(id,{fn,delay});return id;};
global.clearTimeout=id=>pending.delete(id);
const state={
  current:"idle",
  setState(x){this.current=x;},
  getState(){return this.current;}
};
const pair = {
  version:1, origin:"http://127.0.0.1:18753",
  conversation_id:"12345678-abcd",
  reporting_session_id:"rs_"+"a".repeat(32),
  observer_key:"s".repeat(43)
};
global.GM_getValue=()=>pair;
const requests=[];
global.GM_xmlhttpRequest=data=>requests.push(data);
let bridge=null;
const monitor=createResponseMonitor({
  tabState:state,notifications,
  isDomEnabled:()=>modes.domEnabled(),
  beforeArm:()=>uploadReset++,
  onArmed:()=>bridge?.noteArmed(),
  onFinished:()=>queuedActions++
});
bridge=createObservatoryCompletionBridge({
  tabState:state,responseMonitor:monitor,
  isEnabled:()=>modes.observatoryEnabled()
});
const status=(sequence,event,acceptedMs=now)=>({
  ok:true,version:1,conversation_id:pair.conversation_id,
  reporting_session_id:pair.reporting_session_id,
  sequence,event,accepted_unix:acceptedMs/1000
});
const poll=(sequence,event,acceptedMs=now)=>{
  now+=4000;
  bridge.check();
  assert.equal(requests.length,1,"observer-only/both mode polls once");
  requests.pop().onload({
    status:200,responseText:JSON.stringify(status(sequence,event,acceptedMs))
  });
};

// Only Observatory: no DOM-start or DOM-finish.
assert.equal(monitor.armAnswer("send-button"),false);
generating=true;monitor.check();generating=false;monitor.check();
assert.equal(state.current,"idle","DOM must not start in observer-only mode");
assert.equal(uploadReset,0,"DOM-disabled event must not cancel upload");
poll(1,"none",null);
assert.equal(state.current,"idle");
poll(2,"started",now);
assert.equal(state.current,"observatory-working");
assert.equal(uploadReset,0,"observer start must not emulate click");
assert.equal(monitor.isArmed(),true);
assert.equal(queuedActions,0);
generating=true;monitor.check();generating=false;monitor.check();
assert.equal(state.current,"observatory-working","DOM cannot complete observer run");
poll(3,"progress",now);
assert.equal(state.current,"observatory-working");
poll(4,"completed",now);
assert.equal(state.current,"observatory-fresh");
assert.deepEqual(notices,["observatory"]);
assert.equal(queuedActions,0,"observer finish does not auto-send");
assert.equal(monitor.isArmed(),false);

// A fresh progress event can indicate start if started was missed by polling.
poll(5,"progress",now);
assert.equal(state.current,"observatory-working");
poll(6,"completed",now);
assert.equal(state.current,"observatory-fresh");
assert.equal(queuedActions,0);

// Stale older progress/start cannot wake an idle tab.
state.setState("idle");
poll(7,"started",now-180000);
assert.equal(state.current,"idle");
poll(8,"progress",now-180000);
assert.equal(state.current,"idle");

// Existing old completed on first poll after navigation must not finish new task.
bridge.resetForNavigation();
state.setState("idle");
poll(9,"completed",now);
assert.equal(state.current,"idle");

// Late HTTP response after turning Observatory off must be ignored.
now+=4000;bridge.check();
assert.equal(requests.length,1);
modes.toggleObservatory();check("off",false,false);
requests.pop().onload({status:200,responseText:JSON.stringify(status(10,"started"))});
assert.equal(state.current,"idle");
now+=4000;bridge.check();
assert.equal(requests.length,0,"no polling in off mode");

// DOM-only: click and native DOM detection set state, native finish fires queue.
modes.toggleDom();check("dom",true,false);
assert.notEqual(monitor.armAnswer("manual"),false, "enabled DOM arm proceeds");
assert.equal(state.current,"working");
assert.equal(uploadReset,1);
generating=true;monitor.check();
generating=false;monitor.check();
const [timerId1,timer]=Array.from(pending.entries()).filter(([,x])=>x.delay===1800).at(-1);
assert.ok(timer,"native finish confirmation timer set");
pending.delete(timerId1);
timer.fn();
assert.equal(state.current,"fresh");
assert.deepEqual(notices,["observatory","observatory","dom"]);
assert.equal(queuedActions,1);
now+=4000;bridge.check();assert.equal(requests.length,0);

// Both: DOM begins; Observatory confirms work with blue; DOM detects native end.
modes.toggleObservatory();check("both",true,true);
monitor.armAnswer("manual");
assert.equal(state.current,"working");
poll(11,"started",now);
assert.equal(state.current,"observatory-working");
generating=true;monitor.check();
assert.equal(state.current,"observatory-working","blue source kept during streaming");
generating=false;monitor.check();
const [timerId2,timer2]=Array.from(pending.entries()).filter(([,x])=>x.delay===1800).at(-1);
assert.ok(timer2);
pending.delete(timerId2);
timer2.fn();
assert.equal(state.current,"fresh");
assert.equal(queuedActions,2);

// Off: neither source can start or finish.
modes.toggleDom();modes.toggleObservatory();check("off",false,false);
state.setState("idle");monitor.resetForNavigation();
assert.equal(monitor.armAnswer("manual"),false);
generating=true;monitor.check();
assert.equal(state.current,"idle");
now+=4000;bridge.check();
assert.equal(requests.length,0);
global.setTimeout=originalTimeout;
global.clearTimeout=originalClear;
console.log("DUAL_START_FINISH_FOUR_MODES_TEST PASS");

