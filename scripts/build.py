#!/usr/bin/env python3
"""Build both languages from shared JSON; standard library only.
English is the default URL. /zh/ is explicit, with no locale auto-redirect.
Existing Hexo archive paths and the two CV PDF files remain unchanged.
"""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))
I18N = json.loads((ROOT / "data/i18n.json").read_text(encoding="utf-8"))
ESC = html.escape
ARROW = '<span aria-hidden="true">↗</span>'
ASSET_VERSION = "20261019-blog-archive"


def route(path="/", lang="en"):
    return ("/zh" if lang == "zh" else "") + path


def localized(item, key, lang):
    return item.get(key + "_zh", item.get(key, "")) if lang == "zh" else item.get(key, "")


def link(url, label, cls=""):
    attrs = ' target="_blank" rel="noopener noreferrer"' if url.startswith("https:") else ""
    return f'<a class="{cls}" href="{ESC(url, quote=True)}"{attrs}>{label}</a>'


def head(title, path="/", lang="en"):
    text = I18N[lang]
    description = text["description"]
    url = "https://lujunru.github.io" + route(path, lang)
    person = {"@context": "https://schema.org", "@type": "Person", "name": "Junru Lu", "alternateName": "陆俊如", "url": "https://lujunru.github.io/", "jobTitle": "Foundation Model Researcher", "affiliation": {"@type": "Organization", "name": "Tencent YouTu Lab"}, "sameAs": [DATA["scholar"], DATA["github"], DATA["linkedin"]]}
    return f'''<!doctype html>
<html lang="{text['language']}" data-language="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ESC(title)}</title><meta name="description" content="{ESC(description, quote=True)}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="https://lujunru.github.io{route(path, 'en')}">
<link rel="alternate" hreflang="zh-CN" href="https://lujunru.github.io{route(path, 'zh')}">
<link rel="alternate" hreflang="x-default" href="https://lujunru.github.io{route(path, 'en')}">
<meta name="theme-color" content="#f8faf8"><meta property="og:type" content="website">
<meta property="og:title" content="{ESC(title, quote=True)}"><meta property="og:description" content="{ESC(description, quote=True)}">
<meta property="og:url" content="{url}"><meta property="og:locale" content="{'zh_CN' if lang == 'zh' else 'en_US'}">
<meta property="og:image" content="https://lujunru.github.io/assets/portrait.jpg">
<meta name="twitter:card" content="summary"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/site.css?v={ASSET_VERSION}"><script src="/assets/site.js?v={ASSET_VERSION}" defer></script>
<script type="application/ld+json">{json.dumps(person, ensure_ascii=False)}</script>
</head><body><a class="skip-link" href="#main">{text['skip']}</a>'''


def nav(active="research", lang="en", page="/"):
    text = I18N[lang]
    other = "en" if lang == "zh" else "zh"
    return f'''<header class="site-header"><div class="nav-inner">
<a class="brand" href="{route('/', lang)}" aria-label="{text['home_label']}"><span class="monogram">jl<span>.</span></span><span class="brand-name">{text['name']}</span></a>
<nav aria-label="{text['navigation']}">
<a href="{route('/', lang)}#research"{' class="active"' if active == 'research' else ''}>{text['research']}</a>
<a href="{route('/', lang)}#publications">{text['publications']}</a><a href="{route('/', lang)}#experience">{text['experience']}</a>
<a href="{route('/blog/', lang)}"{' class="active"' if active == 'blog' else ''}>{text['notes']}</a>
<a class="nav-cv" href="{route('/resume/', lang)}"{' aria-current="page"' if active == 'cv' else ''}>{text['cv']} {ARROW}</a>
<a class="love-entry" href="/love/?lang={lang}" aria-label="{'Our shared days' if lang == 'en' else '我们的日期计时'}" title="{'Our shared days' if lang == 'en' else '我们的日期计时'}"><svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/></svg></a>
<a class="language-switch" href="{route(page, other)}" lang="{I18N[other]['language']}" hreflang="{I18N[other]['language']}" aria-label="{text['switch_label']}">{text['switch_text']}</a>
</nav></div></header>'''


def footer(lang="en", home=False, blog=False):
    text = I18N[lang]
    footer_class = "site-footer home-footer" if home else ("site-footer blog-footer" if blog else "site-footer")
    return f'''<footer class="{footer_class}"><div><a class="footer-name" href="{route('/', lang)}">{text['name']} <span>{text['secondary_name']}</span></a><p>{text['footer_topics']}</p></div>
<div class="footer-links">{link('mailto:' + DATA['email'], text['get_in_touch'] + ' ↗')}{link('https://github.com/LuJunru/LuJunru.github.io', text['source'] + ' ↗')}<span>© 2026 Junru Lu</span></div></footer></body></html>'''


def authors_markup(authors):
    return ESC(authors).replace("Junru Lu", '<strong class="own-name">Junru Lu</strong>')


def publication(p, lang="en"):
    text = I18N[lang]
    links = " ".join(link(v, f'{ESC(text["link_labels"].get(k, k.capitalize()))} {ARROW}', 'paper-link') for k, v in p.get("links", {}).items())
    searchable = ' '.join([p['title'], p['authors'], p['venue'], p['topic'], I18N['en']['topics'][p['topic']], I18N['zh']['topics'][p['topic']]]).lower()
    venue = text['venues'].get(p['venue'], p['venue'])
    return f'''<article class="publication" data-id="{ESC(p['id'])}" data-arxiv="{ESC(p['arxiv_id'])}" data-topic="{ESC(p['topic'])}" data-search="{ESC(searchable, quote=True)}">
<div class="pub-year">{p['year']}</div><div class="pub-main"><h3 lang="en">{ESC(p['title'])}</h3>
<p class="authors" lang="en">{authors_markup(p['authors'])}</p><div class="pub-meta"><span class="venue">{ESC(venue)}</span><span class="pub-topic">{ESC(text['topics'][p['topic']])}</span><div class="paper-links">{links}</div></div></div></article>'''


def diagram(kind):
    # Decorative motifs, not experimental results or architecture claims.
    if kind == "model":
        shapes = ''.join(f'<rect x="{38+i*52}" y="{30+j*28}" width="38" height="18" rx="4" fill="{["#bad3cc", "#79a99c", "#316d61"][j]}" opacity="{0.48+i*0.10}"/>' for j in range(3) for i in range(4))
        shapes += '<path d="M38 127 H232" stroke="#316d61" stroke-width="1"/><text x="135" y="145" text-anchor="middle" fill="#316d61" font-family="monospace" font-size="11">PRETRAIN · REASON · ACT</text>'
    elif kind == "sparse":
        shapes = ''.join(f'<rect x="{44+i*24}" y="{25+j*24}" width="17" height="17" rx="2" fill="{("#477884" if (i==j or i==0 or i==j-2) else "#dce7e8")}"/>' for j in range(5) for i in range(7))
    else:
        shapes = '<path d="M40 85 H238 M75 85 V42 H185 V85 M130 85 V128 H220 V85" stroke="#9c94b0" stroke-width="1.3" fill="none"/>'
        shapes += ''.join(f'<rect x="{x}" y="{y}" width="35" height="27" rx="6" fill="{c}"/>' for x, y, c in [(34,72,'#d9d5e1'),(92,72,'#b1a7c3'),(150,72,'#7c6d99'),(208,72,'#54456f'),(109,29,'#c7bfd5'),(166,114,'#c7bfd5')])
    return f'<svg viewBox="0 0 270 166" aria-hidden="true">{shapes}</svg>'


def article_cards(lang="en"):
    text = I18N[lang]
    cards = []
    for article in sorted(DATA['articles'], key=lambda item: item['date'], reverse=True):
        topic = text['article_topics'][article['topic']]
        cards.append(f'''<article class="article-card"><div class="article-meta"><time datetime="{ESC(article['date'])}">{ESC(article['date'])}</time><span>{ESC(topic)}</span></div>
<h3 lang="zh-CN">{link(article['url'], ESC(article['title']))}</h3><p lang="zh-CN">{ESC(article['summary'])}</p>
{link(article['url'], text['read_hf'] + ' ' + ARROW, 'article-link')}</article>''')
    return '<div class="article-grid">' + ''.join(cards) + '</div>'


def homepage(lang="en"):
    text = I18N[lang]
    socials = ' '.join(link(url, label + ' ' + ARROW, 'social-link') for label, url in [(text['email'], 'mailto:' + DATA['email']), (text['scholar'], DATA['scholar']), ('GitHub', DATA['github']), ('Hugging Face', DATA['huggingface']), ('LinkedIn', DATA['linkedin'])])
    cards = ''
    for i, f in enumerate(DATA['featured'], 1):
        cards += f'''<article class="feature-card {f['kind']}"><div class="feature-art">{diagram(f['kind'])}</div>
<div class="feature-body"><div class="feature-eyebrow"><span>0{i} / {ESC(localized(f, 'area', lang))}</span><span>{ESC(text['venues'].get(f['venue'], f['venue']))}</span></div><h3>{ESC(f['name'])}</h3><p>{ESC(localized(f, 'summary', lang))}</p>
{link(f['url'], text['explore'] + ' ' + ARROW, 'feature-link')}</div></article>'''
    pubs = ''.join(publication(p, lang) for p in DATA['publications'])
    news = ''.join(f'<li><time datetime="{n["date"]}">{ESC(localized(n, "label", lang))}</time><p>{localized(n, "html", lang)}</p></li>' for n in DATA['news'])
    education = ''.join(f'<li><div><h3>{ESC(localized(e, "institution", lang))}</h3><p>{ESC(localized(e, "degree", lang))}</p>{"<small>"+localized(e,"advisor",lang)+"</small>" if e.get("advisor") else ""}</div><span>{ESC(e["dates"])}</span></li>' for e in DATA['education'])
    filters = ''.join(f'<button type="button" class="filter-button" data-filter="{k}" aria-pressed="false">{ESC(v)}</button>' for k,v in text['topics'].items())
    tags = ''.join(f'<span>{ESC(tag)}</span>' for tag in text['tags'])
    count = text['count_all'].format(n=len(DATA['publications']))
    return head(text['home_title'], lang=lang) + nav(lang=lang) + f'''<main id="main" class="page-shell">
<section class="hero" id="about" aria-labelledby="hero-title"><div class="hero-copy"><p class="eyebrow"><span class="status-dot"></span> {text['affiliation']}</p>
<h1 id="hero-title">{text['name']}<span class="chinese-name" lang="{'en' if lang == 'zh' else 'zh-CN'}">{text['secondary_name']}</span></h1><p class="hero-role">{text['role']}</p>
<p class="hero-lead">{text['hero_lead']}</p><p class="hero-bio">{text['hero_bio']}</p>
<div class="social-links">{socials}</div><div class="hero-cv"><span>{text['cv_label']}</span><a href="/pdf/En_resume.pdf">English {ARROW}</a><span class="cv-separator">/</span><a href="/pdf/Zh_resume.pdf" lang="zh-CN">中文 {ARROW}</a></div></div>
<figure class="portrait-block"><div class="portrait-frame"><img src="/assets/portrait.jpg" width="420" height="560" alt="{text['portrait_alt']}" fetchpriority="high"></div><figcaption>{text['name']} <span>{text['secondary_name']}</span><span class="portrait-rule"></span>{text['portrait_caption']}</figcaption></figure></section>
<section id="research" class="research-section"><div class="section-heading"><div><p class="eyebrow">{text['research_eyebrow']}</p><h2>{text['selected_work']}</h2></div><p>{text['research_caption']}</p></div><div class="feature-grid">{cards}</div></section>
<section class="updates-section"><div class="section-heading compact"><h2>{text['recent_updates']}</h2><span class="section-note">{text['public_releases']}</span></div><ul class="news-list">{news}</ul></section>
<section id="writing" class="writing-section"><div class="section-heading"><div><p class="eyebrow">{text['writing_eyebrow']}</p><h2>{text['writing_heading']}</h2></div><a class="text-link" href="{route('/blog/', lang)}">{text['all_writing']} {ARROW}</a></div>{article_cards(lang)}</section>
<section id="publications" class="publications-section"><div class="section-heading"><div><p class="eyebrow">{text['publications_eyebrow']}</p><h2>{text['papers_heading']}</h2></div><div class="publication-source-links">{link(DATA['scholar'], text['full_list'] + ' ' + ARROW, 'text-link')}{link(DATA['papers_source'], 'Hugging Face ' + ARROW, 'text-link')}</div></div>
<div class="publication-tools" hidden><div class="filters" role="group" aria-label="{text['filter_label']}"><button class="filter-button selected" type="button" data-filter="all" aria-pressed="true">{text['all_work']}</button>{filters}</div><label class="search-box"><span class="search-icon" aria-hidden="true">⌕</span><span class="sr-only">{text['search_label']}</span><input id="paper-search" type="search" placeholder="{text['search_placeholder']}" autocomplete="off"></label></div>
<p id="pub-count" class="pub-count" aria-live="polite" data-all-template="{ESC(text['count_all'], quote=True)}" data-filtered-template="{ESC(text['count_filtered'], quote=True)}">{count}</p><div id="publication-list">{pubs}</div><p id="empty-state" hidden>{text['no_results']}</p></section>
<section id="experience" class="experience-section"><div class="section-heading"><div><p class="eyebrow">{text['background_eyebrow']}</p><h2>{text['background_heading']}</h2></div><a class="text-link" href="{route('/resume/', lang)}">{text['view_cv']} {ARROW}</a></div>
<div class="background-grid"><div class="career-block"><p class="mini-heading">{text['experience_label']}</p><h3>{text['tencent']}</h3><p class="role">{text['role']}</p><p class="muted">{text['career_dates']}</p><p>{text['career_summary']}</p><div class="research-tags">{tags}</div></div>
<div class="education-block"><p class="mini-heading">{text['education_label']}</p><ul>{education}</ul></div></div></section>
<details class="earlier-notes home-archive"><summary><span class="archive-title">{text['earlier_notes']}</span><span class="archive-dates">2017–2019</span><span class="archive-chevron" aria-hidden="true">⌄</span></summary><div class="archive-content"><p class="muted">{text['notes_intro']}</p><a class="text-link" href="{route('/blog/', lang)}#earlier-notes">{text['browse_archive']} {ARROW}</a></div></details>
</main>''' + footer(lang, home=True)


def cvpage(lang="en"):
    text = I18N[lang]
    default = "Zh" if lang == "zh" else "En"
    return head(text['cv_title'], '/resume/', lang) + nav('cv', lang, '/resume/') + f'''<main id="main" class="page-shell cv-page"><p class="eyebrow">{text['cv_eyebrow']}</p><h1>{text['cv_heading']}</h1><p class="page-intro">{text['cv_intro']}</p>
<div class="cv-download-grid"><a class="cv-download" href="/pdf/En_resume.pdf"><span class="mini-heading">{text['en_pdf']}</span><h2>{text['en_cv_heading']}</h2><p>{text['en_cv_intro']}</p><span class="feature-link">{text['open_en_cv']} ↗</span></a><a class="cv-download" href="/pdf/Zh_resume.pdf"><span class="mini-heading">{text['zh_pdf']}</span><h2 lang="zh-CN">{text['zh_cv_heading']}</h2><p lang="zh-CN">{text['zh_cv_intro']}</p><span class="feature-link" lang="zh-CN">{text['open_zh_cv']} ↗</span></a></div>
<div class="cv-preview-heading"><h2>{text['preview']}</h2><label for="cv-language">{text['preview_language']} <select id="cv-language"><option value="En"{' selected' if default == 'En' else ''}>English</option><option value="Zh"{' selected' if default == 'Zh' else ''}>中文</option></select></label></div><iframe id="cv-preview" class="cv-preview" title="{text['preview_zh'] if default == 'Zh' else text['preview_en']}" data-title-en="{text['preview_en']}" data-title-zh="{text['preview_zh']}" src="/pdf/{default}_resume.pdf#view=FitH"></iframe><p class="muted">{text['preview_unavailable']}</p></main>''' + footer(lang)


def blogpage(lang="en"):
    text = I18N[lang]
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
    return head(text['blog_title'], '/blog/', lang) + nav('blog', lang, '/blog/') + f'''<main id="main" class="page-shell blog-page"><p class="eyebrow">{text['blog_eyebrow']}</p><h1>{text['blog_heading']}</h1><p class="page-intro">{text['blog_intro']}</p>
<section class="blog-writing" aria-labelledby="essays-heading"><div class="section-heading"><h2 id="essays-heading">{text['technical_essays']}</h2>{link(DATA['articles_url'], text['on_hf'] + ' ' + ARROW, 'text-link')}</div>{article_cards(lang)}</section>
<details id="earlier-notes" class="earlier-notes"><summary><span class="archive-title">{text['earlier_notes']}</span><span class="archive-dates">2017–2019</span><span class="archive-chevron" aria-hidden="true">⌄</span></summary><div class="archive-content"><div class="notes-list">{rows}</div><a class="text-link" href="/about/">{text['personal_notes']} {ARROW}</a></div></details></main>''' + footer(lang, blog=True)


def errorpage(lang="en"):
    text = I18N[lang]
    return head(text['error_title'], '/404.html', lang) + nav(lang=lang, page='/404.html') + f'''<main id="main" class="page-shell error-page"><p class="eyebrow">{text['error_eyebrow']}</p><h1>{text['error_heading']}</h1><p>{text['error_intro']}</p><a class="outline-button" href="{route('/', lang)}">{text['back_research']} ↗</a> <a class="text-link" href="{route('/blog/', lang)}">{text['browse_notes']} ↗</a></main>''' + footer(lang)


def build():
    for lang in ('en', 'zh'):
        for path, content in [('index.html', homepage(lang)), ('resume/index.html', cvpage(lang)), ('blog/index.html', blogpage(lang)), ('404.html', errorpage(lang))]:
            output = ROOT / ('zh' if lang == 'zh' else '') / path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding='utf-8')
    # One-time styling only; never translate or rewrite original article bodies.
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
    print(f'Built 8 bilingual pages; {len(DATA["publications"])} papers; {len(DATA["articles"])} articles; {changed} legacy pages refreshed.')

if __name__ == '__main__':
    build()
