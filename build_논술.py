#!/usr/bin/env python3
"""논술 summary MD → 메르_리더 스타일 HTML 통합 빌드"""

import os
import re
import html
from pathlib import Path
from collections import defaultdict

SUMMARY_ROOT = Path("/Users/pc/Downloads/피티/논술")
OUTPUT_ROOT = Path("/Users/pc/메르_리더/output/논술")

def find_summaries():
    """모든 *_summary.md 파일 수집, 카테고리별 그룹화"""
    categories = defaultdict(list)
    for md in SUMMARY_ROOT.rglob("*_summary.md"):
        # 카테고리 = summary 폴더의 부모 경로 (논술/ 기준 상대)
        rel = md.parent.parent.relative_to(SUMMARY_ROOT)
        cat = str(rel)
        title = md.stem.replace("_summary", "")
        categories[cat].append({"title": title, "path": md})
    # 각 카테고리 내 제목순 정렬
    for cat in categories:
        categories[cat].sort(key=lambda x: x["title"])
    return dict(sorted(categories.items()))

def md_to_html_content(md_text):
    """마크다운 텍스트를 간단한 HTML로 변환"""
    lines = md_text.split("\n")
    out = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<br>")
            continue

        # 헤더
        if stripped.startswith("# "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f'<h2 class="md-h1">{html.escape(stripped[2:])}</h2>')
        elif stripped.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f'<h3 class="md-h2">{html.escape(stripped[3:])}</h3>')
        elif stripped.startswith("### "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f'<h4 class="md-h3">{html.escape(stripped[4:])}</h4>')
        elif stripped.startswith("---"):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append('<hr class="md-hr">')
        elif re.match(r'^[\d]+\.\s', stripped):
            # 숫자 리스트
            content = re.sub(r'^[\d]+\.\s', '', stripped)
            if not in_list:
                out.append('<ul class="md-list">')
                in_list = True
            out.append(f'<li>{format_inline(content)}</li>')
        elif stripped.startswith("* ") or stripped.startswith("- "):
            content = stripped[2:]
            if not in_list:
                out.append('<ul class="md-list">')
                in_list = True
            out.append(f'<li>{format_inline(content)}</li>')
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f'<p class="md-p">{format_inline(stripped)}</p>')

    if in_list:
        out.append("</ul>")

    return "\n".join(out)

def format_inline(text):
    """인라인 마크다운 (bold, emoji 등)"""
    t = html.escape(text)
    # **bold**
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    # *italic*
    t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
    return t

def render_category_page(cat_name, articles):
    """카테고리별 HTML 페이지 생성"""
    cards_html = []
    for i, art in enumerate(articles):
        md_text = art["path"].read_text(encoding="utf-8")
        content = md_to_html_content(md_text)
        title_escaped = html.escape(art["title"])
        cards_html.append(f'''
<div class="card" data-idx="{i}">
  <div class="card-header" onclick="this.parentElement.classList.toggle('open')">
    <div class="card-header-left">
      <div class="card-title">{title_escaped}</div>
    </div>
    <div class="card-toggle">▾</div>
  </div>
  <div class="card-body">
    {content}
  </div>
</div>''')

    cat_escaped = html.escape(cat_name)
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>논술 — {cat_escaped}</title>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="theme-color" content="#1a1a1a">
{CSS}
</head>
<body>
<nav class="nav">
  <a href="../index.html" class="back">← 논술</a>
  <span class="logo">{cat_escaped}</span>
</nav>

<div class="timeline-header">
  <h1>{cat_escaped}</h1>
  <div class="sub">{len(articles)}개 요약</div>
</div>

<div class="filter-bar">
  <input class="search-input" type="text" placeholder="제목·내용 검색..." id="searchInput">
  <span class="filter-count" id="filterCount">{len(articles)}개</span>
</div>

<div class="timeline" id="timeline">
{"".join(cards_html)}
</div>

<div class="no-results" id="noResults">검색 결과가 없습니다</div>

{SEARCH_JS}
</body>
</html>'''

def render_index(categories):
    """메인 인덱스 페이지"""
    total = sum(len(v) for v in categories.values())
    cards = []
    for cat, articles in categories.items():
        cat_escaped = html.escape(cat)
        # 폴더명을 URL-safe하게
        folder = cat.replace("/", "_")
        cards.append(f'''
<a href="{folder}/index.html">
  <div class="folder-card">
    <div class="folder-name">{cat_escaped}</div>
    <div class="folder-count">{len(articles)}<span>개 요약</span></div>
  </div>
</a>''')

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>논술 요약 리더</title>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="theme-color" content="#1a1a1a">
{CSS}
</head>
<body>
<nav class="nav">
  <a href="../index.html" class="back">← 메르 리더</a>
  <span class="logo">논술 요약</span>
</nav>

<div class="index-hero">
  <h1>논술 요약 리더</h1>
  <p>{total}개 논술 요약 — {len(categories)}개 카테고리</p>
</div>

<div class="folder-grid">
{"".join(cards)}
</div>

</body>
</html>'''


# ── 스타일 (메르_리더 동일) ──

CSS = '''<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif; background: #f5f5f0; color: #1a1a1a; line-height: 1.7; }
a { color: inherit; text-decoration: none; }

.nav { background: #1a1a1a; color: #fff; padding: 14px 24px; display: flex; align-items: center; gap: 16px; position: sticky; top: 0; z-index: 100; }
.nav .logo { font-size: 1.1rem; font-weight: 700; letter-spacing: -0.5px; }
.nav .back { font-size: 0.85rem; opacity: 0.6; }
.nav .back:hover { opacity: 1; }

.filter-bar { max-width: 780px; margin: 0 auto; padding: 16px 24px 0; display: flex; gap: 10px; align-items: center; }
.search-input { flex: 1; min-width: 200px; padding: 9px 14px; border: 1px solid #e0e0d8; border-radius: 8px; font-size: 0.9rem; background: #fff; outline: none; }
.search-input:focus { border-color: #1a1a1a; }
.filter-count { font-size: 0.8rem; color: #aaa; white-space: nowrap; }

.index-hero { padding: 60px 24px 40px; max-width: 900px; margin: 0 auto; }
.index-hero h1 { font-size: 2rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 8px; }
.index-hero p { color: #666; font-size: 0.95rem; }

.folder-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; max-width: 900px; margin: 0 auto; padding: 0 24px 60px; }
.folder-card { background: #fff; border-radius: 12px; padding: 24px; border: 1px solid #e8e8e0; cursor: pointer; transition: box-shadow 0.2s, transform 0.2s; }
.folder-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.1); transform: translateY(-2px); }
.folder-card .folder-name { font-size: 1.2rem; font-weight: 700; margin-bottom: 6px; }
.folder-card .folder-count { font-size: 1.8rem; font-weight: 800; color: #1a1a1a; }
.folder-card .folder-count span { font-size: 0.85rem; font-weight: 400; color: #888; margin-left: 4px; }

.timeline-header { padding: 40px 24px 24px; max-width: 780px; margin: 0 auto; }
.timeline-header h1 { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.5px; }
.timeline-header .sub { color: #888; font-size: 0.85rem; margin-top: 4px; }
.timeline { max-width: 780px; margin: 0 auto; padding: 0 24px 80px; }

.card { background: #fff; border-radius: 12px; border: 1px solid #e8e8e0; margin-bottom: 16px; overflow: hidden; transition: box-shadow 0.2s; }
.card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.card-header { padding: 20px 24px; cursor: pointer; display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.card-header-left { flex: 1; }
.card-title { font-size: 1.05rem; font-weight: 700; letter-spacing: -0.3px; line-height: 1.5; }
.card-toggle { font-size: 1.2rem; color: #ccc; flex-shrink: 0; margin-top: 2px; transition: transform 0.2s; }
.card.open .card-toggle { transform: rotate(180deg); }
.card-body { display: none; border-top: 1px solid #f0f0ea; padding: 24px; }
.card.open .card-body { display: block; }

.no-results { text-align: center; padding: 60px 24px; color: #aaa; font-size: 0.95rem; display: none; }

/* MD 콘텐츠 스타일 */
.md-h1 { font-size: 1.1rem; font-weight: 800; margin: 16px 0 10px; color: #1a1a1a; border-bottom: 2px solid #e8e8e0; padding-bottom: 8px; }
.md-h2 { font-size: 0.95rem; font-weight: 700; margin: 14px 0 8px; color: #333; padding-left: 10px; border-left: 3px solid #1a1a1a; }
.md-h3 { font-size: 0.88rem; font-weight: 700; margin: 12px 0 6px; color: #555; }
.md-p { font-size: 0.88rem; color: #444; line-height: 1.8; margin-bottom: 4px; }
.md-hr { border: none; border-top: 1px solid #e8e8e0; margin: 16px 0; }
.md-list { padding-left: 20px; margin: 6px 0; }
.md-list li { font-size: 0.88rem; color: #444; line-height: 1.8; margin-bottom: 2px; }
.card-body br { display: block; content: ""; margin-top: 4px; }
</style>'''

SEARCH_JS = '''<script>
const cards = document.querySelectorAll('.card');
const searchInput = document.getElementById('searchInput');
const filterCount = document.getElementById('filterCount');
const noResults = document.getElementById('noResults');

searchInput.addEventListener('input', function() {
  const q = this.value.toLowerCase();
  let visible = 0;
  cards.forEach(c => {
    const text = c.textContent.toLowerCase();
    const show = !q || text.includes(q);
    c.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  filterCount.textContent = visible + '개';
  noResults.style.display = visible === 0 ? 'block' : 'none';
});
</script>'''


def main():
    categories = find_summaries()
    total = sum(len(v) for v in categories.values())
    print(f"발견: {total}개 summary, {len(categories)}개 카테고리")

    # 출력 디렉토리
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    # 인덱스
    idx_html = render_index(categories)
    (OUTPUT_ROOT / "index.html").write_text(idx_html, encoding="utf-8")
    print("✓ 논술/index.html")

    # 카테고리별 페이지
    for cat, articles in categories.items():
        folder = cat.replace("/", "_")
        cat_dir = OUTPUT_ROOT / folder
        cat_dir.mkdir(parents=True, exist_ok=True)

        page = render_category_page(cat, articles)
        (cat_dir / "index.html").write_text(page, encoding="utf-8")
        print(f"✓ 논술/{folder}/index.html ({len(articles)}개)")

    print(f"\n완료! {total}개 요약 → {len(categories)}개 카테고리 HTML")

if __name__ == "__main__":
    main()
