"""Read-only DOM inventory and bounded same-origin discovery for WebTrace."""
import asyncio
import re
from urllib.parse import urlsplit, urldefrag

def origin(url):
    p = urlsplit(url)
    return p.scheme.lower(), (p.hostname or '').lower(), p.port or (443 if p.scheme == 'https' else 80)

def discovery_target(url, start):
    """Exclude fragments, query variants of the same page, and action-like links."""
    p, base = urlsplit(url), urlsplit(start)
    if p.scheme not in {'http', 'https'} or p.username or p.password or origin(url) != origin(start):
        return None
    if p.path == base.path:
        return None
    if re.search(r'(?:^|[/_.-])(logout|signout|delete|remove|unsubscribe|checkout|payment|purchase|submit|confirm)(?:$|[/_.-])', p.path, re.I):
        return None
    if p.query:  # Query links can trigger actions even with GET.
        return None
    return urldefrag(url)[0]

async def inspect_page(page):
    return await page.evaluate('''() => {
      const selector = e => e.id ? '#' + CSS.escape(e.id) :
        e.getAttribute('name') ? e.tagName.toLowerCase()+'[name='+JSON.stringify(e.getAttribute('name'))+']' : null;
      const fields = [...document.querySelectorAll('input:not([type=hidden]),select,textarea')].slice(0,60).map(e => ({
        selector: selector(e), type: e.type || e.tagName.toLowerCase(),
        label: (e.labels?.[0]?.innerText || e.getAttribute('aria-label') || e.getAttribute('placeholder') || '').slice(0,120),
        required: e.required, visible: e.getClientRects().length > 0
      }));
      const anchors = [...document.querySelectorAll('a[href]')];
      return {title:document.title, links:anchors.length, forms:document.forms.length,
        inputs:fields.length, fields, headings:[...document.querySelectorAll('h1,h2')].slice(0,15).map(e=>e.innerText.slice(0,160)),
        link_targets:anchors.slice(0,100).map(e=>({url:e.href,text:e.innerText.slice(0,100)}))};
    }''')

async def discover(context, first_page, start_url, max_pages, depth, check_url, screenshot_dir, run_id, on_page, first_status=None):
    queue = [(start_url, 0)]
    seen = {urldefrag(start_url)[0]}
    results = []
    while queue and len(results) < max_pages:
        url, level = queue.pop(0)
        page = first_page if not results else await context.new_page()
        record = {'url': url, 'depth':level}
        try:
            await asyncio.to_thread(check_url, url)
            if results:
                response = await page.goto(url, wait_until='domcontentloaded', timeout=12000)
                record['http_status'] = response.status if response else None
            else:
                record['http_status'] = first_status
            if origin(page.url) != origin(start_url):
                raise ValueError('Discovery redirected outside the authorized origin')
            inventory = await inspect_page(page)
            record.update(inventory, final_url=page.url, status='failed' if (record['http_status'] or 200) >= 400 else 'visited')
            path = screenshot_dir / f'{run_id}_discovery_{len(results)+1}.png'
            await page.screenshot(path=str(path), full_page=False)
            record['screenshot_url'] = '/screenshots/' + path.name
            if level < depth:
                for anchor in inventory['link_targets']:
                    target = discovery_target(anchor['url'], start_url)
                    if target and target not in seen and len(seen) < 30:
                        seen.add(target)
                        queue.append((target, level+1))
        except Exception as exc:
            record.update(status='blocked' if isinstance(exc, ValueError) else 'error', error=str(exc).splitlines()[0][:200])
        finally:
            if page is not first_page:
                await page.close()
        results.append(record)
        on_page(record)
    return results
