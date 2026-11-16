"""Offline integration: real narrow runtime, loopback fake plane, synthetic MCP.

No real profiles, keys, Docker, production tunnel or external endpoint are used.
Run with --runtime /absolute/path/tunnel-client-runtime [--expect-old-failure].
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import hashlib
import os
from pathlib import Path
import queue
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from urllib.error import HTTPError
from urllib.request import ProxyHandler, build_opener

TUNNEL_ID = 'tunnel_' + '0' * 32
LOOPBACK_HTTP = build_opener(ProxyHandler({}))
COMMAND_ARG = '--import=data:text/javascript;base64,Zm9ydGlzLWNvbW1hbmQtYXJnPQ=='


def stub(events, command_arg):
    def record(kind, **data):
        with open(events, 'a', encoding='utf-8') as f:
            f.write(json.dumps(dict(kind=kind, pid=os.getpid(), **data)) + '\n')

    record('start', command_arg_sha256=hashlib.sha256(command_arg.encode()).hexdigest())
    for line in sys.stdin:
        request = json.loads(line)
        method = request.get('method')
        if 'id' not in request:
            continue
        response = dict(jsonrpc='2.0', id=request['id'])
        if method == 'initialize':
            response['result'] = dict(
                protocolVersion=request['params']['protocolVersion'],
                capabilities={'tools': {}}, serverInfo={'name': 'fortis-test', 'version': '1'})
        elif method == 'tools/list':
            response['result'] = {'tools': [dict(
                name='counter', description='Synthetic test counter',
                inputSchema={'type': 'object', 'properties': {}})]}
        elif method == 'tools/call':
            marker = request['params']['arguments']['marker']
            record('call', marker=marker)
            if request['params']['name'] == 'test_child_exit':
                os._exit(0)
            response['result'] = {'content': [{'type': 'text', 'text': marker}]}
        else:
            response['error'] = {'code': -32601, 'message': 'Method not found'}
        print(json.dumps(response), flush=True)
    record('eof')


class Plane(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        super().__init__(('127.0.0.1', 0), Handler)
        self.commands = queue.Queue()
        self.responses = {}
        self.post_attempts = Counter()
        self.fault_response = None
        self.poll_faults = queue.Queue()
        self.poll_faults_seen = Counter()
        self.polls = 0
        self.lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_):
        pass

    def reply(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Request-Id', 'req_fortis_synthetic')
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def disconnect(self):
        # Deliberately incomplete HTTP status line: unexpected EOF before headers.
        try:
            self.connection.sendall(b'HTTP/1.1 200')
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.close_connection = True

    def do_GET(self):
        if '/poll' not in self.path:
            self.reply(200, {'id': TUNNEL_ID, 'name': 'fortis-test'})
            return
        with self.server.lock:
            self.server.polls += 1
        try:
            fault = self.server.poll_faults.get_nowait()
        except queue.Empty:
            fault = None
        if fault:
            with self.server.lock:
                self.server.poll_faults_seen[fault] += 1
            if fault == 'timeout':
                time.sleep(2)
                self.disconnect()
            elif fault == 'eof':
                self.disconnect()
            else:
                self.reply(int(fault), {'error': {
                    'code': 'token_invalidated' if fault == '401' else 'permission_denied',
                    'message': 'synthetic authorization failure'}})
            return
        try:
            command = self.server.commands.get(timeout=0.15)
        except queue.Empty:
            self.reply(200, {'commands': []})
        else:
            self.reply(200, {'commands': [command]})

    def do_POST(self):
        if not self.path.endswith('/response'):
            self.reply(404, {})
            return
        size = int(self.headers['Content-Length'])
        if size > 1024 * 1024:
            self.reply(413, {})
            return
        body = json.loads(self.rfile.read(size))
        rid = body['request_id']
        with self.server.lock:
            self.server.post_attempts[rid] += 1
            self.server.responses[rid] = body
        if rid == self.server.fault_response:
            self.disconnect()
        else:
            self.reply(200, {})


def until(predicate, message, timeout=25):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError(message)


def run(runtime, old_failure, work):
    plane = Plane()
    thread = threading.Thread(target=plane.serve_forever, daemon=True)
    thread.start()
    events = work / 'synthetic-events.jsonl'
    log = work / 'runtime.jsonl'
    stub_command = [sys.executable, str(Path(__file__).resolve()), '--mcp-stub', str(events)]
    stub_command.append('--command-arg=' + COMMAND_ARG)
    if os.name == 'nt':
        stub_command = [arg.replace('\\', '/') for arg in stub_command]
    command = subprocess.list2cmdline(stub_command) if os.name == 'nt' else shlex.join(stub_command)
    argv = [str(runtime), 'run',
            '--control-plane.base-url', f'http://127.0.0.1:{plane.server_port}',
            '--control-plane.tunnel-id', TUNNEL_ID,
            '--control-plane.api-key', 'env:FORTIS_SYNTHETIC_KEY',
            '--control-plane.poll-timeout', '500ms',
            '--control-plane.poll-deadline-guardrail', '500ms',
            '--mcp.command', 'command=' + command,
            '--harpoon.additional-transport=', '--health.listen-addr', '127.0.0.1:0',
            '--log.level', 'debug', '--log.format', 'json', '--log.file=',
            '--log.http-raw-unsafe=false']
    if not old_failure:
        argv += ['--mcp.stdio-failure-policy=restart', '--pid.file', str(work / 'runtime.pid'),
                 '--health.url-file', str(work / 'health.url')]
    # Whitelist environment: no caller profile, API key, proxy or tunnel settings.
    env = {'PATH': os.defpath, 'HOME': str(work), 'USERPROFILE': str(work),
           'TMPDIR': str(work), 'TEMP': str(work), 'TMP': str(work),
           'APPDATA': str(work / 'roaming'), 'LOCALAPPDATA': str(work / 'local'),
           'FORTIS_SYNTHETIC_KEY': 'sk-fortis-offline-synthetic-not-a-real-key'}
    (work / 'roaming').mkdir()
    (work / 'local').mkdir()
    for key in ('SYSTEMROOT', 'WINDIR', 'COMSPEC'):
        if key in os.environ:
            env[key] = os.environ[key]

    def observed_events():
        if not events.exists():
            return []
        return [json.loads(line) for line in events.read_text().splitlines() if line]

    def log_text():
        return log.read_text(errors='replace')

    seq = 0

    def enqueue(method, params=None, notification=False, fault=False):
        nonlocal seq
        seq += 1
        rid = f'cmd_fortis_test_{seq}'
        rpc = dict(jsonrpc='2.0', method=method)
        if not notification:
            rpc['id'] = seq
        if params is not None:
            rpc['params'] = params
        if fault:
            plane.fault_response = rid
        plane.commands.put(dict(
            request_id=rid, shard_token='synthetic-shard', command_type='jsonrpc',
            channel='main', created_at=datetime.now(timezone.utc).isoformat(),
            response_timeout='120s', headers={'Mcp-Protocol-Version': ['2025-03-26']},
            jsonrpc=rpc))
        return rid

    def request(method, params=None, notification=False):
        rid = enqueue(method, params, notification)
        result = until(lambda: plane.responses.get(rid), f'No response for {method}; runtime status {proc.poll()}')
        return result

    def initialize():
        result = request('initialize', {'protocolVersion': '2025-03-26',
                         'capabilities': {}, 'clientInfo': {'name': 'fortis-test', 'version': '1'}})
        assert 'result' in result['resp_json'], result
        request('notifications/initialized', notification=True)

    def counter(marker):
        result = request('tools/call', {'name': 'counter', 'arguments': {'marker': marker}})
        assert result['resp_json']['result']['content'][0]['text'] == marker, result

    checks = []
    with log.open('w', encoding='utf-8') as output:
        proc = subprocess.Popen(argv, stdout=output, stderr=subprocess.STDOUT,
                                env=env, cwd=work, start_new_session=(os.name != 'nt'))
        try:
            until(lambda: plane.polls > 0 or proc.poll() is not None, 'Runtime did not start')
            assert proc.poll() is None, log_text()[-5000:]
            if not old_failure:
                until(lambda: (work / 'runtime.pid').exists() and (work / 'health.url').exists(),
                      'Runtime PID/health evidence files missing', timeout=5)
                assert int((work / 'runtime.pid').read_text().strip()) == proc.pid
                checks.append('runtime-pid-file-matches-process')
                health = (work / 'health.url').read_text().strip().rstrip('/')
                assert health.startswith('http://127.0.0.1:')
                for route in ('/ui', '/admin'):
                    try:
                        with LOOPBACK_HTTP.open(health + route, timeout=2):
                            raise AssertionError('Unexpected admin route: ' + route)
                    except HTTPError as error:
                        assert error.code == 404, error.code
                checks.append('loopback-health-without-admin-ui')
                with LOOPBACK_HTTP.open(health + '/metrics', timeout=2) as metrics:
                    assert TUNNEL_ID in metrics.read().decode()
                checks.append('legacy-tunnel-id-metrics-compatible')
            initialize()
            assert observed_events()[0]['command_arg_sha256'] == hashlib.sha256(COMMAND_ARG.encode()).hexdigest()
            checks.append('data-uri-command-argument-preserved')
            counter('before-fault')
            checks.append('initialization-and-tool-call')
            before_starts = [e['pid'] for e in observed_events() if e['kind'] == 'start']
            fault = enqueue('tools/call', {'name': 'counter', 'arguments': {'marker': 'fault-once'}}, fault=True)
            result = until(lambda: plane.responses.get(fault), 'MCP result never reached synthetic plane')
            assert result['resp_json']['result']['content'][0]['text'] == 'fault-once', result
            until(lambda: 'failed to post response to control plane' in log_text(),
                  'Expected terminal response delivery failure missing')
            if old_failure:
                until(lambda: proc.poll() is not None, 'Old runtime did not reproduce shutdown', timeout=20)
                assert 'requesting tunnel-client shutdown' in log_text(), log_text()[-3000:]
                assert Counter(e['marker'] for e in observed_events() if e['kind'] == 'call')['fault-once'] == 1
                checks.append('old-response-post-failure-shuts-down-runtime-reproduced')
            else:
                counter('after-fault')
                assert proc.poll() is None
                assert [e['pid'] for e in observed_events() if e['kind'] == 'start'] == before_starts
                assert not any(e['kind'] == 'eof' for e in observed_events())
                checks += ['failed-post-preserves-stdio', 'next-tool-call-succeeds']
                for fault_name in ('eof', 'timeout', '401', '403'):
                    plane.poll_faults.put(fault_name)
                    until(lambda: plane.poll_faults_seen[fault_name], 'Poll fault not consumed')
                    counter('after-poll-' + fault_name)
                    assert proc.poll() is None
                    checks.append('poll-' + fault_name + '-recovers')
                text = log_text()
                assert 'token_invalidated' in text and 'permission_denied' in text
                checks.append('authorization-errors-visible')
                enqueue('tools/call', {'name': 'test_child_exit', 'arguments': {'marker': 'child-exit-once'}})
                until(lambda: len([e for e in observed_events() if e['kind'] == 'start']) > len(before_starts),
                      'Runtime did not replace exited MCP child')
                assert proc.poll() is None
                rejected = request('tools/list')
                assert rejected['resp_code'] == 409, rejected
                initialize()
                counter('after-child-reinitialize')
                checks += ['unexpected-child-exit-recovers', 'legacy-initialization-guard', 'caller-reinitializes-replacement']
                calls = Counter(e['marker'] for e in observed_events() if e['kind'] == 'call')
                assert all(n == 1 for n in calls.values()), calls
                assert calls['fault-once'] == calls['child-exit-once'] == 1
                checks.append('no-tool-execution-replay')
                starts = len([e for e in observed_events() if e['kind'] == 'start'])
                proc.terminate()
                proc.wait(timeout=10)
                time.sleep(0.3)
                assert len([e for e in observed_events() if e['kind'] == 'start']) == starts
                checks.append('intentional-stop-no-respawn')
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
            if os.name != 'nt':
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            plane.shutdown()
            plane.server_close()
    return dict(status='PASS', expectation='old-failure' if old_failure else 'resilient',
                checks=checks, runtime_exit=proc.returncode,
                synthetic_tool_executions=dict(Counter(
                    e['marker'] for e in observed_events() if e['kind'] == 'call')),
                terminal_post_attempts=plane.post_attempts.get(fault, 0),
                child_generations=len([e for e in observed_events() if e['kind'] == 'start']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--expect-old-failure', action='store_true')
    parser.add_argument('--evidence-dir', type=Path)
    parser.add_argument('--mcp-stub', type=Path)
    parser.add_argument('--command-arg', default='')
    args = parser.parse_args()
    if args.mcp_stub:
        stub(args.mcp_stub, args.command_arg)
        return
    if not args.runtime or not args.runtime.resolve().is_file():
        parser.error('--runtime must name an existing narrow runtime binary')
    if args.evidence_dir:
        args.evidence_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
        result = run(args.runtime.resolve(), args.expect_old_failure, args.evidence_dir.resolve())
        (args.evidence_dir / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    else:
        with tempfile.TemporaryDirectory(prefix='fortis-runtime-test-') as folder:
            result = run(args.runtime.resolve(), args.expect_old_failure, Path(folder))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
