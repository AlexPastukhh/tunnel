"use strict";
// Synthetic no-browser regression test for distinct Observatory tab indicators.
const assert = require("node:assert/strict");
const path = require("node:path");
const source = process.argv[2];
if (!source) throw Error("Usage: node test_color.js <patched-notifier-root>");
const req = name => require(path.resolve(source, "src", name));
const {SYMBOLS, STORAGE_KEY} = req("config.js");
const {cleanTitle, faviconSvg} = req("title-utils.js");
const {createTabStateController} = req("tab-state.js");
const {createNotificationService} = req("notifications.js");
const {createResponseMonitor} = req("response-monitor.js");

const storage = new Map();
const icons = new Map();
const notifications = [];
global.GM_notification = data => notifications.push(data);
global.location = {href: "https://chatgpt.com/c/12345678-abcd"};
global.sessionStorage = {
  getItem: key => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, value)
};
global.document = {
  title: "Synthetic conversation",
  hidden: true,
  hasFocus: () => false,
  getElementById: id => icons.get(id) ?? null,
  createElement: tag => ({tagName: tag, remove() { icons.delete(this.id); }}),
  head: {appendChild: element => { if (element.id) icons.set(element.id, element); }},
  querySelectorAll: () => [],
  querySelector: () => null
};

assert.equal(SYMBOLS.fresh, "●");
assert.equal(SYMBOLS.viewed, "✓");
assert.equal(SYMBOLS["observatory-fresh"], "🔷");
assert.equal(SYMBOLS["observatory-viewed"], "🔹");
assert.equal(cleanTitle("🔷 Synthetic conversation"), "Synthetic conversation");
assert.equal(cleanTitle("🔹 Synthetic conversation"), "Synthetic conversation");
assert.ok(decodeURIComponent(faviconSvg("observatory-fresh")).includes("#2563eb"));
assert.ok(decodeURIComponent(faviconSvg("observatory-viewed")).includes("#1d4ed8"));

const state = createTabStateController({});
const notice = createNotificationService(state);
let queuedActions = 0;
const monitor = createResponseMonitor({
  tabState: state, notifications: notice,
  onFinished: () => queuedActions++
});
monitor.armAnswer("synthetic");
assert.equal(state.getState(), "working");
assert.ok(document.title.startsWith("⏳ "));
assert.equal(monitor.finishFromExternal(), true);
assert.equal(state.getState(), "observatory-fresh");
assert.ok(document.title.startsWith("🔷 "));
assert.equal(queuedActions, 0);
assert.equal(notifications.length, 1);
assert.ok(notifications[0].title.startsWith("Fortis Observatory"));
assert.equal(JSON.parse(storage.get(STORAGE_KEY)).state, "observatory-fresh");

state.markViewed();
assert.equal(state.getState(), "observatory-viewed");
assert.ok(document.title.startsWith("🔹 "));
assert.equal(JSON.parse(storage.get(STORAGE_KEY)).state, "observatory-viewed");
monitor.armAnswer("next-message");
assert.equal(state.getState(), "working");
assert.ok(document.title.startsWith("⏳ "));
state.setState("fresh");
notice.notifyFinished();
assert.equal(notifications[1].title, "ChatGPT — ответ готов");
state.markViewed();
assert.equal(state.getState(), "viewed");
assert.ok(document.title.startsWith("✓ "));
monitor.resetForNavigation();
console.log("COLOR_AND_SOURCE_REGRESSION_TEST PASS");
