"""Read-only rollout preflight. Never starts/stops services or issues POSTs."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BUNDLE = Path('/workspace/repo/fortis-rollout-5.7.25-20261021')
MANIFEST_SHA = '885bb8eec66fd82251dc7544dee0c38665e20766aeaa4076754c0ff5585bb6da'
STATE = Path('/workspace/repo/fortis-observatory-repo-v1')
SOURCE = Path('/workspace/repos/tunnel/observatory/v1')
NOTIFIER = Path('/workspace/repos/tabnotifier-fileautosend-autochat')


def regular(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('regular_file_required')
    return path.read_bytes()


def verify_bundle(bundle=BUNDLE, source=SOURCE, notifier=NOTIFIER):
    if bundle.is_symlink() or not bundle.is_dir():
        raise ValueError('bundle_unavailable')
    raw = regular(bundle / 'manifest.json')
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA:
        raise ValueError('manifest_changed')
    obj = json.loads(raw)
    if obj.get('version') != 1 or obj.get('source_version') != '5.7.25':
        raise ValueError('manifest_version')
    for kind in ('baseline', 'candidate'):
        folder = bundle / kind
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError('bundle_folder')
        for name, expected in obj[kind].items():
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or not re.fullmatch(r'[0-9a-f]{64}', expected):
                raise ValueError('manifest_shape')
            if hashlib.sha256(regular(folder / name)).hexdigest() != expected:
                raise ValueError('bundle_file_changed')
            if kind == 'candidate':
                current = (notifier if name == 'chatgpt-tab-notifier.user.js' else source) / name
                if hashlib.sha256(regular(current)).hexdigest() != expected:
                    raise ValueError('candidate_source_changed')
    return {'baseline_files': len(obj['baseline']), 'candidate_files': len(obj['candidate'])}


def inspect_live(state=STATE, opener=urlopen, proc=Path('/proc')):
    if state.is_symlink() or not state.is_dir():
        raise ValueError('state_unavailable')
    raw_pid = regular(state / '.service.pid')
    if not re.fullmatch(rb'[1-9][0-9]{0,9}\s*', raw_pid):
        raise ValueError('pid_invalid')
    pid = int(raw_pid)
    args = regular(proc / str(pid) / 'cmdline').split(b'\0')
    if not any(Path(x.decode()).name == 'repo_service.py' for x in args if x):
        raise ValueError('service_identity')
    if b'run' not in args or b'--state-dir' not in args:
        raise ValueError('service_arguments')
    at = args.index(b'--state-dir')
    if at + 1 >= len(args) or args[at + 1].decode() != str(state):
        raise ValueError('service_state_mismatch')
    token = regular(state / '.repo-http-token').decode('ascii').strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{40,90}', token):
        raise ValueError('token_invalid')
    headers = {'Authorization': 'Bearer ' + token}
    def get(path):
        with opener(Request('http://127.0.0.1:18754' + path, headers=headers, method='GET'), timeout=4) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError('response_too_large')
            return json.loads(raw)
    data = get('/api/state')
    if data.get('ok') is not True or not isinstance(data.get('sessions'), list):
        raise ValueError('live_state_invalid')
    sessions = data['sessions']
    supports = None
    if sessions:
        sid = sessions[0].get('reporting_session_id')
        if not isinstance(sid, str) or not re.fullmatch(r'rs_[0-9a-f]{32}', sid):
            raise ValueError('live_session_invalid')
        try:
            reply = get('/api/task-intents?session=' + sid)
            supports = reply.get('ok') is True
            if not supports:
                raise ValueError('live_intents_invalid')
        except HTTPError as ex:
            if ex.code != 404:
                raise ValueError('live_intents_unavailable') from None
            supports = False
    if regular(state / '.service.pid') != raw_pid:
        raise ValueError('service_changed_during_check')
    return {'live_read_ok': True, 'service_pid': pid, 'sessions_count': len(sessions),
            'live_has_task_intents': supports}


def main():
    try:
        data = {'ok': True, **verify_bundle(), **inspect_live()}
    except Exception as ex:
        print(json.dumps({'ok': False, 'error': type(ex).__name__}))
        return 1
    print(json.dumps(data, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
