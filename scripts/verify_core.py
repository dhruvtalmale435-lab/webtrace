"""Integration verification against a running backend. Generates REAL persisted tests."""
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE = 'http://127.0.0.1:8000'
DEMO = BASE + '/demo/assessment.html?mode='

def request(path, data=None, method=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode() if data is not None else None, headers={'Content-Type':'application/json'}, method=method)
    deadline = time.monotonic() + 150
    while True:
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or time.monotonic() >= deadline:
                raise
            time.sleep(.5)

def wait(rid):
    deadline = time.monotonic() + 140
    while time.monotonic() < deadline:
        run = request('/api/tests/' + rid)
        if run['status'] not in {'running','queued'}:
            assert run['status'] == 'completed', run.get('error')
            return run
        time.sleep(.5)
    raise AssertionError('Run exceeded deadline')

def main():
    results = []
    for prompt in ['assessment', 'forms', 'responsive', 'navigation', 'login', 'custom']:
        pair = []
        for mode in ['normal','defective']:
            body = {'url': DEMO+mode, 'objective': f'Integration verification: {prompt} / {mode}', 'prompt': prompt, 'authorized': True}
            if prompt == 'custom': body['expected_selectors'] = ['h1', '#login-button']
            pair.append((mode, request('/api/tests', body)['run_id']))
        for mode, rid in pair:
            run = wait(rid)
            failed = run['summary']['steps_failed']
            if mode == 'normal':
                assert failed == 0, run['steps']
                assert not run['issues'], run['issues']
            if mode == 'defective' and prompt in {'assessment','forms','responsive','navigation'}:
                assert failed > 0, 'Expected a planted defect'
            if mode == 'defective':
                cats = {i['category'] for i in run['issues']}
                assert {'broken_image','empty_button'}.issubset(cats), cats
                evidence = run['issues'][0]['screenshot_url']
                with urllib.request.urlopen(BASE+evidence) as image:
                    assert image.read(8) == b'\x89PNG\r\n\x1a\n'
            item = {'run_id':rid,'prompt':prompt,'mode':mode,'passed_steps':run['summary']['steps_passed'],'total_steps':run['summary']['steps_total'],'issues':len(run['issues']),'duration_seconds':run['duration_seconds']}
            results.append(item)
            print(json.dumps(item),flush=True)
    first = results[1]['run_id']
    rerun = wait(request('/api/tests/'+first+'/rerun',{})['run_id'])
    assert rerun['run_id'] != first
    assert request('/api/tests/'+first)['run_id'] == first
    dashboard = request('/api/dashboard')
    assert any(r['runs'] >= 2 for r in dashboard['recurring'])
    issue = rerun['issues'][0]
    request('/api/issues/'+issue['id'], {'status':'in_progress','priority':'P0'}, 'PATCH')
    changed = request('/api/tests/'+rerun['run_id'])['issues'][0]
    assert changed['status'] == 'in_progress' and changed['priority'] == 'P0'
    assert request('/api/issues/'+issue['id']+'/history')[-1]['to'] == 'in_progress'
    for url in ['http://127.0.0.1:8000/docs','http://169.254.169.254/','http://[::1]/','http://localhost:8000/demo/../docs','http://user:pass@127.0.0.1:8000/demo/assessment.html']:
        try:
            request('/api/tests',{'url':url,'objective':'Check unsafe URL rejection','authorized':True})
            raise AssertionError('Unsafe URL was accepted: '+url)
        except urllib.error.HTTPError as exc: assert exc.code in {400,422}, exc
    try:
        urllib.request.urlopen(BASE+'/screenshots/not-a-registered-evidence.png')
        raise AssertionError('Unknown evidence accessible')
    except urllib.error.HTTPError as exc: assert exc.code == 404
    output = {'checks':'passed', 'runs':results,'rerun_id':rerun['run_id'],'recurring_patterns':len(dashboard['recurring']),'security_checks':6}
    Path('verification').mkdir(exist_ok=True)
    Path('verification/core-results.json').write_text(json.dumps(output,indent=2))
    print('PASS: real browser checks, screenshots, rerun, recurrence, status history and URL security',flush=True)

if __name__ == '__main__': main()
