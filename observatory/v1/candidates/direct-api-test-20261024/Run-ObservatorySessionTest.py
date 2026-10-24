"""One owner-local test: connect the exact chat 'Тест связи' and request one Send.
Uses the running Viewer's protected launcher locally; never prints its token.
No service restart, permission changes, persistent bridge, or automatic resend.
"""
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

BASE = "http://127.0.0.1:18755"
TARGET = "Тест связи"
MESSAGE = "Тест"
SID = re.compile(r"rs_[0-9a-f]{32}\Z")
CHAT = re.compile(r"[A-Za-z0-9-]{8,100}\Z")
DID = re.compile(r"dispatch_[0-9a-f]{32}\Z")
FP = re.compile(r"[0-9a-f]{12}\Z")


class StopTest(Exception):
    pass


class ApiError(Exception):
    def __init__(self, code):
        self.code = code


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Api:
    def __init__(self, token):
        self.token = token
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def __call__(self, method, path, body=None):
        headers = {"Authorization": "Bearer " + self.token, "Origin": BASE}
        payload = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = Request(BASE + path, data=payload, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=5) as response:
                result = json.loads(response.read(12 * 1024 * 1024).decode("utf-8"))
        except HTTPError as exc:
            raise ApiError(exc.code) from None
        except (URLError, TimeoutError, OSError):
            raise ApiError("connection") from None
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise StopTest("API вернул неподтверждённый результат.")
        return result


def authenticate():
    if sys.platform != "win32":
        raise StopTest("Запустите скрипт в обычном Windows PowerShell владельца.")
    directory = Path(os.environ["LOCALAPPDATA"]) / "FortisObservatoryV1" / "Viewer"
    if not (directory / "owner_viewer.py").is_file():
        raise StopTest("Установленный Windows Viewer не найден.")
    sys.path.insert(0, str(directory))
    owner = importlib.import_module("owner_viewer")
    config = owner.read_owner_config()
    owner.assert_owner_only_launcher_dir(directory, config["owner_sid"])
    validate = lambda path: owner.assert_owner_only_launcher_file(path, config["owner_sid"])
    launchers = sorted(directory.glob("viewer-private-launch-*.html"),
                       key=lambda path: path.stat().st_mtime, reverse=True)[:16]
    for path in launchers:
        validate(path)
        raw = path.read_text(encoding="utf-8")
        match = re.search(r'^const code = ("[A-Za-z0-9_-]{32,128}");\s*$', raw, re.M)
        if not match:
            continue
        api = Api(json.loads(match.group(1)))
        try:
            api("GET", "/api/state")
        except ApiError as exc:
            if exc.code == 401:
                continue
            raise
        return api, directory, validate
    raise StopTest("Локальная авторизация не найдена. Viewer должен быть запущен с авто-входом.")


def normal(value):
    return " ".join(str(value or "").split()).casefold()


def select_target(state, discovery, archived):
    sessions = state.get("sessions", [])
    titles = discovery.get("session_titles", {})
    rows = discovery.get("chats", [])
    matches = {}
    for session in sessions:
        sid = session.get("reporting_session_id", "")
        title = titles.get(sid) or session.get("title")
        if normal(title) == normal(TARGET):
            matches.setdefault(session.get("conversation_id"), []).append(session)
    for row in rows:
        if normal(row.get("title")) == normal(TARGET):
            matches.setdefault(row.get("chat"), [])
    if len(matches) != 1:
        raise StopTest("Точное название «Тест связи» не найдено либо неоднозначно. Отправки не было.")
    chat, registered = next(iter(matches.items()))
    if not isinstance(chat, str) or not CHAT.fullmatch(chat) or len(registered) > 1:
        raise StopTest("Адресат неоднозначен. Отправки не было.")
    sid = registered[0].get("reporting_session_id") if registered else None
    if sid is not None and not SID.fullmatch(sid):
        raise StopTest("Неверный ID сессии.")
    if chat in archived.values() or (sid and sid in archived):
        raise StopTest("Сессия архивирована. Автоматическое восстановление не выполняется.")
    discovered = [row for row in rows if row.get("chat") == chat]
    if len(discovered) > 1:
        raise StopTest("Несколько записей обнаружения для одного чата.")
    row = discovered[0] if discovered else None
    return chat, sid, row


def save_journal(path, record, create=False):
    with path.open("x" if create else "w", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())


def observe(api, sid, record, path, validate, sleep):
    command_id = record.get("dispatch_id")
    if not isinstance(command_id, str) or not DID.fullmatch(command_id):
        raise StopTest("Предыдущая попытка могла начаться; её dispatch_id неизвестен. Повтор заблокирован.")
    last_status = None
    for _ in range(70):
        snapshot = api("GET", "/api/dispatch/status?session=" + quote(sid))
        command = snapshot.get("dispatch")
        if not command or command.get("dispatch_id") != command_id:
            raise StopTest("Результат именно этой команды недоступен. Повтор заблокирован.")
        status = command.get("status")
        if status != last_status:
            print("STATUS=" + str(status), flush=True)
            last_status = status
        if status not in ("pending", "claimed"):
            record["status"] = status
            record["task_id"] = command.get("task_id")
            validate(path)
            save_journal(path, record)
            if status == "send_initiated":
                print("SEND_ATTEMPT_REPORTED=True")
                print("DELIVERY_CONFIRMED=False")
                print("TASK_ID=" + str(command.get("task_id") or "unknown"))
                return 0
            raise StopTest("Успешная попытка Send не подтверждена. Повтор заблокирован.")
        sleep(1)
    raise StopTest("Время ожидания истекло. Повтор заблокирован; проверьте чат и Observatory.")


def run(api, directory, validate, sleep=time.sleep):
    state = api("GET", "/api/state")
    discovery = api("GET", "/api/notifier/discovered")
    archived = api("GET", "/api/session-visibility").get("archived", {})
    chat, sid, row = select_target(state, discovery, archived)
    stamp = hashlib.sha256((chat + "\0" + MESSAGE).encode("utf-8")).hexdigest()[:24]
    path = directory / ("direct-api-test-" + stamp + ".json")
    if path.exists() or path.is_symlink():
        validate(path)
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("chat") != chat or not SID.fullmatch(record.get("session", "")):
            raise StopTest("Журнал предыдущей попытки не прошёл проверку. Повтор заблокирован.")
        print("PREVIOUS_ATTEMPT_FOUND=True")
        return observe(api, record["session"], record, path, validate, sleep)
    print("TARGET=" + TARGET)
    print("CHAT_ID=" + chat)
    if row and not row.get("blocked"):
        fingerprints = row.get("fingerprints", [])
        if len(fingerprints) != 1 or not FP.fullmatch(str(fingerprints[0])):
            raise StopTest("Обнаружено несколько клиентов чата. Отправки не было.")
        result = api("POST", "/api/notifier/connect",
                     {"chat": chat, "fingerprint": fingerprints[0]})
        if (result.get("approved") is not True or result.get("conversation_id") != chat
                or not SID.fullmatch(result.get("session", ""))):
            raise StopTest("Подключение не подтверждено. Отправки не было.")
        sid = result["session"]
        print("SESSION_CONNECTED=True")
    if sid is None:
        raise StopTest("Нет подключённой сессии для выбранного чата.")
    snapshot = None
    for attempt in range(16):
        snapshot = api("GET", "/api/dispatch/status?session=" + quote(sid))
        if snapshot.get("available") is True:
            break
        if attempt == 15:
            raise StopTest("Notifier не подтвердил доступность за 30 секунд. Отправки не было.")
        sleep(2)
    previous = snapshot.get("dispatch") or {}
    if previous.get("status") in ("pending", "claimed", "unconfirmed"):
        raise StopTest("Есть незавершённая или неподтверждённая команда. Новая отправка не выполняется.")
    # Recheck recipient title and archive state immediately before sending.
    fresh = api("GET", "/api/notifier/discovered")
    latest = api("GET", "/api/state")
    archives = api("GET", "/api/session-visibility").get("archived", {})
    checked_chat, checked_sid, _ = select_target(latest, fresh, archives)
    if checked_chat != chat or checked_sid != sid:
        raise StopTest("Адресат изменился. Отправки не было.")
    record = {"chat": chat, "session": sid, "status": "request_may_start",
              "message_sha256": hashlib.sha256(MESSAGE.encode("utf-8")).hexdigest()}
    # Durable guard BEFORE POST. It also covers a lost POST response.
    save_journal(path, record, create=True)
    validate(path)
    answer = api("POST", "/api/dispatch",
                 {"session": sid, "chat": chat, "mode": "send", "text": MESSAGE})
    command_id = answer.get("dispatch_id")
    if not isinstance(command_id, str) or not DID.fullmatch(command_id):
        raise StopTest("Ответ отправки не прошёл проверку. Повтор заблокирован.")
    record["dispatch_id"] = command_id
    record["status"] = "pending"
    save_journal(path, record)
    print("DISPATCH_ID=" + command_id)
    return observe(api, sid, record, path, validate, sleep)


def print_candidates(state, discovery, archived):
    sessions = state.get("sessions", [])
    rows = discovery.get("chats", [])
    titles = discovery.get("session_titles", {})
    print("REGISTERED_COUNT=" + str(len(sessions)))
    print("DISCOVERED_COUNT=" + str(len(rows)))
    for session in sessions:
        sid = session.get("reporting_session_id", "")
        chat = session.get("conversation_id", "")
        title = titles.get(sid) or session.get("title") or ""
        print("REGISTERED " + json.dumps({
            "title_repr": repr(str(title)[:160]),
            "chat": chat if isinstance(chat, str) and CHAT.fullmatch(chat) else "<invalid>",
            "session": sid if isinstance(sid, str) and SID.fullmatch(sid) else "<invalid>",
            "archived": sid in archived or chat in archived.values()
        }, ensure_ascii=False))
    for row in rows:
        chat = row.get("chat", "")
        print("DISCOVERED " + json.dumps({
            "title_repr": repr(str(row.get("title") or "")[:160]),
            "chat": chat if isinstance(chat, str) and CHAT.fullmatch(chat) else "<invalid>",
            "clients": len(row.get("fingerprints", [])),
            "blocked": row.get("blocked"),
            "last_seen_seconds_ago": row.get("last_seen_seconds_ago")
        }, ensure_ascii=False))


def check_only(api):
    snapshots = {}
    for label, path in (("STATE", "/api/state"),
                        ("DISCOVERY", "/api/notifier/discovered"),
                        ("ARCHIVE", "/api/session-visibility")):
        started = time.perf_counter()
        snapshots[label] = api("GET", path)
        print(label + "_MS=" + str(round((time.perf_counter() - started) * 1000)))
    print_candidates(snapshots["STATE"], snapshots["DISCOVERY"],
                     snapshots["ARCHIVE"].get("archived", {}))
    chat, sid, row = select_target(snapshots["STATE"], snapshots["DISCOVERY"],
                                   snapshots["ARCHIVE"].get("archived", {}))
    print("TARGET=" + TARGET)
    print("CHAT_ID=" + chat)
    print("SESSION_REGISTERED=" + str(sid is not None))
    print("DISCOVERED_CLIENTS=" + str(len(row.get("fingerprints", [])) if row else 0))
    if sid is not None:
        snapshot = api("GET", "/api/dispatch/status?session=" + quote(sid))
        print("NOTIFIER_AVAILABLE=" + str(snapshot.get("available") is True))
        print("NOTIFIER_PAIRED=" + str(snapshot.get("paired") is True))
    print("READ_ONLY_CHECK_OK=True")
    print("NO_CONNECT_OR_SEND_REQUESTED=True")
    return 0


def main():
    try:
        if sys.argv[1:] not in ([], ["--check"]):
            raise StopTest("Допустим только флаг --check или запуск без аргументов.")
        api, directory, validate = authenticate()
        if sys.argv[1:] == ["--check"]:
            return check_only(api)
        return run(api, directory, validate)
    except ApiError as exc:
        print("STOP: API " + str(exc.code) + ". Автоматического повтора нет.")
    except StopTest as exc:
        print("STOP: " + str(exc))
    except Exception as exc:
        # Never echo arbitrary exceptions, HTTP bodies, headers or a bearer.
        print("STOP: локальная проверка не пройдена (" + type(exc).__name__ + ").")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
