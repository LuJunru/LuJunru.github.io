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
PROFILE_VERSION = '20261110-compact'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.papers = []
        self.language_switch = None
        self.lang = None
        self.earlier_notes = []
        self.portraits = []
        self.og_images = []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == 'html':
            self.lang = data.get('lang')
        if tag == 'img' and urlsplit(data.get('src', '')).path == '/assets/portrait.jpg':
            self.portraits.append(data['src'])
        if tag == 'meta' and data.get('property') == 'og:image':
            self.og_images.append(data.get('content'))
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
official_code_urls = {
    'https://github.com/TencentCloudADP/youtu-tip/tree/master/youtu-llm',
    'https://github.com/TencentCloudADP/youtu-tip',
    'https://github.com/TencentCloudADP/youtu-vl',
}
assert all(item.get('label_zh') and (item['url'].startswith(('https://huggingface.co/', 'https://arxiv.org/')) or item['url'] in official_code_urls) for model in open_models for item in model['links']), '模型链接必须指向模型卡、论文或指定官方代码'
models_by_name = {model['name']: model for model in open_models}
llm_links = {item['url'] for item in models_by_name['Youtu-LLM-2B']['links']}
vl_links = {item['url'] for item in models_by_name['Youtu-VL-4B']['links']}
assert {'https://huggingface.co/tencent/Youtu-LLM-2B/tree/GGUF', 'https://github.com/TencentCloudADP/youtu-tip/tree/master/youtu-llm', 'https://github.com/TencentCloudADP/youtu-tip'} <= llm_links, '缺少 Youtu-LLM 的 GGUF、代码或部署入口'
assert {'https://github.com/TencentCloudADP/youtu-vl', 'https://github.com/TencentCloudADP/youtu-tip'} <= vl_links, '缺少 Youtu-VL 的代码或部署入口'
pretraining_scales = ('2B', '4B', '30B-A3B', '32B-A4B', '120B-A7B', '640B-A31B')
for lang in ('en', 'zh'):
    assert all(value in translations[lang]['career_summary'] for value in ('31B',) + pretraining_scales), '工作经历缺少已确认的预训练模型系列'
    duties = translations[lang]['career_responsibilities']
    assert len(duties) == 5 and len({item['label'] for item in duties}) == 5, '五条核心研发职责缺失或重复'
    assert all(term in duties[0]['text'] for term in ('20TB+', '5TB+')), '文本或多模态数据规模口径缺失'
    assert all(item['label'] and item['text'] for item in duties), '研发职责正文缺失'
    assert '440B' not in translations[lang]['career_summary'], '工作经历仍包含旧模型规模'
assert 'core member of youtu' in translations['en']['career_summary'].lower(), '英文工作经历未说明团队核心研发定位'
assert '团队核心研发' in translations['zh']['career_summary'], '中文工作经历未说明团队核心研发定位'
en_duties = translations['en']['career_responsibilities']
zh_duties = translations['zh']['career_responsibilities']
assert all(term in en_duties[1]['text'] for term in ('decisions', 'sparse-attention', 'native multimodal')), '英文架构职责未对齐定稿简历'
assert all(term in zh_duties[1]['text'] for term in ('决策', '稀疏注意力', '原生多模态')), '中文架构职责未对齐定稿简历'
assert all(term in en_duties[2]['text'] for term in ('Contributed', 'FP8', 'co-designed', 'LightningMoBA')), '英文算子职责未对齐定稿简历'
assert all(term in zh_duties[2]['text'] for term in ('参与研发', 'FP8', 'co-design', 'LightningMoBA')), '中文算子职责未对齐定稿简历'
assert all(term in en_duties[3]['text'] for term in ('downstream metrics', 'model health', 'training stability')), '英文缺少三维训练监控'
assert all(term in zh_duties[3]['text'] for term in ('下游指标', '模型健康度', '训练稳定性')), '中文缺少三维训练监控'
assert all(term in en_duties[4]['text'] for term in ('automated', 'long-context', 'agentic', 'benchmarks')), '英文评测职责未对齐定稿简历'
assert all(term in zh_duties[4]['text'] for term in ('自动化', '长上下文', 'Agentic', '评测基准')), '中文评测职责未对齐定稿简历'
for lang in ('en', 'zh'):
    compact = translations[lang]['career_highlights']
    assert len(compact) == 5, '主页摘要必须保留五条研发主线'
    assert sum(len(item['text']) for item in compact) < sum(len(item['text']) for item in translations[lang]['career_responsibilities']) * 0.6, '主页摘要未明显缩短'
    assert all(term in compact[0]['text'] for term in ('20TB+', '5TB+')), '主页摘要丢失两类语料规模'
    assert 'LightningMoBA' in compact[2]['text'], '主页摘要丢失新版算子共同设计'
    assert 'agentic' in compact[4]['text'].lower(), '主页摘要丢失Agentic评测'
    assert len(compact[0]['label']) <= 10, '主页摘要标签过长'
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
    assert parser.og_images == [f'https://lujunru.github.io/assets/portrait.jpg?v={PROFILE_VERSION}'], f'头像分享图缺少新缓存版本：{filename}'
    assert all(value == f'/assets/portrait.jpg?v={PROFILE_VERSION}' for value in parser.portraits), f'头像图片缺少新缓存版本：{filename}'
    suffix = filename.removeprefix('zh/').removesuffix('index.html')
    expected_switch = '/' + ('' if is_zh else 'zh/') + suffix
    assert parser.language_switch == expected_switch, f'Wrong language-switch destination: {filename}'
    assert f'/love/?lang={"zh" if is_zh else "en"}' in parser.links, f'Missing discreet counter entry: {filename}'
    if filename in ('blog/index.html', 'zh/blog/index.html'):
        assert '<footer class="site-footer blog-footer">' in contents, f'Blog archive/footer seam changed: {filename}'
    if filename in ('index.html', 'zh/index.html'):
        assert parser.portraits == [f'/assets/portrait.jpg?v={PROFILE_VERSION}'], f'首页头像引用不正确：{filename}'
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
