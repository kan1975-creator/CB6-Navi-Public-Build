#!/usr/bin/env python3
"""Jules bridge. No implicit send, no plan approval, no PR creation."""
import argparse, hashlib, json, os, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

BASE = 'https://jules.googleapis.com/v1alpha'
DEFAULT_SESSION = '8061497760758145992'

def api(path, payload=None):
    key = os.environ.get('JULES_API_KEY')
    if not key:
        raise RuntimeError('JULES_API_KEY not configured')
    body = None if payload is None else json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(BASE + path, data=body, headers={'x-goog-api-key':key, 'Content-Type':'application/json'}, method='POST' if payload is not None else 'GET')
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read(5_000_001)
            if len(raw) > 5_000_000: raise RuntimeError('API response size limit exceeded')
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'Jules API HTTP {exc.code}') from None
    except urllib.error.URLError:
        # Never expose URLs, proxy details, or connection diagnostics in public logs.
        raise RuntimeError('Jules API network error') from None
    except TimeoutError:
        raise RuntimeError('Jules API timeout') from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise RuntimeError('Jules API invalid JSON response') from None

def read(session, output):
    info = api(f'/sessions/{session}')
    activities=[]; token=None
    for _ in range(20):
        query = {'pageSize':'100'}
        if token: query['pageToken']=token
        page=api(f'/sessions/{session}/activities?'+urllib.parse.urlencode(query))
        activities.extend(page.get('activities',[]))
        if len(activities)>2000: raise RuntimeError('activity count limit exceeded')
        token=page.get('nextPageToken')
        if not token: break
    else: raise RuntimeError('pagination limit exceeded')
    evidence={'session':info,'activities':activities,'evidence_grade':'raw API response; PASS not independently verified'}
    encoded=json.dumps(evidence,ensure_ascii=False,indent=2).encode('utf-8')
    if len(encoded)>10_000_000: raise RuntimeError('evidence size limit exceeded')
    Path(output).write_bytes(encoded)
    print('Session state:',info.get('state','UNKNOWN'))
    print('Activities:',len(activities))
    print('Evidence SHA-256:',hashlib.sha256(encoded).hexdigest())
    print('Evidence retained locally only:',output)

def send(session, message_file, approved_digest):
    if os.environ.get('CB6_SEND_APPROVED')!='true': raise RuntimeError('SEND approval gate missing')
    data=Path(message_file).read_bytes()
    if not (1 <= len(data) <= 20000): raise RuntimeError('message length invalid')
    digest=hashlib.sha256(data).hexdigest()
    if digest!=approved_digest.lower() or len(approved_digest)!=64: raise RuntimeError('message SHA-256 mismatch')
    prompt=data.decode('utf-8')
    if not prompt.strip(): raise RuntimeError('empty prompt')
    api(f'/sessions/{session}:sendMessage',{'prompt':prompt})
    print('Jules sendMessage accepted. SHA-256:',digest)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('read','send'),required=True)
    p.add_argument('--session',default=DEFAULT_SESSION)
    p.add_argument('--output',default='jules_evidence.json')
    p.add_argument('--message-file')
    p.add_argument('--approved-sha256')
    a=p.parse_args()
    if not a.session.isdigit(): raise RuntimeError('invalid session ID')
    if a.mode=='read': read(a.session,a.output)
    else:
        if not a.message_file or not a.approved_sha256: raise RuntimeError('message and digest required')
        send(a.session,a.message_file,a.approved_sha256)
if __name__=='__main__':
    try: main()
    except (RuntimeError, ValueError, UnicodeError, OSError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        sys.exit(1)
