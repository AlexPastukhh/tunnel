"""Fortis Observatory: owner Windows or unified Repo Docker local HTTP API.

Owner-specific and Repo deployments have different trust boundaries.
The metadata event inbox never carries full conversation bodies.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os
from pathlib import Path
import secrets
import shlex
import sys
import threading
from urllib.parse import parse_qs, urlsplit

from store import Store, ID_RE, _dir
from task_intents import TaskIntents, strict_object, session_overview

HERE = Path(__file__).resolve().parent
MAX_POST = 1024
MAX_MESSAGE_POST = 4 * 1024 * 1024
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
          "/index.html": ("index.html", "text/html; charset=utf-8"),
          "/client.js": ("client.js", "application/javascript; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8")}


def repo_bootstrap():
    """Stable, ID-free one-time startup instruction. No session memory needed."""
    return "\n".join([
                    "Fortis Observatory — BOOTSTRAP (Repo, без ID).",
                    "Это правила работы, а не параметры конкретной беседы.",
                    "НЕ переноси task_id, reporting_session_id, Chat ID и sequence из предыдущих сообщений.",
                    "Для каждого запроса используй только новый [Fortis task context] от поведенческого модуля Notifier.",
                    "В текущем контексте нужны task_id и conversation_id; reporting_session_id может отсутствовать до pairing.",
                    "Основной инструмент AI: Fortis Repo. НЕ G2, Windows owner HOST или browser relay.",
                    "События вызывай реально через Fortis Repo, например:",
                    "python3 /workspace/repos/tunnel/observatory/v1/repo_task.py event --session <reporting_session_id> --chat-id <conversation_id> --task <task_id> --event progress --stage reviewing --summary 'Проверяю запрос'",
                    "В новом Repo runtime для содержательного шага можно передать подробное пояснение:",
                    "echo 'Проверено действие, найден результат, дальше проверю...' | python3 /workspace/repos/tunnel/observatory/v1/repo_task.py event --session <reporting_session_id> --chat-id <conversation_id> --task <task_id> --event progress --stage reviewing --summary 'Проверка выполнена' --detail-stdin",
                    "Длинное пояснение — только реальные действия/результаты, не скрытые мысли и не ключи.",
                    "Полные interim/final ответы AI передавай через Fortis Repo UTF-8 STDIN:",
                    "python3 /workspace/repos/tunnel/observatory/v1/repo_task.py message --session <reporting_session_id> --chat-id <conversation_id> --task <task_id> --kind final",
                    "Без reporting_session_id опусти --session: запись останется в локальной очереди до однозначной регистрации этого conversation_id.",
                    "Не создавай привязку сам. При нескольких сессиях одного чата очередь ждёт без выбора наугад.",
                    "Записывай события и КАЖДЫЙ полный interim/final даже при недоступности Observatory или Windows Viewer.",
                    "Не проверяй HTTP, pairing и receipt перед записью; локальный sender не зависит от работающего Observatory.",
                    "Отсутствие связи не означает failed и не отменяет выполнение запроса.",
                    "После нового запроса сначала user_message, при существенной работе содержательные progress/checkpoint;",
                    "assistant_message и completed/failed — только по реальному состоянию. Не имитируй работу пустыми событиями.",
                    "Для user_message и assistant_message нужны стандартные безопасные summary; не цитируй текст чата в metadata.",
                    "Полные AI сообщения и metadata пишутся в разные каталоги одного Repo Docker volume.",
                    "Точный оригинал пользователя передаётся отдельно Notifier после принятого события, AI его не реконструирует.",
                    "STAGED_ONLY означает очередь, НЕ приём Observatory. Для заявления о приёме проверяй receipt/историю.",
                    "Идентификаторы из текущего сообщения не являются секретными observer/writer ключами.",
                    "Ключи привязки, owner bearer, тексты чата и приватные данные нельзя писать в summaries, команды или Git.",
                    "Если актуального корректного контекста или Repo нет, НЕ используй старые ID и НЕ выдумывай отправку.",
                    "Не задерживай полезный ответ ради телеметрии; действия отправителя не доказывают отображение в DOM."
                ])



class Application:
    def __init__(self, archive, inboxes, sender_inboxes=None, token=None,
                 allow_private_user_messages=True):
        self.store = Store(archive, inboxes)
        # Docker Repo is a lower-trust metadata workspace, NOT owner-private.
        self.allow_private_user_messages = bool(allow_private_user_messages)
        self.token = token or secrets.token_urlsafe(32)
        self.sender_inboxes = sender_inboxes or {}
        self.lock = threading.RLock()
        self.stop = threading.Event()

    def instructions(self, sid):
        with self.lock:
            s = self.store._session(sid)
            if s is None:
                raise ValueError("session_missing")
            route = s["route"]
            if route == "repo":
                # Owner/Repo Viewer always receives stable identity-free instructions.
                # Internal V1/V2 registration compatibility is NOT part of AI prompts.
                return repo_bootstrap()
            path = self.sender_inboxes.get(route)
            if not path:
                return ("Маршрут записи не настроен для отправителя. "
                        "События нельзя отправлять до отдельного разрешения каталога.")
            if route == "repo":
                start = ("python3 /workspace/repos/tunnel/observatory/v1/emit.py "
                         "--inbox " + shlex.quote(path))
            else:
                start = ("py -3 emit.py --inbox " + json.dumps(path))
            enrollment_id = s["task_id"]  # Legacy per-session task; V2 sender proof only.
            args = (" --session " + s["reporting_session_id"] +
                    " --task task_НОВЫЙ_ID --version 2 --session-task " + enrollment_id +
                    " --route " + route)
            current = next(
                (item for item in self.store.sessions() if item["reporting_session_id"] == sid),
                None,
            )
            next_sequence = max((e["sequence"] for e in current["events"]), default=-1) + 1 if current else 0
            quote = shlex.quote if route == "repo" else lambda value: json.dumps(value, ensure_ascii=False)
            def example(kind, stage, summary, sequence):
                return (start + args + " --sequence " + str(sequence) +
                        " --event " + kind + " --stage " + stage +
                        " --summary " + quote(summary))
            text = "\n".join([
                "Fortis Observatory V2 source — добровольная привязка событий к сообщению.",
                ("ОСНОВНОЙ ИНСТРУМЕНТ AI: Fortis Repo. Вызывай его реально для записи файлов,"
                 if getattr(self, "repo_messages", None) is not None
                 else "Используй только разрешённый инструмент для указанного маршрута."),
                ("НЕ вызывай Fortis G2, Windows owner HOST или browser relay для отправки"
                 if getattr(self, "repo_messages", None) is not None
                 else "Не обходи права указанного маршрута."),
                ("Отправка сообщения в обычном тексте ответа не равна вызову Repo tool."
                 if getattr(self, "repo_messages", None) is not None
                 else "Не утверждай факт записи, если инструмент не вызывался."),
                "Chat ID: " + s["conversation_id"],
                "Reporting session ID: " + s["reporting_session_id"],
                "Session enrollment ID: " + enrollment_id + " (в команде --session-task; НЕ ID сообщения).",
                "Маршрут: " + route + ". Это не журнал реальных вызовов инструментов.",
                "Если текст от Tab Notifier содержит [Fortis task context] с валидным task_id,",
                "используй именно его для ВСЕХ событий и сообщений этого запроса: не генерируй другой.",
                "Для КАЖДОГО НОВОГО сообщения пользователя создай отдельный task_id: task_ + 32 hex-символа UUID4,",
                "ТОЛЬКО если Notifier не предоставил ID в текущем сообщении.",
                "Генерация в разрешённом Repo: python3 -c 'import uuid; print(\"task_\" + uuid.uuid4().hex)'",
                "Сохрани созданный task_id для текущего сообщения: пользовательское сообщение,",
                "все его started/progress/checkpoint/blocked/completed/failed и маркер ответа",
                "отправляй ТОЛЬКО с этим task_id. Следующее сообщение пользователя — новый task_id.",
                "Даже при продолжении той же темы новый пользовательский запрос получает свой task_id.",
                "ПРИМЕЧАНИЕ: имя --session-task сохраняет старый session.task_id только ради совместимости",
                "и проверки действующего подключения. Его нельзя заменять на новый task_id.",
                "Слова task_НОВЫЙ_ID в примерах замени на ID из текущего Notifier-сообщения",
                "или на новый UUID4, если пользователь отправил сообщение без task_id.",
                "После понимания запроса по возможности перед длительной работой отправь первый",
                "содержательный сигнал с тем же ID (started либо progress и т. п.).",
                "Ориентир около 10–15 секунд мягкий, не срок: качество работы приоритетнее.",
                "Не отправляй пустой started ради таймера. Любое первое принятое событие",
                "или метаданный маркер сообщения считается sender-claimed активностью по ID.",
                "sequence отправителя — подсказка порядка в рамках reporting session, не ID шага.",
                "Ранее принятый архив предлагает номер: " + str(next_sequence) + ".",
                "Если Observatory выключен, этот номер может устареть: НЕ пытайся",
                "переспрашивать сервер перед каждым событием и НЕ задерживай работу.",
                "Локальный emit.py пишет файл независимо от Observatory (STAGED_ONLY).",
                "V2 приёмник сохранит отличающиеся event_id даже при совпавшем sequence:",
                "при конфликте присвоит свободный архивный sequence и сохранит sender_sequence.",
                "Входящие JSON имеют временной префикс для best-effort порядка накопления;",
                "это НЕ гарантированный порядок модельных действий при параллельных отправителях.",
                "События с временно неизвестной сессией остаются во входящей очереди;",
                "файлы с неправильным enrollment и нарушением схемы отклоняются.",
                "Лимит очереди 512 JSON файлов; при переполнении запись NOT_STAGED,",
                "не обещай неограниченное накопление. Не передавай в event inbox текст чата.",
                "Для каждого пользовательского сообщения при разрешённом инструменте отправь",
                "метаданный маркер user_message, затем значимые события работы во время выполнения.",
                "Перед финальным ответом можно отправить маркер assistant_message и завершение completed",
                "только когда это соответствует фактическому состоянию. Никакой маркер не доказывает",
                "что ChatGPT сохранил полный ответ, а completed — что браузер его полностью отобразил.",
                "Сообщения в этих маркерах НЕ передаются: V2 сохраняет только факт, роль и task_id.",
                ("В этом Docker Repo режиме ПОЛНЫЕ AI сообщения сохраняются отдельно"
                 if getattr(self, "repo_messages", None) is not None
                 else "Полный текст сообщений в данном режиме не архивируется."),
                ("в /workspace/repo/fortis-observatory-repo-v1/inbox/messages через Repo sender."
                 if getattr(self, "repo_messages", None) is not None
                 else "Не передавай полный текст в event inbox."),
                "Никогда не отправляй полный текст в metadata /inbox/repo.",
                "summary — безопасное краткое описание до 140 символов, не полный текст сообщения,",
                "не содержит секретов, путей, команд, URL или цитат из чата.",
                "РЕЖИМ ПОШАГОВОЙ ТЕЛЕМЕТРИИ: для существенной работы показывай реальные этапы",
                "пользователю и одновременно отправляй progress/checkpoint по соответствующим переходам.",
                "Обычно 2–6 содержательных промежуточных событий; для короткой работы не выдумывай шаги.",
                "События по ходу работы, не в конце пачкой. Телеметрия не должна тормозить ответ.",
                "Допустимые stage: planning, editing, testing, waiting_tool, reviewing, other.",
                "Пример маркера нового сообщения (новый task_id и актуальный sequence обязательны):",
                example("user_message", "other", "Получено сообщение пользователя", next_sequence),
                "Пример этапа работы (следующий sequence, тот же task_id):",
                example("progress", "reviewing", "Изучаю структуру проекта", next_sequence + 1),
                "Пример маркера ответа (не полный текст ответа):",
                example("assistant_message", "other", "Ответ ChatGPT заявлен отправителем", next_sequence + 2),
                "После него при фактическом завершении может идти completed с новым sequence.",
                "STAGED_ONLY — запись в очередь, а не receipt Observatory; при timeout сначала проверь эффект.",
                "При недоступном инструменте не обходи границы и всё равно отвечай пользователю.",
                "Read-only /api/observer-status по-прежнему показывает только последний шаг,",
                "а /api/task-activity возвращает первый принятый сигнал каждого task_id,",
                "включая маркеры сообщений, без текста. Сигнал не доказывает реальную работу.",
                "Для режима только Observatory отдельно привяжи чат в меню Tab Notifier,",
                "ключ привязки нельзя помещать в чат. Существующая Windows-установка V1",
                "не обновляется этой инструкцией автоматически."
            ])
            if getattr(self, "repo_messages", None) is not None:
                text += "\n" + "\n".join([
                    "DOCKER REPO FULL-MESSAGE PATH (этот экземпляр, не Windows owner):",
                    "Файлы событий и ПОЛНЫХ сообщений пишутся в РАЗНЫЕ папки",
                    "внутреннего Docker volume, доступного Fortis Repo tool.",
                    "ВЫЗЫВАЙ ТОЛЬКО Fortis Repo tool (команда в Linux-контейнере).",
                    "Для события вызывай указанный выше emit.py через Fortis Repo tool;",
                    "для полного сообщения AI вызывай sender из Fortis Repo tool:",
                    "Полные ответы AI (interim/final) передавай через UTF-8 STDIN:",
                    "python3 /workspace/repos/tunnel/observatory/v1/repo_message_sender.py",
                    "  --session " + s["reporting_session_id"] +
                    " --session-task " + enrollment_id +
                    " --task task_НОВЫЙ_ID --kind interim",
                    "Для final укажи --kind final. Не помещай текст в аргументы CLI,",
                    "summary событий, Repo metadata inbox, URL, логи или Git.",
                    "Sender выдаст message_id и STAGED_ONLY; это НЕ ACK импорта.",
                    "После реального вызова Repo tool при необходимости проверь import",
                    "командой repo_service.py status/history; не придумывай accepted.",
                    "Никакого отдельного Windows/G2/HTTP browser relay для AI не требуется.",
                    "Для повторной отправки сохрани тот же --message-id msg_32hex.",
                    "Контент доступен обладателям полномочий Repo. Не считать его",
                    "Windows-owner-private. Не выдавай модельные утверждения за DOM.",
                    "Точный оригинал пользователя НЕ нужно реконструировать AI:",
                    "он должен прийти отдельно из Notifier после accepted event.",
                    "Посмотреть связанную историю при авторизованном запросе:",
                    "python3 /workspace/repos/tunnel/observatory/v1/repo_service.py",
                    "  history --session " + s["reporting_session_id"] +
                    " --task task_НОВЫЙ_ID",
                ])
            return text



def handler_for(app):
    class Handler(BaseHTTPRequestHandler):
        server_version = "FortisObservatoryV1"
        sys_version = ""

        def log_message(self, fmt, *args):
            # No URLs, headers, tokens, incoming payloads, or chat text in logs.
            pass

        def _headers(self, code, body_len, kind):
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(body_len))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; "
                             "style-src 'self'; connect-src 'self'; base-uri 'none'; "
                             "form-action 'none'; frame-ancestors 'none'")
            self.end_headers()

        def _json(self, code, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._headers(code, len(body), "application/json; charset=utf-8")
            self.wfile.write(body)

        def _valid_host(self):
            host = (self.headers.get("Host") or "").casefold()
            port = self.server.server_port
            return host in (f"127.0.0.1:{port}", f"localhost:{port}")

        def _authorized(self):
            # Loopback and Host are not enough: Windows guest SIDs share localhost.
            host = (self.headers.get("Host") or "").casefold()
            port = self.server.server_port
            if not self._valid_host():
                return False
            if (self.headers.get("Sec-Fetch-Site") or "").casefold() == "cross-site":
                return False
            return hmac.compare_digest(self.headers.get("Authorization") or "", "Bearer " + app.token)

        def _api_guard(self):
            if self._authorized():
                return True
            self._json(401, {"ok": False, "error": "owner_authorization_required"})
            return False

        def _intent_body(self):
            # New metadata protocol: bounded JSON, no duplicate fields/framing.
            lengths = self.headers.get_all("Content-Length", [])
            if (len(lengths) != 1 or not lengths[0].isascii() or
                    not lengths[0].isdigit() or self.headers.get("Transfer-Encoding") or
                    len(self.headers.get_all("Content-Type", [])) != 1 or
                    self.headers.get_content_type() != "application/json"):
                raise ValueError("invalid_intent_framing")
            length = int(lengths[0])
            if not 0 < length <= MAX_POST:
                raise ValueError("intent_body_size")
            body = json.loads(self.rfile.read(length).decode("utf-8"),
                              object_pairs_hook=strict_object)
            if not isinstance(body, dict):
                raise ValueError("invalid_intent_body")
            return body

        def do_HEAD(self):
            # Never allow HEAD to bypass the API authorization check.
            if urlsplit(self.path).path.startswith("/api/") and not self._authorized():
                self._headers(401, 0, "text/plain")
            else:
                self._headers(405, 0, "text/plain")

        def do_GET(self):
            parsed = urlsplit(self.path)
            if parsed.path == "/api/observer-status":
                # This read-only route requires a distinct, per-session capability.
                # It never accepts or reveals the owner panel token.
                if not self._valid_host():
                    self._json(403, {"ok": False, "error": "host_refused"})
                    return
                sid = parse_qs(parsed.query).get("session", [""])[0]
                key = self.headers.get("X-Fortis-Observer-Key") or ""
                with app.lock:
                    try:
                        status = app.store.observer_status(sid, key)
                        # Same read-only session capability; no task bodies or keys.
                        try:
                            overview = session_overview(TaskIntents(app.store).snapshot(sid))
                        except (ValueError, OSError, UnicodeError, TypeError, KeyError):
                            overview = {"version": 2, "basis": "latest_task", "available": False,
                                        "reason": "task_status_unavailable"}
                        status = {**status, "task_overview": overview}
                    except (ValueError, OSError, PermissionError):
                        self._json(403, {"ok": False, "error": "observer_access_refused"})
                        return
                self._json(200, {"ok": True, **status})
                return
            if parsed.path == "/api/task-activity":
                # Paired browsers receive metadata for a single task only.
                # The per-session observer key is never accepted as owner bearer.
                if not self._valid_host():
                    self._json(403, {"ok": False, "error": "host_refused"})
                    return
                query = parse_qs(parsed.query)
                sid = query.get("session", [""])[0]
                task = query.get("task", [""])[0]
                key = self.headers.get("X-Fortis-Observer-Key") or ""
                with app.lock:
                    try:
                        status = app.store.task_activity(sid, key, task)
                    except (ValueError, OSError, PermissionError):
                        self._json(403, {"ok": False, "error": "observer_access_refused"})
                        return
                self._json(200, {"ok": True, **status})
                return
            if parsed.path.startswith("/api/"):
                if not self._api_guard():
                    return
                with app.lock:
                    if parsed.path == "/api/task-intents":
                        try:
                            query = parse_qs(parsed.query, strict_parsing=True,
                                             keep_blank_values=True)
                            if set(query) != {"session"} or len(query["session"]) != 1:
                                raise ValueError("invalid_intent_query")
                            result = TaskIntents(app.store).snapshot(query["session"][0])
                        except (ValueError, TypeError, UnicodeError):
                            self._json(409, {"ok": False, "error": "invalid_task_intents"})
                            return
                        except OSError:
                            self._json(503, {"ok": False, "error": "task_intents_unavailable"})
                            return
                        self._json(200, {"ok": True, **result})
                        return
                    if parsed.path == "/api/state":
                        state = {"ok": True, "sessions": app.store.sessions(),
                                 "ingest": dict(app.store.recent_ingest),
                                 "routes": sorted(app.store.inboxes)}
                        if getattr(app, "repo_messages", None) is not None:
                            state["messages_ingest"] = dict(app.repo_messages.last_import)
                        self._json(200, state)
                        return
                    if parsed.path == "/api/repo-history":
                        if getattr(app, "repo_messages", None) is None:
                            self._json(404, {"ok": False, "error": "not_found"})
                            return
                        q = parse_qs(parsed.query)
                        sid = q.get("session", [""])[0]
                        task = q.get("task", [""])[0]
                        try:
                            history = app.repo_messages.history(sid, task)
                        except (ValueError, OSError):
                            self._json(404, {"ok": False, "error": "history_unavailable"})
                            return
                        self._json(200, {"ok": True, **history})
                        return
                    if parsed.path == "/api/observer-pair":
                        sid = parse_qs(parsed.query).get("session", [""])[0]
                        try:
                            sess = app.store._session(sid)
                            if sess is None:
                                raise ValueError("session_missing")
                            key = app.store.observer_key(sid)
                        except (ValueError, OSError):
                            self._json(404, {"ok": False, "error": "session_missing"})
                            return
                        self._json(200, {"ok": True, "pairing": {
                            "version": 1, "origin": f"http://127.0.0.1:{self.server.server_port}",
                            "conversation_id": sess["conversation_id"],
                            "reporting_session_id": sid,
                            "observer_key": key,
                        }})
                        return
                    if parsed.path == "/api/message-writer-pair":
                        if not app.allow_private_user_messages:
                            self._json(403, {"ok": False, "error": "private_messages_disabled"})
                            return
                        # Explicit owner UI action; unlike observer-pair, this
                        # grants per-session conditional FULL TEXT write only.
                        sid = parse_qs(parsed.query).get("session", [""])[0]
                        try:
                            sess = app.store._session(sid)
                            if sess is None:
                                raise ValueError("session_missing")
                            observer_key = app.store.observer_key(sid)
                            writer_key = app.store.message_writer_key(sid)
                        except (ValueError, OSError):
                            self._json(404, {"ok": False, "error": "session_missing"})
                            return
                        self._json(200, {"ok": True, "pairing": {
                            "version": 1, "origin": f"http://127.0.0.1:{self.server.server_port}",
                            "conversation_id": sess["conversation_id"],
                            "reporting_session_id": sid,
                            "observer_key": observer_key,
                            "message_writer_key": writer_key,
                        }})
                        return
                    if parsed.path == "/api/instructions":
                        sid = parse_qs(parsed.query).get("session", [""])[0]
                        try:
                            txt = app.instructions(sid)
                        except (ValueError, OSError):
                            self._json(404, {"ok": False, "error": "session_missing"})
                            return
                        self._json(200, {"ok": True, "text": txt})
                        return
                self._json(404, {"ok": False, "error": "not_found"})
                return
            item = ASSETS.get(parsed.path)
            if item is None:
                self._json(404, {"ok": False, "error": "not_found"})
                return
            filename, media = item
            if (HERE / filename).is_symlink():
                self._json(404, {"ok": False, "error": "unavailable"})
                return
            body = (HERE / filename).read_bytes()
            self._headers(200, len(body), media)
            self.wfile.write(body)

        def do_POST(self):
            parsed = urlsplit(self.path)
            if parsed.path in ("/api/task-intents", "/api/task-send-state", "/api/task-intent-pair"):
                origin = self.headers.get("Origin")
                if (parsed.query or not self._valid_host() or
                        (self.headers.get("Sec-Fetch-Site") or "").casefold() == "cross-site" or
                        origin not in (None, f"http://127.0.0.1:{self.server.server_port}",
                                       f"http://localhost:{self.server.server_port}")):
                    self._json(403, {"ok": False, "error": "origin_refused"})
                    return
                pairing = parsed.path == "/api/task-intent-pair"
                if pairing and not self._api_guard():
                    return
                try:
                    body = self._intent_body()
                    with app.lock:
                        intents = TaskIntents(app.store)
                        if pairing:
                            if (set(body) != {"version", "reporting_session_id", "conversation_id"} or
                                    type(body["version"]) is not int or body["version"] != 1 or
                                    not isinstance(body["conversation_id"], str)):
                                raise ValueError("invalid_intent_pair")
                            key = intents.issue_key(body["reporting_session_id"],
                                                    body["conversation_id"])
                            result = {"ok": True, "pairing": {**body, "task_intent_key": key}}
                            code = 200
                        else:
                            keys = self.headers.get_all("X-Fortis-Task-Intent-Key", [])
                            if len(keys) != 1:
                                raise PermissionError("intent_capability_required")
                            receipt = (intents.send_state(body, keys[0]) if parsed.path == "/api/task-send-state"
                                       else intents.register(body, keys[0]))
                            result = {"ok": True, **receipt}
                            code = 201 if receipt["status"] == "created" else 200
                except PermissionError:
                    self._json(403, {"ok": False, "error": "intent_access_refused"})
                    return
                except (ValueError, TypeError, UnicodeError, KeyError, RecursionError):
                    self._json(409, {"ok": False, "error": "invalid_or_conflicting_task_intent"})
                    return
                except OSError:
                    self._json(503, {"ok": False, "error": "task_intents_unavailable"})
                    return
                self._json(code, result)
                return
            if parsed.path == "/api/user-messages":
                if not app.allow_private_user_messages:
                    self._json(403, {"ok": False, "error": "private_messages_disabled"})
                    return
                if not self._valid_host() or (self.headers.get("Sec-Fetch-Site") or "").casefold() == "cross-site":
                    self._json(403, {"ok": False, "error": "origin_refused"})
                    return
                origin = self.headers.get("Origin")
                if origin not in (None, f"http://127.0.0.1:{self.server.server_port}",
                                  f"http://localhost:{self.server.server_port}"):
                    self._json(403, {"ok": False, "error": "origin_refused"})
                    return
                try:
                    n = int(self.headers.get("Content-Length", "0"))
                    if n <= 0 or n > MAX_MESSAGE_POST:
                        raise ValueError("invalid_body_length")
                    body = json.loads(self.rfile.read(n).decode("utf-8"))
                    if not isinstance(body, dict) or set(body) != {
                            "reporting_session_id", "conversation_id", "task_id", "original_text"}:
                        raise ValueError("invalid_message_schema")
                    key = self.headers.get("X-Fortis-Message-Writer-Key") or ""
                    with app.lock:
                        receipt = app.store.write_user_message(
                            body["reporting_session_id"], key, body["task_id"],
                            body["conversation_id"], body["original_text"])
                except (PermissionError,):
                    self._json(403, {"ok": False, "error": "writer_access_refused"})
                    return
                except (ValueError, TypeError, UnicodeError, KeyError):
                    self._json(409, {"ok": False, "error": "invalid_or_conflicting_user_message"})
                    return
                except OSError:
                    self._json(503, {"ok": False, "error": "archive_unavailable"})
                    return
                self._json(201 if receipt["status"] == "created" else 200,
                           {"ok": True, **receipt})
                return
            if not parsed.path.startswith("/api/") or not self._api_guard():
                return
            origin = self.headers.get("Origin")
            if origin not in (None, f"http://127.0.0.1:{self.server.server_port}",
                              f"http://localhost:{self.server.server_port}"):
                self._json(403, {"ok": False, "error": "origin_refused"})
                return
            if parsed.path != "/api/sessions":
                self._json(404, {"ok": False, "error": "not_found"})
                return
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if n <= 0 or n > MAX_POST:
                    raise ValueError("body_size")
                data = json.loads(self.rfile.read(n))
                if not isinstance(data, dict) or set(data) != {"url", "route", "title"}:
                    raise ValueError("invalid_fields")
                with app.lock:
                    result = app.store.register(data["url"], data["route"], data["title"])
            except (ValueError, KeyError, TypeError, OSError):
                self._json(400, {"ok": False, "error": "invalid_registration"})
                return
            self._json(201, {"ok": True, "session": result})

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True, help="owner-private folder")
    parser.add_argument("--repo-inbox", type=Path, help="existing authorized owner-readable inbox")
    parser.add_argument("--g2-inbox", type=Path, help="ONLY if separately authorized")
    parser.add_argument("--repo-sender-inbox", help="approved repo-side location for copy instructions")
    parser.add_argument("--g2-sender-inbox", help="approved guest-side location for copy instructions")
    parser.add_argument("--port", type=int, default=18753)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise SystemExit("Invalid port")
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise SystemExit("An interactive local console is required")
    if args.repo_sender_inbox is not None:
        path = args.repo_sender_inbox
        if not path.startswith("/workspace/files/") or ".." in path.split("/"):
            raise SystemExit("Repo sender inbox must be an existing allowed Workfiles path")
    if sys.platform == "win32":
        import ctypes
        buf = ctypes.create_unicode_buffer(257)
        n = ctypes.c_uint32(257)
        if not ctypes.windll.advapi32.GetUserNameW(buf, ctypes.byref(n)) or buf.value.casefold() != "alexa":
            raise SystemExit("Owner Windows identity required")
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise SystemExit("Interactive owner console required")
        # Source from the writable Repo checkout must NOT run as the owner.
        source = HERE.resolve()
        unsafe = (Path.home() / "Repos", Path.home() / "Workfiles")
        if any(source.is_relative_to(x.resolve()) for x in unsafe):
            raise SystemExit("Copy independently reviewed/pinned source to owner-protected location first")
        archive = args.archive.resolve()
        if not archive.is_relative_to(Path.home().resolve()) or any(
            archive.is_relative_to(x.resolve()) for x in unsafe
        ):
            raise SystemExit("Owner archive must be inside protected owner home, outside Repo RW mounts")
        if args.repo_inbox is not None and not args.repo_inbox.resolve().is_relative_to(
            (Path.home() / "Workfiles").resolve()
        ):
            raise SystemExit("Repo inbox must remain inside already-mounted Workfiles")
    inboxes = {route: path for route, path in
               (("repo", args.repo_inbox), ("g2", args.g2_inbox)) if path is not None}
    app = Application(_dir(args.archive), inboxes,
                      {"repo": args.repo_sender_inbox, "g2": args.g2_sender_inbox})
    print("FORTIS OWNER V1 TOKEN (private console only; never paste into chat):")
    print(app.token, flush=True)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(app))
    print(f"Owner-only Observatory V1 preview: http://127.0.0.1:{args.port}/", flush=True)

    def poll_safely():
        with app.lock:
            try:
                app.store.poll()
            except Exception:
                # Keep the collector alive; report failure without exposing event payloads.
                app.store.recent_ingest = {
                    "state": "failed", "accepted": 0, "rejected": 0,
                    "duplicate": 0, "unknown_session": 0, "retryable": 0, "error": 1,
                }

    def sampler():
        while not app.stop.wait(3):
            poll_safely()

    poll_safely()
    thread = threading.Thread(target=sampler, daemon=True)
    thread.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app.stop.set()
        server.server_close()


if __name__ == "__main__":
    main()
