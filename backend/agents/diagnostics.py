"""Capture bounded real browser diagnostics without request bodies or headers."""
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

def safe_url(url):
    p = urlsplit(url)
    query = [(k, '[redacted]' if any(s in k.lower() for s in ('token','password','secret','auth','session','key')) else v) for k,v in parse_qsl(p.query, keep_blank_values=True)]
    return urlunsplit((p.scheme, p.netloc.split('@')[-1], p.path, urlencode(query), ''))

class BrowserDiagnostics:
    def __init__(self, record):
        self.record = record

    def emit(self, kind, **fields):
        self.record({'kind':kind,'at':datetime.now(timezone.utc).isoformat(), **fields})

    def attach(self, context):
        def page_open(page):
            page.on('console', lambda message: self.emit('console', level=message.type, message=message.text[:1200], url=safe_url(page.url)) if message.type in {'error','warning'} else None)
            page.on('pageerror', lambda error: self.emit('javascript', level='error', message=str(error)[:1200], url=safe_url(page.url)))
        context.on('page', page_open)
        context.on('response', lambda response: self.emit('http', level='error', status=response.status, method=response.request.method, url=safe_url(response.url)) if response.status >= 400 else None)
        context.on('requestfailed', lambda request: self.emit('network', level='error', message=(request.failure or 'Request failed')[:500], method=request.method, url=safe_url(request.url)))

GUIDANCE = {
    'broken_image': ('A requested image did not render.', 'Check the image URL, file deployment, response status and content type.'),
    'empty_button': ('A visible button has no accessible name.', 'Add visible button text or a descriptive aria-label.'),
    'horizontal_overflow': ('Content extends past the viewport.', 'Inspect fixed widths, min-width, long text and flex/grid shrinking at the failing viewport.'),
    'javascript_error': ('The browser raised an uncaught JavaScript error.', 'Inspect the recorded error and trace; correct the failing script before retesting.'),
    'page_http_error': ('The page returned an HTTP error.', 'Inspect the server route, authorization and server logs.'),
    'discovery_http': ('A discovered page returned an HTTP error.', 'Fix the destination or update the link; inspect its HTTP status and screenshot.'),
}

def explain(issue):
    category = issue['category']
    description = issue['description']
    if category == 'functional':
        if 'horizontal overflow' in description:
            cause, fix = GUIDANCE['horizontal_overflow']
        elif 'empty required fields' in description:
            cause, fix = 'The form permits empty required inputs.', 'Add required constraints and validate again on the server.'
        elif 'placeholder destinations' in description:
            cause, fix = 'Navigation contains placeholder destinations.', 'Replace placeholder href values with working authorized destinations.'
        else:
            cause, fix = 'The observed behavior did not satisfy the expected result.', 'Compare expected and actual results, then inspect the screenshot, console/network events and trace.'
    else:
        cause, fix = GUIDANCE.get(category, ('A browser or DOM check flagged this element.', 'Review its captured evidence and reproduce the check before changing the page.'))
    return {'source':'rule-based guidance', 'possible_cause':cause, 'suggested_fix':fix}
