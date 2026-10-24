"""Repo Docker unified history lifecycle tests; no Windows owner processes."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid

from store import stage
from repo_messages import stage_assistant


@unittest.skipUnless(Path('/workspace/repo').is_dir(), 'Repo volume is required')
class RepoServiceLifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fortis-repo-test-', dir='/workspace/repo')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.child = None

    def tearDown(self):
        self.stop()

    def stop(self):
        if self.child is None:
            return
        self.child.terminate()
        try:
            self.child.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            self.child.kill()
            self.child.communicate(timeout=5)
        self.child = None

    def start(self):
        self.child = subprocess.Popen(
            [sys.executable, '-u', 'repo_service.py', 'run',
             '--state-dir', str(self.root), '--port', str(self.port)],
            cwd=Path(__file__).parent, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for _ in range(45):
            if self.child.poll() is not None:
                stdout, stderr = self.child.communicate()
                self.fail('repo service exited early: ' + stderr[:450])
            try:
                with urlopen(f'http://127.0.0.1:{self.port}/', timeout=.25) as response:
                    if response.status == 200:
                        return
            except (OSError, TimeoutError):
                time.sleep(.1)
        self.fail('repo service never became available')

    def request(self, path, method='GET', body=None, auth=True):
        token_path = self.root / '.repo-http-token'
        headers = {}
        if auth:
            headers['Authorization'] = 'Bearer ' + token_path.read_text(encoding='ascii')
        if body is not None:
            headers['Content-Type'] = 'application/json'
        r = Request(f'http://127.0.0.1:{self.port}{path}',
                    data=json.dumps(body).encode() if body is not None else None,
                    headers=headers, method=method)
        try:
            with urlopen(r, timeout=2) as x:
                return x.status, json.load(x)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_repo_service_persists_offline_events_and_requires_writer_capability(self):
        self.start()
        self.assertEqual(self.request('/api/state', auth=False)[0], 401)
        self.assertEqual(self.request('/api/user-messages', 'POST', body={})[0], 409)
        self.assertEqual(self.request('/api/state')[0], 200)
        cli = subprocess.run([sys.executable, 'repo_service.py', 'status',
                              '--state-dir', str(self.root), '--port', str(self.port)],
                             cwd=Path(__file__).parent, capture_output=True, text=True, timeout=5)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        self.assertTrue(json.loads(cli.stdout)['assistant_spool'])
        status, created = self.request('/api/sessions', 'POST',
            body={'url': 'https://chatgpt.com/c/synthetic-12345678',
                  'route': 'repo', 'title': 'Synthetic Repo Test'})
        self.assertEqual(status, 201)
        session = created['session']
        cli_sessions = subprocess.run([sys.executable, 'repo_service.py', 'sessions',
                                       '--state-dir', str(self.root), '--port', str(self.port)],
                                      cwd=Path(__file__).parent, capture_output=True, text=True, timeout=5)
        self.assertEqual(cli_sessions.returncode, 0, cli_sessions.stderr)
        self.assertEqual(len(json.loads(cli_sessions.stdout)['sessions']), 1)
        cli_help = subprocess.run([sys.executable, 'repo_service.py', 'instructions',
                                   '--state-dir', str(self.root), '--port', str(self.port),
                                   '--session', session['reporting_session_id']],
                                  cwd=Path(__file__).parent, capture_output=True, text=True, timeout=5)
        self.assertEqual(cli_help.returncode, 0, cli_help.stderr)
        self.assertNotIn(str(self.root / 'inbox' / 'repo'), cli_help.stdout)
        self.assertIn('STAGED_ONLY', cli_help.stdout)
        self.assertIn('repo_task.py message', cli_help.stdout)
        self.assertIn('Основной инструмент AI: Fortis Repo', cli_help.stdout)
        self.assertIn('Windows owner HOST или browser relay', cli_help.stdout)
        self.assertNotIn('Полный текст сообщений пока НЕ архивируется', cli_help.stdout)
        self.assertNotIn(session['reporting_session_id'], cli_help.stdout)
        self.assertNotIn(session['task_id'], cli_help.stdout)
        self.assertIn('BOOTSTRAP', cli_help.stdout)
        self.assertIn('одного Repo Docker volume', cli_help.stdout)
        self.assertEqual(
            self.request('/api/message-writer-pair?session=' + session['reporting_session_id'])[0], 200)
        self.assertEqual(
            self.request('/api/observer-pair?session=' + session['reporting_session_id'])[0], 200)
        self.assertEqual(os.stat(self.root).st_mode & 0o777, 0o700)
        self.assertEqual(os.stat(self.root / '.repo-http-token').st_mode & 0o777, 0o600)

        # Shutdown before staging; no Observatory sampler can import anything.
        self.stop()
        task = 'task_' + uuid.uuid4().hex
        inbox = self.root / 'inbox' / 'repo'
        for kind in ('user_message', 'progress', 'assistant_message'):
            stage(inbox, {'version': 2, 'event_id': uuid.uuid4().hex,
                          'reporting_session_id': session['reporting_session_id'],
                          'task_id': task, 'session_task_id': session['task_id'],
                          'sequence': 0, 'route': 'repo', 'event': kind,
                          'stage': 'other',
                          'summary': ('Получено сообщение пользователя' if kind == 'user_message' else
                                      'Ответ ChatGPT заявлен отправителем' if kind == 'assistant_message' else
                                      'Проверяю накопленные события')})
        self.assertEqual(len(list(inbox.glob('*.json'))), 3)
        self.start()
        for _ in range(50):
            state = self.request('/api/state')[1]
            if state.get('ok') and len(state['sessions'][0]['events']) == 3:
                break
            time.sleep(.1)
        else:
            self.fail('backlog not imported after restart')
        self.assertEqual(len(list(inbox.glob('*.json'))), 0)
        sequence = [x['sequence'] for x in state['sessions'][0]['events']]
        self.assertEqual(sequence, [0, 1, 2])
        self.assertEqual([x['sender_sequence'] for x in state['sessions'][0]['events']], [0, 0, 0])
        self.assertEqual(self.request('/api/user-messages', 'POST', body={})[0], 409)
        self.assertEqual(self.request('/api/message-writer-pair?session=' +
                                      session['reporting_session_id'])[0], 200)
        self.stop()
        self.assertEqual(len(list((self.root / 'archive' / 'sessions' /
                                   session['reporting_session_id'] / 'events').glob('*.md'))), 3)


    def test_offline_assistant_full_text_and_user_original_share_one_docker_archive(self):
        self.start()
        sid, enrollment = None, None
        status, r = self.request('/api/sessions', 'POST',
                  body={'url': 'https://chatgpt.com/c/synthetic-87654321',
                        'route': 'repo', 'title': 'Unified Repo Test'})
        self.assertEqual(status, 201)
        meta = r['session']
        sid, enrollment = meta['reporting_session_id'], meta['task_id']
        task = 'task_' + uuid.uuid4().hex
        msg1, msg2 = 'msg_' + uuid.uuid4().hex, 'msg_' + uuid.uuid4().hex
        inbox = self.root / 'inbox' / 'messages'
        original = "  Synthetic original \n <markup> \n"
        ai_one = "Synthetic interim answer\nline 2"
        ai_two = "Synthetic final answer <node>\nUnicode 文字"
        # User original cannot be archived until accepted V2 event.
        status, no_signal = self.request('/api/user-messages', 'POST',
                    body={'reporting_session_id': sid,
                          'conversation_id': meta['conversation_id'],
                          'task_id': task, 'original_text': original})
        self.assertEqual(status, 403)  # no writer capability

        self.stop()
        assert not inbox.is_symlink()
        for mid, kind, body in ((msg1,'interim',ai_one), (msg2,'final',ai_two)):
            staged = stage_assistant(inbox, {
                'version': 1, 'message_id': mid, 'reporting_session_id': sid,
                'session_task_id': enrollment, 'task_id': task,
                'role': 'assistant', 'kind': kind, 'body': body})
            self.assertTrue(staged.exists())
        # Test the same sender CLI that ChatGPT can invoke; body only on stdin.
        mid3 = 'msg_' + uuid.uuid4().hex
        cli = subprocess.run(
            [sys.executable, 'repo_message_sender.py', '--state-dir', str(self.root),
             '--session', sid, '--session-task', enrollment,
             '--task', task, '--message-id', mid3, '--kind', 'interim'],
            cwd=Path(__file__).parent, input='Additional synthetic interim',
            capture_output=True, text=True, timeout=5)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        self.assertIn('STAGED_ONLY', cli.stdout)
        self.assertNotIn('Additional synthetic interim', cli.stdout)
        stage(self.root / 'inbox' / 'repo', {
            'version': 2, 'event_id': uuid.uuid4().hex,
            'reporting_session_id': sid, 'session_task_id': enrollment,
            'task_id': task, 'sequence': 0, 'route': 'repo',
            'event': 'progress', 'stage': 'other',
            'summary': 'Synthetic task activity'})
        self.assertEqual(len(list(inbox.glob('*.json'))), 3)
        self.start()
        for _ in range(40):
            status, obj = self.request('/api/state')
            if (obj.get('messages_ingest', {}).get('accepted') == 3 and
                    obj.get('sessions') and obj['sessions'][0]['events_count'] == 1):
                break
            time.sleep(.12)
        else:
            self.fail('offline assistant body import failed')
        self.assertEqual(len(list(inbox.glob('*.json'))), 0)
        self.assertEqual(self.request('/api/repo-history?session=' + sid + '&task=' + task,
                                      auth=False)[0], 401)
        status, history = self.request('/api/repo-history?session=' + sid + '&task=' + task)
        self.assertEqual(status, 200)
        self.assertIsNone(history['original_text'])
        bodies = {m['message_id']: m['body'] for m in history['assistant_messages']}
        self.assertEqual(bodies, {msg1: ai_one, msg2: ai_two, mid3: 'Additional synthetic interim'})
        self.assertEqual(len(history['events']), 1)
        # Archive exact user original via distinct writer key, only after accepted.
        status, pair = self.request('/api/message-writer-pair?session=' + sid)
        self.assertEqual(status, 200)
        posted = {'reporting_session_id': sid, 'conversation_id': meta['conversation_id'],
                  'task_id': task, 'original_text': original}
        status, receipt = self.request('/api/user-messages', 'POST', body=posted, auth=False)
        self.assertEqual(status, 403)
        # Request helper does not expose custom headers; use owner-local stdin-only CLI.
        archived = subprocess.run(
            [sys.executable, 'repo_service.py', 'archive-original',
             '--state-dir', str(self.root), '--port', str(self.port),
             '--session', sid, '--task', task],
            cwd=Path(__file__).parent, input=original, capture_output=True, text=True, timeout=5)
        self.assertEqual(archived.returncode, 0, archived.stderr)
        self.assertTrue(json.loads(archived.stdout)['archived'])
        receipt_again = subprocess.run(
            [sys.executable, 'repo_service.py', 'archive-original',
             '--state-dir', str(self.root), '--port', str(self.port),
             '--session', sid, '--task', task],
            cwd=Path(__file__).parent, input=original, capture_output=True, text=True, timeout=5)
        self.assertEqual(json.loads(receipt_again.stdout)['status'], 'existing')
        status, after = self.request('/api/repo-history?session=' + sid + '&task=' + task)
        self.assertEqual(status, 200)
        self.assertEqual(after['original_text'], original)
        self.assertEqual(len(after['assistant_messages']), 3)
        history_cli = subprocess.run(
            [sys.executable, 'repo_service.py', 'history',
             '--state-dir', str(self.root), '--port', str(self.port),
             '--session', sid, '--task', task],
            cwd=Path(__file__).parent, capture_output=True, text=True, timeout=5)
        self.assertEqual(history_cli.returncode, 0, history_cli.stderr)
        self.assertEqual(json.loads(history_cli.stdout)['original_text'], original)
        self.stop()
        self.start()
        self.assertEqual(self.request('/api/repo-history?session=' + sid + '&task=' + task)[1]['original_text'],
                         original)

    def test_assistant_message_idempotent_and_conflict_goes_private_quarantine(self):
        self.start()
        status, response = self.request('/api/sessions', 'POST',
                  body={'url': 'https://chatgpt.com/c/synthetic-abcxyz12',
                        'route': 'repo', 'title': 'Messages Test'})
        meta = response['session']; task = 'task_' + uuid.uuid4().hex
        message = {'version': 1, 'message_id': 'msg_' + uuid.uuid4().hex,
                   'reporting_session_id': meta['reporting_session_id'],
                   'session_task_id': meta['task_id'], 'task_id': task,
                   'role': 'assistant', 'kind': 'final', 'body': 'Synthetic A'}
        inbox = self.root / 'inbox' / 'messages'
        stage_assistant(inbox,message)
        for _ in range(40):
            status, obj = self.request('/api/state')
            if obj.get('messages_ingest',{}).get('accepted',0)==1:
                break
            time.sleep(.12)
        else: self.fail('first message not imported')
        stage_assistant(inbox,message)
        for _ in range(40):
            status, obj = self.request('/api/state')
            if obj.get('messages_ingest',{}).get('duplicate',0)==1:
                break
            time.sleep(.12)
        else: self.fail('idempotent retry not deduped')
        altered = {**message, 'body':'Changed body'}
        stage_assistant(inbox,altered)
        for _ in range(40):
            status, obj = self.request('/api/state')
            if obj.get('messages_ingest',{}).get('quarantined',0)==1:
                break
            time.sleep(.12)
        else: self.fail('conflict not quarantined')
        self.assertEqual(len(list((self.root/'quarantine'/'messages').glob('*.json'))),1)
        status, hist = self.request('/api/repo-history?session='+meta['reporting_session_id']+
                                     '&task='+task)
        self.assertEqual(hist['assistant_messages'][0]['body'],'Synthetic A')
        self.assertEqual(len(hist['assistant_messages']),1)


    def test_foreign_message_is_quarantined_and_missing_session_is_deferred(self):
        self.start()
        status, response = self.request('/api/sessions', 'POST',
                  body={'url': 'https://chatgpt.com/c/synthetic-99998888',
                        'route': 'repo', 'title': 'Security Test'})
        meta = response['session']
        task = 'task_' + uuid.uuid4().hex
        inbox = self.root / 'inbox' / 'messages'
        base = {'version': 1, 'message_id': 'msg_' + uuid.uuid4().hex,
                'reporting_session_id': meta['reporting_session_id'],
                'session_task_id': 'task_' + uuid.uuid4().hex,
                'task_id': task, 'role': 'assistant', 'kind': 'final',
                'body': 'Synthetic hostile enrollment'}
        stage_assistant(inbox, base)
        for _ in range(45):
            obj = self.request('/api/state')[1]
            if obj.get('messages_ingest',{}).get('quarantined',0)==1:
                break
            time.sleep(.1)
        else: self.fail('wrong enrollment not quarantined')
        self.assertFalse(list(inbox.glob('*.json')))
        self.assertEqual(len(list((self.root/'quarantine'/'messages').glob('*.json'))), 1)
        self.assertEqual(self.request('/api/repo-history?session='+
                          meta['reporting_session_id']+'&task='+task)[1]['assistant_messages'], [])
        sid_missing = 'rs_' + uuid.uuid4().hex
        stage_assistant(inbox, {**base, 'message_id': 'msg_' + uuid.uuid4().hex,
                                'reporting_session_id': sid_missing})
        for _ in range(45):
            obj = self.request('/api/state')[1]
            if obj.get('messages_ingest',{}).get('deferred',0)==1:
                break
            time.sleep(.1)
        else: self.fail('missing session not deferred')
        self.assertEqual(len(list(inbox.glob('*.json'))), 1)
        self.assertEqual(len(list((self.root/'quarantine'/'messages').glob('*.json'))), 1)
        self.assertEqual(self.request('/api/repo-history?session=' +
                          sid_missing + '&task=' + task)[0], 404)


    def test_direct_repo_tool_cli_emits_metadata_and_full_assistant_text(self):
        """The AI tool uses Repo-local CLI, not G2, Windows relay or HTTP bearer."""
        from store import Store
        # Source-local synthetic enrollment: real persistent Repo session is untouched.
        store = Store(self.root / 'archive', {'repo': self.root / 'inbox' / 'repo'})
        (self.root / 'archive').mkdir(mode=0o700, exist_ok=True)
        (self.root / 'inbox').mkdir(mode=0o700, exist_ok=True)
        (self.root / 'inbox' / 'repo').mkdir(mode=0o700, exist_ok=True)
        (self.root / 'inbox' / 'messages').mkdir(mode=0o700, exist_ok=True)
        (self.root / 'quarantine' / 'messages').mkdir(mode=0o700, parents=True, exist_ok=True)
        meta = store.register('https://chatgpt.com/c/synthetic-repotool-01',
                              'repo', 'Source test')
        task = 'task_' + uuid.uuid4().hex
        summary = 'Проверен синтетический этап работы'
        event_call = subprocess.run([
            sys.executable, 'emit.py',
            '--inbox', str(self.root / 'inbox' / 'repo'),
            '--session', meta['reporting_session_id'],
            '--session-task', meta['task_id'],
            '--task', task, '--version', '2', '--route', 'repo',
            '--sequence', '0', '--event', 'progress', '--stage', 'testing',
            '--summary', summary
        ], cwd=Path(__file__).parent, capture_output=True, text=True, timeout=5)
        self.assertEqual(event_call.returncode, 0, event_call.stderr)
        self.assertIn('STAGED_ONLY', event_call.stdout)
        body = 'Синтетическое сообщение AI через Fortis Repo (полный текст).'
        message_call = subprocess.run([
            sys.executable, 'repo_message_sender.py',
            '--state-dir', str(self.root),
            '--session', meta['reporting_session_id'],
            '--session-task', meta['task_id'], '--task', task, '--kind', 'final'
        ], cwd=Path(__file__).parent, input=body,
            capture_output=True, text=True, timeout=5)
        self.assertEqual(message_call.returncode, 0, message_call.stderr)
        self.assertIn('STAGED_ONLY', message_call.stdout)
        self.assertNotIn(body, message_call.stdout)
        # Store.register creates directories for owner-like mode; the Repo
        # service enforces strict 0700 and this isolated test must do so too.
        (self.root / 'archive').chmod(0o700)
        (self.root / 'quarantine').chmod(0o700)
        self.assertEqual(len(list((self.root / 'inbox' / 'repo').glob('*.json'))), 1)
        self.assertEqual(len(list((self.root / 'inbox' / 'messages').glob('*.json'))), 1)
        self.start()
        for _ in range(60):
            status, response = self.request('/api/repo-history?session=' +
                    meta['reporting_session_id'] + '&task=' + task)
            if (status == 200 and response.get('events') and
                    response.get('assistant_messages')):
                break
            time.sleep(.1)
        else:
            self.fail('actual Repo CLI sender did not produce accepted event and text')
        self.assertEqual(len(response['events']), 1)
        self.assertEqual(response['assistant_messages'][0]['body'], body)
        self.assertEqual(response['assistant_messages'][0]['kind'], 'final')
        self.assertEqual(len(list((self.root / 'inbox' / 'repo').glob('*.json'))), 0)
        self.assertEqual(len(list((self.root / 'inbox' / 'messages').glob('*.json'))), 0)
        event_files = list((self.root / 'archive' / 'sessions' /
            meta['reporting_session_id'] / 'events').glob('*.md'))
        self.assertEqual(len(event_files), 1)
        self.assertNotIn(body, event_files[0].read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
