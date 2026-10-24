"""Verify the independently implemented discovery and browser-evidence features."""
import json
import sys
import io
import zipfile
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.verify_core import request, wait, BASE, DEMO
from backend.agents.explorer import discovery_target
from backend.agents.diagnostics import safe_url

def main():
    results = []
    for mode in ['normal','defective']:
        body = {'url':DEMO+mode,'objective':'Verify discovery, traces and diagnostics '+mode,'prompt':'assessment','authorized':True,'crawl_pages':3,'crawl_depth':1,'capture_trace':True}
        run = wait(request('/api/tests',body)['run_id'])
        expected_pages = 2 if mode == 'normal' else 1  # Defective mode intentionally replaces its help link with '#'.
        assert len(run['discovery']) == expected_pages, run['discovery']
        assert all(p['status']=='visited' for p in run['discovery'])
        if mode == 'normal':
            assert any(p['url'].endswith('assessment-help.html') for p in run['discovery'])
        assert any(f['selector']=='#email' for f in run['discovery'][0]['fields'])
        assert 'Synthetic123!' not in json.dumps(run['discovery'])
        for page in run['discovery']:
            with urllib.request.urlopen(BASE+page['screenshot_url']) as image:
                assert image.read(8) == b'\x89PNG\r\n\x1a\n'
        with urllib.request.urlopen(BASE+run['artifacts']['trace_url']) as response:
            data = response.read()
            assert response.headers['Content-Type'].startswith('application/zip')
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            assert any(name.endswith('.trace') for name in archive.namelist())
            assert any(name.endswith('.network') for name in archive.namelist())
        if mode == 'normal':
            assert run['summary']['steps_passed']==9 and not run['issues'], run['issues']
        else:
            assert run['summary']['steps_failed']==1
            assert any(e['kind']=='http' and e['status']==404 and e['url'].endswith('missing.png') for e in run['diagnostics'])
            assert any(e['kind']=='console' for e in run['diagnostics'])
            failure = next(i for i in run['issues'] if i['category']=='functional')
            assert failure['expected']=='Assessment submitted successfully'
            assert failure['actual'].startswith('Not found:')
            assert failure['analysis']['source']=='rule-based guidance'
        results.append({'run_id':run['run_id'],'mode':mode,'pages':len(run['discovery']),'diagnostic_events':len(run['diagnostics']),'trace_bytes':len(data),'steps_passed':run['summary']['steps_passed'],'issues':len(run['issues'])})
        print(json.dumps(results[-1]),flush=True)
    limited = wait(request('/api/tests',{'url':DEMO+'normal','objective':'Verify one-page limit and disabled trace','authorized':True,'crawl_pages':1,'capture_trace':False})['run_id'])
    assert len(limited['discovery'])==1 and not limited['artifacts']
    for rid in ['unknown',limited['run_id']]:
        try:
            urllib.request.urlopen(BASE+'/api/tests/'+rid+'/artifacts/trace')
            raise AssertionError('Unregistered trace was accessible')
        except urllib.error.HTTPError as exc: assert exc.code==404
    for url in ['http://localhost:8000/docs','https://external.example/help','http://127.0.0.1:8000/logout','http://127.0.0.1:8000/help?delete=true']:
        assert discovery_target(url,DEMO+'normal') is None
    assert 'secretvalue' not in safe_url('https://example.com/?api_key=secretvalue&mode=normal')
    from backend import storage
    loaded = storage.load_runs()
    for row in results:
        snapshot = loaded[row['run_id']]
        assert snapshot['artifacts']['trace_url'] and len(snapshot['discovery'])==row['pages']
    output={'checks':'passed','runs':results,'page_limit_run_id':limited['run_id'],'trace_access_checks':2,'discovery_safety_checks':4}
    Path('verification/evidence-results.json').write_text(json.dumps(output,indent=2))
    print('PASS: discovery, DOM inventory, diagnostics, trace ZIPs, guidance, safety and persistence',flush=True)

if __name__=='__main__': main()
