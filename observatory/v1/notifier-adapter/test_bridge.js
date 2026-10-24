"use strict";
const assert = require("node:assert/strict");
const { createObservatoryCompletionBridge } = require("./observatory-completion.js");

let now = 1700000000000;
Date.now = () => now;
global.location = { href: "https://chatgpt.com/c/12345678-abcd" };
const pair = {
  version: 1, origin: "http://127.0.0.1:18753", conversation_id: "12345678-abcd",
  reporting_session_id: "rs_" + "1".repeat(32), observer_key: "s".repeat(43)
};
let saved = pair;
let sent = [];
let currentState = "working";
let finishes = 0;
global.GM_getValue = () => saved;
global.GM_xmlhttpRequest = args => { sent.push(args); };

const bridge = createObservatoryCompletionBridge({
  tabState: { getState: () => currentState },
  responseMonitor: { finishFromExternal: () => { finishes++; currentState = "fresh"; return true; } }
});
bridge.noteArmed();
bridge.check();
assert.equal(sent.length, 1, "paired chat polls Observatory");
assert.equal(sent[0].headers["X-Fortis-Observer-Key"], pair.observer_key);
const answer = (sequence, event, accepted) => ({
  ok: true, version: 1, conversation_id: pair.conversation_id,
  reporting_session_id: pair.reporting_session_id, sequence, event,
  accepted_unix: accepted / 1000
});
sent.pop().onload({status:200,responseText:JSON.stringify(answer(1,"completed",now-5000))});
assert.equal(finishes, 0, "old completed event does not finish a newly started response");
now += 4000;
bridge.check();
sent.pop().onload({status:200,responseText:JSON.stringify(answer(2,"completed",now))});
assert.equal(finishes, 1, "new chat event finishes when notifier is stuck");
now += 4000;
bridge.check();
sent.pop().onload({status:200,responseText:JSON.stringify(answer(2,"completed",now))});
assert.equal(finishes, 1, "same completion is not repeated");
currentState = "working";
bridge.noteArmed();
now += 4000;
bridge.check();
sent.pop().onload({status:200,responseText:JSON.stringify(answer(2,"completed",now-3000))});
assert.equal(finishes, 1, "previous task completion does not finish later work");
global.location.href = "https://chatgpt.com/c/87654321-abcd";
saved = null;
now += 4000;
bridge.check();
assert.equal(sent.length, 0, "unpaired chat cannot poll or inherit other chat credentials");
console.log("OBSERVER_NOTIFIER_BRIDGE_TESTS PASS");
