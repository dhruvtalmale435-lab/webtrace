"""Durable run snapshots and indexed issue occurrences; SQLite via SQLAlchemy."""
import hashlib
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, Column, String, JSON, Integer, select, delete
from sqlalchemy.orm import DeclarativeBase, Session

data_dir = Path(os.getenv('WEBTRACE_DATA_DIR', str(Path(__file__).parent)))
data_dir.mkdir(parents=True, exist_ok=True)
engine = create_engine('sqlite:///' + str(data_dir / 'webtrace.db'), connect_args={'check_same_thread': False, 'timeout': 30})
class Base(DeclarativeBase): pass
class Run(Base):
    __tablename__ = 'runs'
    id = Column(String, primary_key=True)
    data = Column(JSON, nullable=False)
class Record(Base):
    __tablename__ = 'run_records'
    id = Column(Integer, primary_key=True)
    run_id = Column(String, index=True)
    kind = Column(String, index=True)
    data = Column(JSON)
class Issue(Base):
    __tablename__ = 'issues'
    id = Column(String, primary_key=True)
    run_id = Column(String, index=True)
    fingerprint = Column(String, index=True)
    data = Column(JSON)
class History(Base):
    __tablename__ = 'issue_status_history'
    id = Column(Integer, primary_key=True)
    issue_id = Column(String, index=True)
    data = Column(JSON)
class SavedTest(Base):
    __tablename__ = 'saved_tests'
    id = Column(String, primary_key=True)
    data = Column(JSON)
Base.metadata.create_all(engine)

def save_run(state):
    with Session(engine) as db:
        db.merge(Run(id=state['run_id'], data=state))
        db.commit()

def load_runs():
    with Session(engine) as db:
        return {r.id: r.data for r in db.scalars(select(Run)).all()}

def finalize(state):
    rid = state['run_id']
    audit = state.get('visual_audit') or {}
    issues = [dict(i) for i in audit.get('issues', [])]
    for step in state['steps']:
        if step['status'] == 'failed':
            issues.append(dict(category='functional', severity='high', description=step['message'], element=step.get('target'), expected=step.get('expected'), actual=step.get('actual',step['message']), screenshot_url=step.get('screenshot_url')))
    for page in state.get('discovery', []):
        if page.get('depth', 0) > 0 and page.get('status') == 'failed':
            issues.append(dict(category='discovery_http', severity='high', description=f"Discovered page returned HTTP {page['http_status']}: {page['url']}", element=page['url'], expected='Page responds without an HTTP error', actual=f"HTTP {page['http_status']}", screenshot_url=page.get('screenshot_url')))
    from backend.agents.diagnostics import explain
    with Session(engine) as db:
        for n, issue in enumerate(issues):
            issue['id'] = f'{rid}-{n}'
            issue['fingerprint'] = hashlib.sha256(f"{state['url']}|{issue['category']}|{issue.get('element')}|{issue['description']}".encode()).hexdigest()
            issue['priority'] = 'P1' if issue['severity'] == 'high' else 'P2' if issue['severity'] == 'medium' else 'P3'
            issue['status'] = 'open'
            issue['analysis'] = explain(issue)
            issue['screenshot_url'] = issue.get('screenshot_url') or audit.get('annotated_screenshot_url')
            issue['reproduction_steps'] = [f"Open {state['url']}"]
            if issue['category'] == 'functional':
                for step in state.get('plan', [])[1:]:
                    issue['reproduction_steps'].append(f"{step['action'].capitalize()} {step.get('target') or ''}" + (f" with synthetic value {step['value']}" if step.get('value') else '') + (f"; expect {step['expected']}" if step.get('expected') else ''))
            issue['reproduction_steps'].append(f"Inspect {issue.get('element') or issue['category']}: {issue['description']}")
            db.merge(Issue(id=issue['id'], run_id=rid, fingerprint=issue['fingerprint'], data=issue))
        for kind, values in [('step', state['steps']), ('observation', state['logs']), ('discovery', state.get('discovery',[])), ('diagnostic', state.get('diagnostics',[])), ('artifact', [state['artifacts']] if state.get('artifacts') else []), ('screenshot', [s['screenshot_url'] for s in state['steps'] if s.get('screenshot_url')])]:
            for value in values: db.add(Record(run_id=rid, kind=kind, data=value))
        db.commit()
    state['issues'] = issues
    if state.get('summary'):
        state['summary']['issues_total'] = len(issues)
        state['summary']['by_severity'] = dict(Counter(i['severity'] for i in issues))
        state['summary']['by_category'] = dict(Counter(i['category'] for i in issues))
        if issues and state['summary']['verdict'] == 'passed': state['summary']['verdict'] = 'issues_found'
    save_run(state)

def issue_update(iid, changes):
    with Session(engine) as db:
        row = db.get(Issue, iid)
        if not row: return None
        data = dict(row.data)
        before = data['status']
        data.update(changes)
        row.data = data
        db.add(History(issue_id=iid, data={'from': before, 'to': data['status'], 'priority': data['priority'], 'at': datetime.now(timezone.utc).isoformat()}))
        run = db.get(Run, row.run_id)
        snapshot = dict(run.data)
        snapshot['issues'] = [data if i['id'] == iid else i for i in snapshot.get('issues', [])]
        if snapshot.get('visual_audit'):
            snapshot['visual_audit']['issues'] = [data if i['id'] == iid else i for i in snapshot['visual_audit'].get('issues', [])]
        run.data = snapshot
        db.commit()
        return row.run_id, snapshot

def recurring():
    groups = {}
    with Session(engine) as db:
        for row in db.scalars(select(Issue)).all():
            group = groups.setdefault(row.fingerprint, {'description': row.data['description'], 'category': row.data['category'], 'severity': row.data['severity'], 'run_ids': set()})
            group['run_ids'].add(row.run_id)
    return [{**{k:v for k,v in g.items() if k != 'run_ids'}, 'runs': len(g['run_ids'])} for g in groups.values() if len(g['run_ids']) > 1]
