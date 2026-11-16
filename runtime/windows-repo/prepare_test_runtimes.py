"""Download fixed public upstream runtime fixtures into a new test directory.

Never installs into C:\\Tools, starts a runtime or reads real profiles/keys.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
from urllib.request import urlopen
import zipfile

FIXTURES = {
    ('0.0.15', 'windows-amd64'): (
        'aa5ddb14dddd602fa59f3e6f4401aa8a79a218e341466226b7434127dff65dbc',
        'a922d372d6be0649156fbc1c8a040597f1f4bb5b4356890151d7875602593b1a'),
    ('0.0.21', 'windows-amd64'): (
        'd991623bd171049e2100b402d72af7ebc8edf558051ae8fc924173373d1611a8',
        'db590a52993c830a4c806108c3f25345ea986c6248210b86df640e5081ff6a0b'),
    ('0.0.15', 'linux-amd64'): (
        'f26f8b3ee6c335e38fa5cfbe6ce5635f53738f08a26eecf07d6cebacab4a1abf',
        '9755c5f60f40ac64e1a71f9b7d14bc6135fb3fe7170d79c6695881d3aa1255d5'),
    ('0.0.21', 'linux-amd64'): (
        'fa53182b766aeaceb652d86aee291c48daf7b90b5d73586dba370f4c1801325e',
        'd82fa113e4bc7ab896ff143120b725e588c2f244935e6d315ccea4ee90c03647'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--platform', choices=('windows-amd64', 'linux-amd64'), required=True)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    records = []
    for version in ('0.0.15', '0.0.21'):
        archive_hash, executable_hash = FIXTURES[(version, args.platform)]
        name = f'tunnel-client-runtime-v{version}-{args.platform}.zip'
        url = f'https://github.com/openai/tunnel-client/releases/download/v{version}/{name}'
        with urlopen(url, timeout=60) as response:
            data = response.read(100 * 1024 * 1024 + 1)
        if len(data) > 100 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != archive_hash:
            raise ValueError('Test fixture archive SHA-256 mismatch')
        executable = 'tunnel-client-runtime' + ('.exe' if args.platform == 'windows-amd64' else '')
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if archive.testzip() is not None:
                raise ValueError('Corrupt fixture archive')
            entry = archive.getinfo(executable)
            if entry.file_size > 100 * 1024 * 1024:
                raise ValueError('Unexpected executable size')
            binary = archive.read(executable)
        if hashlib.sha256(binary).hexdigest() != executable_hash:
            raise ValueError('Test fixture executable SHA-256 mismatch')
        target = args.directory / ('v' + version) / executable
        target.parent.mkdir(mode=0o700)
        with target.open('xb') as output:
            output.write(binary)
        if args.platform == 'linux-amd64':
            target.chmod(0o700)
        records.append(dict(version=version, platform=args.platform, url=url,
                            archive_sha256=archive_hash, executable_sha256=executable_hash))
    (args.directory / 'fixtures.json').write_text(json.dumps(records, indent=2) + '\n')
    print('FORTIS_TEST_FIXTURE_HASHES_PASS', args.platform)


if __name__ == '__main__':
    main()
