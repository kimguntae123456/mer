#!/usr/bin/env python3
"""
메르 리더 HTML 렌더러
processed/ JSON → output/ HTML 타임라인
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROCESSED = BASE / "processed"
OUTPUT = BASE / "output"

FOLDERS = [
    "지정학", "금융·통화", "미국·글로벌", "부동산",
    "기술·산업", "에너지·자원", "자본시장", "중후장대", "한국경제"
]

FOLDER_DESC = {
    "지정학": "중동·지정학 · 중국경제·정치",
    "금융·통화": "금리·채권·통화정책 · 환율·외환시장",
    "미국·글로벌": "미국경제·정책 · 글로벌 기타",
    "부동산": "부동산·건설·PF",
    "기술·산업": "반도체·AI·기술 · 배터리·전기차",
    "에너지·자원": "에너지·원자재·기후",
    "자본시장": "주식·투자·금융",
    "중후장대": "조선·방위산업",
    "한국경제": "한국경제·정책",
}

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif; background: #f5f5f0; color: #1a1a1a; line-height: 1.7; }
a { color: inherit; text-decoration: none; }

/* 상단 네비 */
.nav { background: #1a1a1a; color: #fff; padding: 14px 24px; display: flex; align-items: center; gap: 16px; position: sticky; top: 0; z-index: 100; }
.nav .logo { font-size: 1.1rem; font-weight: 700; letter-spacing: -0.5px; }
.nav .back { font-size: 0.85rem; opacity: 0.6; }
.nav .back:hover { opacity: 1; }

/* 검색/필터 바 */
.filter-bar { max-width: 780px; margin: 0 auto; padding: 16px 24px 0; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.search-input { flex: 1; min-width: 200px; padding: 9px 14px; border: 1px solid #e0e0d8; border-radius: 8px; font-size: 0.9rem; background: #fff; outline: none; }
.search-input:focus { border-color: #1a1a1a; }
.filter-count { font-size: 0.8rem; color: #aaa; white-space: nowrap; }
.tag-filter-bar { max-width: 780px; margin: 0 auto; padding: 10px 24px 0; display: flex; flex-wrap: wrap; gap: 6px; }
.tag-btn { font-size: 0.75rem; background: #f0f0ea; color: #555; padding: 4px 10px; border-radius: 20px; cursor: pointer; border: 1px solid transparent; transition: all 0.15s; }
.tag-btn:hover { background: #e0e0d8; }
.tag-btn.active { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
.tag-btn.clear-btn { background: #fff; border-color: #ddd; color: #999; }

/* 날짜 그룹 헤더 */
.date-group-header { font-size: 0.78rem; font-weight: 700; letter-spacing: 1px; color: #aaa; padding: 20px 0 8px; text-transform: uppercase; }

/* 결과 없음 */
.no-results { text-align: center; padding: 60px 24px; color: #aaa; font-size: 0.95rem; display: none; }

/* 인덱스 페이지 */
.index-hero { padding: 60px 24px 40px; max-width: 900px; margin: 0 auto; }
.index-hero h1 { font-size: 2rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 8px; }
.index-hero p { color: #666; font-size: 0.95rem; }
.folder-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; max-width: 900px; margin: 0 auto; padding: 0 24px 60px; }
.folder-card { background: #fff; border-radius: 12px; padding: 24px; border: 1px solid #e8e8e0; cursor: pointer; transition: box-shadow 0.2s, transform 0.2s; }
.folder-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.1); transform: translateY(-2px); }
.folder-card .folder-name { font-size: 1.2rem; font-weight: 700; margin-bottom: 6px; }
.folder-card .folder-sub { font-size: 0.8rem; color: #888; margin-bottom: 12px; }
.folder-card .folder-count { font-size: 1.8rem; font-weight: 800; color: #1a1a1a; }
.folder-card .folder-count span { font-size: 0.85rem; font-weight: 400; color: #888; margin-left: 4px; }

/* 타임라인 페이지 */
.timeline-header { padding: 40px 24px 24px; max-width: 780px; margin: 0 auto; }
.timeline-header h1 { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.5px; }
.timeline-header .sub { color: #888; font-size: 0.85rem; margin-top: 4px; }
.timeline { max-width: 780px; margin: 0 auto; padding: 0 24px 80px; }

/* 카드 */
.card { background: #fff; border-radius: 12px; border: 1px solid #e8e8e0; margin-bottom: 16px; overflow: hidden; transition: box-shadow 0.2s; }
.card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.card-header { padding: 20px 24px; cursor: pointer; display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.card-header-left { flex: 1; }
.card-date { font-size: 0.78rem; color: #999; margin-bottom: 6px; letter-spacing: 0.3px; }
.card-title { font-size: 1.05rem; font-weight: 700; letter-spacing: -0.3px; line-height: 1.5; }
.card-tags { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
.tag { font-size: 0.75rem; background: #f0f0ea; color: #555; padding: 3px 8px; border-radius: 20px; }
.card-toggle { font-size: 1.2rem; color: #ccc; flex-shrink: 0; margin-top: 2px; transition: transform 0.2s; }
.card.open .card-toggle { transform: rotate(180deg); }

/* 카드 본문 */
.card-body { display: none; border-top: 1px solid #f0f0ea; padding: 24px; }
.card.open .card-body { display: block; }

.section { margin-bottom: 24px; }
.section-label { font-size: 0.72rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #aaa; margin-bottom: 10px; }

/* 도입 */
.intro-text { font-size: 0.95rem; color: #333; line-height: 1.8; }

/* 단락 */
.para { margin-bottom: 16px; }
.para-title { font-size: 0.85rem; font-weight: 700; color: #1a1a1a; margin-bottom: 6px; padding-left: 10px; border-left: 3px solid #1a1a1a; }
.para-body { font-size: 0.9rem; color: #444; line-height: 1.8; }

/* 주석 */
.annotations { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.annotation { font-size: 0.82rem; background: #f7f7f2; border-radius: 6px; padding: 8px 12px; color: #555; line-height: 1.6; }
.annotation .ann-type { font-weight: 700; color: #888; margin-right: 6px; font-size: 0.75rem; }
.annotation .ann-target { font-weight: 700; color: #333; margin-right: 4px; }

/* 질문 + 답 */
.question-box { background: #1a1a1a; color: #fff; border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; }
.question-box .q-label { font-size: 0.72rem; font-weight: 700; letter-spacing: 1px; color: #888; margin-bottom: 6px; }
.question-box .q-text { font-size: 0.92rem; line-height: 1.6; }
.answer-box { background: #f7f7f2; border-radius: 10px; padding: 16px 20px; }
.answer-box .a-label { font-size: 0.72rem; font-weight: 700; letter-spacing: 1px; color: #aaa; margin-bottom: 6px; }
.answer-box .a-text { font-size: 0.92rem; color: #333; line-height: 1.6; }

/* 원본 링크 */
.source-link { margin-top: 16px; font-size: 0.8rem; color: #aaa; }
.source-link a { color: #888; text-decoration: underline; }
.source-link a:hover { color: #333; }
"""

JS = """
// 카드 펼치기
document.querySelectorAll('.card-header').forEach(h => {
    h.addEventListener('click', () => h.closest('.card').classList.toggle('open'));
});

// 검색 + 태그 필터
const searchInput = document.getElementById('searchInput');
const filterCount = document.getElementById('filterCount');
const noResults = document.getElementById('noResults');
const cards = Array.from(document.querySelectorAll('.card'));
const dateGroups = Array.from(document.querySelectorAll('.date-group'));
let activeTag = null;

function getCardText(card) {
    return card.dataset.title + ' ' + card.dataset.tags + ' ' + card.dataset.date;
}

function applyFilters() {
    const q = searchInput ? searchInput.value.trim().toLowerCase() : '';
    let visible = 0;

    cards.forEach(card => {
        const text = getCardText(card).toLowerCase();
        const matchSearch = !q || text.includes(q);
        const matchTag = !activeTag || card.dataset.tags.includes(activeTag);
        const show = matchSearch && matchTag;
        card.style.display = show ? '' : 'none';
        if (show) visible++;
    });

    // 날짜 그룹 헤더: 하위 카드 모두 숨겨지면 헤더도 숨김
    dateGroups.forEach(group => {
        const groupCards = Array.from(group.querySelectorAll('.card'));
        const anyVisible = groupCards.some(c => c.style.display !== 'none');
        group.style.display = anyVisible ? '' : 'none';
    });

    if (filterCount) filterCount.textContent = visible + '개';
    if (noResults) noResults.style.display = visible === 0 ? 'block' : 'none';
}

if (searchInput) searchInput.addEventListener('input', applyFilters);

// 태그 버튼
document.querySelectorAll('.tag-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tag = btn.dataset.tag;
        if (tag === '__clear__') {
            activeTag = null;
            document.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('active'));
        } else if (activeTag === tag) {
            activeTag = null;
            btn.classList.remove('active');
        } else {
            activeTag = tag;
            document.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }
        applyFilters();
    });
});
"""


def render_annotations(annotations):
    if not annotations:
        return ""
    items = []
    for ann in annotations:
        t = ann.get("유형", "")
        target = ann.get("대상", "")
        content = ann.get("내용", "")
        if t == "용어풀이":
            items.append(f'<div class="annotation"><span class="ann-type">용어</span><span class="ann-target">{target}</span>{content}</div>')
        elif t == "맥락풀이":
            items.append(f'<div class="annotation"><span class="ann-type">맥락</span>{content}</div>')
    return f'<div class="annotations">{"".join(items)}</div>' if items else ""


def render_card(d):
    title = d.get("글_제목", d.get("원본_제목", ""))
    date = d.get("날짜", "")
    link = d.get("원본_링크", "")
    tags = d.get("태그", [])
    q = d.get("메르가_던지는_질문", "")
    ans = d.get("나의_답", "")
    body = d.get("이_글이_말하는_것", {})

    # 태그
    tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags)
    tags_data = " ".join(tags)

    # 도입
    intro = body.get("도입", "")
    intro_ann = render_annotations(body.get("도입_주석", []))
    intro_html = f'<div class="section"><div class="section-label">이 글이 말하는 것</div><p class="intro-text">{intro}</p>{intro_ann}</div>'

    # 단락들
    paras_html = ""
    for key in ["단락1", "단락2", "단락3", "단락4"]:
        para = body.get(key)
        if not para:
            continue
        pt = para.get("제목", "") if isinstance(para, dict) else ""
        pb = para.get("본문", "") if isinstance(para, dict) else str(para)
        ann = render_annotations(para.get("주석", []) if isinstance(para, dict) else [])
        paras_html += f'<div class="para"><div class="para-title">{pt}</div><div class="para-body">{pb}</div>{ann}</div>'

    # 질문 + 답
    qa_html = ""
    if q:
        qa_html += f'<div class="question-box"><div class="q-label">메르가 던지는 질문</div><div class="q-text">{q}</div></div>'
    if ans:
        qa_html += f'<div class="answer-box"><div class="a-label">나의 답</div><div class="a-text">{ans}</div></div>'

    source_html = f'<div class="source-link"><a href="{link}" target="_blank">원문 보기 →</a></div>' if link else ""

    return f"""
<div class="card" data-title="{title}" data-tags="{tags_data}" data-date="{date}">
  <div class="card-header">
    <div class="card-header-left">
      <div class="card-date">{date}</div>
      <div class="card-title">{title}</div>
      <div class="card-tags">{tags_html}</div>
    </div>
    <div class="card-toggle">▼</div>
  </div>
  <div class="card-body">
    {intro_html}
    <div class="section">{paras_html}</div>
    <div class="section">{qa_html}</div>
    {source_html}
  </div>
</div>"""


def render_timeline_page(folder, cards):
    count = len(cards)
    desc = FOLDER_DESC.get(folder, "")

    # 날짜별 그룹핑 (연-월)
    from collections import defaultdict
    groups = defaultdict(list)
    for d in cards:
        date = d.get("날짜", "")
        ym = date[:7] if date else "날짜 없음"  # YYYY-MM
        groups[ym].append(d)

    # 전체 태그 수집 (빈도순)
    from collections import Counter
    tag_counter = Counter()
    for d in cards:
        for t in d.get("태그", []):
            tag_counter[t] += 1
    top_tags = [t for t, _ in tag_counter.most_common(30)]

    # 날짜 그룹 HTML
    timeline_html = ""
    for ym in sorted(groups.keys()):
        year, month = (ym[:4], ym[5:7]) if len(ym) >= 7 else (ym, "")
        label = f"{year}년 {int(month)}월" if month else ym
        group_cards = "\n".join(render_card(d) for d in groups[ym])
        timeline_html += f"""
<div class="date-group">
  <div class="date-group-header">{label} · {len(groups[ym])}개</div>
  {group_cards}
</div>"""

    # 태그 버튼
    tag_btns = '<button class="tag-btn clear-btn" data-tag="__clear__">전체</button>'
    tag_btns += "".join(f'<button class="tag-btn" data-tag="{t}">{t}</button>' for t in top_tags)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>메르 리더 — {folder}</title>
<link rel="manifest" href="../manifest.json">
<meta name="theme-color" content="#1a1a1a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<style>{CSS}</style>
</head>
<body>
<nav class="nav">
  <span class="logo">메르 리더</span>
  <a href="../index.html" class="back">← 전체 목록</a>
</nav>
<div class="timeline-header">
  <h1>{folder}</h1>
  <div class="sub">{desc} · <span id="filterCount">{count}개</span> 글</div>
</div>
<div class="filter-bar">
  <input id="searchInput" class="search-input" type="text" placeholder="제목·태그 검색...">
</div>
<div class="tag-filter-bar">
  {tag_btns}
</div>
<div class="timeline" style="margin-top:16px">
{timeline_html}
</div>
<div class="no-results" id="noResults">검색 결과가 없습니다.</div>
<script>{JS}</script>
</body>
</html>"""


INDEX_JS = """
const allData = ALL_ARTICLES_JSON;
let view = 'folders';
let searchQ = '';
let sortDesc = true; // true=최신순, false=오래된순

const searchInput = document.getElementById('globalSearch');
const folderSection = document.getElementById('folderSection');
const allSection = document.getElementById('allSection');
const allList = document.getElementById('allList');
const resultCount = document.getElementById('resultCount');

function renderAnnotations(anns) {
    if (!anns || !anns.length) return '';
    return '<div class="annotations">' + anns.map(a => {
        if (a.유형 === '용어풀이') return `<div class="annotation"><span class="ann-type">용어</span><span class="ann-target">${a.대상||''}</span>${a.내용||''}</div>`;
        return `<div class="annotation"><span class="ann-type">맥락</span>${a.내용||''}</div>`;
    }).join('') + '</div>';
}

function renderCard(d) {
    const tagsHtml = d.tags.map(t=>`<span class="tag">${t}</span>`).join('');
    const parasHtml = (d.paras||[]).map(p =>
        `<div class="para"><div class="para-title">${p.title||''}</div><div class="para-body">${p.body||''}</div>${renderAnnotations(p.anns)}</div>`
    ).join('');
    return `
<div class="card" style="margin-bottom:12px">
  <div class="card-header" onclick="this.closest('.card').classList.toggle('open')">
    <div class="card-header-left">
      <div class="card-date">${d.date} &nbsp;·&nbsp; <span style="color:#aaa;font-size:0.75rem">${d.folder}</span></div>
      <div class="card-title">${d.title}</div>
      <div class="card-tags">${tagsHtml}</div>
    </div>
    <div class="card-toggle">▼</div>
  </div>
  <div class="card-body">
    <div class="section">
      <div class="section-label">이 글이 말하는 것</div>
      <p class="intro-text">${d.intro}</p>
      ${renderAnnotations(d.intro_anns)}
    </div>
    <div class="section">${parasHtml}</div>
    <div class="section">
      ${d.question ? `<div class="question-box"><div class="q-label">메르가 던지는 질문</div><div class="q-text">${d.question}</div></div>` : ''}
      ${d.answer ? `<div class="answer-box" style="margin-top:8px"><div class="a-label">나의 답</div><div class="a-text">${d.answer}</div></div>` : ''}
    </div>
    ${d.link ? `<div class="source-link"><a href="${d.link}" target="_blank">원문 보기 →</a></div>` : ''}
  </div>
</div>`;
}

function applyFilters() {
    const q = searchQ.trim().toLowerCase();
    let filtered = [...allData];
    if (q) {
        filtered = filtered.filter(d =>
            d.title.toLowerCase().includes(q) ||
            d.tags.join(' ').toLowerCase().includes(q) ||
            d.intro.toLowerCase().includes(q) ||
            (d.paras||[]).some(p => (p.body||'').toLowerCase().includes(q))
        );
    }
    filtered.sort((a,b) => sortDesc ? b.date.localeCompare(a.date) : a.date.localeCompare(b.date));
    if (!filtered.length) {
        allList.innerHTML = '<div style="text-align:center;padding:60px;color:#aaa">검색 결과가 없습니다.</div>';
    } else {
        allList.innerHTML = filtered.map(renderCard).join('');
    }
    resultCount.textContent = filtered.length + '개';
}

document.getElementById('btnAll').addEventListener('click', () => {
    view = 'all';
    folderSection.style.display = 'none';
    allSection.style.display = 'block';
    document.getElementById('btnAll').classList.add('active');
    document.getElementById('btnFolders').classList.remove('active');
    applyFilters();
});

document.getElementById('btnFolders').addEventListener('click', () => {
    view = 'folders';
    folderSection.style.display = 'block';
    allSection.style.display = 'none';
    document.getElementById('btnFolders').classList.add('active');
    document.getElementById('btnAll').classList.remove('active');
});

document.getElementById('btnSort').addEventListener('click', () => {
    sortDesc = !sortDesc;
    document.getElementById('btnSort').textContent = sortDesc ? '최신순 ↓' : '오래된순 ↑';
    if (view === 'all') applyFilters();
});

searchInput.addEventListener('input', e => {
    searchQ = e.target.value;
    if (view === 'folders' && searchQ.trim()) {
        document.getElementById('btnAll').click();
    } else if (view === 'all') {
        applyFilters();
    }
});
"""


def render_index_page(folder_counts, all_cards):
    folder_cards_html = ""
    for folder in FOLDERS:
        cnt = folder_counts.get(folder, 0)
        desc = FOLDER_DESC.get(folder, "")
        folder_cards_html += f"""
<a href="{folder}/index.html">
  <div class="folder-card">
    <div class="folder-name">{folder}</div>
    <div class="folder-sub">{desc}</div>
    <div class="folder-count">{cnt}<span>개 글</span></div>
  </div>
</a>"""

    total = sum(folder_counts.values())

    # 전체 카드 데이터
    import html as html_mod
    compact = []
    for d in sorted(all_cards, key=lambda x: x.get("날짜", ""), reverse=True):
        body = d.get("이_글이_말하는_것", {})
        paras = []
        for key in ["단락1", "단락2", "단락3", "단락4"]:
            p = body.get(key)
            if p and isinstance(p, dict):
                paras.append({
                    "title": p.get("제목", ""),
                    "body": p.get("본문", ""),
                    "anns": p.get("주석", []),
                })
        compact.append({
            "title": html_mod.escape(d.get("글_제목", d.get("원본_제목", ""))),
            "date": d.get("날짜", ""),
            "folder": d.get("섹터_통합", ""),
            "tags": d.get("태그", []),
            "intro": html_mod.escape(body.get("도입", "")),
            "intro_anns": body.get("도입_주석", []),
            "paras": paras,
            "question": html_mod.escape(d.get("메르가_던지는_질문", "")),
            "answer": html_mod.escape(d.get("나의_답", "")),
            "link": d.get("원본_링크", ""),
        })
    all_json = json.dumps(compact, ensure_ascii=False)
    js = INDEX_JS.replace("ALL_ARTICLES_JSON", all_json)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>메르 리더</title>
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#1a1a1a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="메르 리더">
<style>
{CSS}
.view-btns {{ display:flex; gap:8px; }}
.view-btn {{ padding:7px 16px; border-radius:20px; border:1px solid #e0e0d8; background:#fff; font-size:0.85rem; cursor:pointer; transition:all 0.15s; }}
.view-btn.active {{ background:#1a1a1a; color:#fff; border-color:#1a1a1a; }}
.index-search {{ flex:1; min-width:200px; padding:9px 14px; border:1px solid #e0e0d8; border-radius:8px; font-size:0.9rem; background:#fff; outline:none; }}
.index-search:focus {{ border-color:#1a1a1a; }}
</style>
</head>
<body>
<nav class="nav">
  <span class="logo">메르 리더</span>
</nav>
<div class="index-hero">
  <h1>메르 리더</h1>
  <p>메르 블로그 {total}개 글 — 섹터별 타임라인</p>
  <div style="display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;align-items:center;">
    <div class="view-btns">
      <button class="view-btn active" id="btnFolders">섹터별</button>
      <button class="view-btn" id="btnAll">전체보기 <span id="resultCount" style="color:#aaa;font-size:0.8rem"></span></button>
      <button class="view-btn" id="btnSort">최신순 ↓</button>
    </div>
    <input id="globalSearch" class="index-search" type="text" placeholder="제목·태그·내용 검색...">
  </div>
</div>

<div id="folderSection">
  <div class="folder-grid">
    {folder_cards_html}
  </div>
</div>

<div id="allSection" style="display:none;max-width:780px;margin:0 auto;padding:0 24px 80px;">
  <div id="allList"></div>
</div>

<script>{js}</script>
<script>if('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js');</script>
</body>
</html>"""


def main():
    OUTPUT.mkdir(exist_ok=True)
    folder_counts = {}
    all_cards = []

    for folder in FOLDERS:
        folder_dir = PROCESSED / folder
        if not folder_dir.exists():
            continue

        jsons = sorted(folder_dir.glob("*.json"))
        cards = []
        for jf in jsons:
            try:
                d = json.loads(jf.read_text(encoding="utf-8"))
                cards.append(d)
                all_cards.append(d)
            except Exception as e:
                print(f"  [SKIP] {jf.name}: {e}")

        cards.sort(key=lambda x: x.get("날짜", "0000-00-00"))
        folder_counts[folder] = len(cards)

        out_dir = OUTPUT / folder
        out_dir.mkdir(exist_ok=True)
        html = render_timeline_page(folder, cards)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  {folder}: {len(cards)}개 → {out_dir}/index.html")

    # 인덱스
    index_html = render_index_page(folder_counts, all_cards)
    (OUTPUT / "index.html").write_text(index_html, encoding="utf-8")
    print(f"\n완료: {OUTPUT}/index.html")

    # PWA 파일
    manifest = {
        "name": "메르 리더",
        "short_name": "메르 리더",
        "description": "메르 블로그 경제 분석 리더",
        "start_url": ".",
        "display": "standalone",
        "background_color": "#f5f5f0",
        "theme_color": "#1a1a1a",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    sw_js = """const CACHE = 'mer-v1';
const SHELL = ['./'];
self.addEventListener('install', e => {
    e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
    self.skipWaiting();
});
self.addEventListener('activate', e => {
    e.waitUntil(caches.keys().then(keys =>
        Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ));
    self.clients.claim();
});
self.addEventListener('fetch', e => {
    e.respondWith(
        fetch(e.request).catch(() => caches.match(e.request))
    );
});
"""
    (OUTPUT / "sw.js").write_text(sw_js, encoding="utf-8")
    print("PWA 파일 생성 완료 (manifest.json, sw.js)")


if __name__ == "__main__":
    main()
