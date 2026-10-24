"""Manual Windows-owner Edge viewer for the SINGLE Fortis Repo Docker archive.

This owner-local viewer permits scoped registration and explicit per-session
Notifier dispatch after owner-granted pairing. It is NOT a second Observatory,
archive or AI message path. Dispatch remains in memory and is at-most-once.
Only docker exec with a pinned container name is used.
No Docker TCP ports are exposed. Only the approved Windows user may launch
from a protected local installation with an owner-private approval file.

The ephemeral localhost HTTP bearer is printed to the owner console, not
embedded in a URL, disk file, ChatGPT prompt or browser storage.
"""
import argparse
import csv
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import threading
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit
from owner_notifier_bridge import owner_pair, scoped_request
from owner_dispatch import DispatchBoard
from owner_enrollment import Enrollment

WIN_PORT = 18755
DOCKER_SERVICE = "/workspace/repos/tunnel/observatory/v1/repo_service.py"
DOCKER_READER = "/workspace/repos/tunnel/observatory/v1/repo_viewer_export.py"
REPO_STATE = "/workspace/repo/fortis-observatory-repo-v1"
SID = re.compile(r"rs_[0-9a-f]{32}\Z")
TASK = re.compile(r"task_[0-9a-f]{32}\Z")
CONTAINER = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{2,119}\Z")
WIN_SID = re.compile(r"S-1-5-(?:[0-9]+-){2,}[0-9]+\Z")
CHAT_URL = re.compile(r"https://chatgpt\.com/c/([A-Za-z0-9-]{8,100})\Z")
SAFE_TITLE = re.compile(r"[\w .,;:!?()\-–]{1,80}\Z", re.UNICODE)
BAD_TITLE = re.compile(r"(?i)(?:\b(?:password|secret|bearer|token|api.?key)\b|\bsk-[a-z0-9]+)")
MAX_REGISTER_BODY = 512
MAX_DISPATCH_BODY = 1024 * 1024
MAX_ORIGINAL_BODY = 4 * 1024 * 1024
MAX_PAYLOAD = 5 * 1024 * 1024

# Render all untrusted text through textContent, never innerHTML.
PAGE = r'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fortis Observatory — Docker archive</title>
<style nonce="__NONCE__">
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:#10151f;color:#e8ecf4;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0 auto;max-width:1700px;padding:15px clamp(12px,2vw,30px)}
h1{font-size:1.35rem;margin:0}h2{font-size:1.08rem;margin:0 0 12px}h3{font-size:1rem}
p{line-height:1.5}.dim{color:#9eafc6}
.sticky-top{position:sticky;top:0;z-index:30;background:#10151f;padding:10px 0 8px;box-shadow:0 4px 12px #10151f}
.masthead{display:flex;align-items:baseline;flex-wrap:wrap;gap:8px 22px;margin:0 0 10px}
.masthead .dim{font-size:.84rem;margin:0}
.panel{border:1px solid #34465f;border-radius:10px;background:#192231;padding:15px}
button,input,textarea{font:inherit;border-radius:6px;padding:9px 12px}
input,textarea{background:#0e1521;border:1px solid #596782;color:white;max-width:100%}
textarea{width:100%;resize:vertical}
label{display:block;margin:10px 0}label input{display:block;width:min(100%,700px);margin-top:6px}
button{border:1px solid #6981a6;background:#2b3e5a;color:white;cursor:pointer}
button:hover{background:#384f6f}button:focus-visible,input:focus-visible,textarea:focus-visible{outline:2px solid #8abaff;outline-offset:2px}
button.secondary{background:#213148;border-color:#536783}
button.active,.action-toggle[aria-expanded="true"]{border-color:#a3c4f7;background:#385478}
.toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:10px 12px;margin:0;border:1px solid #34465f;border-radius:10px;background:#192231}
.toolbar button{padding:7px 11px}
#status{margin-left:auto;color:#b5c8df;font-size:.84rem}
.session-tab-bar{display:block;padding:5px 12px 6px;
  border:1px solid #34465f;border-top:0;border-radius:0 0 10px 10px;background:#192231;min-width:0}
.session-online-row{display:flex;align-items:stretch;gap:12px;min-width:0}
.session-secondary-row{display:flex;align-items:center;gap:9px;margin:3px 0 2px;
  min-width:0;border-top:1px solid #34465f;padding:6px 0 2px;flex-wrap:wrap}
.session-secondary-row[hidden]{display:none}
.session-secondary-row .group-label{color:#8ce2db;font-size:.79rem;white-space:nowrap}
#discoveryTabs{display:flex;gap:5px;overflow-x:auto;min-width:0;scrollbar-width:thin}
#discoveryTabs button{flex:0 0 auto;max-width:230px;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;padding:5px 11px;border:1px dashed #50b9b5;
  color:#b6fff0;background:#123c45}
#discoveryTabs button:hover{background:#20505b}
.session-fold{border-top:1px solid #34465f;padding-top:5px;margin:3px 0}
.session-fold[hidden]{display:none}
.session-fold summary{cursor:pointer;font-size:.8rem;color:#d5c8ad;padding:4px 0;
  list-style:disclosure-closed}
.session-fold[open] summary{list-style:disclosure-open}
.offline-tabs{display:flex;flex-wrap:wrap;gap:5px;padding:5px 0}
.offline-tabs button{font-size:.82rem;padding:5px 11px;border-color:#806d58;
  background:#38342e;color:#edcaaa;max-width:240px;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.offline-tabs button.linked{background:#4c3527;color:#ffdcad;border-color:#d9a258}
.offline-tabs button.unpaired{background:#243140;color:#b5c7d9;border-color:#6d819c}
.offline-tabs button[aria-selected="true"]{color:#fff;border:2px solid #fff3c2;
  box-shadow:0 0 0 2px #18283c}
.archive-tab-list{display:flex;flex-wrap:wrap;gap:7px;padding:7px 0}
.archive-tab-list button{background:#273647;font-size:.8rem;padding:5px 10px}
#sessionArchiveNotice{font-size:.76rem;color:#a6c1d5}
#sessions button.session.active{
  background:#365c93;border-color:#f1f8ff;color:#fff;font-weight:750;
  outline:2px solid #a8d5ff;outline-offset:-3px;
  box-shadow:0 0 0 2px #132e51,0 4px 14px #0009}
#sessions button.session.active::before{content:"●";color:#d6f9ff;margin-right:7px}
#sessions button.session.available{border-top:2px solid #66d7a8}
#sessions button.session:not(.active){color:#cbdcf3}
.session-tab-bar .tab-label{flex:0 0 auto;font-size:.78rem;color:#a9bed8;
  align-self:center;white-space:nowrap}
#sessions{display:flex;flex:1 1 auto;gap:6px;min-width:0;padding:4px 0 6px;
  overflow-x:auto;overflow-y:hidden;scrollbar-width:thin;overscroll-behavior-x:contain}
#sessions button.session{flex:0 0 auto;width:auto;max-width:220px;min-height:36px;
  text-align:left;margin:0;padding:7px 12px;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap;border-bottom:3px solid transparent;border-radius:7px 7px 3px 3px}
#sessions button.session.active{background:#385478;border-color:#a3c4f7}
#sessions button.session{cursor:grab;touch-action:pan-y;user-select:none;-webkit-user-select:none}
#sessions button.session.sliding{cursor:grabbing;position:relative;z-index:3;
  box-shadow:0 7px 18px #0009;filter:brightness(1.14);will-change:transform}
#sessions.sliding-tabs{cursor:grabbing}
@media(prefers-reduced-motion:reduce){
  #sessions button.session.sliding{filter:none}
}
#sessions button.session[data-status]{border-left:1px solid #6981a6;
  border-bottom-color:var(--status-color)}
#sessions button.session .status-line,#sessions button.session .status-note{
  position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;
  overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0}
.action-panel{margin:0 0 12px}
.action-panel textarea{max-width:100%;margin:6px 0}
.action-panel button{margin:6px 8px 0 0}
.workspace-viewport{overflow-x:auto;margin-top:12px}
.grid{display:grid;min-width:1090px;grid-template-columns:minmax(165px,.8fr) 10px minmax(205px,1fr) 10px minmax(250px,1.35fr) 10px minmax(325px,1.8fr);gap:0;align-items:start}
.grid>.panel{min-width:0;min-height:calc(100vh - 160px)}
.grid h2{display:flex;align-items:baseline;justify-content:space-between;gap:8px}
.grid h2 small{font-size:.8rem;font-weight:400}
#tasks,#records{overflow-y:auto;max-height:calc(100vh - 275px)}
.column-resizer{align-self:stretch;min-height:220px;cursor:col-resize;touch-action:none;position:relative;outline-offset:-2px}
.column-resizer::after{content:"";position:absolute;top:0;bottom:0;left:4px;width:2px;background:#425674;border-radius:3px}
.column-resizer:hover::after,.column-resizer:focus-visible::after,.column-resizer.dragging::after{background:#96bfff;width:4px;left:3px}
.column-resizer:focus-visible{outline:2px solid #96bfff}
.record{display:block;width:100%;text-align:left;margin:8px 0;padding:10px 11px;overflow-wrap:anywhere;line-height:1.4;border-left-width:4px}
.record-label{display:block;font-size:.87rem;font-weight:650}
.record-preview{display:block;margin-top:4px;color:#cbd8e8;font-size:.81rem;white-space:normal}
.record-time{display:block;margin-top:5px;color:#b5c5d9;font-size:.73rem}
.record.user{border-left-color:#68cfa7;background:#1b3c39}
.record.event{border-left-color:#f3bd6a;background:#453623}
.record.message{border-left-color:#8caaff;background:#293d64}
.record.active{outline:2px solid #c2d7fa;outline-offset:-2px}
.record-detail-head{display:flex;flex-wrap:wrap;align-items:center;gap:10px}
.record-type{font-size:.8rem;font-weight:650;border-radius:4px;padding:3px 9px;background:#283b54}
.record-type.user{color:#99ebc7}
.record-type.event{color:#f3c680}
.record-type.message{color:#b5c7ff}
#history{overflow-wrap:anywhere;max-height:calc(100vh - 295px);overflow-y:auto}
#composeArea{margin:12px 0;border:1px solid #3a5870;border-radius:8px;padding:12px;background:#152237}
#composePanel{margin:8px 0 0}
#composePanel button{margin:4px 6px 2px 0;font-size:.88rem}
#composeText{display:block;width:100%;min-height:120px;resize:vertical}
.compose-profile-row{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin:9px 0}
.compose-profile-row label{display:flex;align-items:center;gap:8px}
#composeProfileSelect{min-width:180px;max-width:360px}
#composeProfileHint{font-size:.83rem}
.compose-command-row{display:flex;align-items:flex-start;gap:18px;flex-wrap:wrap}
.compose-actions{display:flex;flex:0 1 510px;flex-wrap:wrap;gap:7px}
.compose-events{flex:1 1 330px;min-width:250px;border:1px solid #435878;border-radius:7px;padding:9px;font-size:.82rem}
#composeEvents{max-height:175px;overflow-y:auto;line-height:1.5}
#composeEvents p{margin:5px 0;border-bottom:1px solid #34445b;overflow-wrap:anywhere}
#composeEvents .dim{font-size:.78rem}

.compose-modules{margin:10px 0;border:1px solid #3a5870;border-radius:7px;padding:8px}
.compose-modules summary{cursor:pointer;font-weight:600}
.compose-module-row{display:flex;gap:8px;align-items:start;padding:5px 0;overflow-wrap:anywhere}
.compose-module-row input{width:auto;margin:3px 0 0}
#composeStatus{font-size:.84rem;overflow-wrap:anywhere}
.session-diagnostics{border:1px solid #465c79;border-radius:7px;padding:10px;margin-bottom:12px;background:#111c2c;font-size:.8rem}
.session-diagnostics p{margin:5px 0;overflow-wrap:anywhere}
.session-diagnostics a{color:#a8ceff;overflow-wrap:anywhere}
.session-diagnostics button{margin-top:6px;font-size:.85rem;padding:6px 9px}
#notifierConnection{font-weight:600}
.session-diagnostics summary{cursor:pointer;font-weight:650;color:#c9e1ff;line-height:1.5}
.session-diagnostics[open] summary{margin-bottom:8px}
.follow-toggle{display:inline-flex;align-items:center;gap:5px;cursor:pointer;font-size:.84rem;white-space:nowrap}
.follow-toggle input{width:auto;margin:0}
#autoRefreshHint{font-size:.78rem}
#history pre{max-height:none;overflow:auto;font-size:.9rem;line-height:1.5}
#history .message-body{font-family:inherit;font-size:.95rem;line-height:1.6;white-space:pre-wrap}
[hidden]{display:none!important}
button.task{display:block;width:100%;text-align:left;margin:8px 0;overflow-wrap:anywhere}
button.session{font-size:.87rem;line-height:1.4}
button.task{padding:10px 11px;line-height:1.45}
.status-line{display:block;font-size:.8rem;line-height:1.45;margin-top:5px}
.status-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;background:var(--status-color);vertical-align:baseline}
[data-status="yellow"]{--status-color:#facc15}
[data-status="blue"]{--status-color:#60a5fa}
[data-status="purple"]{--status-color:#c084fc}
[data-status="green"]{--status-color:#4ade80}
[data-status="red"]{--status-color:#f87171}
button.session[data-status],button.task[data-status]{border-left:4px solid var(--status-color)}
.status-counts{display:flex;flex-wrap:wrap;gap:5px;margin-top:7px}
.status-count{font-size:.72rem;line-height:1.45;padding:2px 5px;border:1px solid #49617f;border-radius:5px}
.status-count[data-status]{border-color:var(--status-color)}
.status-note{display:block;font-size:.74rem;margin-top:5px;color:#d8e5fa}
.task-preview{display:block;font-size:13px;font-weight:600}
.task-time{display:block;font-size:11px;color:#b1c6e0;margin-top:4px}
button.task.active .task-time{color:#d9e8ff}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#101823;border:1px solid #3e526f;padding:13px;border-radius:6px}
.timeline{padding-left:24px}.timeline li{padding:6px 0;border-bottom:1px solid #3e506a}
section.entry{margin-top:14px;padding-top:8px;border-top:1px solid #40516b}
#discoveryPanel{padding-bottom:12px;margin-bottom:12px;border-bottom:1px solid #40516b}
#discoveryHeading{cursor:pointer;font-weight:700}
.discovered-chat{margin:8px 0;padding:10px;border:1px solid #a68b35;border-radius:6px;overflow-wrap:anywhere}
.discovered-chat p{margin:6px 0;font-size:.85rem}
.discovered-chat small{display:block;margin-top:7px;font-size:.72rem}
small{color:#9fb5ce}#unlock{max-width:720px}
.grid>.panel{margin:0 1px}
@media(max-width:700px){body{padding:8px}#status{margin-left:0;width:100%}.sticky-top{padding-top:7px}.masthead .dim{font-size:.77rem}.session-tab-bar{gap:7px;padding:5px 8px}.session-tab-bar .tab-label{display:none}#sessions button.session{max-width:165px}}
</style></head><body>
<div class="sticky-top">
<header class="masthead"><h1>Fortis Observatory</h1>
<p class="dim">Единый архив в Fortis Repo Docker · данные заявлены отправителем, не проверены по DOM ChatGPT</p></header>
<nav id="toolbar" class="toolbar" aria-label="Действия с архивом" hidden>
<button id="refresh" type="button">Обновить</button>
<label class="follow-toggle" for="autoFollow"><input id="autoFollow" type="checkbox"> Автоследование</label>
<span class="dim" id="autoRefreshHint">Обновление каждые 5 сек.</span>
<button id="toggleRegister" class="secondary action-toggle" type="button" aria-controls="registerPanel" aria-expanded="false">＋ Ссылка вручную</button>
<button id="toggleInstructions" class="secondary action-toggle" type="button" aria-controls="instructionPanel" aria-expanded="false">Инструкция</button>
<button id="togglePair" class="secondary action-toggle" type="button" aria-controls="pairPanel" aria-expanded="false">Привязка Notifier</button>
<span id="status" role="status" aria-live="polite">История ещё не загружена</span>
</nav>
<nav id="sessionTabBar" class="session-tab-bar" aria-label="Сессии и доступные чаты" hidden>
<div class="session-online-row"><span class="tab-label" aria-hidden="true">На связи</span>
<div id="sessions" role="tablist" aria-label="Подключённые доступные сессии"></div></div>
<div id="discoveryTabRow" class="session-secondary-row" hidden>
<span class="group-label">Доступны · не подключены</span>
<div id="discoveryTabs" role="group" aria-label="Доступные неподключённые чаты"></div></div>
<details id="offlineSessionGroup" class="session-fold" hidden>
<summary id="offlineSessionHeading">Недоступные подключённые (0)</summary>
<div id="offlineSessions" class="offline-tabs" role="group" aria-label="Недоступные зарегистрированные сессии"></div></details>
<details id="archivedSessionGroup" class="session-fold" hidden>
<summary id="archivedSessionHeading">Архив (0) · восстановить</summary>
<div id="archivedSessions" class="archive-tab-list" role="group" aria-label="Архивированные сессии"></div>
<p id="sessionArchiveNotice">История и задачи остаются в Docker; отправка через Notifier отключена.</p></details>
</nav>
</div>
<section id="unlock" class="panel"><h2>Локальный просмотр</h2>
<p>Вставьте одноразовый код из защищённой консоли Windows, которая запустила просмотрщик. Код остаётся в памяти этой вкладки.</p>
<form id="form"><input id="secret" type="password" autocomplete="off" required aria-label="Код просмотра">
<button type="submit">Открыть</button></form></section>
<section id="app" hidden>
<section id="composeArea" class="compose-area">
<button id="toggleCompose" class="secondary" type="button" aria-expanded="false"
  aria-controls="composePanel">✎ Текстбокс выбранной сессии ▾</button>
<section id="composePanel" hidden aria-label="Текстбокс выбранной сессии">
<p id="composeTarget" class="dim"></p>
<textarea id="composeText" rows="5" maxlength="400000" aria-label="Сообщение для выбранного чата"
  placeholder="Точный текст сообщения..."></textarea>
<div class="compose-profile-row">
<label for="composeProfileSelect">Профиль Notifier:
<select id="composeProfileSelect" aria-label="Профиль Notifier для выбранной сессии"></select>
</label>
<span id="composeProfileHint" class="dim">Ожидаю список профилей из Notifier…</span>
</div>
<div class="compose-command-row">
<div class="compose-actions">
<button id="composeFile" type="button" class="secondary" title="Отдать Notifier текст как .txt; без Send">Файл</button>
<button id="composeInsert" type="button" class="secondary" title="Вставить через Notifier без Send">Вставить</button>
<button id="composeSend" type="button" title="Прикрепить TXT и один раз нажать Send">Файл + Send</button>
<label for="composeSendDelay">Задержка после файла:
<select id="composeSendDelay" aria-label="Задержка перед Send после готового файла">
<option value="500">0,5 сек</option><option value="1000" selected>1 сек</option>
<option value="2000">2 сек</option><option value="3000">3 сек</option>
<option value="5000">5 сек</option><option value="10000">10 сек</option>
</select></label>
<button id="toggleComposeModules" type="button" class="secondary" aria-expanded="false" aria-controls="composeModulesPanel">⚙ Модули</button>
<button id="composeSendPrepared" type="button" class="secondary"
 title="Нажать Send для УЖЕ прикреплённого файла и сохранённого task_id; не прикреплять повторно">Нажать Send</button>
</div>
<section class="compose-events" aria-label="Журнал действий текстбокса">
<strong>События текстбокса</strong>
<div id="composeEvents" role="log" aria-live="polite" aria-relevant="additions text"></div>
</section></div>
<details id="composeModulesPanel" class="compose-modules">
<summary>Модули выбранного профиля · Planning Helper</summary>
<p class="dim">Это модули из каталога Notifier открытой вкладки. Текущие настройки в Tampermonkey не изменяются.
Снимите или поставьте галочки для этой сессии в Observatory.</p>
<input id="composeModuleSearch" type="search" maxlength="120"
  aria-label="Поиск модуля Planning Helper" placeholder="Поиск по названию или ID…">
<div id="composeModulesList"><p class="dim">Ожидаю подключённый Notifier…</p></div>
</details>
<p id="composeStatus" role="status" aria-live="polite">Только открытые привязанные чаты. Нет очереди для закрытых вкладок.</p>
<details id="composeLocalDraft"><summary>Локальный черновик · восстановление</summary>
<p class="dim">Сохраняется только в этом профиле Edge. Не отправляется в Docker; при очистке данных Edge может пропасть.</p>
<button id="composeRestoreDraft" type="button" class="secondary">Восстановить сохранённый текст</button>
<span id="composeDraftStatus" role="status" class="dim"></span></details>
</section></section>
<div class="action-area">
<section id="registerPanel" class="panel action-panel" hidden><h2>Подключить чат ChatGPT</h2>
<p class="dim">Вставьте ссылку на беседу и выберите название. Маршрут сообщений: только Fortis Repo.</p>
<form id="registerForm">
<label>Ссылка на беседу <input id="chatUrl" type="url" required maxlength="240"
placeholder="https://chatgpt.com/c/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"></label>
<label>Название <input id="chatTitle" type="text" required maxlength="80" placeholder="Мой проект"></label>
<button id="registerButton" type="submit">Подключить сессию</button>
</form><p id="registerStatus" role="status"></p>
</section>
<section id="instructionPanel" class="panel action-panel" hidden>
<h2>Инструкция для выбранной беседы</h2>
<p class="dim">Скопируйте её в соответствующую беседу ChatGPT, где подключён Fortis Repo. Секреты Docker не включены.</p>
<textarea id="instructions" readonly rows="11" aria-label="Инструкция Fortis Repo"></textarea>
<button id="copyInstructions" type="button" class="secondary">Скопировать инструкцию</button>
<p id="instructionStatus" role="status"></p>
</section>
<section id="pairPanel" class="panel action-panel" hidden>
<h2>Привязка Notifier к выбранной сессии</h2>
<p class="dim">Обычно ручной код НЕ нужен: Notifier сам обнаружится в сессии, затем подтвердите его кнопкой в колонке «Сессии». Этот код — резервный ручной способ через Tampermonkey → «Fortis: привязать текущий чат».
Код даёт доступ к статусу и оригиналам этой сессии, а также отдельное разрешение принимать адресные команды «Вставить»/«Отправить». Не отправляйте код в переписку.</p>
<button id="makePair" type="button" class="secondary">Создать код привязки Notifier</button>
<button id="revokeDispatch" type="button" class="secondary">Отозвать право адресной отправки</button>
<textarea id="pairValue" rows="4" readonly aria-label="Код привязки Notifier"></textarea>
<button id="copyPair" type="button" class="secondary">Скопировать код привязки</button>
<p id="pairStatus" role="status"></p>
</section>
</div>
<div class="workspace-viewport" aria-label="Четыре колонки Observatory — ширину можно менять за разделители">
<main id="workspaceGrid" class="grid">
<section class="panel sessions-column" aria-labelledby="sessionsHeading"><h2 id="sessionsHeading">Чаты и привязка <small id="sessionCount"></small></h2>
<details id="discoveryPanel" aria-labelledby="discoveryHeading">
<summary id="discoveryHeading">Чаты из браузера</summary>
<p class="dim">Вкладки ChatGPT с работающим Notifier. «Подключить» связывает чат и Notifier; сообщения отправляются отдельной кнопкой.</p>
<div id="discoveredChats"></div>
<p id="discoveryStatus" class="dim" role="status" aria-live="polite">Ожидаю открытые чаты…</p>
</details>
<details id="sessionDiagnostics" class="session-diagnostics">
<summary id="sessionDetailsHeading">Подробности сессии</summary>
<div class="session-diagnostics-body">
<p><strong>Чат:</strong> <a id="sessionChatLink" target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer">—</a></p>
<p>Chat ID: <span id="diagnosticChatId">—</span></p>
<p>Reporting session: <span id="diagnosticSessionId">—</span></p>
<p id="notifierConnection" role="status">Связь с Notifier ещё не проверена</p>
<p class="dim">Активная привязка подтверждается запросом из вкладки за 15 секунд. Разрешение на автоматическое восстановление хранится в защищённом каталоге Windows и действует после перезапуска.</p>
<p id="enrollmentStatus">Ожидаю установленный Notifier в выбранном чате…</p>
<button id="approveNotifier" class="secondary" type="button" hidden>Одобрить найденный Notifier (один раз)</button>
<button id="enableTaskIntents" class="secondary" type="button" hidden>Разрешить метаданные сохранённых задач</button>
<button id="revokeAutoNotifier" class="secondary" type="button" hidden>Отозвать постоянную привязку</button>
<button id="checkNotifierConnection" class="secondary" type="button">Проверить связь Notifier</button>
<button id="disconnectSession" class="secondary" type="button">Отключить Notifier</button>
<button id="archiveSession" class="secondary" type="button">Архивировать сессию</button>
<p id="sessionVisibilityStatus" role="status" class="dim"></p>
</div></details></section>
<div id="resize0" class="column-resizer" role="separator" tabindex="0" aria-label="Изменить ширину сессий и задач" aria-orientation="vertical"></div>
<section class="panel tasks-column" aria-labelledby="tasksHeading"><h2 id="tasksHeading">Задачи <small id="taskCount"></small></h2><p id="taskStatusNotice" class="status-note" role="status" hidden></p><div id="tasks"></div></section>
<div id="resize1" class="column-resizer" role="separator" tabindex="0" aria-label="Изменить ширину задач и записей" aria-orientation="vertical"></div>
<section class="panel records-column" aria-labelledby="recordsHeading"><h2 id="recordsHeading">Записи <small id="recordCount"></small></h2>
<p class="dim legend">Пользователь · Событие · AI</p><div id="records"></div></section>
<div id="resize2" class="column-resizer" role="separator" tabindex="0" aria-label="Изменить ширину записей и подробностей" aria-orientation="vertical"></div>
<section class="panel history-column" aria-labelledby="historyHeading"><h2 id="historyHeading">Подробности</h2>
<div id="history"><p class="dim">Выберите запись задачи.</p></div></section>
</main>
</div>
</section>
<script nonce="__NONCE__">
"use strict";
let token="", state=null, chosenSession="", chosenTask="", taskCards=[];
let discoveredChats=[], discoveryReadBusy=false;
let sessionLiveIds=new Set(),sessionConnectedIds=new Set(),sessionPresenceKnown=false;
let archivedSessions=new Map(),archiveVisibilityKnown=false;
let autoOpenedOfflineForSession="";
const CHAT_RE=/^[A-Za-z0-9-]{8,100}$/;
const connectingChats=new Set();
let sessionTitlesById=new Map();
function validTabTitle(value){
 return typeof value==="string"&&[...value].length<=128&&new TextEncoder().encode(value).length<=512&&
  !/[\u0000-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069]/.test(value)
}
function sessionDisplayTitle(record){
 return sessionTitlesById.get(record?.reporting_session_id)||record?.title||record?.conversation_id||record?.reporting_session_id||"Сессия"
}
const connectionBySession=new Map();
const enrollmentBySession=new Map();
let chosenRecord="", recordItems=[], activeHistory=null;
let historyReadSerial=0, archiveRefreshBusy=false;
// In-memory only. Enabling follow reselects the freshest task + record.
const autoFollow=()=>Boolean($("autoFollow").checked);
let composeSession="";
const composeDrafts=new Map();
const composePendingSends=new Map();
const SESSION_RE=/^rs_[0-9a-f]{32}$/;
const draftKey=sid=>"fortis-owner-draft-v1-"+sid;
function safeDraftWrite(sid,text){
 if(!SESSION_RE.test(sid)||typeof text!=="string"||text.length>400000)return false;
 composeDrafts.set(sid,text);
 try{
  const storage=window.localStorage;
  if(!storage)return false;
  const payload=JSON.stringify({version:1,source:"owner-local-draft",text,at:Date.now()});
  storage.setItem(draftKey(sid),payload);
  return storage.getItem(draftKey(sid))===payload
 }catch(_){return false}
}
function safeDraftRecovery(sid){
 if(!SESSION_RE.test(sid))return null;
 try{
  const value=JSON.parse(window.localStorage?.getItem(draftKey(sid))||"null");
  if(value?.version===1&&typeof value.text==="string"&&value.text.length<=400000)
   return value
 }catch(_){}
 return null
}
function safeDraftRead(sid){
 const value=safeDraftRecovery(sid);
 if(value)return value.sent===true?"":value.text;
 return composeDrafts.get(sid)||""
}
function markDraftSent(sid,text){
 if(!SESSION_RE.test(sid)||typeof text!=="string")return false;
 const old=safeDraftRecovery(sid);
 if(!old||old.text!==text)return false;
 try{
  const payload=JSON.stringify({...old,sent:true,sent_at:Date.now()});
  window.localStorage.setItem(draftKey(sid),payload);
  return window.localStorage.getItem(draftKey(sid))===payload
 }catch(_){return false}
}
let composeDraftTimer=null;
function storeComposeDraft(){
 if(!composeSession)return false;
 // An empty editor following Send is not a new blank draft: keep the
 // recovered original until the owner deliberately starts another message.
 const recovered=safeDraftRecovery(composeSession);
 if(!$("composeText").value&&recovered?.sent===true)return true;
 const ok=safeDraftWrite(composeSession,$("composeText").value);
 $("composeDraftStatus").textContent=ok?"Черновик сохранён локально":"Хранилище недоступно — текст не удаляйте";
 return ok
}
function deferComposeSave(){
 if(composeDraftTimer!==null)window.clearTimeout?.(composeDraftTimer);
 composeDraftTimer=window.setTimeout?.(()=>{composeDraftTimer=null;storeComposeDraft()},500)??null;
 if(composeDraftTimer===null)storeComposeDraft()
}
const composeModulesBySession=new Map();
const composeProfilesBySession=new Map();
const composeProfileManuallySelected=new Set();
const composeProfileAppliedBySession=new Map();
const composeModuleEditedBySession=new Set();
const composeCatalogBySession=new Map();
const defaultWidths=[.16,.21,.27,.36], minWidths=[165,205,250,325];
let columnWidths=defaultWidths.slice(), dragState=null;
const $=id=>document.getElementById(id);
function el(tag,txt){const x=document.createElement(tag);if(txt!==undefined)x.textContent=String(txt);return x}
function clear(x){x.replaceChildren()}
function status(txt){$("status").textContent=String(txt)}
function showTime(value){
 if(!value)return "время неизвестно";
 const stamp=new Date(value);
 return Number.isNaN(stamp.getTime())?"время неизвестно":
  stamp.toLocaleString("ru-RU",{year:"numeric",month:"2-digit",day:"2-digit",
   hour:"2-digit",minute:"2-digit",second:"2-digit"});
}
async function req(path,options={}){
 const headers={"Authorization":"Bearer "+token,...(options.headers||{})};
 const res=await fetch(path,{...options,credentials:"omit",cache:"no-store",headers});
 if(!res.ok)throw Error("HTTP "+res.status);
 return res.json()
}
function visibleRegisteredSessions(){
 if(!archiveVisibilityKnown)return [];
 return (Array.isArray(state?.sessions)?state.sessions:[]).filter(s=>
  SESSION_RE.test(s?.reporting_session_id||"")&&!archivedSessions.has(s.reporting_session_id))
}
function availableDiscoveredChats(){
 if(!archiveVisibilityKnown)return [];
 const archivedChats=new Set(archivedSessions.values());
 return discoveredChats.filter(row=>!archivedChats.has(row.chat) &&
   !row.blocked&&row.fingerprints.length===1)
}
function renderDiscoveredChats(stale=false){
 const list=$("discoveredChats");clear(list);
 if(!archiveVisibilityKnown){
  list.append(el("p","Список архивированных сессий не проверен: чаты скрыты до восстановления связи."));
  return
 }
 const archivedChats=new Set(archivedSessions.values());
 for(const item of discoveredChats){
  if(archivedChats.has(item.chat))continue;
  const row=el("div");row.className="discovered-chat";
  const link=el("a",item.title||item.chat);link.href="https://chatgpt.com/c/"+item.chat;
  link.target="_blank";link.rel="noopener noreferrer";link.referrerPolicy="no-referrer";
  const info=el("p","Обнаружен "+item.last_seen_seconds_ago+" сек. назад");
  const button=el("button","Подключить");button.type="button";button.className="secondary";
  button.setAttribute("aria-label","Подключить чат "+item.chat);
  button.disabled=stale||connectingChats.has(item.chat)||item.blocked||item.fingerprints.length!==1;
  if(item.blocked)info.textContent="Этот чат уже привязан к другому Notifier.";
  else if(item.fingerprints.length!==1)info.textContent="Найдено несколько Notifier для этого чата; подключение не выбрано.";
  button.onclick=()=>connectDiscoveredChat(item.chat,item.fingerprints[0]);
  const identity=el("small","ID: "+item.chat);
  row.append(link,info,button,identity);list.append(row)
 }
}
async function refreshDiscoveredChats(){
 if(!token||discoveryReadBusy)return;
 discoveryReadBusy=true;
 try{
  const data=await req("/api/notifier/discovered");
  if(!token)return;
  if(data?.ok!==true||!Array.isArray(data.chats)||data.chats.length>200)throw Error("Неверный список чатов");
  const seen=new Set();
  const rows=data.chats.map(item=>{
   if(!item||!/^[-A-Za-z0-9]{8,100}$/.test(item.chat||"")||seen.has(item.chat)||
      !Array.isArray(item.fingerprints)||!item.fingerprints.length||item.fingerprints.length>200||
      item.fingerprints.some(fp=>typeof fp!=="string"||!/^[a-f0-9]{12}$/.test(fp))||
      !Number.isInteger(item.last_seen_seconds_ago)||item.last_seen_seconds_ago<0||
      item.last_seen_seconds_ago>180||typeof item.blocked!=="boolean"||
      (item.title!==undefined&&!validTabTitle(item.title)))throw Error("Неверный чат");
   seen.add(item.chat);
   return {chat:item.chat,title:item.title||"",fingerprints:[...item.fingerprints],
     last_seen_seconds_ago:item.last_seen_seconds_ago,blocked:item.blocked}
  });
  const fresh=new Set(data.available_sessions??[]);
  const connected=new Set(data.connected_sessions??[]);
  if(fresh.size>256||connected.size>256 ||
     [...fresh,...connected].some(id=>!SESSION_RE.test(id)))throw Error("Неверная сводка доступности");
  sessionLiveIds=fresh;sessionConnectedIds=connected;sessionPresenceKnown=true;
  const titles=data.session_titles??{};
  if(typeof titles!=="object"||titles===null||Array.isArray(titles)||Object.keys(titles).length>256)
   throw Error("Неверные названия сессий");
  const validatedTitles=new Map();
  for(const [sid,title] of Object.entries(titles)){
   if(!/^rs_[0-9a-f]{32}$/.test(sid)||!validTabTitle(title))throw Error("Неверное название сессии");
   if(title)validatedTitles.set(sid,title)
  }
  sessionTitlesById=validatedTitles;
  discoveredChats=rows;renderDiscoveredChats();renderSessions();
  $("discoveryStatus").textContent=rows.length
   ?"Выберите чат для подключения."
   :"Новых чатов пока нет. Откройте беседу ChatGPT с включённым Notifier.";
 }catch(error){
  sessionPresenceKnown=false;
  renderDiscoveredChats(true);renderSessions();
  $("discoveryStatus").textContent="Список чатов недоступен: "+error.message;
 }finally{discoveryReadBusy=false}
}
async function connectDiscoveredChat(chat,fingerprint){
 const item=discoveredChats.find(row=>row.chat===chat);
 if(!token||!archiveVisibilityKnown||connectingChats.has(chat)||!item||item.blocked||
    item.fingerprints.length!==1||item.fingerprints[0]!==fingerprint)return;
 connectingChats.add(chat);renderDiscoveredChats();
 $("discoveryStatus").textContent="Подключение чата…";
 try{
  const data=await req("/api/notifier/connect",{method:"POST",
   headers:{"Content-Type":"application/json"},body:JSON.stringify({chat,fingerprint})});
  if(data?.ok!==true||data.approved!==true||data.conversation_id!==chat||
     !/^rs_[0-9a-f]{32}$/.test(data.session||""))throw Error("Неверный ответ подключения");
  discoveredChats=discoveredChats.filter(row=>row.chat!==chat);renderDiscoveredChats();
  // Keep the selected session/task; connecting another tab must not steal focus.
  await refresh();
  $("discoveryStatus").textContent="Чат подключён. Notifier подтвердит связь автоматически.";
 }catch(error){
  $("discoveryStatus").textContent="Подключение не завершено: "+error.message+". Обновите список и повторите.";
 }finally{connectingChats.delete(chat);renderDiscoveredChats()}
}
const actions={toggleRegister:"registerPanel",toggleInstructions:"instructionPanel",togglePair:"pairPanel"};
function closeActions(){
 for(const [button,panel] of Object.entries(actions)){
  $(panel).hidden=true;$(button).setAttribute("aria-expanded","false")
 }
}
function openAction(button){
 closeActions();$(actions[button]).hidden=false;$(button).setAttribute("aria-expanded","true")
}
function toggleAction(button){
 if(!$(actions[button]).hidden){closeActions();return}
 openAction(button)
}
function resetSessionActions(){
 closeActions();$("instructions").value="";$("instructionStatus").textContent="";
 $("pairValue").value="";$("pairStatus").textContent=""
}
function historyPlaceholder(message){
 clear($("history"));$("history").append(el("p",message))
}
function recordsPlaceholder(message){
 clear($("records"));$("records").append(el("p",message));
 $("recordCount").textContent="0"
}
function resetRecordView(message){
 ++historyReadSerial;
 activeHistory=null;recordItems=[];chosenRecord="";
 recordsPlaceholder(message);historyPlaceholder(message)
}
function newestTaskId(cards){
 // Viewer task list may be oldest-first, newest-first or unordered.
 // Prefer the actual first_seen_at timestamp; use backend list order as
 // a deterministic fallback for tied/missing timestamps.
 let newest=null, latest=-Infinity;
 for(const card of cards){
  const parsed=Date.parse(card.first_seen_at||"");
  const stamp=Number.isFinite(parsed)?parsed:-Infinity;
  if(newest===null||stamp>=latest){newest=card.task_id;latest=stamp}
 }
 return newest||"";
}
function scrollRecordsToBottom(){
 const list=$("records");
 list.scrollTop=list.scrollHeight
}
// The three separators redistribute space only between their adjacent panels.
// No dimensions or archive content are persisted in browser storage.
function applyColumnWidths(){
 const grid=$("workspaceGrid"), usable=grid.clientWidth-30;
 if(usable<=0)return;
 const px=columnWidths.map(width=>width*usable);
 grid.style.gridTemplateColumns=px.map(x=>x+"px").join(" 10px ") 
 for(let i=0;i<3;i++){
  $("resize"+i).setAttribute("aria-valuenow",String(Math.round(columnWidths[i]*100)));
  $("resize"+i).setAttribute("aria-valuemin","0");
  $("resize"+i).setAttribute("aria-valuemax","100")
 }
}
function adjustColumnDivider(index,delta){
 const usable=$("workspaceGrid").clientWidth-30;
 if(usable<=0 || !Number.isFinite(delta))return;
 const first=columnWidths[index]*usable;
 const second=columnWidths[index+1]*usable;
 const moved=Math.max(minWidths[index]-first,
  Math.min(second-minWidths[index+1],delta));
 columnWidths[index]=(first+moved)/usable;
 columnWidths[index+1]=(second-moved)/usable;
 applyColumnWidths()
}
for(let i=0;i<3;i++){
 const handle=$("resize"+i);
 handle.addEventListener("pointerdown",event=>{
  if(event.button!==0)return;
  dragState={index:i,pointerId:event.pointerId,lastX:event.clientX};
  handle.setPointerCapture(event.pointerId);handle.classList.add("dragging");
  event.preventDefault()
 });
 handle.addEventListener("pointermove",event=>{
  if(!dragState||dragState.index!==i||dragState.pointerId!==event.pointerId)return;
  adjustColumnDivider(i,event.clientX-dragState.lastX);
  dragState.lastX=event.clientX
 });
 const stop=event=>{
  if(!dragState||dragState.index!==i||dragState.pointerId!==event.pointerId)return;
  handle.classList.remove("dragging");dragState=null;
  if(handle.hasPointerCapture(event.pointerId))handle.releasePointerCapture(event.pointerId)
 };
 handle.addEventListener("pointerup",stop);
 handle.addEventListener("pointercancel",stop);
 handle.addEventListener("keydown",event=>{
  if(event.key!=="ArrowLeft"&&event.key!=="ArrowRight")return;
  event.preventDefault();
  adjustColumnDivider(i,(event.key==="ArrowRight"?1:-1)*(event.shiftKey?30:12))
 });
 handle.addEventListener("dblclick",()=>{
  columnWidths=defaultWidths.slice();applyColumnWidths()
 })
}
window.addEventListener("resize",applyColumnWidths);
async function showInstructions(sid){
 if(!sid){status("Сначала выберите сессию.");return}
 openAction("toggleInstructions");
 $("instructionStatus").textContent="Загрузка инструкции…";
 $("instructions").value="";
 try{
  const data=await req("/api/instructions?session="+encodeURIComponent(sid));
  if(sid!==chosenSession)return;
  if(data.session!==sid)throw Error("Неверная сессия");
  $("instructions").value=data.text;
  $("instructionStatus").textContent="Инструкция загружена для выбранной сессии."
 }catch(error){
  if(sid!==chosenSession)return;
  $("instructionStatus").textContent="Не удалось получить инструкцию: "+error.message
 }
}
function describeNotifierConnection(data){
 if(!data||data.ok!==true)return "Связь с Notifier: нет проверенных данных";
 if(data.available===true)return "Notifier: ПОДКЛЮЧЁН · авторизованный запрос "+String(data.last_seen_seconds_ago??0)+" сек. назад";
 if(data.paired===false)return "Notifier: код привязки ещё не создавался в этом запуске Viewer";
 if(data.ever_seen===true)return "Notifier: ранее отвечал, но сейчас НЕТ СВЯЗИ · последний запрос "+String(data.last_seen_seconds_ago??"?")+" сек. назад";
 return "Notifier: код создан, но вкладка ещё не подтвердила привязку";
}
function renderSessionDiagnostics(session){
 const cid=String(session?.conversation_id||"");
 const valid=/^[A-Za-z0-9-]{8,100}$/.test(cid);
 const a=$("sessionChatLink");
 if(valid){
  const url="https://chatgpt.com/c/"+cid;
  a.href=url;
  a.textContent=url;
 }else{
  a.removeAttribute("href");
  a.textContent="Нет корректного URL";
 }
 $("diagnosticChatId").textContent=valid?cid:"—";
 $("diagnosticSessionId").textContent=String(session?.reporting_session_id||"—");
 const info=session?connectionBySession.get(session.reporting_session_id):null;
 $("notifierConnection").textContent=info?.error||describeNotifierConnection(info?.data);
 $("checkNotifierConnection").disabled=!session;
 $("archiveSession").disabled=!session||!archiveVisibilityKnown;
 $("disconnectSession").disabled=!session||!archiveVisibilityKnown;
 const auto=session?enrollmentBySession.get(session.reporting_session_id):null;
 const approval=$("approveNotifier"),revoke=$("revokeAutoNotifier");
 const pending=Array.isArray(auto?.pending)?auto.pending:[];
 approval.hidden=pending.length!==1||auto?.approved===true;
 revoke.hidden=auto?.approved!==true;
 $("enableTaskIntents").hidden=!auto?.approved||auto?.task_intents===true;
 $("enrollmentStatus").textContent=auto?.approved
   ?"Постоянная привязка одобрена для этого чата (переживает перезапуск)."
   :pending.length===1
     ?"Notifier обнаружен для этого URL. Код подтверждения: "+pending[0].fingerprint+
       ". Нажми «Одобрить», только если ожидаешь свою вкладку."
     :pending.length>1
       ?"Найдено несколько Notifier. Автоматическая привязка заблокирована до устранения дубликатов."
       :"Ожидаю установленный Notifier в открытой зарегистрированной беседе…";
}
async function refreshNotifierEnrollment(){
 const sid=chosenSession;
 if(!sid||!token)return;
 try{
  const data=await req("/api/notifier/pending?session="+encodeURIComponent(sid));
  if(sid!==chosenSession)return;
  enrollmentBySession.set(sid,data);
 }catch(error){
  if(sid!==chosenSession)return;
  enrollmentBySession.delete(sid);
  $("enrollmentStatus").textContent="Автопривязка недоступна: "+error.message;
  return;
 }
 const item=(Array.isArray(state?.sessions)?state.sessions:[])
   .find(row=>row.reporting_session_id===sid);
 renderSessionDiagnostics(item);
}
async function approveNotifierEnrollment(){
 const sid=chosenSession,info=enrollmentBySession.get(sid);
 const item=(Array.isArray(state?.sessions)?state.sessions:[])
   .find(row=>row.reporting_session_id===sid);
 if(!item||info?.approved||info?.pending?.length!==1)return;
 $("approveNotifier").disabled=true;
 try{
  await req("/api/notifier/approve",{
   method:"POST",headers:{"Content-Type":"application/json"},
   body:JSON.stringify({session:sid,chat:item.conversation_id,
      fingerprint:info.pending[0].fingerprint})
  });
  $("enrollmentStatus").textContent="Одобрено. Вкладка подключится без ручного кода.";
  await refreshNotifierEnrollment();
 }catch(error){
  $("enrollmentStatus").textContent="Одобрение не выполнено: "+error.message;
 }finally{$("approveNotifier").disabled=false}
}
async function revokeAutoEnrollment(){
 const sid=chosenSession;
 if(!sid||!enrollmentBySession.get(sid)?.approved)return;
 $("revokeAutoNotifier").disabled=true;
 try{
  await req("/api/notifier/revoke",{
   method:"POST",headers:{"Content-Type":"application/json"},
   body:JSON.stringify({session:sid})
  });
  connectionBySession.delete(sid);
  await refreshNotifierEnrollment();
  await refreshNotifierConnection();
 }catch(error){
  $("enrollmentStatus").textContent="Отзыв не выполнен: "+error.message;
 }finally{$("revokeAutoNotifier").disabled=false}
}
async function refreshNotifierConnection(){
 const sid=chosenSession;
 if(!sid||!token)return;
 try{
  const data=await req("/api/dispatch/status?session="+encodeURIComponent(sid));
  if(chosenSession!==sid)return;
  connectionBySession.set(sid,{data});
 }catch(error){
  if(chosenSession!==sid)return;
  connectionBySession.set(sid,{error:"Диагностика Notifier недоступна: "+error.message});
 }
 const item=(Array.isArray(state?.sessions)?state.sessions:[])
   .find(row=>row.reporting_session_id===sid);
 renderSessionDiagnostics(item);
}
let archiveStatusStale=false, taskStatusStale=false;
const STATUS_COLORS=new Set(["yellow","blue","purple","green","red"]);
function staleStatus(stamp){
 const now=Date.now()/1000;
 return !Number.isFinite(stamp)||stamp<=0||stamp>now+30||now-stamp>20;
}
function statusLine(label,color){
 const line=el("span");line.className="status-line";
 if(STATUS_COLORS.has(color)){
  line.setAttribute("data-status",color);
  const dot=el("span");dot.className="status-dot";dot.setAttribute("aria-hidden","true");line.append(dot);
 }
 line.append(el("span",label));return line;
}
function renderSessionStatus(button,overview){
 button.removeAttribute("data-status");
 if(overview?.version!==2||overview.basis!=="latest_task"||overview.available!==true){
  button.append(statusLine("Статусы задач недоступны",null));return;
 }
 const stale=archiveStatusStale||staleStatus(overview.checked_at_unix);
 const color=stale?null:overview.primary_color;
 if(STATUS_COLORS.has(color))button.setAttribute("data-status",color);
 button.append(statusLine(String(overview.primary_label||"Нет известных задач")+
   (stale?" · данные устарели":""),color));
 if(overview.incomplete===true){const note=el("span","Сводка неполная");note.className="status-note";button.append(note);}
}
function renderTaskStatus(button,record){
 button.removeAttribute("data-status");
 const known=typeof record.status_label==="string";
 const stale=known&&(archiveStatusStale||taskStatusStale||staleStatus(record.status_checked_at_unix));
 const color=known&&!stale?record.status_color:null;
 if(STATUS_COLORS.has(color))button.setAttribute("data-status",color);
 button.append(statusLine((known?record.status_label:"Статус задачи недоступен")+
   (stale?" · данные устарели":""),color));
 if(typeof record.send_label==="string"){
  const note=el("span",record.send_label);note.className="status-note";button.append(note);
 }
}
const TAB_ORDER_KEY="fortis-owner-session-tab-order-v1";
async function refreshSessionVisibility(){
 try{
  const response=await req("/api/session-visibility");
  if(response?.ok!==true||!response.archived||
     typeof response.archived!=="object"||Array.isArray(response.archived)||
     Object.keys(response.archived).length>256)throw Error("Неверная структура архива");
  const next=new Map();
  for(const [id,chat] of Object.entries(response.archived)){
   if(!SESSION_RE.test(id)||typeof chat!=="string"||!CHAT_RE.test(chat))
    throw Error("Неверная запись архива");
   next.set(id,chat)
  }
  archivedSessions=next;archiveVisibilityKnown=true;
  return true
 }catch(error){
  archiveVisibilityKnown=false;
  $("sessionVisibilityStatus").textContent="Архив сессий недоступен: "+error.message;
  return false
 }
}
async function sessionVisibilityAction(action,sid){
 const record=(state?.sessions||[]).find(s=>s.reporting_session_id===sid);
 const chat=record?.conversation_id||archivedSessions.get(sid);
 if(!SESSION_RE.test(sid)||typeof chat!=="string"||!CHAT_RE.test(chat))return;
 const label=String(sessionDisplayTitle(record||{reporting_session_id:sid,conversation_id:chat}));
 if(action==="archive"&&!window.confirm?.(
   "Архивировать «"+label+"»? Сессия исчезнет из обычных списков; связь Notifier будет отозвана, история останется."))return;
 if(action==="disconnect"&&!window.confirm?.(
   "Отключить Notifier для «"+label+"»? История и регистрация сессии сохранятся."))return;
 const button=action==="archive"?$("archiveSession"):$("disconnectSession");
 button.disabled=true;
 try{
  const result=await req("/api/session-visibility",{method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({action,session:sid,chat})});
  if(result?.ok!==true||result.session!==sid)throw Error("Не подтверждено");
  connectionBySession.delete(sid);enrollmentBySession.delete(sid);
  if(!await refreshSessionVisibility())throw Error("Не удалось подтвердить запись в архиве");
  await refresh();
  $("sessionVisibilityStatus").textContent=action==="archive"
   ?"Сессия архивирована. Задачи не удалены."
   :action==="restore"?"Сессия восстановлена. Для Notifier может потребоваться новое одобрение."
   :"Notifier отключён. Зарегистрированная сессия сохранена.";
 }catch(error){
  $("sessionVisibilityStatus").textContent="Действие не подтверждено: "+error.message+
   ". Обновите архив перед повторной попыткой.";
  await refreshSessionVisibility();renderSessions()
 }finally{button.disabled=false}
}
$("archiveSession").addEventListener("click",()=>sessionVisibilityAction("archive",chosenSession));
$("disconnectSession").addEventListener("click",()=>sessionVisibilityAction("disconnect",chosenSession));
$("offlineSessionGroup").addEventListener("toggle",()=>{
 try{window.localStorage?.setItem("fortis-session-offline-open-v1",
   $("offlineSessionGroup").open?"1":"0")}catch(_){}
});
try{$("offlineSessionGroup").open=window.localStorage?.getItem("fortis-session-offline-open-v1")==="1"}catch(_){}

let tabOrder=[];
try{
 const saved=JSON.parse(window.localStorage?.getItem(TAB_ORDER_KEY)||"[]");
 if(Array.isArray(saved)&&saved.length<=1000&&saved.every(id=>SESSION_RE.test(id))&&
    new Set(saved).size===saved.length)tabOrder=saved
}catch(_){}
function persistSessionOrder(next){
 if(!Array.isArray(next)||next.length>1000||new Set(next).size!==next.length||
    next.some(id=>!SESSION_RE.test(id)))return false;
 try{
  const string=JSON.stringify(next);
  window.localStorage?.setItem(TAB_ORDER_KEY,string);
  if(window.localStorage?.getItem(TAB_ORDER_KEY)!==string)throw Error("readback");
  tabOrder=next;return true
 }catch(_){status("Порядок вкладок не сохранён; изменений нет");return false}
}
function moveSessionTab(source,target){
 if(!SESSION_RE.test(source)||!SESSION_RE.test(target)||source===target)return;
 const ids=visibleRegisteredSessions().map(s=>s.reporting_session_id);
 if(!ids.includes(source)||!ids.includes(target))return;
 const next=[...new Set([...tabOrder.filter(id=>ids.includes(id)),...ids])];
 next.splice(next.indexOf(source),1);
 next.splice(next.indexOf(target),0,source);
 if(persistSessionOrder(next))renderSessions()
}
// Native browser-style tab sliding: move the *real* button under the pointer,
// shift neighbours during the gesture, and persist exactly once on release.
// Do not rebuild the header or change the selected session during a gesture.
let tabSlide=null;
let tabSlideNeedsRender=false;
let tabSlideClickGuard={id:"",at:0};
const slideButtons=()=>Array.from($("sessions").children)
 .filter(node=>SESSION_RE.test(node.dataset?.sessionId||""));
function animateShiftedTabs(before,dragged){
 for(const tab of slideButtons()){
  if(tab===dragged||!before.has(tab))continue;
  const oldLeft=before.get(tab),newLeft=tab.getBoundingClientRect().left;
  const delta=oldLeft-newLeft;
  if(Math.abs(delta)>0.5&&typeof tab.animate==="function"&&
     !window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches){
   tab.animate([{transform:"translateX("+delta+"px)"},
     {transform:"translateX(0)"}],{duration:165,easing:"ease-out"})
  }
 }
}
function updateSlidePosition(gesture){
 const box=gesture.button.getBoundingClientRect();
 const baseLeft=box.left-gesture.translate;
 gesture.translate=gesture.initialLeft+gesture.pointerX-gesture.startX-baseLeft;
 gesture.button.style.transform="translate3d("+gesture.translate+"px,0,0)"
}
function slidePreviewAt(gesture){
 const list=$("sessions"),dragged=gesture.button;
 const others=slideButtons().filter(tab=>tab!==dragged);
 const beforeTab=others.find(tab=>{
  const box=tab.getBoundingClientRect();
  return gesture.pointerX<box.left+box.width/2
 })||null;
 const oldIndex=slideButtons().indexOf(dragged);
 const newIndex=beforeTab?others.indexOf(beforeTab):others.length;
 if(newIndex!==oldIndex){
  const oldPositions=new Map(others.map(tab=>[tab,tab.getBoundingClientRect().left]));
  list.insertBefore(dragged,beforeTab);
  animateShiftedTabs(oldPositions,dragged)
 }
 updateSlidePosition(gesture)
}
function slideEdgeScroll(){
 const g=tabSlide;
 if(!g||!g.active)return;
 const list=$("sessions"),box=list.getBoundingClientRect();
 const edge=28;
 const direction=g.pointerX<box.left+edge?-1:
  g.pointerX>box.right-edge?1:0;
 const previous=list.scrollLeft;
 if(direction&&list.scrollWidth>list.clientWidth){
  list.scrollLeft+=direction*16;
  if(list.scrollLeft!==previous)slidePreviewAt(g)
 }
 g.raf=null;
 if(direction&&list.scrollLeft!==previous&&window.requestAnimationFrame)
  g.raf=window.requestAnimationFrame(slideEdgeScroll)
}
function startTabSlide(event,button){
 if(tabSlide||event.button!==0||event.isPrimary===false||
    !SESSION_RE.test(button.dataset?.sessionId||""))return;
 const box=button.getBoundingClientRect();
 tabSlide={button,pointerId:event.pointerId,startX:event.clientX,
  startY:event.clientY,pointerX:event.clientX,initialLeft:box.left,
  translate:0,active:false,raf:null,
  initialOrder:slideButtons()};
 // Do not capture on pointerdown: capturing the tablist would swallow an
 // ordinary button click. Capture only once an actual horizontal drag starts.
}
function continueTabSlide(event){
 const g=tabSlide;
 if(!g||event.pointerId!==g.pointerId)return;
 if(!g.active){
  const dx=event.clientX-g.startX,dy=event.clientY-g.startY;
  if(Math.abs(dx)<7||Math.abs(dx)<Math.abs(dy))return;
  g.active=true;g.button.classList.add("sliding");
  $("sessions").classList.add("sliding-tabs");
  $("sessions").setPointerCapture?.(g.pointerId)
 }
 event.preventDefault();
 g.pointerX=event.clientX;
 slidePreviewAt(g);
 if(g.raf===null&&window.requestAnimationFrame)
  g.raf=window.requestAnimationFrame(slideEdgeScroll)
}
function finishTabSlide(event,cancel=false){
 const g=tabSlide;
 if(!g||event.pointerId!==g.pointerId)return;
 tabSlide=null;
 if(g.raf!==null)window.cancelAnimationFrame?.(g.raf);
 const list=$("sessions");
 if(g.active){
  event.preventDefault?.();
  tabSlideClickGuard={id:g.button.dataset.sessionId,at:Date.now()};
  if(cancel){
   const positions=new Map(slideButtons().map(tab=>[tab,tab.getBoundingClientRect().left]));
   for(const tab of g.initialOrder)list.append(tab);
   animateShiftedTabs(positions,g.button)
  }else{
   const next=slideButtons().map(tab=>tab.dataset.sessionId);
   if(!persistSessionOrder(next)){
    for(const tab of g.initialOrder)list.append(tab)
   }
  }
  const translate=g.translate;
  g.button.style.transform="";
  if(!cancel&&Math.abs(translate)>0.5&&
     typeof g.button.animate==="function"&&
     !window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches){
   g.button.animate([{transform:"translateX("+translate+"px)"},
     {transform:"translateX(0)"}],{duration:150,easing:"ease-out"})
  }
  g.button.classList.remove("sliding");
  list.classList.remove("sliding-tabs")
 }
 if(list.hasPointerCapture?.(g.pointerId))
  list.releasePointerCapture(g.pointerId);
 if(tabSlideNeedsRender){
  tabSlideNeedsRender=false;
  // Let the sliding animation complete before polling rebuilds the header.
  window.setTimeout?.(()=>{if(!tabSlide)renderSessions()},190)
 }
}
function selectRegisteredSession(sid){
 if(!SESSION_RE.test(sid)||archivedSessions.has(sid)||
    !visibleRegisteredSessions().some(s=>s.reporting_session_id===sid)||
    chosenSession===sid)return;
 chosenSession=sid;chosenTask="";taskCards=[];
 resetSessionActions();resetRecordView("Загрузка задач…");
 renderSessions();void loadTasks();void refreshNotifierConnection();
 void refreshNotifierEnrollment()
}
function renderSessions(){
 if(tabSlide?.active){tabSlideNeedsRender=true;return}
 updateComposeTarget();
 const list=$("sessions"), tasks=$("tasks");
 const sessionScrollLeft=list.scrollLeft,taskScroll=tasks.scrollTop;
 clear(list);clear(tasks);
 const sessions=visibleRegisteredSessions().slice();
 sessions.sort((a,b)=>{
  const aa=tabOrder.indexOf(a.reporting_session_id),bb=tabOrder.indexOf(b.reporting_session_id);
  return (aa<0?Number.MAX_SAFE_INTEGER:aa)-(bb<0?Number.MAX_SAFE_INTEGER:bb)
 });
 const online=sessions.filter(s=>sessionPresenceKnown&&sessionLiveIds.has(s.reporting_session_id));
 const offline=sessions.filter(s=>!sessionPresenceKnown||!sessionLiveIds.has(s.reporting_session_id));
 const discovered=availableDiscoveredChats();
 const allSessions=Array.isArray(state?.sessions)?state.sessions:[];
 const archived=[...archivedSessions].filter(([sid,chat])=>
  allSessions.some(s=>s.reporting_session_id===sid&&s.conversation_id===chat));
 $("sessionTabBar").hidden=!sessions.length&&!discovered.length&&!archived.length;
 $("sessionCount").textContent=String(sessions.length);
 $("taskCount").textContent=chosenSession?String(taskCards.length):"—";
 const discoveredList=$("discoveryTabs");clear(discoveredList);
 for(const item of discovered){
  const button=el("button",item.title||item.chat);button.type="button";
  button.title="Доступен в Edge · подключить Notifier и сессию";
  button.setAttribute("aria-label","Подключить доступный чат "+item.chat);
  button.disabled=connectingChats.has(item.chat)||!sessionPresenceKnown;
  button.onclick=()=>connectDiscoveredChat(item.chat,item.fingerprints[0]);
  discoveredList.append(button)
 }
 $("discoveryTabRow").hidden=!discovered.length;
 const unavailable=$("offlineSessions");clear(unavailable);
 const linkedCount=offline.filter(item=>sessionConnectedIds.has(item.reporting_session_id)).length;
 $("offlineSessionHeading").textContent=(sessionPresenceKnown
  ?"Нет связи · привязаны ("+linkedCount+"), без привязки ("+(offline.length-linkedCount)+")"
  :"Доступность не подтверждена ("+offline.length+")");
 $("offlineSessionGroup").hidden=!offline.length;
 for(const item of offline){
  const button=el("button",String(sessionDisplayTitle(item)));
  const linked=sessionConnectedIds.has(item.reporting_session_id);
  button.type="button";button.className=linked?"linked":"unpaired";
  button.title=!sessionPresenceKnown?"Доступность Notifier не подтверждена":
   linked?"Привязка есть, но активная вкладка Notifier не отвечает":
    "Сессия зарегистрирована, но привязка Notifier не одобрена";
  button.setAttribute("aria-selected",chosenSession===item.reporting_session_id?"true":"false");
  button.onclick=()=>selectRegisteredSession(item.reporting_session_id);
  unavailable.append(button)
 }
 if(offline.some(s=>s.reporting_session_id===chosenSession)){
  if(autoOpenedOfflineForSession!==chosenSession){
   $("offlineSessionGroup").open=true;
   autoOpenedOfflineForSession=chosenSession
  }
 }else autoOpenedOfflineForSession="";
 const archiveList=$("archivedSessions");clear(archiveList);
 $("archivedSessionHeading").textContent="Архив ("+archived.length+") · восстановить";
 $("archivedSessionGroup").hidden=!archived.length;
 for(const [sid,chat] of archived){
  const record=allSessions.find(s=>s.reporting_session_id===sid);
  const button=el("button","Восстановить · "+String(sessionDisplayTitle(record)));
  button.type="button";button.title="Вернуть сессию в рабочий список, сохранив историю";
  button.onclick=()=>sessionVisibilityAction("restore",sid);
  archiveList.append(button)
 }
 if(!online.length){
  list.append(el("span","Нет подключённых сессий на связи."));
 }
 for(const s of online){
  const b=el("button",String(sessionDisplayTitle(s)));
  b.title="Диагностика событий: "+String(s.state||"нет")+
   (s.task_overview?.primary_label?" · "+String(s.task_overview.primary_label):"");
  b.type="button";b.className="session available"+
    (chosenSession===s.reporting_session_id?" active":"");
  b.setAttribute("role","tab");b.setAttribute("aria-controls","workspaceGrid");
  b.setAttribute("aria-selected",chosenSession===s.reporting_session_id?"true":"false");
  b.tabIndex=chosenSession===s.reporting_session_id?0:-1;
  b.dataset.sessionId=s.reporting_session_id;
  b.addEventListener("pointerdown",event=>startTabSlide(event,b));
  renderSessionStatus(b,s.task_overview);
  b.onclick=event=>{
   if(event?.detail>0&&tabSlideClickGuard.id===s.reporting_session_id&&
      Date.now()-tabSlideClickGuard.at<450){
     event.preventDefault?.();return
   }
   selectRegisteredSession(s.reporting_session_id)
  };
  list.append(b)
 }
 const current=sessions.find(s=>s.reporting_session_id===chosenSession);
 renderSessionDiagnostics(current);
 if(!current){tasks.append(el("p","Выберите сессию."));return}
 if(!taskCards.length){tasks.append(el("p","В этой сессии пока нет задач."));return}
 for(const [index,record] of taskCards.entries()){
  const id=record.task_id;
  const b=el("button");b.type="button";b.className="task"+(chosenTask===id?" active":"");
  const preview=record.original_received
   ? (record.original_preview || "(пустой оригинал)")
   : "— Оригинал ещё не получен";
  const title=el("span",(index+1)+". "+preview);title.className="task-preview";
  const time=el("span",showTime(record.first_seen_at));time.className="task-time";
  b.append(title,time);b.title=id;renderTaskStatus(b,record);
  b.onclick=()=>{
   if(chosenTask===id)return;
   chosenTask=id;resetRecordView("Загрузка записей…");
   renderSessions();void showHistory({follow:true})
  };
  tasks.append(b)
 }
 list.scrollLeft=sessionScrollLeft;tasks.scrollTop=taskScroll
}
// Capture the pointer on the stable tablist, not on a button moved inside it.
$("sessions").addEventListener("pointermove",continueTabSlide);
$("sessions").addEventListener("pointerup",event=>finishTabSlide(event));
$("sessions").addEventListener("pointercancel",event=>finishTabSlide(event,true));
$("sessions").addEventListener("pointerleave",event=>{
 if(tabSlide&&!tabSlide.active)finishTabSlide(event,true)
});
$("sessions").addEventListener("lostpointercapture",event=>finishTabSlide(event,true));
// Tabs remain keyboard operable when their horizontal row overflows.
$("sessions").addEventListener("keydown",event=>{
 if(event.key==="Escape"&&tabSlide?.active){
  event.preventDefault();
  finishTabSlide({pointerId:tabSlide.pointerId,preventDefault(){}},true);
  return
 }
 if(!["ArrowLeft","ArrowRight","Home","End"].includes(event.key))return;
 if(event.altKey&&(event.key==="ArrowLeft"||event.key==="ArrowRight")){
   const buttons=Array.from($("sessions").children),index=buttons.indexOf(event.target);
   if(index<0)return;const next=index+(event.key==="ArrowLeft"?-1:1);
   if(next<0||next>=buttons.length)return;
   event.preventDefault();
   moveSessionTab(event.target.dataset.sessionId,buttons[next].dataset.sessionId);
   Array.from($("sessions").children).find(b=>b.dataset.sessionId===event.target.dataset.sessionId)?.focus();
   return
 }
 const buttons=Array.from($("sessions").children);
 const index=buttons.indexOf(event.target);
 if(index<0||!buttons.length)return;
 event.preventDefault();
 const next=event.key==="Home"?0:event.key==="End"?buttons.length-1:
  (index+(event.key==="ArrowRight"?1:-1)+buttons.length)%buttons.length;
 buttons[next].onclick();
 // The selection rerenders the buttons; focus the replacement, not the old node.
 Array.from($("sessions").children)[next]?.focus();
});
async function loadTasks(){
 const active=chosenSession;
 if(!active)return;
 try{
  const data=await req("/api/tasks?session="+encodeURIComponent(active));
  if(chosenSession!==active)return;
  taskCards=Array.isArray(data.tasks)?data.tasks.filter(x=>
   /^task_[0-9a-f]{32}$/.test(x.task_id||"")):[];
  taskStatusStale=false;
  const notice=$("taskStatusNotice");
  notice.hidden=data.task_status_available!==false&&data.truncated!==true;
  notice.textContent=data.task_status_available===false
    ?"Статусы задач недоступны. Показана доступная история."
    :data.truncated===true?"Список ограничен; сводка задач может быть неполной.":"";
  const previousTask=chosenTask;
  // On opening a session choose the newest task; during 5-second polling
  // switch tasks only if auto-follow is checked or previous task vanished.
  if(autoFollow()||!taskCards.some(x=>x.task_id===chosenTask))
   chosenTask=newestTaskId(taskCards);
  if(chosenTask!==previousTask)
   resetRecordView(chosenTask?"Загрузка записей…":"В этой сессии пока нет задач.");
  renderSessions();
  if(chosenTask)await showHistory({follow:autoFollow()||chosenTask!==previousTask})
  else if(previousTask)resetRecordView("В этой сессии пока нет задач.")
 }catch(error){
  if(chosenSession!==active)return;
  // A temporary polling failure must not erase the user's selection.
  taskStatusStale=true;
  $("taskStatusNotice").hidden=false;
  $("taskStatusNotice").textContent="Список не обновлён. Показаны предыдущие данные.";
  renderSessions();
  status("Список задач недоступен: "+error.message);
 }
}
function renderComposeModules(data){
 const sid=chosenSession;
 composeCatalogBySession.set(sid,data);
 const select=$("composeProfileSelect");
 const profiles=(Array.isArray(data?.profiles)?data.profiles:[]).filter(p=>
   p&&typeof p.id==="string"&&/^[a-z0-9][a-z0-9_-]{0,55}$/.test(p.id)&&
   typeof p.name==="string"&&p.name.trim()&&p.name.length<=70&&
   Array.isArray(p.module_ids));
 let selectedId=composeProfileManuallySelected.has(sid)
   ?composeProfilesBySession.get(sid)||""
   :data?.active_profile_id||"";
 if(!profiles.some(p=>p.id===selectedId)){
  selectedId=profiles.find(p=>p.id===data?.active_profile_id)?.id||
    profiles[0]?.id||"";
 }
 // Store the effective native active profile as well as explicit owner choices.
 if(selectedId)composeProfilesBySession.set(sid,selectedId);
 const profile=profiles.find(p=>p.id===selectedId);
 clear(select);
 if(!profiles.length){
  const option=el("option","Активный профиль Notifier (ожидаю список)");
  option.value="";select.append(option);select.value="";
 }else{
  for(const p of profiles){
   const option=el("option",p.name+(p.id===data?.active_profile_id?" · активный":""));
   option.value=p.id;select.append(option);
  }
  select.value=selectedId;
 }
 select.disabled=!profile;
 $("composeProfileHint").textContent=profile
  ?"Профиль из Notifier: его модули и поведение применяются без изменения настроек."
  :"Ожидаю профили Notifier; пока используется его активный профиль.";
 const modules=Array.isArray(data?.modules)?data.modules:[];
 const valid=modules.filter(m=>m&&typeof m.id==="string"&&
   /^[a-z0-9][a-z0-9._-]{0,79}$/.test(m.id)&&typeof m.title==="string");
 const defaults=Array.isArray(profile?.module_ids)
   ?profile.module_ids:(Array.isArray(data?.default_module_ids)?data.default_module_ids:[]);
 const signature=selectedId+"|"+JSON.stringify(defaults);
 if(composeProfileAppliedBySession.get(sid)!==signature){
  if(composeProfileAppliedBySession.get(sid)?.split("|")[0]!==selectedId||
     !composeModuleEditedBySession.has(sid)){
   composeModulesBySession.set(sid,new Set(defaults));
   composeModuleEditedBySession.delete(sid);
  }
  composeProfileAppliedBySession.set(sid,signature);
 }
 const picked=composeModulesBySession.get(sid)||new Set(defaults);
 if(!composeModulesBySession.has(sid)&&profile)
  composeModulesBySession.set(sid,picked);
 const list=$("composeModulesList");clear(list);
 const search=$("composeModuleSearch").value.trim().toLowerCase();
 // Profiles remain visible if Planning Helper is temporarily offline.
 for(const id of picked){
  if(valid.some(m=>m.id===id))continue;
  if(search&&!id.toLowerCase().includes(search))continue;
  const row=el("label");row.className="compose-module-row";
  const checkbox=el("input");checkbox.type="checkbox";checkbox.checked=true;
  checkbox.value=id;checkbox.disabled=true;
  row.append(checkbox,el("span",id+" · недоступен в каталоге Helper"));
  list.append(row);
 }
 for(const m of valid){
  if(search&&!String(m.title+" "+m.id).toLowerCase().includes(search))continue;
  const row=el("label");row.className="compose-module-row";
  const box=el("input");box.type="checkbox";box.value=m.id;box.checked=picked.has(m.id);
  box.addEventListener("change",()=>{
   composeModuleEditedBySession.add(sid);
   if(box.checked)picked.add(m.id);else picked.delete(m.id);
  });
  row.append(box,el("span",m.title+" · "+m.id));list.append(row)
 }
 if(!list.children.length)
  list.append(el("p",data?.modules_synced
   ?"Нет доступных модулей по текущему поиску."
   :"Каталог Helper ещё не подключён. Профили Notifier сохраняются."));
}
function updateComposeTarget(){
 const next=chosenSession||"";
 if(composeSession!==next){
  if(composeSession)storeComposeDraft();
  composeSession=next;$("composeText").value=safeDraftRead(next);
  $("composeModuleSearch").value="";
  renderComposeModules(composeCatalogBySession.get(next)||null);
  $("composeStatus").textContent="Только открытая привязанная вкладка. Проверяю доступность…"
 }
 const record=(Array.isArray(state?.sessions)?state.sessions:[])
   .find(item=>item.reporting_session_id===next);
 $("composeTarget").textContent=record
  ?"Адресат: "+String(sessionDisplayTitle(record))+" · "+String(record.conversation_id||"")
  :"Сначала выберите сессию";
 $("composeSend").disabled=!record;$("composeInsert").disabled=!record;
 $("composeFile").disabled=!record;
 $("composeSendPrepared").disabled=!record
}
const composerActionNames={file:"Файл",insert:"Вставить",
 send:"Файл + Send",send_prepared:"Нажать Send"};
const composerEventNames={queued:"Команда поставлена в очередь Viewer",
 claimed:"Notifier принял команду",expired:"Команда истекла без получения",
 unconfirmed:"Notifier не подтвердил выполнение вовремя",
 preparing:"Notifier начал подготовку",inserted:"Контекст вставлен без Send",
 file_attached:"Файл и контекст подготовлены без Send",
 attachment_unconfirmed:"Одна попытка загрузки файла. Карточка не распознана; файл МОГ прикрепиться. Не повторять и не нажимать Send!",
 attachment_only:"Карточка файла обнаружена, но Fortis-контекст НЕ подготовлен. Не нажимать Send!",
 send_initiated:"Попытка штатного Send; приём ChatGPT не подтверждён",
 refused:"Notifier отказал"};
const composerReasonNames={busy:"занят другим действием",
 no_composer:"редактор ChatGPT недоступен",
 native_draft_occupied:"редактор содержит другой текст",
 prepared_missing:"нет готового черновика с task_id",
 context_mismatch:"текст и сохранённый контекст не совпадают",
 attachment_missing:"карточка вложения не подтверждена",
 send_button_not_ready:"кнопка Send недоступна",
 upload_unconfirmed:"прикрепление файла не подтверждено",
 duplicate:"совпадающий SHA-256",modules_unavailable:"модули недоступны",
 not_confirmed:"не удалось подтвердить состояние",unknown:"не удалось установить причину"};
function renderComposeEvents(data){
 const log=$("composeEvents"),oldScroll=log.scrollTop,oldMax=log.scrollHeight;
 clear(log);
 const events=Array.isArray(data?.history)?data.history:[];
 if(!events.length){log.append(el("p","Событий пока нет."));return}
 for(const event of events){
  const line=el("p");
  const when=String(event?.at||"").replace("T"," ").slice(11,19);
  const prefix=(when?when+" · ":"")+
   (composerActionNames[event.mode]||"Команда")+" · ";
  const reason=event.reason?" ("+(composerReasonNames[event.reason]||"ошибка")+")":"";
  const task=typeof event.task_id==="string"&&/^task_[0-9a-f]{32}$/.test(event.task_id)
   ?" · "+event.task_id:"";
  const legacyMissingId=(event.event==="file_attached"||event.event==="inserted")&&!task;
  const detail=event.mode==="file"&&typeof event.detail==="string"&&event.detail.length<=512
   ?" · Полное сообщение Notifier: "+event.detail:"";
  line.textContent=prefix+(legacyMissingId?"Операция без подтверждённого task_id":
    (composerEventNames[event.event]||"Статус неизвестен"))+reason+task+detail;
  log.append(line)
 }
 if(oldMax===0||oldScroll>=oldMax-log.clientHeight-25)
  log.scrollTop=log.scrollHeight;
 else log.scrollTop=oldScroll
}
async function checkComposeStatus(){
 if($("composePanel").hidden||!chosenSession)return;
 const sid=chosenSession;
 try{
  const data=await req("/api/dispatch/status?session="+encodeURIComponent(sid));
  if(sid!==chosenSession||$("composePanel").hidden)return;
  renderComposeModules(data);
  renderComposeEvents(data);
  const event=data.dispatch;
  let message=data.available?"Вкладка Notifier подключена":"Вкладка недоступна — отправка запрещена";
  if(event){
   const statuses={pending:"команда ожидает вкладку",claimed:"команда выдана по запросу вкладки; подтверждения выполнения ещё нет",
    inserted:"контекст вставлен; Send не нажат",
    file_attached:"файл и контекст подготовлены; Send не нажат",
    attachment_unconfirmed:"одна попытка прикрепления; результат не подтверждён. Файл мог прикрепиться, повторять нельзя",
    attachment_only:"карточка файла обнаружена, но task_id / Fortis-контекст не подтверждены. Не отправлять",
    send_initiated:"Notifier сообщил об одной попытке Send; приём ChatGPT не подтверждён",
    refused:"Notifier отказал; текст сохранён в поле Observatory",
    unconfirmed:"нет подтверждения после получения команды — возможна отправка, автоматического повтора нет",
    expired:"команда не была получена вовремя"};
   message+=" · "+(statuses[event.status]||"неизвестное состояние");
   if((event.status==="file_attached"||event.status==="inserted")&&!event.task_id)
    message+=" · ВНИМАНИЕ: task_id не подтверждён (старый протокол)";
   if(event.task_id)message+=" · task_id: "+event.task_id
  }
  $("composeStatus").textContent=message
  // Only the exact dispatch ACK may clear the field; queue receipt is insufficient.
  const pending=composePendingSends.get(sid);
  if(pending && event?.dispatch_id===pending.dispatchId &&
     event?.status==="send_initiated"&&/^task_[0-9a-f]{32}$/.test(event.task_id||"")){
    composePendingSends.delete(sid);
    if($("composeText").value===pending.original &&markDraftSent(sid,pending.original)){
      $("composeText").value="";
      // Keep the locally saved exact original available for restoration.
      $("composeStatus").textContent+=" · Поле очищено; оригинал доступен в истории Notifier и локальном черновике";
    }
  }else if(pending&&event?.dispatch_id===pending.dispatchId&&
           ["refused","expired","unconfirmed"].includes(event.status)){
    composePendingSends.delete(sid)
  }
  return event
 }catch(error){
  if(sid===chosenSession)$("composeStatus").textContent="Связь с адресатом недоступна: "+error.message
 }
}
async function dispatchCompose(mode){
 const sid=chosenSession;
 const session=(Array.isArray(state?.sessions)?state.sessions:[])
  .find(item=>item.reporting_session_id===sid);
 const original=mode==="send_prepared"?"":$("composeText").value;
 // Same Notifier behavior: an oversized Insert prepares a .txt instead of
 // attempting to paste tens of thousands of characters into ChatGPT.
 const actualMode=mode==="insert"&&original.length>=12000?"file":mode;
 if(!session||(mode!=="send_prepared"&&!original.trim())){
  $("composeStatus").textContent="Выберите сессию и введите текст";return
 }
 const button=$(mode==="send_prepared"?"composeSendPrepared":
  mode==="send"?"composeSend":mode==="file"?"composeFile":"composeInsert");
 const selected=composeModulesBySession.get(sid);
 const profileId=composeProfilesBySession.get(sid)||null;
 // Null when no profile data yet: Notifier uses the current active profile.
 const moduleIds=mode==="send_prepared"?null:
  selected&&composeModuleEditedBySession.has(sid)?Array.from(selected):null;
 button.disabled=true;
 try{
  // Read-back is compulsory before dispatch of a new original and clearing.
  if(mode!=="send_prepared"&&!safeDraftWrite(sid,original)){
   $("composeStatus").textContent="Черновик не сохранился локально. Команда отменена.";return
  }
  const answer=await req("/api/dispatch",{
   method:"POST",headers:{"Content-Type":"application/json"},
   body:JSON.stringify({session:sid,chat:session.conversation_id,
     mode:actualMode,text:original,module_ids:moduleIds,
     profile_id:mode==="send_prepared"?null:profileId,
     ...(mode==="send"?{delay_ms:Number($("composeSendDelay").value)}:{})})});
  if(sid!==chosenSession)return;
  $("composeStatus").textContent="Команда "+answer.dispatch_id+" принята локально. Это ещё не подтверждение действия."
  if(mode==="send"||mode==="send_prepared")
   composePendingSends.set(sid,{dispatchId:answer.dispatch_id,
    original:mode==="send_prepared"?$("composeText").value:original});
  await checkComposeStatus()
 }catch(error){
  if(sid===chosenSession)$("composeStatus").textContent=
   "Команда не доставлена: "+error.message+". Текст сохранён."
 }finally{button.disabled=false}
}
$("toggleCompose").addEventListener("click",async()=>{
 const visible=$("composePanel").hidden;
 $("composePanel").hidden=!visible;
 $("toggleCompose").setAttribute("aria-expanded",String(visible));
 if(visible)await checkComposeStatus()
});
$("composeInsert").addEventListener("click",()=>dispatchCompose("insert"));
$("composeSend").addEventListener("click",()=>dispatchCompose("send"));
$("composeFile").addEventListener("click",()=>dispatchCompose("file"));
$("composeSendPrepared").addEventListener("click",()=>dispatchCompose("send_prepared"));
$("toggleComposeModules").addEventListener("click",()=>{
 const panel=$("composeModulesPanel");
 panel.open=!panel.open;
 $("toggleComposeModules").setAttribute("aria-expanded",String(panel.open));
});
$("composeModuleSearch").addEventListener("input",()=>{
 renderComposeModules(composeCatalogBySession.get(chosenSession)||null)
});
$("composeProfileSelect").addEventListener("change",()=>{
 const sid=chosenSession;
 const chosen=$("composeProfileSelect").value;
 const data=composeCatalogBySession.get(sid);
 if(!Array.isArray(data?.profiles)||!data.profiles.some(p=>p.id===chosen))return;
 composeProfilesBySession.set(sid,chosen);
 composeProfileManuallySelected.add(sid);
 composeModuleEditedBySession.delete(sid);
 composeProfileAppliedBySession.delete(sid);
 renderComposeModules(data)
});
$("composeText").addEventListener("input",deferComposeSave);
$("composeRestoreDraft").addEventListener("click",()=>{
 if(!chosenSession)return;
 if($("composeText").value.trim()){
  $("composeDraftStatus").textContent="Поле занято: ничего не заменено";return
 }
 const saved=safeDraftRecovery(chosenSession);
 $("composeText").value=saved?.text||safeDraftRead(chosenSession);
 $("composeDraftStatus").textContent="Сохранённый оригинал восстановлен без Send"
});
window.setInterval?.(()=>{if(!$("composePanel").hidden)checkComposeStatus()},5000);
function previewText(value,maxLength=118){
 const cleaned=String(value??"").replace(/\s+/g," ").trim();
 return cleaned.length>maxLength?cleaned.slice(0,maxLength)+"…":cleaned
}
function buildRecords(data,sid,tid){
 const session=Array.isArray(state?.sessions)
  ?state.sessions.find(item=>item.reporting_session_id===sid):null;
 const events=Array.isArray(session?.events)?session.events:[];
 const result=[];
 result.push({id:"user",type:"user",time:null,body:data.original_text,
  label:data.original_text===null?"Оригинал не получен":"Оригинал пользователя",
  preview:data.original_text===null?"Точный текст из браузера пока отсутствует":
   previewText(data.original_text)||"(пустой оригинал)"});
 const historyEvents=Array.isArray(data.events)?data.events:[];
 for(const [index,event] of historyEvents.entries()){
  const meta=events.find(item=>item.task_id===tid &&
   item.sequence===event.sequence && item.event===event.event)||event;
  result.push({id:"event:"+(meta.event_id||String(event.sequence)+":"+index),
   type:"event",time:meta.accepted_at||null,sequence:meta.sequence,
   event:meta.event,stage:meta.stage||null,summary:meta.summary||null,
   detail:typeof event.detail==="string"?event.detail:null,
   label:"Событие · "+String(meta.event||""),
   preview:previewText(meta.summary||("Шаг №"+String(meta.sequence)))})
 }
 const messages=Array.isArray(data.assistant_messages)?data.assistant_messages:[];
 for(const [index,message] of messages.entries()){
  result.push({id:"message:"+(message.message_id||index),type:"message",
   time:message.accepted_at||null,kind:message.kind||"assistant",
   provenance:message.provenance||"sender_claim",body:message.body??"",
   label:"Сообщение AI · "+String(message.kind||""),
   preview:previewText(message.body)||"(пустое сообщение)"})
 }
 const original=result.shift();
 // User-original is listed first, but it has no acceptance time in history.
 result.sort((a,b)=>{
  if(a.time && b.time){
   const diff=Date.parse(a.time)-Date.parse(b.time);
   if(Number.isFinite(diff)&&diff!==0)return diff
  }else if(a.time!==b.time)return a.time? -1:1;
  if(a.type==="event" && b.type==="event")return (a.sequence??0)-(b.sequence??0);
  return 0
 });
 return [original,...result]
}
function showRecordDetails(){
 const selected=recordItems.find(item=>item.id===chosenRecord);
 const display=$("history");clear(display);display.scrollTop=0;
 if(!selected){display.append(el("p","Выберите запись."));return}
 const header=el("div");header.className="record-detail-head";
 const badge=el("span",selected.type==="user"?"Пользователь":
  selected.type==="event"?"Событие":"Сообщение AI");
 badge.className="record-type "+selected.type;
 header.append(badge,el("h3",selected.label));display.append(header);
 if(selected.time)display.append(el("p","Принято: "+showTime(selected.time)));
 if(selected.type==="user"){
  if(selected.body===null){
   display.append(el("p","Точный оригинал ещё не получен из браузерного Notifier. Текст не восстанавливается из ответа AI."))
  }else{
   display.append(el("p","Точный сохранённый оригинал пользователя."));
   const content=el("pre",selected.body);content.className="message-body";
   display.append(content)
  }
 }else if(selected.type==="event"){
  display.append(el("p","Шаг работы, а не полный ответ AI."));
  display.append(el("p","Тип: "+selected.event));
  if(selected.stage)display.append(el("p","Стадия: "+selected.stage));
  display.append(el("p","Порядковый номер: "+selected.sequence));
  if(selected.summary)display.append(el("pre",selected.summary));
  else display.append(el("p","Краткое описание события недоступно."));
  if(selected.detail){
   display.append(el("h4","Подробное пояснение шага"));
   const detail=el("pre",selected.detail);detail.className="message-body";
   display.append(detail)
  }else display.append(el("p","Для этого события подробное пояснение не передано."))
 }else{
  display.append(el("p","Тип сообщения: "+selected.kind));
  display.append(el("small","Источник: "+selected.provenance+" · полный текст из архива"));
  const content=el("pre",selected.body);content.className="message-body";
  display.append(content)
 }
}
function renderRecords({scrollBottom=false}={}){
 const list=$("records"),previousScroll=list.scrollTop;clear(list);
 $("recordCount").textContent=String(recordItems.length);
 if(!recordItems.length){list.append(el("p","Записей нет."));historyPlaceholder("Выберите запись.");return}
 for(const item of recordItems){
  const b=el("button");b.type="button";
  b.className="record "+item.type+(chosenRecord===item.id?" active":"");
  const label=el("span",item.label);label.className="record-label";
  const preview=el("span",item.preview);preview.className="record-preview";
  b.append(label,preview);
  if(item.time){
   const t=el("span",showTime(item.time));t.className="record-time";b.append(t)
  }
  b.onclick=()=>{chosenRecord=item.id;renderRecords();showRecordDetails()};
  list.append(b)
 }
 if(scrollBottom)scrollRecordsToBottom();
 else list.scrollTop=previousScroll
}
async function showHistory({follow=false}={}){
 if(!chosenSession||!chosenTask)return;
 const sid=chosenSession, tid=chosenTask, serial=++historyReadSerial;
 if(!activeHistory||activeHistory.session!==sid||activeHistory.task_id!==tid){
  recordsPlaceholder("Загрузка записей…");historyPlaceholder("Загрузка…")
 }
 try{
  const data=await req("/api/history?session="+encodeURIComponent(sid)+"&task="+encodeURIComponent(tid));
  if(sid!==chosenSession||tid!==chosenTask||serial!==historyReadSerial)return;
  if(data.session!==sid||data.task_id!==tid)throw Error("Неверная сессия");
  const previousRecord=chosenRecord, previousDetailScroll=$("history").scrollTop;
  activeHistory=data;recordItems=buildRecords(data,sid,tid);
  // The last chronological record might be a completed event AFTER final AI.
  // Show it rather than preferentially choosing an older AI message.
  if(follow||!recordItems.some(item=>item.id===chosenRecord))
   chosenRecord=recordItems.at(-1)?.id||"";
  renderRecords({scrollBottom:follow});
  showRecordDetails();
  if(!follow&&previousRecord===chosenRecord)
   $("history").scrollTop=previousDetailScroll
 }catch(error){
  if(sid!==chosenSession||tid!==chosenTask||serial!==historyReadSerial)return;
  // Preserve a readable old snapshot during a transient poll failure.
  status("История недоступна: "+error.message);
  if(!activeHistory)resetRecordView("Не удалось прочитать историю.")
 }
}
async function refresh(){
 if(!token||archiveRefreshBusy)return;
 archiveRefreshBusy=true;
 try{
  const next=await req("/api/state");
  if(!token)return;
  state=next;archiveStatusStale=false;
  await refreshSessionVisibility();
  const sessions=Array.isArray(state.sessions)?state.sessions:[];
  const visible=archiveVisibilityKnown
   ?sessions.filter(s=>!archivedSessions.has(s.reporting_session_id)):[];
  if(!visible.some(s=>s.reporting_session_id===chosenSession)){
   chosenSession=visible.find(s=>sessionLiveIds.has(s.reporting_session_id))?.reporting_session_id||
     visible[0]?.reporting_session_id||"";
   chosenTask="";taskCards=[];resetSessionActions();
   resetRecordView("Загрузка задач…")
  }
  renderSessions();
  await refreshDiscoveredChats();
  status("Сессий: "+sessions.length+" · обновлено "+new Date().toLocaleTimeString("ru-RU"));
  if(chosenSession){
   await loadTasks();
   await Promise.all([refreshNotifierConnection(),refreshNotifierEnrollment()]);
  }else resetRecordView("Добавьте сессию, чтобы увидеть историю.")
 }catch(error){archiveStatusStale=true;renderSessions();status("Чтение недоступно: "+error.message)}
 finally{archiveRefreshBusy=false}
}
$("toggleRegister").addEventListener("click",()=>toggleAction("toggleRegister"));
$("toggleInstructions").addEventListener("click",()=>{
 if(!$("instructionPanel").hidden){closeActions();return}
 return showInstructions(chosenSession)
});
$("togglePair").addEventListener("click",()=>{
 if(!chosenSession){status("Сначала выберите сессию.");return}
 toggleAction("togglePair")
});
async function unlockViewer(value){
 token=String(value||"").trim();
 if(!token)return false;
 try{
  state=await req("/api/state");
  $("unlock").hidden=true;$("app").hidden=false;
  const sessions=Array.isArray(state.sessions)?state.sessions:[];
  await refreshSessionVisibility();
  if(sessions.length){
   const first=sessions.find(s=>!archivedSessions.has(s.reporting_session_id));
   chosenSession=first?.reporting_session_id||"";
  }
  $("toolbar").hidden=false;applyColumnWidths();
  renderSessions();status("Подключено · сессий: "+sessions.length);
  await refreshDiscoveredChats();
  if(chosenSession){await loadTasks();await refreshNotifierConnection();await refreshNotifierEnrollment();}
  else resetRecordView("Добавьте сессию, чтобы увидеть историю.");
  return true;
 }catch(error){token="";return false;}
}
$("form").addEventListener("submit",async ev=>{
 ev.preventDefault();const v=$("secret").value.trim();$("secret").value="";
 if(!await unlockViewer(v))alert("Код не принят или Docker недоступен");
});
// The owner-only file:// launcher passes the existing bearer through postMessage.
// Never return a token in HTTP HTML, API, cookies, URL, or a new bearer-less route.
window.addEventListener("message",async event=>{
 if(event.origin!=="null"||event.source!==window.opener||token)return;
 if(!event.data||event.data.type!=="fortis-observatory-owner-unlock-v1"||
    typeof event.data.code!=="string"||
    !/^[A-Za-z0-9_-]{32,128}$/.test(event.data.code))return;
 if(await unlockViewer(event.data.code)){
  try{window.opener.postMessage({type:"fortis-observatory-unlocked-v1"},"*")}catch(_){}
 }
});
$("refresh").addEventListener("click",refresh);
$("autoFollow").addEventListener("change",()=>{
 if(autoFollow()&&token&&chosenSession)void loadTasks()
});
$("checkNotifierConnection").addEventListener("click",async()=>{
 await refreshNotifierConnection();await refreshNotifierEnrollment();
});
$("enableTaskIntents").addEventListener("click",async()=>{
 const sid=chosenSession;
 const item=(state?.sessions||[]).find(s=>s.reporting_session_id===sid);
 if(!item)return;
 $("enableTaskIntents").disabled=true;
 try{
  await req("/api/notifier/task-intents",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({session:sid,chat:item.conversation_id})});
  if(sid===chosenSession)await refreshNotifierEnrollment();
 }catch(error){if(sid===chosenSession)$("enrollmentStatus").textContent="Разрешение не выдано: "+error.message;}
 finally{$("enableTaskIntents").disabled=false;}
});
$("approveNotifier").addEventListener("click",approveNotifierEnrollment);
$("revokeAutoNotifier").addEventListener("click",revokeAutoEnrollment);
if(typeof setInterval==="function"){
 // One read-only poll for archive, task, history and pairing every 5 seconds.
 // No browser Send or command dispatch is triggered here.
 setInterval(()=>{
  if(!token)return;
  if(archiveRefreshBusy){renderSessions();return;}
  return refresh();
 },5000);
}
$("registerForm").addEventListener("submit",async event=>{
 event.preventDefault();
 const button=$("registerButton");
 button.disabled=true;$("registerStatus").textContent="Подключение...";
 try{
  const url=$("chatUrl").value.trim(), title=$("chatTitle").value.trim();
  const result=await req("/api/register",{
   method:"POST",headers:{"Content-Type":"application/json"},
   body:JSON.stringify({url,title})});
  if(!/^rs_[0-9a-f]{32}$/.test(result.session))throw Error("Неожиданный ответ");
  if(archivedSessions.has(result.session)){
   $("registerStatus").textContent="Эта сессия в архиве. Восстановите её через группу «Архив».";
   return
  }
  chosenSession=result.session;chosenTask="";taskCards=[];
  resetSessionActions();resetRecordView("Загрузка задач…");await refresh();
  $("registerStatus").textContent=result.created?"Сессия подключена.":"Этот чат уже подключён.";
  await showInstructions(result.session);
 }catch(error){
  $("registerStatus").textContent="Ошибка подключения: "+error.message;
  openAction("toggleRegister")
 }finally{button.disabled=false}
});
$("makePair").addEventListener("click",async()=>{
 const sid=chosenSession;
 if(!/^rs_[0-9a-f]{32}$/.test(sid))return;
 $("pairStatus").textContent="Получение кода для выбранной сессии...";
 try{
  const response=await req("/api/notifier-pair?session="+encodeURIComponent(sid));
  if(sid!==chosenSession)return;
  if(response.pairing?.reporting_session_id!==sid ||
     response.pairing?.origin!=="http://127.0.0.1:18755")
    throw Error("Неверная привязка");
  $("pairValue").value=JSON.stringify(response.pairing);
  $("pairStatus").textContent="Код готов, но это НЕ подтверждение подключения. Скопируй его в Tampermonkey.";
  await refreshNotifierConnection();
 }catch(error){
  if(sid!==chosenSession)return;
  $("pairValue").value="";$("pairStatus").textContent="Привязка недоступна: "+error.message
 }
});
$("revokeDispatch").addEventListener("click",async()=>{
 const sid=chosenSession;
 if(!sid)return;
 try{
  const result=await req("/api/dispatch/revoke",{
   method:"POST",headers:{"Content-Type":"application/json"},
   body:JSON.stringify({session:sid})});
  if(sid!==chosenSession)return;
  $("pairValue").value="";
  $("pairStatus").textContent=result.revoked
    ?"Доступ к адресным командам отозван. Ранее выданная команда могла уже исполняться."
    :"У этой сессии не было активного права адресной отправки.";
  $("composeStatus").textContent="Повторно привяжите Notifier для восстановления доступа.";
  await refreshNotifierConnection()
 }catch(error){if(sid===chosenSession)$("pairStatus").textContent=
   "Не удалось отозвать доступ: "+error.message}
});
$("copyPair").addEventListener("click",async()=>{
 if(!$("pairValue").value)return;
 try{
  await navigator.clipboard.writeText($("pairValue").value);
  $("pairStatus").textContent="Код скопирован; вставь его в окно Tampermonkey.";
 }catch(error){
  $("pairValue").focus();$("pairValue").select();
  $("pairStatus").textContent="Код выделен — нажми Ctrl+C.";
 }
});
$("copyInstructions").addEventListener("click",async()=>{
 try{
  await navigator.clipboard.writeText($("instructions").value);
  $("instructionStatus").textContent="Инструкция скопирована.";
 }catch(error){
  $("instructions").focus();$("instructions").select();
  $("instructionStatus").textContent="Скопируйте выделенный текст вручную (Ctrl+C).";
 }
});
</script></body></html>'''


def read_owner_config(install=None, environ=os.environ, platform=sys.platform, whoami=None):
    if platform != "win32":
        raise ValueError("windows_owner_only")
    if not install:
        install = Path(environ["LOCALAPPDATA"]) / "FortisObservatoryV1" / "Viewer"
    install = Path(install).resolve(strict=True)
    expected = (Path(environ["LOCALAPPDATA"]).resolve() /
                "FortisObservatoryV1" / "Viewer")
    if install != expected or install.is_symlink():
        raise ValueError("not_protected_owner_install")
    script = Path(__file__).resolve()
    if script.parent != install or script.is_symlink():
        raise ValueError("viewer_source_not_installed")
    config = install / "approved-owner.json"
    if config.is_symlink() or not config.is_file() or config.stat().st_size > 2048:
        raise ValueError("approved_owner_config_missing")
    obj = json.loads(config.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or set(obj) != {"owner_sid", "container"}:
        raise ValueError("bad_config")
    if not WIN_SID.fullmatch(obj["owner_sid"]) or not CONTAINER.fullmatch(obj["container"]):
        raise ValueError("bad_approval")
    if whoami is None:
        probe = subprocess.run(["whoami.exe", "/user", "/fo", "csv", "/nh"],
                               capture_output=True, timeout=5, check=True)
        whoami = probe.stdout.decode("utf-8-sig", "replace")
    identities = list(csv.reader(io.StringIO(whoami)))
    if len(identities) != 1 or len(identities[0]) < 2 or identities[0][-1].strip() != obj["owner_sid"]:
        raise ValueError("unapproved_owner_sid")
    # NTFS ACL of the approved config/installed source still needs to be
    # checked independently; current user SID is not an ACL guarantee.
    return obj


def docker_command(container, argv, docker_cli="docker.exe", runner=subprocess.run,
                   timeout=12):
    if not isinstance(container, str) or not CONTAINER.fullmatch(container):
        raise ValueError("invalid_container")
    if any(not isinstance(x, str) for x in argv):
        raise ValueError("invalid_argv")
    command = [docker_cli, "exec", container, "python3", *argv]
    out = runner(command, capture_output=True, timeout=timeout, check=False)
    return out


def repo_read(container, action, session=None, task=None, docker_cli="docker.exe",
              runner=subprocess.run):
    if action == "state" and (session is not None or task is not None):
        raise ValueError("invalid_state_ids")
    if action == "tasks" and (not SID.fullmatch(session or "") or task is not None):
        raise ValueError("invalid_task_listing")
    if action == "instructions" and (not SID.fullmatch(session or "") or task is not None):
        raise ValueError("invalid_instructions_id")
    if action == "history" and (not SID.fullmatch(session or "") or
                                not TASK.fullmatch(task or "")):
        raise ValueError("invalid_history_ids")
    if action not in ("state", "tasks", "history", "instructions"):
        raise ValueError("invalid_action")
    cmd = [DOCKER_READER, action]
    if action == "tasks":
        cmd.extend(["--session", session])
    if action == "instructions":
        cmd = [DOCKER_SERVICE, "instructions", "--session", session]
    if action == "history":
        cmd.extend(["--session", session, "--task", task])
    result = docker_command(container, cmd, docker_cli, runner)
    if result.returncode != 0 or len(result.stdout) > MAX_PAYLOAD:
        raise ValueError("repo_read_unavailable")
    if action == "instructions":
        content = result.stdout.decode("utf-8")
        if not content.strip() or len(content) > 65536:
            raise ValueError("instructions_unavailable")
        return {"ok": True, "session": session, "text": content}
    value = json.loads(result.stdout.decode("utf-8"))
    if not isinstance(value, dict) or value.get("ok") is not True:
        raise ValueError("bad_repo_response")
    return value


def valid_registration(url, title):
    if not isinstance(url, str) or not CHAT_URL.fullmatch(url):
        raise ValueError("invalid_chat_url")
    if (not isinstance(title, str) or not SAFE_TITLE.fullmatch(title) or
            title != title.strip() or BAD_TITLE.search(title)):
        raise ValueError("invalid_title")
    return CHAT_URL.fullmatch(url).group(1), title


def repo_register(container, url, title, docker_cli="docker.exe",
                  runner=subprocess.run):
    """One narrow owner-authorized mutation: register a Repo route session.

    Reuses an existing chat registration to avoid ordinary duplicate clicks.
    Does not grant observer or writer pairing, disclose secrets, or register
    arbitrary URLs. No shell or HTTP port exposure.
    """
    chat_id, title = valid_registration(url, title)
    state = repo_read(container, "state", docker_cli=docker_cli, runner=runner)
    existing = next((s for s in state.get("sessions", [])
                     if s.get("conversation_id") == chat_id and s.get("route") == "repo"), None)
    if existing:
        return {"ok": True, "created": False,
                "session": existing["reporting_session_id"],
                "session_task_id": existing["task_id"],
                "conversation_id": chat_id}
    result = docker_command(container,
            [DOCKER_SERVICE, "register", "--chat-id", chat_id, "--title", title],
            docker_cli=docker_cli, runner=runner)
    if result.returncode != 0 or len(result.stdout) > 4096:
        raise ValueError("registration_failed")
    meta = json.loads(result.stdout.decode("utf-8"))
    sid = meta.get("reporting_session_id")
    session_task = meta.get("session_task_id")
    if (not SID.fullmatch(sid or "") or not TASK.fullmatch(session_task or "") or
            meta.get("conversation_id") != chat_id or meta.get("route") != "repo"):
        raise ValueError("invalid_registration_reply")
    return {"ok": True, "created": True, "session": sid,
            "session_task_id": session_task, "conversation_id": chat_id}


def ensure_repo_running(container, docker_cli="docker.exe",
                        runner=subprocess.run):
    """Start only existing Repo Observatory process if it is not responding."""
    status = docker_command(container, [DOCKER_SERVICE, "status"], docker_cli, runner)
    if status.returncode == 0:
        value = json.loads(status.stdout.decode("utf-8"))
        if value.get("state") != "running":
            raise ValueError("unexpected_service_state")
        return "already_running"
    if status.returncode not in (1,):
        raise ValueError("unexpected_status_failure")
    # No unapproved shell, network publishing, mounted new volume, or separate
    # server. Docker exec detached runs one Repo service in the existing volume.
    spawn = runner([docker_cli, "exec", "-d", container, "python3",
                    DOCKER_SERVICE, "run", "--state-dir", REPO_STATE,
                    "--port", "18754"], capture_output=True,
                   timeout=12, check=False)
    if spawn.returncode != 0:
        raise ValueError("docker_start_failed")
    import time
    for _ in range(12):
        time.sleep(.4)
        result = docker_command(container, [DOCKER_SERVICE, "status"], docker_cli, runner)
        if result.returncode == 0:
            obj = json.loads(result.stdout.decode("utf-8"))
            if obj.get("state") == "running":
                return "started"
    raise ValueError("repo_service_not_ready")



class OwnerSessionArchive:
    """Owner-private view lifecycle, separate from immutable Docker task history.

    Persist *only* IDs of hidden sessions; no messages, secrets or credentials.
    Archiving revokes Notifier grants/dispatch in the owner handler, not in Docker.
    """
    FILENAME = "archived-sessions.json"

    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / self.FILENAME
        self.lock = threading.RLock()
        self.items = self._load()

    @staticmethod
    def _valid(value):
        if not isinstance(value, dict) or value.get("version") != 1 or set(value) != {"version", "sessions"}:
            raise ValueError("invalid_session_archive")
        sessions = value["sessions"]
        if not isinstance(sessions, dict) or len(sessions) > 256 or any(
            not SID.fullmatch(sid) or not isinstance(chat, str) or
            not re.fullmatch(r"[A-Za-z0-9-]{8,100}", chat)
            for sid, chat in sessions.items()
        ):
            raise ValueError("invalid_archive_entries")
        return sessions

    def _load(self):
        if self.path.is_symlink():
            raise ValueError("archive_symlink_denied")
        if not self.path.exists():
            return {}
        if self.path.stat().st_size > 64000:
            raise ValueError("archive_too_large")
        return self._valid(json.loads(self.path.read_text(encoding="ascii")))

    def _write(self, values):
        if not self.directory.is_dir() or self.directory.is_symlink() or self.path.is_symlink():
            raise ValueError("archive_path_denied")
        payload = json.dumps({"version":1,"sessions":values},sort_keys=True,separators=(",",":"))
        temp = self.directory / ("." + self.FILENAME + ".new")
        if temp.exists() or temp.is_symlink():
            raise ValueError("archive_temp_collision")
        fd = os.open(temp, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="ascii") as out:
                out.write(payload)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp,self.path)
        finally:
            if temp.exists():temp.unlink()
        if self._load()!=values:
            raise ValueError("archive_readback_failed")

    def snapshot(self):
        with self.lock:
            return dict(self.items)

    def has(self, sid, chat=None):
        with self.lock:
            value = self.items.get(sid)
            return value is not None and (chat is None or value==chat)

    def archive(self, sid, chat):
        if not SID.fullmatch(sid or "") or not isinstance(chat,str) or not re.fullmatch(r"[A-Za-z0-9-]{8,100}", chat):
            raise ValueError("invalid_archive_target")
        with self.lock:
            if sid in self.items and self.items[sid]!=chat:
                raise ValueError("archive_identity_conflict")
            new={**self.items,sid:chat}
            self._valid({"version":1,"sessions":new})
            self._write(new)
            self.items=new
            return {"ok":True,"archived":True,"session":sid}

    def restore(self,sid,chat):
        if not SID.fullmatch(sid or ""):
            raise ValueError("invalid_restore_target")
        with self.lock:
            if self.items.get(sid)!=chat:
                raise ValueError("archive_restore_identity_mismatch")
            new=dict(self.items);del new[sid]
            self._write(new)
            self.items=new
            return {"ok":True,"archived":False,"session":sid}


def handler_for(token, read_data, nonce, register_data=None,
                notifier_pair=None, notifier_forward=None, dispatch_board=None,
                enrollment=None, session_archive=None):
    """Owner viewer plus narrow session-keyed Notifier transport."""
    registration_lock = threading.Lock()

    def resolve_chat(chat):
        if not isinstance(chat,str) or not re.fullmatch(r"[A-Za-z0-9-]{8,100}",chat):
            return None
        data=read_data("state",None,None)
        matches=[i for i in data.get("sessions",[]) if
                 i.get("conversation_id")==chat and i.get("route")=="repo" and
                 SID.fullmatch(i.get("reporting_session_id") or "")]
        if len(matches)!=1:return None
        match=matches[0]
        if session_archive is not None and session_archive.has(match["reporting_session_id"],chat):
            return None
        return match

    def valid_session(sid,chat):
        item=resolve_chat(chat)
        return bool(item and item.get("reporting_session_id")==sid)

    class Handler(BaseHTTPRequestHandler):
        server_version = "FortisOwnerViewer"
        sys_version = ""

        def log_message(self, *args):
            pass  # No URL/task/body/key in console logs.

        def write_reply(self, code, payload, media="application/json; charset=utf-8"):
            body = (json.dumps(payload, ensure_ascii=True).encode("ascii")
                    if isinstance(payload, dict) else payload)
            self.send_response(code)
            for k,v in (("Content-Type",media),("Content-Length",str(len(body))),
                        ("Cache-Control","no-store"),("X-Content-Type-Options","nosniff"),
                        ("Referrer-Policy","no-referrer"),("X-Frame-Options","DENY"),
                        ("Cross-Origin-Resource-Policy","same-origin"),
                        ("Content-Security-Policy",
                         "default-src 'none'; script-src 'nonce-"+nonce+
                         "'; style-src 'nonce-"+nonce+
                         "'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")):
                self.send_header(k,v)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            host=self.headers.get("Host","")
            uri=urlsplit(self.path)
            origin=self.headers.get("Origin")
            if uri.path in ("/api/task-activity", "/api/observer-status") and notifier_forward:
                if (host != f"127.0.0.1:{WIN_PORT}" or
                    uri.scheme or uri.netloc or uri.fragment or
                    origin not in (None, "https://chatgpt.com", "https://chat.openai.com")):
                    self.write_reply(403,{"ok":False,"error":"notifier_origin_denied"})
                    return
                try:
                    code,body=notifier_forward("GET",self.path,
                                  self.headers.get("X-Fortis-Observer-Key",""),None)
                    self.write_reply(code,body)
                except (ValueError, OSError, TypeError, subprocess.SubprocessError):
                    self.write_reply(503,{"ok":False,"error":"notifier_read_unavailable"})
                return
            if uri.path == "/api/dispatch/poll" and dispatch_board is not None:
                if (host != f"127.0.0.1:{WIN_PORT}" or
                        uri.scheme or uri.netloc or uri.fragment or
                        origin not in (None, "https://chatgpt.com", "https://chat.openai.com")):
                    self.write_reply(403, {"ok": False, "error": "dispatch_origin_refused"})
                    return
                try:
                    params = parse_qs(uri.query, strict_parsing=True)
                    if (set(params) != {"session", "chat"} or
                            any(len(v) != 1 for v in params.values())):
                        raise ValueError("invalid_poll")
                    data = dispatch_board.poll(params["session"][0], params["chat"][0],
                         self.headers.get("X-Fortis-Dispatch-Key", ""))
                    self.write_reply(200, data)
                except (ValueError, PermissionError, KeyError):
                    self.write_reply(403, {"ok": False, "error": "dispatch_not_authorized"})
                return
            if (host!=f"127.0.0.1:{WIN_PORT}" or
                uri.scheme or uri.netloc or uri.fragment):
                self.write_reply(403,{"ok":False,"error":"denied"})
                return
            if uri.path=="/" and not uri.query:
                # The owner-private file:// launcher opens this PUBLIC shell via
                # cross-site top-level navigation. It contains no bearer or
                # archive data; only the /api/* handlers access private state.
                # Keep cross-site fetch/subresource access to / forbidden.
                file_navigation=(
                    origin in (None,"null") and
                    self.headers.get("Sec-Fetch-Site","")=="cross-site" and
                    self.headers.get("Sec-Fetch-Mode","")=="navigate" and
                    self.headers.get("Sec-Fetch-Dest","")=="document")
                normal_navigation=(
                    origin in (None,f"http://127.0.0.1:{WIN_PORT}") and
                    self.headers.get("Sec-Fetch-Site","")!="cross-site")
                if not (file_navigation or normal_navigation):
                    self.write_reply(403,{"ok":False,"error":"denied"})
                    return
                self.write_reply(200,PAGE.replace("__NONCE__",nonce).encode("utf-8"),
                                 "text/html; charset=utf-8")
                return
            # Preserve EXACTLY the previous origin / cross-site protection
            # for sensitive API endpoints and all other URL paths.
            if (origin not in (None,f"http://127.0.0.1:{WIN_PORT}") or
                    self.headers.get("Sec-Fetch-Site","")=="cross-site"):
                self.write_reply(403,{"ok":False,"error":"denied"})
                return
            if not uri.path.startswith("/api/"):
                self.write_reply(404,{"ok":False,"error":"not_found"})
                return
            if not secrets.compare_digest(
                    self.headers.get("Authorization",""),"Bearer "+token):
                self.write_reply(401,{"ok":False,"error":"viewer_key_required"})
                return
            params=parse_qs(uri.query,strict_parsing=True) if uri.query else {}
            try:
                if uri.path=="/api/state" and not params:
                    data=read_data("state",None,None)
                elif (uri.path=="/api/tasks" and set(params)=={"session"} and
                      len(params["session"])==1 and SID.fullmatch(params["session"][0])):
                    data=read_data("tasks",params["session"][0],None)
                elif (uri.path=="/api/notifier-pair" and set(params)=={"session"} and
                      len(params["session"])==1 and SID.fullmatch(params["session"][0]) and
                      notifier_pair):
                    pair = notifier_pair(params["session"][0])
                    if dispatch_board is not None:
                        pair = {**pair, "dispatch_key": dispatch_board.pair(
                            params["session"][0], pair["conversation_id"])}
                    data={"ok":True,"pairing":pair}
                elif uri.path == "/api/notifier/discovered" and not params and enrollment is not None:
                    data = enrollment.discovered_for_owner()
                    if session_archive is not None:
                        archived_chats=set(session_archive.snapshot().values())
                        data["chats"]=[chat for chat in data["chats"] if chat["chat"] not in archived_chats]
                        data["available_sessions"]=[sid for sid in data["available_sessions"]
                          if not session_archive.has(sid)]
                        data["connected_sessions"]=[sid for sid in data["connected_sessions"]
                          if not session_archive.has(sid)]
                elif uri.path == "/api/session-visibility" and not params and session_archive is not None:
                    data={"ok":True,"archived":session_archive.snapshot()}
                elif (uri.path=="/api/notifier/pending" and set(params)=={"session"} and
                      len(params["session"])==1 and SID.fullmatch(params["session"][0]) and
                      enrollment is not None):
                    data=enrollment.pending_for(params["session"][0])
                elif (uri.path=="/api/dispatch/status" and set(params)=={"session"} and
                      len(params["session"])==1 and SID.fullmatch(params["session"][0]) and
                      dispatch_board is not None):
                    data=dispatch_board.status(params["session"][0])
                elif (uri.path=="/api/instructions" and set(params)=={"session"} and
                      len(params["session"])==1 and SID.fullmatch(params["session"][0])):
                    data=read_data("instructions",params["session"][0],None)
                elif (uri.path=="/api/history" and set(params)=={"session","task"} and
                      all(len(v)==1 for v in params.values()) and
                      SID.fullmatch(params["session"][0]) and TASK.fullmatch(params["task"][0])):
                    data=read_data("history",params["session"][0],params["task"][0])
                else:
                    raise ValueError("bad_query_or_route")
                self.write_reply(200,data)
            except (ValueError,OSError,subprocess.SubprocessError,
                    UnicodeError,json.JSONDecodeError):
                self.write_reply(503,{"ok":False,"error":"read_unavailable"})

        def do_POST(self):
            uri = urlsplit(self.path)
            if uri.path == "/api/notifier/enroll" and enrollment is not None:
                # No capability without an explicitly owner-approved claimant
                # proof; Chat ID alone is never sufficient.
                if (self.headers.get("Host")!=f"127.0.0.1:{WIN_PORT}" or
                    uri.scheme or uri.netloc or uri.query or uri.fragment or
                    self.headers.get("Origin") not in
                        (None,"https://chatgpt.com","https://chat.openai.com") or
                    self.headers.get("Transfer-Encoding") is not None or
                    self.headers.get("Content-Type","").lower()!="application/json"):
                    self.write_reply(403,{"ok":False,"error":"enrollment_origin_denied"})
                    return
                try:
                    n=int(self.headers.get("Content-Length",""))
                    if not 2<=n<=1024: raise ValueError("enrollment_size")
                    data=json.loads(self.rfile.read(n).decode("utf-8"))
                    if not isinstance(data,dict) or set(data) not in ({"chat","proof"}, {"chat","proof","title"}):
                        raise ValueError("enrollment_shape")
                    discovery = {**enrollment.discover(data["chat"], data["proof"], data.get("title")),
                                 "supports_tab_titles": True}
                    try:
                        session=resolve_chat(data["chat"])
                    except (ValueError, OSError, subprocess.SubprocessError, UnicodeError):
                        # Presence is local; an offline Repo must not hide a new tab.
                        self.write_reply(200, discovery)
                        return
                    if not session:
                        self.write_reply(200, discovery)
                        return
                    result=enrollment.announce(session["reporting_session_id"],
                                               data["chat"],data["proof"],valid_session, data.get("title"))
                    self.write_reply(200,{**result, "supports_tab_titles": True})
                except (ValueError,TypeError,KeyError,UnicodeError,
                        OSError,subprocess.SubprocessError,json.JSONDecodeError):
                    self.write_reply(403,{"ok":False,"error":"enrollment_refused"})
                return
            if uri.path == "/api/dispatch/modules" and dispatch_board is not None:
                if (self.headers.get("Host") != f"127.0.0.1:{WIN_PORT}" or
                        uri.scheme or uri.netloc or uri.query or uri.fragment or
                        self.headers.get("Origin") not in
                            (None,"https://chatgpt.com","https://chat.openai.com") or
                        self.headers.get("Transfer-Encoding") is not None or
                        self.headers.get("Content-Type","").lower() != "application/json"):
                    self.write_reply(403,{"ok":False,"error":"module_origin_denied"})
                    return
                try:
                    n=int(self.headers.get("Content-Length",""))
                    if not 2<=n<=512*1024: raise ValueError("module_size")
                    data=json.loads(self.rfile.read(n).decode("utf-8"))
                    if not isinstance(data,dict) or set(data) not in ({"session","chat","modules","default_module_ids"},
                                     {"session","chat","modules","default_module_ids",
                                      "profiles","active_profile_id"}):
                        raise ValueError("module_fields")
                    result=dispatch_board.update_modules(
                        data["session"],data["chat"],
                        self.headers.get("X-Fortis-Dispatch-Key",""),
                        data["modules"],data["default_module_ids"],
                        data.get("profiles"),data.get("active_profile_id"))
                    self.write_reply(200,result)
                except (ValueError,TypeError,PermissionError,UnicodeError,
                        OSError,json.JSONDecodeError):
                    self.write_reply(403,{"ok":False,"error":"module_sync_refused"})
                return
            if uri.path == "/api/dispatch/ack" and dispatch_board is not None:
                if (self.headers.get("Host") != f"127.0.0.1:{WIN_PORT}" or
                        uri.scheme or uri.netloc or uri.query or uri.fragment or
                        self.headers.get("Origin") not in
                           (None, "https://chatgpt.com", "https://chat.openai.com") or
                        self.headers.get("Transfer-Encoding") is not None or
                        self.headers.get("Content-Type", "").lower() != "application/json"):
                    self.write_reply(403, {"ok": False, "error": "dispatch_ack_denied"})
                    return
                try:
                    length=int(self.headers.get("Content-Length", ""))
                    if not 2 <= length <= 2048:
                        raise ValueError("bad_length")
                    data=json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(data, dict) or set(data) not in ({
                            "session", "chat", "dispatch_id", "status", "task_id"},
                            {"session", "chat", "dispatch_id", "status", "task_id", "reason"},
                            {"session", "chat", "dispatch_id", "status", "task_id", "detail"},
                            {"session", "chat", "dispatch_id", "status", "task_id", "reason", "detail"}):
                        raise ValueError("invalid_ack_body")
                    result=dispatch_board.ack(
                        data["session"], data["chat"],
                        self.headers.get("X-Fortis-Dispatch-Key", ""),
                        data["dispatch_id"], data["status"], data["task_id"],
                        data.get("reason"), data.get("detail"))
                    self.write_reply(200,result)
                except (ValueError, TypeError, PermissionError, UnicodeError,
                        json.JSONDecodeError):
                    self.write_reply(403, {"ok": False, "error": "ack_refused"})
                return
            if uri.path in ("/api/task-intents", "/api/task-send-state") and notifier_forward:
                if (self.headers.get("Host") != f"127.0.0.1:{WIN_PORT}" or
                        uri.scheme or uri.netloc or uri.query or uri.fragment or
                        self.headers.get("Origin") not in
                            (None, "https://chatgpt.com", "https://chat.openai.com") or
                        self.headers.get("Transfer-Encoding") is not None or
                        len(self.headers.get_all("Content-Length", [])) != 1 or
                        len(self.headers.get_all("Content-Type", [])) != 1 or
                        self.headers.get_content_type() != "application/json" or
                        len(self.headers.get_all("X-Fortis-Task-Intent-Key", [])) != 1):
                    self.write_reply(403, {"ok": False, "error": "metadata_origin_denied"})
                    return
                try:
                    from owner_notifier_bridge import validate_task_metadata
                    length = int(self.headers.get("Content-Length", ""))
                    if not 2 <= length <= 1024:
                        raise ValueError("metadata_size")
                    # Local duplicate-field guard avoids importing Repo Store on Windows.
                    def unique(pairs):
                        result = {}
                        for name, value in pairs:
                            if name in result:
                                raise ValueError("duplicate_metadata_field")
                            result[name] = value
                        return result
                    body = json.loads(self.rfile.read(length).decode("utf-8"), object_pairs_hook=unique)
                    validate_task_metadata(uri.path, body)
                    code, result = notifier_forward("POST", uri.path,
                        self.headers.get("X-Fortis-Task-Intent-Key", ""), body)
                    self.write_reply(code, result)
                except (ValueError, TypeError, UnicodeError, OSError, subprocess.SubprocessError):
                    self.write_reply(403, {"ok": False, "error": "metadata_refused"})
                return
            if uri.path == "/api/user-messages" and notifier_forward:
                if (self.headers.get("Host") != f"127.0.0.1:{WIN_PORT}" or
                    uri.scheme or uri.netloc or uri.query or uri.fragment or
                    self.headers.get("Origin") not in
                       (None,"https://chatgpt.com","https://chat.openai.com") or
                    self.headers.get("Transfer-Encoding") is not None):
                    self.write_reply(403,{"ok":False,"error":"notifier_origin_denied"})
                    return
                if self.headers.get("Content-Type","").lower() != "application/json":
                    self.write_reply(415,{"ok":False,"error":"json_only"})
                    return
                try:
                    length=int(self.headers.get("Content-Length",""))
                    if not 2 <= length <= MAX_ORIGINAL_BODY:
                        raise ValueError("bad_length")
                    body=json.loads(self.rfile.read(length).decode("utf-8"))
                    code,response=notifier_forward("POST","/api/user-messages",
                         self.headers.get("X-Fortis-Message-Writer-Key",""),body)
                    self.write_reply(code,response)
                except (ValueError, TypeError, UnicodeError, subprocess.SubprocessError,
                        OSError, json.JSONDecodeError):
                    self.write_reply(403,{"ok":False,"error":"notifier_post_refused"})
                return
            # Explicit same-origin requirement for every state-changing request.
            if (self.headers.get("Host") != f"127.0.0.1:{WIN_PORT}" or
                    self.headers.get("Origin") != f"http://127.0.0.1:{WIN_PORT}" or
                    self.headers.get("Sec-Fetch-Site", "same-origin") != "same-origin"):
                self.write_reply(403, {"ok": False, "error": "origin_refused"})
                return
            if not secrets.compare_digest(
                    self.headers.get("Authorization", ""), "Bearer " + token):
                self.write_reply(401, {"ok": False, "error": "viewer_key_required"})
                return
            if uri.path == "/api/session-visibility" and session_archive is not None:
                if (uri.query or uri.fragment or uri.scheme or uri.netloc or
                    self.headers.get("Content-Type","").lower() != "application/json" or
                    self.headers.get("Transfer-Encoding") is not None):
                    self.write_reply(403,{"ok":False,"error":"visibility_denied"})
                    return
                try:
                    size=int(self.headers.get("Content-Length",""))
                    if not 2<=size<=256:raise ValueError("visibility_size")
                    obj=json.loads(self.rfile.read(size).decode("utf-8"))
                    if (not isinstance(obj,dict) or set(obj)!={"action","session","chat"} or
                        obj["action"] not in ("archive","restore","disconnect") or
                        not SID.fullmatch(obj["session"] or "") or
                        not isinstance(obj["chat"],str)):
                        raise ValueError("invalid_visibility_request")
                    sid=obj["session"];chat=obj["chat"]
                    state=read_data("state",None,None)
                    match=[item for item in state.get("sessions",[]) if
                      item.get("reporting_session_id")==sid and item.get("conversation_id")==chat
                      and item.get("route")=="repo"]
                    if len(match)!=1:raise ValueError("unknown_session")
                    if obj["action"]=="archive":
                        result=session_archive.archive(sid,chat)
                        # Cancel pending dispatch immediately, even if revocation
                        # of the persisted Notifier grant subsequently fails.
                        if dispatch_board is not None:dispatch_board.revoke(sid)
                        if enrollment is not None:enrollment.revoke(sid)
                    elif obj["action"]=="restore":
                        result=session_archive.restore(sid,chat)
                    else:
                        if session_archive.has(sid):raise ValueError("archived_not_disconnected")
                        if enrollment is not None:enrollment.revoke(sid)
                        if dispatch_board is not None:dispatch_board.revoke(sid)
                        result={"ok":True,"disconnected":True,"session":sid}
                    self.write_reply(200,result)
                except (ValueError, TypeError, KeyError, UnicodeError, OSError, json.JSONDecodeError):
                    self.write_reply(403,{"ok":False,"error":"visibility_refused"})
                return
            if uri.path == "/api/notifier/connect" and enrollment is not None and register_data:
                if (uri.query or uri.fragment or uri.scheme or uri.netloc or
                        self.headers.get("Content-Type", "").lower() != "application/json" or
                        self.headers.get("Transfer-Encoding") is not None):
                    self.write_reply(403, {"ok": False, "error": "connect_denied"})
                    return
                try:
                    n = int(self.headers.get("Content-Length", ""))
                    if not 2 <= n <= 512:
                        raise ValueError("connect_size")
                    body = json.loads(self.rfile.read(n).decode("utf-8"))
                    if not isinstance(body, dict) or set(body) != {"chat", "fingerprint"}:
                        raise ValueError("connect_fields")
                    with registration_lock:
                        result = enrollment.connect_discovered(body["chat"], body["fingerprint"],
                                                               register_data, valid_session)
                    self.write_reply(201 if result["created"] else 200, result)
                except (ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError):
                    self.write_reply(403, {"ok": False, "error": "discovery_selection_refused"})
                except (OSError, subprocess.SubprocessError):
                    self.write_reply(503, {"ok": False, "error": "connect_unavailable"})
                return
            if uri.path in ("/api/notifier/approve","/api/notifier/revoke", "/api/notifier/task-intents") and enrollment is not None:
                if (uri.query or uri.fragment or uri.scheme or uri.netloc or
                    self.headers.get("Content-Type","").lower()!="application/json" or
                    self.headers.get("Transfer-Encoding") is not None):
                    self.write_reply(403,{"ok":False,"error":"approval_denied"})
                    return
                try:
                    n=int(self.headers.get("Content-Length",""))
                    if not 2<=n<=512: raise ValueError("approval_size")
                    body=json.loads(self.rfile.read(n).decode("utf-8"))
                    if not isinstance(body,dict): raise ValueError("approval_body")
                    if uri.path=="/api/notifier/approve":
                        if set(body)!={"session","chat","fingerprint"}:
                            raise ValueError("approval_fields")
                        result=enrollment.approve(body["session"],body["chat"],
                                                  body["fingerprint"],valid_session)
                    elif uri.path == "/api/notifier/task-intents":
                        if set(body) != {"session", "chat"}:
                            raise ValueError("intent_grant_fields")
                        result = enrollment.enable_task_intents(body["session"], body["chat"], valid_session)
                    else:
                        if set(body)!={"session"}: raise ValueError("revocation_fields")
                        result=enrollment.revoke(body["session"])
                        if dispatch_board is not None:
                            dispatch_board.revoke(body["session"])
                    self.write_reply(200,result)
                except (ValueError,TypeError,OSError,json.JSONDecodeError,
                        subprocess.SubprocessError):
                    self.write_reply(403,{"ok":False,"error":"approval_refused"})
                return
            if uri.path == "/api/dispatch/revoke" and dispatch_board is not None:
                if (uri.query or uri.fragment or uri.scheme or uri.netloc or
                        self.headers.get("Content-Type", "").lower() != "application/json" or
                        self.headers.get("Transfer-Encoding") is not None):
                    self.write_reply(400, {"ok": False, "error": "invalid_revoke_request"})
                    return
                try:
                    length=int(self.headers.get("Content-Length", ""))
                    if not 2 <= length <= 128:
                        raise ValueError("bad_length")
                    data=json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(data, dict) or set(data) != {"session"}:
                        raise ValueError("bad_revoke")
                    result=dispatch_board.revoke(data["session"])
                    self.write_reply(200,result)
                except (ValueError, TypeError, UnicodeError, json.JSONDecodeError):
                    self.write_reply(400, {"ok": False, "error": "invalid_revoke"})
                return
            if uri.path == "/api/dispatch" and dispatch_board is not None:
                if (uri.query or uri.fragment or uri.scheme or uri.netloc or
                        self.headers.get("Content-Type", "").lower() != "application/json" or
                        self.headers.get("Transfer-Encoding") is not None):
                    self.write_reply(400, {"ok": False, "error": "invalid_dispatch_request"})
                    return
                try:
                    length=int(self.headers.get("Content-Length", ""))
                    if not 2 <= length <= MAX_DISPATCH_BODY:
                        raise ValueError("bad_length")
                    data=json.loads(self.rfile.read(length).decode("utf-8"))
                    if (not isinstance(data,dict) or
                        set(data) not in ({"session","chat","mode","text"},
                                          {"session","chat","mode","text","module_ids"},
                                          {"session","chat","mode","text","module_ids",
                                           "profile_id"},
                                          {"session","chat","mode","text","module_ids",
                                           "profile_id","delay_ms"})):
                        raise ValueError("bad_dispatch_body")
                    current=read_data("state",None,None)
                    matches = [item for item in current.get("sessions", []) if
                        item.get("reporting_session_id")==data["session"] and
                        item.get("route")=="repo" and item.get("conversation_id")==data["chat"]]
                    if len(matches) != 1 or (session_archive is not None and
                        session_archive.has(data["session"],data["chat"])):
                        raise ValueError("unregistered_recipient")
                    result=dispatch_board.enqueue(data["session"],data["chat"],
                        data["mode"],data["text"],data.get("module_ids"),
                        data.get("profile_id"),data.get("delay_ms"))
                    self.write_reply(202,result)
                except (ValueError, TypeError, UnicodeError, json.JSONDecodeError):
                    self.write_reply(409, {"ok": False, "error": "dispatch_unavailable"})
                except (OSError, subprocess.SubprocessError):
                    self.write_reply(503, {"ok": False, "error": "state_unavailable"})
                return
            if (uri.path != "/api/register" or uri.query or uri.fragment or
                    uri.scheme or uri.netloc or not register_data):
                self.write_reply(404, {"ok": False, "error": "not_found"})
                return
            if (self.headers.get("Content-Type", "").lower() != "application/json" or
                    self.headers.get("Transfer-Encoding") is not None):
                self.write_reply(415, {"ok": False, "error": "json_only"})
                return
            try:
                n = int(self.headers.get("Content-Length", ""))
                if not 2 <= n <= MAX_REGISTER_BODY:
                    raise ValueError("invalid_content_length")
                data = json.loads(self.rfile.read(n).decode("utf-8"))
                if not isinstance(data, dict) or set(data) != {"url", "title"}:
                    raise ValueError("invalid_registration_fields")
                valid_registration(data["url"], data["title"])
            except (ValueError, UnicodeError, TypeError, KeyError, json.JSONDecodeError):
                self.write_reply(400, {"ok": False, "error": "invalid_registration"})
                return
            try:
                with registration_lock:
                    result = register_data(data["url"], data["title"])
                self.write_reply(201 if result["created"] else 200, result)
            except (ValueError, OSError, subprocess.SubprocessError,
                    UnicodeError, json.JSONDecodeError, KeyError):
                self.write_reply(503, {"ok": False, "error": "registration_unavailable"})

        def do_OPTIONS(self):
            self.write_reply(405,{"ok":False,"error":"no_cors"})

        def do_HEAD(self):
            self.write_reply(405,{"ok":False,"error":"read_only"})
    return Handler


def open_owner_edge(url, environ=os.environ, launch=subprocess.Popen):
    """Open a public LOCAL URL in Edge without any token or chat text in argv."""
    candidates = [shutil.which("msedge.exe")]
    for root in (environ.get("PROGRAMFILES(X86)"),
                 environ.get("PROGRAMFILES"), environ.get("LOCALAPPDATA")):
        if root:
            candidates.append(str(Path(root) / "Microsoft" / "Edge" /
                                  "Application" / "msedge.exe"))
    for path in candidates:
        if path and Path(path).is_file():
            launch([path, url], stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    return False


def assert_owner_only_launcher_dir(path, owner_sid, runner=subprocess.run,
                                   require_protected=True):
    """Fail closed if the Windows owner install may be read by another user."""
    if sys.platform != "win32":
        raise ValueError("windows_owner_only")
    if not path.exists() or path.is_symlink():
        raise ValueError("unsafe_launcher_path")
    ps = r"""
$ErrorActionPreference = 'Stop'
$p = $env:FORTIS_LAUNCH_ACL_PATH
$owner = $env:FORTIS_LAUNCH_OWNER_SID
$acl = Get-Acl -LiteralPath $p -ErrorAction Stop
if ($env:FORTIS_LAUNCH_REQUIRE_PROTECTED -eq '1' -and
    -not $acl.AreAccessRulesProtected) { throw 'Inherited ACL' }
foreach ($rule in $acl.Access) {
    if ($rule.AccessControlType -ne 'Allow') { continue }
    $sid = $rule.IdentityReference.Translate(
      [Security.Principal.SecurityIdentifier]).Value
    if ($sid -ne $owner -and $sid -ne 'S-1-5-18') {
        throw 'Foreign ACL principal'
    }
}
$item = Get-Item -LiteralPath $p -Force
if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Reparse point'
}
'PRIVATE_ACL_OK'
"""
    env = dict(os.environ)
    env["FORTIS_LAUNCH_ACL_PATH"] = str(path)
    env["FORTIS_LAUNCH_OWNER_SID"] = owner_sid
    env["FORTIS_LAUNCH_REQUIRE_PROTECTED"] = "1" if require_protected else "0"
    command = ["powershell.exe", "-NoProfile", "-NonInteractive",
               "-EncodedCommand",
               __import__("base64").b64encode(ps.encode("utf-16le")).decode("ascii")]
    result = runner(command, capture_output=True, timeout=12, check=False, env=env)
    if result.returncode or b"PRIVATE_ACL_OK" not in result.stdout:
        raise ValueError("private_launcher_acl_denied")


def write_owner_only_launcher(directory, token, owner_sid):
    """Temporary owner-private file: browser gets token, HTTP remains protected."""
    assert_owner_only_launcher_dir(directory, owner_sid)
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", token):
        raise ValueError("invalid_viewer_bearer")
    bootstrap = directory / ("viewer-private-launch-" + secrets.token_hex(12) + ".html")
    # Do not place token in the opened Edge URL, command-line args or HTTP query.
    page = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="referrer" content="no-referrer">
<title>Открыть Fortis Observatory</title>
</head><body><p id="status">Открываем Fortis Observatory…</p>
<button id="open" type="button">Открыть Observatory</button>
<script>
"use strict";
const destination = "http://127.0.0.1:18755/";
const code = __TOKEN__;
let child = null, timer = null, count = 0;
function openViewer() {
 if(child && !child.closed){child.focus();return}
 child = window.open(destination, "_blank");
 if(!child){document.getElementById("status").textContent =
   "Edge заблокировал окно. Нажмите кнопку «Открыть Observatory».";return}
 count=0;clearInterval(timer);
 timer=setInterval(()=>{
   if(!child||child.closed||++count>120){clearInterval(timer);return}
   try{child.postMessage({type:"fortis-observatory-owner-unlock-v1",code},
                         destination.slice(0,-1))}catch(_){}
 },200);
}
window.addEventListener("message",e=>{
 if(e.source!==child||e.origin!==destination.slice(0,-1)||
   !e.data||e.data.type!=="fortis-observatory-unlocked-v1")return;
 clearInterval(timer);
 document.getElementById("status").textContent="Observatory открыт. Эту вкладку можно закрыть.";
});
document.getElementById("open").addEventListener("click",openViewer);
openViewer();
</script></body></html>""".replace("__TOKEN__", json.dumps(token))
    with bootstrap.open("x", encoding="utf-8", newline=None) as out:
        out.write(page)
    try:
        assert_owner_only_launcher_dir(directory, owner_sid)
        # The newly created file must inherit the verified private DACL.
        assert_owner_only_launcher_file(bootstrap, owner_sid)
    except BaseException:
        bootstrap.unlink(missing_ok=True)
        raise
    return bootstrap


def assert_owner_only_launcher_file(path, owner_sid):
    # Apply the same ACL and reparse checks to this created file.
    # Directory check alone is insufficient if the file has a foreign ACE.
    if not path.is_file() or path.is_symlink():
        raise ValueError("unsafe_launcher_file")
    # Reuse directory checker: its ACL logic applies identically to files.
    assert_owner_only_launcher_dir(path, owner_sid, require_protected=False)


def main():
    parser=argparse.ArgumentParser(description="Owner-local manual Observatory viewer")
    parser.add_argument("--container",help="optional exact container; defaults to protected approved-owner.json")
    parser.add_argument("--no-browser",action="store_true")
    parser.add_argument("--auth-mode",choices=("owner-launch","manual"),
                        default="owner-launch",
                        help="owner-launch: no code typing, protected file:// launch; manual: old code form")
    args=parser.parse_args()
    if args.no_browser and args.auth_mode == "owner-launch":
        parser.error("--no-browser requires --auth-mode manual")
    try:
        obj=read_owner_config()
        target=args.container or obj["container"]
        if obj["container"]!=target:
            raise ValueError("unapproved_container")
        docker_cli=shutil.which("docker.exe")
        if not docker_cli:
            raise ValueError("docker_cli_not_found")
        state=ensure_repo_running(target,docker_cli)
        secret=secrets.token_urlsafe(32)
        nonce=secrets.token_urlsafe(16)
        dispatch_board=DispatchBoard()
        # Owner-only directory was ACL-verified by read_owner_config().
        owner_directory=(Path(os.environ["LOCALAPPDATA"]) /
                         "FortisObservatoryV1" / "Viewer")
        def approved_pair(sid):
            pair=owner_pair(target,sid,docker_cli=docker_cli,
                task_intents=enrollment.approved.get(sid,{}).get("task_intents",False))
            return {**pair,"dispatch_key":dispatch_board.pair(sid,pair["conversation_id"])}
        enrollment=Enrollment(owner_directory,approved_pair)
        session_archive=OwnerSessionArchive(owner_directory)
        server=ThreadingHTTPServer(("127.0.0.1",WIN_PORT),
             handler_for(secret,lambda kind,sid,task:repo_read(
                 target,kind,sid,task,docker_cli),nonce,
                 lambda url,title:repo_register(target,url,title,docker_cli),
                 lambda sid:owner_pair(target,sid,docker_cli=docker_cli),
                 lambda method,path,key,body:scoped_request(
                     target,method,path,key,body,docker_cli=docker_cli),
                 dispatch_board,enrollment,session_archive))
    except (OSError, ValueError, TypeError, KeyError,
            subprocess.SubprocessError, json.JSONDecodeError) as ex:
        print("NOT_STARTED: "+type(ex).__name__+" (check approved config, container and Windows ACL)")
        return 1
    print("REPO_OBSERVATORY="+state,flush=True)
    print(f"EDGE_URL=http://127.0.0.1:{WIN_PORT}/",flush=True)
    private_launcher=None
    if args.auth_mode=="manual":
        print("PRIVATE_VIEWER_CODE="+secret,flush=True)
        print("Paste code into Edge ONLY; never copy into ChatGPT, files or logs.",flush=True)
    elif not args.no_browser:
        try:
            private_launcher=write_owner_only_launcher(
                owner_directory, secret, obj["owner_sid"])
        except (OSError, ValueError, subprocess.SubprocessError):
            print("AUTO_LOGIN_NOT_STARTED: owner-only launcher ACL failed",flush=True)
            server.server_close()
            return 1
        print("OWNER_PRIVATE_AUTO_LOGIN=prepared",flush=True)
        print("OWNER_PRIVATE_LAUNCHER="+str(private_launcher),flush=True)
    if not args.no_browser:
        viewer_url=(private_launcher.as_uri() if private_launcher else
                    f"http://127.0.0.1:{WIN_PORT}/")
        if not open_owner_edge(viewer_url):
            print("EDGE_NOT_FOUND: open the approved local viewer manually.",flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if private_launcher is not None:
            private_launcher.unlink(missing_ok=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
