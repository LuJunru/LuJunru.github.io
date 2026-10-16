#!/usr/bin/env python3
"""Build the academic homepage from JSON. Python standard library only.
Run: python3 scripts/build.py. The existing Hexo archive and its URLs stay intact.
"""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))
ESC = html.escape
ARROW = '<span aria-hidden="true">↗</span>'


def link(url, label, cls=""):
    external = url.startswith("https:")
    attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
    return f'<a class="{cls}" href="{ESC(url, quote=True)}"{attrs}>{label}</a>'


def head(title, path="/", desc=None):
    description = desc or DATA["description"]
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ESC(title)}</title><meta name="description" content="{ESC(description, quote=True)}">
<link rel="canonical" href="https://lujunru.github.io{path}">
<meta name="theme-color" content="#f8faf8"><meta property="og:type" content="website">
<meta property="og:title" content="{ESC(title, quote=True)}"><meta property="og:description" content="{ESC(description, quote=True)}">
<meta property="og:url" content="https://lujunru.github.io{path}">
<meta property="og:image" content="https://lujunru.github.io/assets/portrait.jpg">
<meta name="twitter:card" content="summary"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/site.css?v=20261016-writing"><script src="/assets/site.js" defer></script>
<script type="application/ld+json">{json.dumps({'@context': 'https://schema.org', '@type': 'Person', 'name': 'Junru Lu', 'alternateName': '陆俊如', 'url': 'https://lujunru.github.io/', 'jobTitle': 'Foundation Model Researcher', 'affiliation': {'@type': 'Organization', 'name': 'Tencent YouTu Lab'}, 'sameAs': [DATA['scholar'], DATA['github'], DATA['linkedin']]}, ensure_ascii=False)}</script>
</head><body><a class="skip-link" href="#main">Skip to content</a>'''


def nav(active="research"):
    return f'''<header class="site-header"><div class="nav-inner">
<a class="brand" href="/" aria-label="Junru Lu, home"><span class="monogram">jl<span>.</span></span><span class="brand-name">Junru Lu</span></a>
<nav aria-label="Main navigation">
<a href="/#research"{' class="active"' if active == 'research' else ''}>Research</a>
<a href="/#publications">Publications</a><a href="/#experience">Experience</a>
<a href="/blog/"{' class="active"' if active == 'blog' else ''}>Notes</a>
<a class="nav-cv" href="/resume/"{' aria-current="page"' if active == 'cv' else ''}>CV {ARROW}</a>
</nav></div></header>'''


def footer():
    return '''<footer class="site-footer"><div><a class="footer-name" href="/">Junru Lu <span lang="zh-CN">陆俊如</span></a><p>Foundation models · Efficient attention · Agent memory</p></div>
<div class="footer-links"><a href="mailto:junru31415926@gmail.com">Get in touch ↗</a><a href="https://github.com/LuJunru/LuJunru.github.io" target="_blank" rel="noopener noreferrer">Source ↗</a><span>© 2026 Junru Lu</span></div></footer></body></html>'''


def authors_markup(authors):
    return ESC(authors).replace("Junru Lu", '<strong class="own-name">Junru Lu</strong>')


def publication(p):
    links = " ".join(link(v, f'{ESC(k.capitalize())} {ARROW}', 'paper-link') for k, v in p.get("links", {}).items())
    return f'''<article class="publication" data-topic="{ESC(p['topic'])}" data-search="{ESC(' '.join([p['title'], p['authors'], p['venue'], p['topic']]).lower(), quote=True)}">
<div class="pub-year">{p['year']}</div><div class="pub-main"><h3>{ESC(p['title'])}</h3>
<p class="authors">{authors_markup(p['authors'])}</p><div class="pub-meta"><span class="venue">{ESC(p['venue'])}</span><span class="pub-topic">{ESC(DATA['topics'][p['topic']])}</span><div class="paper-links">{links}</div></div></div></article>'''


def diagram(kind):
    # Decorative research motifs, not experimental results or architecture claims.
    if kind == "model":
        shapes = ''.join(f'<rect x="{38+i*52}" y="{30+j*28}" width="38" height="18" rx="4" fill="{["#bad3cc", "#79a99c", "#316d61"][j]}" opacity="{0.48+i*0.10}"/>' for j in range(3) for i in range(4))
        shapes += '<path d="M38 127 H232" stroke="#316d61" stroke-width="1"/><text x="135" y="145" text-anchor="middle" fill="#316d61" font-family="monospace" font-size="11">PRETRAIN · REASON · ACT</text>'
    elif kind == "sparse":
        shapes = ''.join(f'<rect x="{44+i*24}" y="{25+j*24}" width="17" height="17" rx="2" fill="{("#477884" if (i==j or i==0 or i==j-2) else "#dce7e8")}"/>' for j in range(5) for i in range(7))
    else:
        shapes = '<path d="M40 85 H238 M75 85 V42 H185 V85 M130 85 V128 H220 V85" stroke="#9c94b0" stroke-width="1.3" fill="none"/>'
        shapes += ''.join(f'<rect x="{x}" y="{y}" width="35" height="27" rx="6" fill="{c}"/>' for x, y, c in [(34,72,'#d9d5e1'),(92,72,'#b1a7c3'),(150,72,'#7c6d99'),(208,72,'#54456f'),(109,29,'#c7bfd5'),(166,114,'#c7bfd5')])
    return f'<svg viewBox="0 0 270 166" role="img" aria-label="Abstract {kind} research illustration">{shapes}</svg>'


def article_cards():
    cards = []
    for article in sorted(DATA['articles'], key=lambda item: item['date'], reverse=True):
        cards.append(f'''<article class="article-card"><div class="article-meta"><time datetime="{ESC(article['date'])}">{ESC(article['date'])}</time><span>{ESC(article['topic'])}</span></div>
<h3 lang="zh-CN">{link(article['url'], ESC(article['title']))}</h3><p lang="zh-CN">{ESC(article['summary'])}</p>
{link(article['url'], 'Read on Hugging Face ' + ARROW, 'article-link')}</article>''')
    return '<div class="article-grid">' + ''.join(cards) + '</div>'


def homepage():
    socials = ' '.join(link(url, label + ' ' + ARROW, 'social-link') for label, url in [('Email', 'mailto:' + DATA['email']), ('Scholar', DATA['scholar']), ('GitHub', DATA['github']), ('Hugging Face', DATA['huggingface']), ('LinkedIn', DATA['linkedin'])])
    cards = ''
    for i, f in enumerate(DATA['featured'], 1):
        cards += f'''<article class="feature-card {f['kind']}"><div class="feature-art">{diagram(f['kind'])}</div>
<div class="feature-body"><div class="feature-eyebrow"><span>0{i} / {ESC(f['area'])}</span><span>{ESC(f['venue'])}</span></div><h3>{ESC(f['name'])}</h3><p>{ESC(f['summary'])}</p>
{link(f['url'], 'Explore the work ' + ARROW, 'feature-link')}</div></article>'''
    pubs = ''.join(publication(p) for p in DATA['publications'])
    news = ''.join(f'<li><time datetime="{n["date"]}">{ESC(n["label"])}</time><p>{n["html"]}</p></li>' for n in DATA['news'])
    education = ''.join(f'<li><div><h3>{ESC(e["institution"])}</h3><p>{ESC(e["degree"])}</p>{"<small>"+e["advisor"]+"</small>" if e.get("advisor") else ""}</div><span>{ESC(e["dates"])}</span></li>' for e in DATA['education'])
    filters = ''.join(f'<button type="button" class="filter-button" data-filter="{k}" aria-pressed="false">{ESC(v)}</button>' for k,v in DATA['topics'].items())
    return head('Junru Lu | Foundation Model Researcher') + nav() + f'''<main id="main" class="page-shell">
<section class="hero" id="about" aria-labelledby="hero-title"><div class="hero-copy"><p class="eyebrow"><span class="status-dot"></span> TENCENT YOUTU LAB · SHANGHAI</p>
<h1 id="hero-title">Junru Lu<span class="chinese-name" lang="zh-CN">陆俊如</span></h1><p class="hero-role">Foundation Model Researcher</p>
<p class="hero-lead">I work on <strong>foundation models</strong>, <strong>efficient attention</strong>, and <strong>memory for long-horizon agents</strong>.</p>
<p class="hero-bio">My research spans model architecture, pre-training, post-training, and evaluation. I received my Ph.D. in Computer Science from the <a href="https://warwick.ac.uk/fac/sci/dcs/" target="_blank" rel="noopener noreferrer">University of Warwick</a>, advised by <a href="https://sites.google.com/view/yulanhe/home" target="_blank" rel="noopener noreferrer">Prof. Yulan He</a>.</p>
<div class="social-links">{socials}</div><div class="hero-cv"><span>Curriculum vitae</span><a href="/pdf/En_resume.pdf">English {ARROW}</a><span class="cv-separator">/</span><a href="/pdf/Zh_resume.pdf" lang="zh-CN">中文 {ARROW}</a></div></div>
<figure class="portrait-block"><div class="portrait-frame"><img src="/assets/portrait.jpg" width="420" height="560" alt="Portrait of Junru Lu" fetchpriority="high"></div><figcaption>Junru Lu <span>陆俊如</span><span class="portrait-rule"></span>Researcher, Tencent</figcaption></figure></section>
<section id="research" class="research-section"><div class="section-heading"><div><p class="eyebrow">01 / RESEARCH</p><h2>Selected work</h2></div><p>From training models<br>to making them more efficient.</p></div><div class="feature-grid">{cards}</div></section>
<section class="updates-section"><div class="section-heading compact"><h2>Recent updates</h2><span class="section-note">Public releases & research</span></div><ul class="news-list">{news}</ul></section>
<section id="writing" class="writing-section"><div class="section-heading"><div><p class="eyebrow">WRITING / TECHNICAL ESSAYS</p><h2>Ideas, beyond the paper.</h2></div><a class="text-link" href="/blog/">All writing & notes {ARROW}</a></div>{article_cards()}</section>
<section id="publications" class="publications-section"><div class="section-heading"><div><p class="eyebrow">02 / PUBLICATIONS</p><h2>Papers & technical reports</h2></div>{link(DATA['scholar'], 'Full list on Scholar ' + ARROW, 'text-link')}</div>
<div class="publication-tools" hidden><div class="filters" role="group" aria-label="Filter publications"><button class="filter-button selected" type="button" data-filter="all" aria-pressed="true">All work</button>{filters}</div><label class="search-box"><span class="search-icon" aria-hidden="true">⌕</span><span class="sr-only">Search publications by title, author, or venue</span><input id="paper-search" type="search" placeholder="Search papers…" autocomplete="off"></label></div>
<p id="pub-count" class="pub-count" aria-live="polite">{len(DATA['publications'])} selected publications</p><div id="publication-list">{pubs}</div><p id="empty-state" hidden>No matching publications. Try another title, author, or topic.</p></section>
<section id="experience" class="experience-section"><div class="section-heading"><div><p class="eyebrow">03 / BACKGROUND</p><h2>Experience & education</h2></div><a class="text-link" href="/resume/">View my CV {ARROW}</a></div>
<div class="background-grid"><div class="career-block"><p class="mini-heading">EXPERIENCE</p><h3>Tencent YouTu Lab</h3><p class="role">Foundation Model Researcher</p><p class="muted">May 2023 – present · Shanghai, China</p><p>Pre-training data pipelines, sparse attention and native multimodal architectures, GPU-aware acceleration kernels, large-scale MoE training, and model evaluation.</p><div class="research-tags"><span>LLM / MLLM</span><span>Sparse attention</span><span>Agent memory</span></div></div>
<div class="education-block"><p class="mini-heading">EDUCATION</p><ul>{education}</ul></div></div></section>
<section class="notes-teaser"><div><p class="eyebrow">RESEARCH NOTES</p><h2>A notebook, not a newsfeed.</h2><p>Earlier notes on NLP, question answering, algorithms, and learning.</p></div><a class="outline-button" href="/blog/">Browse the archive {ARROW}</a></section>
</main>''' + footer()


def cvpage():
    return head('Curriculum Vitae | Junru Lu', '/resume/') + nav('cv') + '''<main id="main" class="page-shell cv-page"><p class="eyebrow">CURRICULUM VITAE</p><h1>Research, in one page.</h1><p class="page-intro">The same research record, in English and Chinese.</p>
<div class="cv-download-grid"><a class="cv-download" href="/pdf/En_resume.pdf"><span class="mini-heading">ENGLISH · PDF</span><h2>Curriculum vitae</h2><p>Education, experience, and selected publications.</p><span class="feature-link">Open English CV ↗</span></a><a class="cv-download" href="/pdf/Zh_resume.pdf"><span class="mini-heading">中文 · PDF</span><h2 lang="zh-CN">个人简历</h2><p lang="zh-CN">教育经历、工作经历与代表性论文。</p><span class="feature-link" lang="zh-CN">查看中文简历 ↗</span></a></div>
<div class="cv-preview-heading"><h2>Preview</h2><label for="cv-language">Language <select id="cv-language"><option value="En">English</option><option value="Zh">中文</option></select></label></div><iframe id="cv-preview" class="cv-preview" title="English curriculum vitae PDF" src="/pdf/En_resume.pdf#view=FitH"></iframe><p class="muted">If the preview is unavailable, use the PDF links above.</p></main>''' + footer()


def blogpage():
    items = []
    for y in ('2019', '2018', '2017'):
        for p in (ROOT / y).rglob('index.html'):
            s = p.read_text(encoding='utf-8')
            m = re.search(r'<title>(.*?)</title>', s)
            title = html.unescape(m.group(1)).rsplit(' | ', 1)[0] if m else p.parent.name
            date = '-'.join(p.relative_to(ROOT).parts[:3])
            items.append((date, '/' + str(p.parent.relative_to(ROOT)) + '/', title))
    items.sort(reverse=True)
    rows = ''.join(f'<article class="note-row"><time>{date}</time><a href="{ESC(url)}">{ESC(title)} {ARROW}</a></article>' for date, url, title in items)
    return head('Writing & Notes | Junru Lu', '/blog/') + nav('blog') + f'''<main id="main" class="page-shell blog-page"><p class="eyebrow">WRITING & NOTES</p><h1>Research notes.</h1><p class="page-intro">Technical essays on model memory, efficient attention, and preference optimization, alongside an archive of earlier reading notes and projects.</p>
<section class="blog-writing" aria-labelledby="essays-heading"><div class="section-heading"><h2 id="essays-heading">Technical essays</h2>{link(DATA['articles_url'], 'On Hugging Face ' + ARROW, 'text-link')}</div>{article_cards()}</section>
<section aria-labelledby="archive-heading"><div class="section-heading"><h2 id="archive-heading">Earlier notes</h2><span class="section-note">2017–2019 · Original URLs preserved</span></div><div class="notes-list">{rows}</div></section><a class="text-link" href="/about/">Personal notes from the archive {ARROW}</a></main>''' + footer()


def build():
    (ROOT / 'index.html').write_text(homepage(), encoding='utf-8')
    (ROOT / 'resume/index.html').write_text(cvpage(), encoding='utf-8')
    (ROOT / 'blog/index.html').write_text(blogpage(), encoding='utf-8')
    (ROOT / '404.html').write_text(head('Page not found | Junru Lu', '/404.html') + nav() + '<main id="main" class="page-shell error-page"><p class="eyebrow">404 / PAGE NOT FOUND</p><h1>A little off the path.</h1><p>The page may have moved. The research homepage and the notes archive are below.</p><a class="outline-button" href="/">Back to research ↗</a> <a class="text-link" href="/blog/">Browse notes ↗</a></main>' + footer(), encoding='utf-8')
    # Scope visual refresh to legacy pages without changing any article text.
    marker = '<link rel="stylesheet" href="/assets/legacy.css?v=20261016">'
    old_marker = '<link rel="stylesheet" href="/assets/legacy.css">'
    changed = 0
    for base in ('2017','2018','2019','about','archives','categories','tags','page'):
        for path in (ROOT / base).rglob('*.html'):
            s = path.read_text(encoding='utf-8')
            if 'theme-next' not in s or marker in s:
                continue
            if old_marker in s:
                path.write_text(s.replace(old_marker, marker), encoding='utf-8')
                changed += 1
                continue
            s = s.replace('</head>', marker + '</head>', 1)
            s = re.sub(r'(<body\b[^>]*>)', lambda m: m[1] + '<div class="legacy-topbar"><a href="/">Junru Lu</a><nav><a href="/">Research</a><a href="/blog/">Notes archive</a><a href="/resume/">CV ↗</a></nav></div>', s, count=1)
            s = s.replace('http://yoursite.com/', 'https://lujunru.github.io/')
            path.write_text(s, encoding='utf-8')
            changed += 1
    print(f'Built homepage, CV, notebook, 404; {len(DATA["publications"])} publications; {changed} legacy pages refreshed.')

if __name__ == '__main__':
    build()
