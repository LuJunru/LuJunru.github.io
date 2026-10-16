#!/usr/bin/env python3
"""Check static links, publication metadata, CV signatures and rebuild stability."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get('id'):
            self.ids.add(data['id'])
        for name in ('href', 'src'):
            if name in data:
                self.links.append(data[name])

site = json.loads((ROOT / 'data/site.json').read_text())
publications = site['publications']
assert len({p['id'] for p in publications}) == len(publications), 'Duplicate publication id'
assert all('Junru Lu' in p['authors'] for p in publications), 'Missing author attribution'
assert all(p['topic'] in site['topics'] for p in publications), 'Unknown topic'
assert all(p.get('links', {}).get('paper', '').startswith('https://') for p in publications), 'Missing publication URL'

files = ['index.html', 'resume/index.html', 'blog/index.html', '404.html']
errors = []
for filename in files:
    path = ROOT / filename
    parser = Links()
    parser.feed(path.read_text())
    for value in parser.links:
        u = urlsplit(value)
        if u.scheme or u.netloc:
            continue
        if not u.path:
            if u.fragment and u.fragment not in parser.ids:
                errors.append((filename, value, 'missing anchor'))
            continue
        target = ROOT / unquote(u.path.lstrip('/')) if u.path.startswith('/') else path.parent / unquote(u.path)
        if target.is_dir():
            target = target / 'index.html'
        if not target.exists():
            errors.append((filename, value, 'missing file'))
        elif u.fragment and target.suffix == '.html':
            other = Links()
            other.feed(target.read_text())
            if u.fragment not in other.ids:
                errors.append((filename, value, 'missing cross-page anchor'))
assert not errors, errors

for language in ('En', 'Zh'):
    pdf = ROOT / f'pdf/{language}_resume.pdf'
    contents = pdf.read_bytes()
    assert contents.startswith(b'%PDF-'), f'Invalid {pdf.name}'
    print(pdf.relative_to(ROOT), 'SHA256', hashlib.sha256(contents).hexdigest())

before = {filename: (ROOT / filename).read_bytes() for filename in files}
subprocess.run([sys.executable, str(ROOT / 'scripts/build.py')], check=True)
assert all((ROOT / filename).read_bytes() == content for filename, content in before.items()), 'Build is not deterministic'
print(f'PASS: {len(publications)} publications, all generated internal links, two fixed PDF paths, deterministic build.')
