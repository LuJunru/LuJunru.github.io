#!/usr/bin/env python3
"""Check bilingual routes, source coverage, internal links and deterministic build."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.papers = []
        self.language_switch = None
        self.lang = None
        self.earlier_notes = []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == 'html':
            self.lang = data.get('lang')
        if data.get('id'):
            assert data['id'] not in self.ids, f'Duplicate HTML id: {data["id"]}'
            self.ids.add(data['id'])
        if tag == 'details' and 'earlier-notes' in data.get('class', '').split():
            self.earlier_notes.append('open' in data)
        if data.get('data-arxiv'):
            self.papers.append(data['data-arxiv'])
        if 'language-switch' in data.get('class', '').split():
            self.language_switch = data.get('href')
        for name in ('href', 'src'):
            if name in data:
                self.links.append(data[name])

site = json.loads((ROOT / 'data/site.json').read_text())
translations = json.loads((ROOT / 'data/i18n.json').read_text())
assert translations['en'].keys() == translations['zh'].keys(), 'Incomplete translation keys'
for nested in ('topics', 'link_labels', 'venues', 'article_topics'):
    assert translations['en'][nested].keys() == translations['zh'][nested].keys(), f'Incomplete translations: {nested}'
for key in ('featured', 'education', 'news'):
    for item in site[key]:
        expected = {'featured': ('area', 'summary'), 'education': ('institution', 'degree'), 'news': ('label', 'html')}[key]
        assert all(item.get(field + '_zh') for field in expected), f'Missing Chinese content in {key}'
publications = site['publications']
assert len({p['id'] for p in publications}) == len(publications), 'Duplicate publication id'
assert len({p['arxiv_id'] for p in publications}) == len(publications), 'Duplicate arXiv work'
hf_source_ids = set(site['papers_source_ids'])
additional_verified_ids = set(site.get('papers_additional_verified_ids', []))
assert hf_source_ids.isdisjoint(additional_verified_ids), 'Duplicate HF and externally verified paper IDs'
assert set(p['arxiv_id'] for p in publications) == hf_source_ids | additional_verified_ids, 'Incomplete authored-paper coverage'
assert all('Junru Lu' in p['authors'] for p in publications), 'Missing author attribution'
assert all(p['topic'] in site['topics'] for p in publications), 'Unknown topic'
assert all(p.get('links', {}).get('paper', '').startswith('https://') for p in publications), 'Missing publication URL'
assert all(re.fullmatch(r'\d{4}\.\d{4,5}', p['arxiv_id']) for p in publications), 'Invalid arXiv identifier'
open_models = site['open_models']
assert {model['name'] for model in open_models} == {'Youtu-LLM-2B', 'Youtu-VL-4B', 'Youtu-LLM-A7B-Base'}, 'Unexpected model set'
assert all(model.get('variant_zh') and model.get('summary_zh') and model.get('links') for model in open_models), 'Missing model translation or links'
assert all(item.get('label_zh') and item['url'].startswith(('https://huggingface.co/', 'https://arxiv.org/')) for model in open_models for item in model['links']), 'Invalid open-model link'
archive_css = (ROOT / 'assets/site.css').read_text()
assert '.home-archive{margin:48px 0 0}' in archive_css, 'Home archive adds an empty row before the footer'
assert '.site-footer.home-footer{border-top:0}' in archive_css, 'Home footer draws a duplicate separator'
assert '.home-archive{margin:32px 0 0}' in archive_css, 'Mobile archive adds an empty row before the footer'
assert '.blog-page{padding-bottom:0}' in archive_css, 'Blog archive adds an empty row before the footer'
assert '.site-footer.blog-footer{border-top:0}' in archive_css, 'Blog footer draws a duplicate separator'
articles = site['articles']
assert len({a['url'] for a in articles}) == len(articles), 'Duplicate article URL'
assert all(a['url'].startswith('https://huggingface.co/blog/Junrulu/') for a in articles), 'Unexpected article URL'

base_files = ['index.html', 'resume/index.html', 'blog/index.html', '404.html']
files = base_files + ['zh/' + filename for filename in base_files]
errors = []
for filename in files:
    path = ROOT / filename
    parser = Links()
    contents = path.read_text()
    parser.feed(contents)
    is_zh = filename.startswith('zh/')
    assert parser.lang == ('zh-CN' if is_zh else 'en'), f'Wrong page language: {filename}'
    suffix = filename.removeprefix('zh/').removesuffix('index.html')
    expected_switch = '/' + ('' if is_zh else 'zh/') + suffix
    assert parser.language_switch == expected_switch, f'Wrong language-switch destination: {filename}'
    assert f'/love/?lang={"zh" if is_zh else "en"}' in parser.links, f'Missing discreet counter entry: {filename}'
    if filename in ('blog/index.html', 'zh/blog/index.html'):
        assert '<footer class="site-footer blog-footer">' in contents, f'Blog archive/footer seam changed: {filename}'
    if filename in ('index.html', 'zh/index.html'):
        assert '<footer class="site-footer home-footer">' in contents, f'Home archive/footer seam changed: {filename}'
        assert set(parser.papers) == hf_source_ids | additional_verified_ids and len(parser.papers) == len(publications), f'Missing or duplicate papers: {filename}'
        assert site['linkedin'] in parser.links, f'Missing LinkedIn: {filename}'
        assert contents.count('class="model-card"') == len(open_models), f'Missing open-model cards: {filename}'
        assert 'id="open-models"' in contents, f'Missing open-model section: {filename}'
        for model in open_models:
            for model_link in model['links']:
                assert model_link['url'] in parser.links, f'Missing model release link: {filename}: {model["name"]}'
        for code in ('En', 'Zh'):
            assert f'/pdf/{code}_resume.pdf' in parser.links, f'CV path changed: {filename}'
    if filename.endswith('index.html') and 'resume' not in filename:
        assert all(a['url'] in parser.links and a['title'] in contents for a in articles), f'Missing article in {filename}'
        assert parser.earlier_notes == [False], f'Earlier notes must be collapsed by default: {filename}'
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

love_html = (ROOT / 'love/index.html').read_text()
love = Links()
love.feed(love_html)
assert 'noindex, nofollow, noarchive' in love_html, 'Counter page should not be indexed'
assert 'data-start="2016-12-31T10:00:00+08:00"' in love_html, 'Original counter date changed'
assert {'d', 'h', 'm', 's'} <= love.ids, 'Missing counter units'
for value in love.links:
    parsed = urlsplit(value)
    if not parsed.scheme and not value.startswith('/'):
        assert (ROOT / 'love' / unquote(parsed.path)).is_file(), f'Missing counter resource: {value}'
background = (ROOT / 'love/assets/bg.jpg').read_bytes()
assert background[:2] == b'\xff\xd8' and background[-2:] == b'\xff\xd9', 'Incomplete counter background'
assert b'Exif\x00\x00' not in background, 'Counter photo must not expose EXIF metadata'

pdfs = {}
for language in ('En', 'Zh'):
    pdf = ROOT / f'pdf/{language}_resume.pdf'
    pdfs[language] = pdf.read_bytes()
    assert pdfs[language].startswith(b'%PDF-'), f'Invalid {pdf.name}'
    print(pdf.relative_to(ROOT), 'SHA256', hashlib.sha256(pdfs[language]).hexdigest())

before = {filename: (ROOT / filename).read_bytes() for filename in files}
subprocess.run([sys.executable, str(ROOT / 'scripts/build.py')], check=True)
assert all((ROOT / filename).read_bytes() == content for filename, content in before.items()), 'Build is not deterministic'
assert all((ROOT / f'pdf/{code}_resume.pdf').read_bytes() == contents for code, contents in pdfs.items()), 'Build modified a CV'
print(f'PASS: {len(files)} bilingual pages, {len(publications)} authored papers, {len(articles)} articles, language links, fixed CV paths, deterministic build.')
