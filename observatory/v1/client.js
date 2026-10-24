"use strict";
const $ = selector => document.querySelector(selector);
let token = "";
let lastResult = null;
const safe = value => String(value ?? "");
const clock = value => value ? new Date(value).toLocaleString("ru-RU") : "—";
function node(tag, text, cls) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = safe(text);
  if (cls) el.className = cls;
  return el;
}
async function call(path, options={}) {
  if (!token) throw Error("Авторизация не выполнена");
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", "Bearer " + token);
  const resp = await fetch(path,{...options, headers, credentials:"omit", cache:"no-store"});
  if (!resp.ok) throw Error("HTTP " + resp.status);
  return resp.json();
}
function showStatus(text) { $("#formStatus").textContent = safe(text); }
async function showPairing(sid) {
  const info = await call("/api/observer-pair?session=" + encodeURIComponent(sid));
  $("#pairingText").value = JSON.stringify(info.pairing);
  $("#pairingPanel").hidden = false;
  $("#pairingDescription").textContent = "Только чтение состояния сессии; записи текста не разрешены.";
}
async function showWriterPairing(sid) {
  const info = await call("/api/message-writer-pair?session=" + encodeURIComponent(sid));
  $("#pairingText").value = JSON.stringify(info.pairing);
  $("#pairingPanel").hidden = false;
  $("#pairingDescription").textContent =
    "Код содержит отдельное разрешение на запись исходных сообщений в приватный архив " +
    "после принятого сигнала по task_id. Не вставляй его в чат или GitHub.";
}
async function showInstructions(sid) {
  const info = await call("/api/instructions?session=" + encodeURIComponent(sid));
  $("#instructionText").value = info.text;
  $("#instructions").hidden = false;
}
function render(data) {
  lastResult = data;
  const select = $("#route");
  const previous = select.value;
  select.replaceChildren();
  for (const route of data.routes || []) {
    const item = node("option", route);
    item.value = route;
    select.append(item);
  }
  if (data.routes.includes(previous)) select.value = previous;
  $("#register").querySelector("button").disabled = !data.routes.length;
  const stats = data.ingest || {};
  $("#ingest").textContent = "Приёмник: " + safe(stats.state || "unknown") +
    "; принято за последний проход: " + safe(stats.accepted || 0) +
    "; отклонено: " + safe(stats.rejected || 0) +
    "; неизвестная сессия: " + safe(stats.unknown_session || 0);
  const host = $("#sessions");
  host.replaceChildren();
  if (!data.sessions.length) {
    host.append(node("p", "Пока нет вручную подключённых сессий.", "dim"));
    return;
  }
  for (const session of data.sessions) {
    const card = node("article", undefined, "session");
    const header = node("div", undefined, "row");
    const title = node("div");
    title.append(node("h3", session.title));
    title.append(node("small", "Chat ID: " + session.conversation_id +
        " · reporting session: " + session.reporting_session_id +
        " · заявленный маршрут: " + session.route + " · V1 enrollment: " + session.task_id +
        (session.last_task_id ? " · последняя работа: " + session.last_task_id : "")));
    const badge = node("span", session.state, "state");
    header.append(title, badge);
    card.append(header);
    card.append(node("p", "Полученных событий: " + session.events_count +
      " · пропуски в нумерации: " + (session.missing_sequences || 0) +
      " · некорректных файлов: " + (session.invalid_files || 0) +
      (session.truncated_events ? " · история усечена" : "") +
      " · последний сигнал: " + clock(session.last_signal_at), "dim"));
    const more = node("button", "Скопировать инструкцию", "secondary");
    more.type = "button";
    more.addEventListener("click", () => showInstructions(session.reporting_session_id)
      .catch(e => showStatus("Инструкция недоступна: " + e.message)));
    card.append(more);
    const pair = node("button", "Код для Tab Notifier", "secondary");
    pair.type = "button";
    pair.addEventListener("click", () => showPairing(session.reporting_session_id)
      .catch(e => showStatus("Привязка недоступна: " + e.message)));
    card.append(pair);
    const writer = node("button", "Код с правом записи сообщений", "secondary");
    writer.type = "button";
    writer.addEventListener("click", () => showWriterPairing(session.reporting_session_id)
      .catch(e => showStatus("Код записи недоступен: " + e.message)));
    card.append(writer);
    const list = node("ol", undefined, "timeline");
    for (const event of session.events) {
      const line = node("li");
      line.append(node("strong", event.event + " / " + event.stage + " / #" + event.sequence +
        " / task: " + event.task_id));
      line.append(node("time", " · принято: " + clock(event.accepted_at)));
      line.append(node("p", event.summary));
      list.append(line);
    }
    card.append(list);
    host.append(card);
  }
}
async function refresh() {
  if (!token) return;
  try {render(await call("/api/state"));}
  catch(e) {$("#ingest").textContent = "Недоступно: " + e.message;}
}
$("#unlockForm").addEventListener("submit", async e => {
  e.preventDefault();
  const proposed = $("#token").value.trim();
  $("#token").value = "";
  token = proposed;
  try {
    render(await call("/api/state"));
    $("#unlock").hidden = true;
    $("#privateUI").hidden = false;
  } catch(e) {
    token = "";
    $("#unlockError").textContent = "Доступ не подтверждён. Проверь токен в консоли владельца.";
  }
});
$("#register").addEventListener("submit", async e => {
  e.preventDefault();
  showStatus("Подключение…");
  try {
    const body = {url: $("#chatUrl").value.trim(), title: $("#taskTitle").value.trim(),
                  route: $("#route").value};
    const result = await call("/api/sessions", {method:"POST",
      headers: {"Content-Type":"application/json"}, body:JSON.stringify(body)});
    await showInstructions(result.session.reporting_session_id);
    await refresh();
    showStatus("Сессия добавлена. Вставь инструкцию в нужный чат.");
  } catch(e) { showStatus("Ошибка регистрации: " + e.message); }
});
$("#copyInstructions").addEventListener("click", async () => {
  try {await navigator.clipboard.writeText($("#instructionText").value);
       showStatus("Инструкция скопирована.");}
  catch(e) { $("#instructionText").focus(); $("#instructionText").select();
             showStatus("Не удалось скопировать автоматически. Выдели текст и скопируй вручную.");}
});
$("#copyPairing").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText($("#pairingText").value);
    showStatus("Код привязки скопирован. Не вставляй его в чат.");
  } catch(e) {
    $("#pairingText").focus();
    $("#pairingText").select();
    showStatus("Выдели код и скопируй вручную, только в меню Tab Notifier.");
  }
});
$("#refresh").addEventListener("click",refresh);
setInterval(refresh,5000);
