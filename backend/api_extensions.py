"""Dashboard, evidence and saved-test routes for the existing execution engine."""
from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend import storage

def register(app, runs, lock, create, Request, evidence_dir, artifact_dir):
    @app.get('/api/tests/{rid}/artifacts/trace')
    def trace(rid: str):
        with lock:
            run = runs.get(rid)
            if not run or not run.get('artifacts', {}).get('trace_url'):
                raise HTTPException(404, 'No trace recorded for this run')
        path = (artifact_dir / (rid + '.zip')).resolve()
        if path.parent != artifact_dir.resolve() or not path.is_file():
            raise HTTPException(404, 'Trace not found')
        return FileResponse(path, media_type='application/zip', filename='webtrace-'+rid+'.zip', headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    @app.get('/api/dashboard')
    def dashboard():
        with lock:
            all_runs = list(runs.values())
            done = [r for r in all_runs if r['status'] == 'completed']
            issues = [i for r in all_runs for i in r.get('issues', [])]
            dates = {}
            for r in all_runs:
                day = r['created_at'][:10]
                row = dates.setdefault(day, {'date': day, 'runs': 0, 'issues': 0})
                row['runs'] += 1
                row['issues'] += len(r.get('issues', []))
            return {'total_runs': len(all_runs), 'completed_runs': len(done), 'issues': len(issues), 'open_issues': sum(i['status'] != 'resolved' for i in issues), 'pass_rate': round(sum((r.get('summary') or {}).get('verdict') == 'passed' for r in done) * 100 / len(done)) if done else 0, 'active': sum(r['status'] in {'queued','running'} for r in all_runs), 'severity': [{'name': k, 'value': v} for k,v in Counter(i['severity'] for i in issues).items()], 'trend': sorted(dates.values(), key=lambda r:r['date'])[-14:], 'recurring': storage.recurring()}

    @app.post('/api/tests/{rid}/rerun')
    def rerun(rid: str):
        if rid not in runs: raise HTTPException(404, 'Run not found')
        return create(Request(**runs[rid]['request']))

    class Change(BaseModel):
        status: str = Field(pattern='^(open|in_progress|resolved|dismissed)$')
        priority: str = Field(pattern='^P[0-3]$')

    @app.patch('/api/issues/{iid}')
    def change(iid: str, body: Change):
        with lock:
            result = storage.issue_update(iid, body.model_dump())
            if not result: raise HTTPException(404, 'Issue not found')
            rid, snapshot = result
            runs[rid] = snapshot
        return {'updated': True}

    @app.get('/api/issues/{iid}/history')
    def history(iid: str):
        with Session(storage.engine) as db:
            return [r.data for r in db.scalars(select(storage.History).where(storage.History.issue_id == iid)).all()]

    @app.get('/screenshots/{filename}')
    def evidence(filename: str):
        with lock:
            permitted = any('/screenshots/' + filename in str(r) for r in runs.values())
        path = (evidence_dir / filename).resolve()
        if not permitted or path.parent != evidence_dir.resolve() or path.suffix != '.png' or not path.is_file():
            raise HTTPException(404, 'Evidence not found')
        return FileResponse(path, headers={'Cache-Control': 'private, max-age=3600', 'X-Content-Type-Options': 'nosniff'})

    @app.get('/api/saved-tests')
    def saved():
        with Session(storage.engine) as db: return [{'id': r.id, **r.data} for r in db.scalars(select(storage.SavedTest)).all()]

    @app.post('/api/saved-tests')
    def save(body: Request):
        with Session(storage.engine) as db:
            rid = str(uuid4())
            db.add(storage.SavedTest(id=rid, data=body.model_dump(mode='json')))
            db.commit()
        return {'id': rid}
