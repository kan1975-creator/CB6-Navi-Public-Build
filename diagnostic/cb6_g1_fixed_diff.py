#!/usr/bin/env python3
"""Isolated read-only diagnostic. Never changes the checkout or GitHub."""
import base64
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import sys
import urllib.request
import zipfile

ARTIFACT_ID = 13576722723
FIXED_COMMIT = 'd1afd49da4ad35123877a35ec47cf28b3d7b2560'
ZIP_SHA256 = 'b89dc1fec7a963d79e4acf0bfc2452bb8247495a97fe479e2f0cf3ddbdc15db8'
ZIP_BYTES = 23467
FIXED_BLOBS = {'jni': 'a72e49a225865d47336b843d6b8a18efd98e6436',
               'header': '3ebef1a01d6635526331891f74896578bb28f6d7'}
SPECS = [
    dict(name='jni', g1_path='android/sdk/src/main/cpp/app/organicmaps/sdk/cb6_signal_jni.inc',
         fixed_path='v2/signals/native/cb6_signal_jni.inc', g1_bytes=4316,
         g1_sha='c12a4b0a1a62555b7a9d350e4a62101ad5aa4f6f87b1e5fab0722ff8f4ee9de4',
         fixed_bytes=14205, fixed_sha='5835e06db97c26e60b8907e9eef02e3378975680495d2f967a67d432686b210c'),
    dict(name='header', g1_path='libs/map/cb6_signal_mark.hpp',
         fixed_path='v2/signals/native/cb6_signal_mark.hpp', g1_bytes=1292,
         g1_sha='0ef33b34179b207b253b581457ad6d995664c411ec122c9c97c9b0158589199d',
         fixed_bytes=1166, fixed_sha='bd31798db90e80807ab53b0a38a9ddda77c23fad22e9ffb70cd74bc5322af28c')
]

def fetch(url, token, accept):
    """Fetch API inputs; never forward the bearer token to an artifact host."""
    import urllib.error
    from urllib.parse import urlsplit

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    try:
        api_url = urlsplit(url)
        valid_api = (api_url.scheme == 'https' and api_url.hostname == 'api.github.com'
                     and api_url.username is None and api_url.password is None
                     and api_url.port in (None, 443))
    except ValueError:
        valid_api = False
    if not valid_api:
        raise RuntimeError('API_URL_REJECTED')
    is_artifact = api_url.path.endswith(f'/actions/artifacts/{ARTIFACT_ID}/zip')
    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={
        'Authorization': 'Bearer ' + token,
        'Accept': accept,
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'cb6-g1-fixed-diff-readonly'})
    stage = 'ARTIFACT_API' if is_artifact else 'CONTENTS_API'
    try:
        with opener.open(req, timeout=45) as response:
            if is_artifact:
                raise RuntimeError('ARTIFACT_API_EXPECTED_302')
            if response.getcode() != 200:
                raise RuntimeError('CONTENTS_API_UNEXPECTED_STATUS')
            return response.read()
    except urllib.error.HTTPError as exc:
        if not is_artifact or exc.code != 302:
            raise RuntimeError(f'{stage}_HTTP_{exc.code}') from None
        location = exc.headers.get('Location', '')
        # GitHub documents these domains for workflow artifact transfer.
        # This is a transport-domain restriction, NOT proof of GitHub ownership
        # of an individual Azure Blob account. Trust starts at the TLS API 302.
        allowed_exact = {'results-receiver.actions.githubusercontent.com'}
        def allowed_artifact_host(host):
            return (host in allowed_exact or
                    re.fullmatch(r'[a-z0-9-]+\.blob\.core\.windows\.net', host) is not None)
        try:
            target = urlsplit(location)
            host = (target.hostname or '').lower()
            valid = (allowed_artifact_host(host) and target.scheme == 'https'
                     and target.port in (None, 443) and target.username is None
                     and target.password is None and not target.fragment)
        except (ValueError, TypeError):
            valid = False
        if not valid:
            raise RuntimeError('ARTIFACT_REDIRECT_REJECTED') from None
        download = urllib.request.Request(location, headers={
            'User-Agent': 'cb6-g1-fixed-diff-readonly'})
        try:
            with opener.open(download, timeout=45) as response:
                if response.getcode() != 200:
                    raise RuntimeError('ARTIFACT_DOWNLOAD_UNEXPECTED_STATUS')
                return response.read()
        except urllib.error.HTTPError as download_error:
            if download_error.code in (301, 302, 303, 307, 308):
                raise RuntimeError('ARTIFACT_SECOND_REDIRECT_REJECTED') from None
            raise RuntimeError(f'ARTIFACT_DOWNLOAD_HTTP_{download_error.code}') from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise RuntimeError('ARTIFACT_DOWNLOAD_NETWORK_ERROR') from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError(f'{stage}_NETWORK_ERROR') from None

def verify(label, data, expected_bytes, expected_sha):
    sha = hashlib.sha256(data).hexdigest()
    if len(data) != expected_bytes or sha != expected_sha:
        raise ValueError(f'{label}: size/SHA mismatch; actual size={len(data)}, sha={sha}')
    return {'size': len(data), 'sha256': sha, 'verified': True}

def git_blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()

def main():
    token = os.environ['GH_TOKEN']
    repo = os.environ['GH_REPOSITORY']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('Invalid repository')
    if repo != 'kan1975-creator/CB6-Navi-Public-Build':
        raise ValueError('Unexpected repository')
    if os.environ.get('GH_EVENT_NAME') != 'workflow_dispatch' or os.environ.get('GH_RUN_ATTEMPT') != '1' or os.environ.get('GH_REF') != 'refs/heads/cb6-apk-228-r8-fragment-keep-20261104':
        raise ValueError('Execution gate mismatch')
    api = f'https://api.github.com/repos/{repo}'
    archive = fetch(f'{api}/actions/artifacts/{ARTIFACT_ID}/zip', token, 'application/vnd.github+json')
    # GitHub may repackage an artifact ZIP; trust only verified member bytes.
    results = {'artifact_id': ARTIFACT_ID, 'fixed_commit': FIXED_COMMIT,
               'archive': {'size': len(archive), 'sha256': hashlib.sha256(archive).hexdigest(),
                           'matches_reference_zip': len(archive) == ZIP_BYTES and hashlib.sha256(archive).hexdigest() == ZIP_SHA256},
               'files': {}}
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        names = set(z.namelist())
        for s in SPECS:
            # G1 artifact contains paths under g1/; fail closed on unexpected layout.
            archive_path = 'g1/' + s['g1_path']
            if archive_path not in names:
                raise ValueError('Missing exact G1 path: ' + archive_path)
            g1 = z.read(archive_path)
            results['files'][s['name']] = {'g1': verify('G1 ' + s['name'], g1, s['g1_bytes'], s['g1_sha'])}
            s['g1_data'] = g1
    for s in SPECS:
        url = f"{api}/contents/{s['fixed_path']}?ref={FIXED_COMMIT}"
        payload = json.loads(fetch(url, token, 'application/vnd.github+json'))
        if payload.get('encoding') != 'base64' or payload.get('type') != 'file':
            raise ValueError('Unexpected GitHub content encoding/type')
        fixed = base64.b64decode(''.join(payload['content'].split()), validate=True)
        blob = git_blob_sha(fixed)
        if payload.get('sha') != FIXED_BLOBS[s['name']] or blob != FIXED_BLOBS[s['name']]:
            raise ValueError(f"fixed {s['name']}: Git Blob SHA mismatch")
        results['files'][s['name']]['fixed'] = verify('fixed ' + s['name'], fixed, s['fixed_bytes'], s['fixed_sha'])
        results['files'][s['name']]['fixed']['git_blob_sha1'] = blob
        s['fixed_data'] = fixed
    # Diff files are not written until all four SHA-256 verifications pass.
    out = Path('diagnostic-output')
    out.mkdir(exist_ok=True)
    summary = {'verification': results, 'diffs': {}}
    with tempfile.TemporaryDirectory(prefix='cb6-g1-diff-') as temporary:
      for s in SPECS:
        a = Path(temporary) / (s['name'] + '.g1')
        b = Path(temporary) / (s['name'] + '.fixed')
        a.write_bytes(s['g1_data'])
        b.write_bytes(s['fixed_data'])
        result = subprocess.run(['diff', '-u', '--label', 'G1/' + s['g1_path'],
                                 '--label', 'FIXED/' + s['fixed_path'], str(a), str(b)],
                                capture_output=True, check=False)
        if result.returncode not in (0, 1):
            raise RuntimeError(f"diff failed for {s['name']}: exit={result.returncode}")
        patch = result.stdout.decode('utf-8', errors='surrogateescape')
        (out / (s['name'] + '.diff')).write_bytes(result.stdout)
        hunks = sum(line.startswith('@@ ') for line in patch.splitlines())
        added = sum(line.startswith('+') and not line.startswith('+++') for line in patch.splitlines())
        removed = sum(line.startswith('-') and not line.startswith('---') for line in patch.splitlines())
        summary['diffs'][s['name']] = {'exit_code': result.returncode, 'hunks': hunks,
                                      'added_lines': added, 'removed_lines': removed,
                                      'first_hunk': next((line for line in patch.splitlines() if line.startswith('@@ ')), None)}
    (out / 'DIFF_SUMMARY.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    (out / 'SHA256_RESULTS.txt').write_text(json.dumps(results, indent=2) + '\n')
    (out / 'EXECUTION_LOG.txt').write_text('All four inputs verified; two diff -u executions completed; no adoption.\n')
    (out / 'DIAGNOSTIC_SUCCESS.txt').write_text('VERIFIED_4_FILES_AND_2_DIFFS\n')
    print(json.dumps(summary['diffs'], indent=2))

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        out = Path('diagnostic-output')
        out.mkdir(exist_ok=True)
        message = f'STOP: {type(exc).__name__}: {exc}'
        (out / 'DIAGNOSTIC_SUCCESS.txt').unlink(missing_ok=True)
        (out / 'STOP_REASON.txt').write_text(message + '\n')
        print(message, file=sys.stderr)
        sys.exit(2)
