"""Explicit, reproducible plans. Instructions are context, never arbitrary code."""
from urllib.parse import urlsplit
from backend.url_validator import is_bundled_demo_url

class TestPlanner:
    @staticmethod
    def plan(req):
        url = str(req.url)
        demo = is_bundled_demo_url(url) and urlsplit(url).path == '/demo/assessment.html'
        steps = [dict(action='navigate', target=url, expected='Website opens successfully')]
        limits = []
        def add(action, target='', expected='', value=None):
            steps.append(dict(action=action, target=target, expected=expected, value=value))
        if req.prompt == 'responsive':
            for width in [1280, 768, 390]: add('viewport', expected='No horizontal overflow', value=str(width))
        elif req.prompt == 'navigation':
            add('inspect_navigation', expected='No placeholder links')
            if demo:
                add('click', '#help-link'); add('verify', 'text', 'Assessment help')
        elif req.prompt in {'login', 'forms', 'assessment', 'submission'}:
            if not demo:
                limits.append('Interactive workflows are supported only on the bundled assessment demo. This external site received read-only page and UI checks; its workflow was not verified.')
            elif req.prompt == 'forms':
                add('invalid_form', 'form', 'Empty required fields rejected')
            else:
                add('fill', '#email', value='qa@example.test')
                add('fill', '#password', value='Synthetic123!')
                add('click', '#login-button')
                add('verify', 'text', 'Welcome, QA Candidate')
                if req.prompt != 'login':
                    add('click', '#start-assessment')
                    add('click', '#answer-b')
                    add('click', '#submit-assessment')
                    add('verify', 'text', 'Assessment submitted successfully')
        elif req.prompt == 'custom':
            limits.append('Custom mode performs the baseline UI audit plus supplied expected CSS selectors. Free-form instructions are recorded but are not interpreted as arbitrary browser actions.')
        return steps, limits
