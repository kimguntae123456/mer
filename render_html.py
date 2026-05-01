#!/usr/bin/env python3
"""
메르 리더 HTML 렌더러 v2
processed/ JSON → output/index.html (SPA)
standalone 디자인 재현: 섹터 카드 그리드, 날짜별 그룹핑, 상세 펼침, 북마크, 검색
"""
import json
import html as html_mod
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROCESSED = BASE / "processed"
OUTPUT = BASE / "output"

FOLDERS = [
    "지정학", "금융·통화", "미국·글로벌", "부동산",
    "기술·산업", "에너지·자원", "자본시장", "중후장대", "한국경제"
]

FOLDER_META = {
    "지정학": {"emoji": "🌍", "sub": "중동·중국", "desc": "중동·지정학 · 중국경제·정치"},
    "금융·통화": {"emoji": "💵", "sub": "금리·환율", "desc": "금리·채권·통화정책 · 환율·외환시장"},
    "미국·글로벌": {"emoji": "🇺🇸", "sub": "미국경제·정책", "desc": "미국경제·정책 · 글로벌 기타"},
    "부동산": {"emoji": "🏘️", "sub": "건설·PF", "desc": "부동산·건설·PF"},
    "기술·산업": {"emoji": "⚙️", "sub": "반도체·AI·배터리", "desc": "반도체·AI·기술 · 배터리·전기차"},
    "에너지·자원": {"emoji": "⚡", "sub": "원자재·기후", "desc": "에너지·원자재·기후"},
    "자본시장": {"emoji": "📈", "sub": "주식·투자", "desc": "주식·투자·금융"},
    "중후장대": {"emoji": "🚢", "sub": "조선·방산", "desc": "조선·방위산업"},
    "한국경제": {"emoji": "🇰🇷", "sub": "국내정책", "desc": "한국경제·정책"},
}

WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def build_all_data():
    """processed/ 전체 JSON 로드"""
    all_cards = []
    folder_counts = {}

    for folder in FOLDERS:
        folder_dir = PROCESSED / folder
        if not folder_dir.exists():
            folder_counts[folder] = 0
            continue
        jsons = sorted(folder_dir.glob("*.json"))
        count = 0
        for jf in jsons:
            try:
                d = json.loads(jf.read_text(encoding="utf-8"))
                d["_folder"] = folder
                all_cards.append(d)
                count += 1
            except Exception as e:
                print(f"  [SKIP] {jf.name}: {e}")
        folder_counts[folder] = count
    return all_cards, folder_counts


def compact_card(d):
    """JSON 카드 → 프론트 전달용 compact dict"""
    body = d.get("이_글이_말하는_것", {})
    paras = []
    for key in ["단락1", "단락2", "단락3", "단락4"]:
        p = body.get(key)
        if p and isinstance(p, dict):
            paras.append({
                "t": p.get("제목", ""),
                "b": p.get("본문", ""),
                "a": p.get("주석", []),
            })
    return {
        "id": d.get("원본_링크", "").split("/")[-1] or str(hash(d.get("글_제목", ""))),
        "title": d.get("글_제목", d.get("원본_제목", "")),
        "date": d.get("날짜", ""),
        "folder": d.get("_folder", d.get("섹터_통합", "")),
        "sector": d.get("섹터_원래", ""),
        "tags": d.get("태그", []),
        "intro": body.get("도입", ""),
        "intro_a": body.get("도입_주석", []),
        "paras": paras,
        "q": d.get("메르가_던지는_질문", ""),
        "ans": d.get("나의_답", ""),
        "link": d.get("원본_링크", ""),
    }


def render_html(all_cards, folder_counts):
    total = sum(folder_counts.values())
    compact = [compact_card(d) for d in sorted(all_cards, key=lambda x: x.get("날짜", ""), reverse=True)]
    data_json = json.dumps(compact, ensure_ascii=False)
    meta_json = json.dumps(FOLDER_META, ensure_ascii=False)
    folders_json = json.dumps(FOLDERS, ensure_ascii=False)
    counts_json = json.dumps(folder_counts, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>메르 리더</title>
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#faf9f5">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="메르 리더">
<style>
{CSS}
</style>
</head>
<body>
<div id="app">
  <header class="top-bar">
    <div class="top-bar-inner">
      <div class="top-left">
        <div class="logo">메</div>
        <input id="searchInput" class="search-box" type="text" placeholder="제목·태그·본문 검색…">
      </div>
      <div class="top-right">
        <button id="btnView" class="icon-btn" title="보기 방식">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="6" height="6" rx="1"/><rect x="10" y="2" width="6" height="6" rx="1"/><rect x="2" y="10" width="6" height="6" rx="1"/><rect x="10" y="10" width="6" height="6" rx="1"/></svg>
        </button>
        <button id="btnBookmarkNav" class="icon-btn" title="북마크">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 3h8a1 1 0 011 1v12l-5-3-5 3V4a1 1 0 011-1z"/></svg>
        </button>
      </div>
    </div>
  </header>
  <main id="mainContent"></main>
  <nav class="bottom-nav">
    <button class="nav-btn active" data-view="home">
      <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10l7-7 7 7"/><path d="M5 10v7a1 1 0 001 1h3v-4h2v4h3a1 1 0 001-1v-7"/></svg>
      <span>홈</span>
    </button>
    <button class="nav-btn" data-view="sectors">
      <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="10" cy="10" r="7"/><path d="M10 3v14M3 10h14"/></svg>
      <span>섹터</span>
    </button>
    <button class="nav-btn" data-view="bookmarks">
      <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 3h10a1 1 0 011 1v14l-6-3-6 3V4a1 1 0 011-1z"/></svg>
      <span>북마크</span>
    </button>
    <button class="nav-btn" data-view="settings">
      <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="10" cy="10" r="3"/><path d="M10 1v3M10 16v3M1 10h3M16 10h3M3.5 3.5l2.1 2.1M14.4 14.4l2.1 2.1M16.5 3.5l-2.1 2.1M5.6 14.4l-2.1 2.1"/></svg>
      <span>설정</span>
    </button>
  </nav>
</div>

<script>
const DATA = {data_json};
const META = {meta_json};
const FOLDERS = {folders_json};
const COUNTS = {counts_json};
const TOTAL = {total};
const WEEKDAYS = {json.dumps(WEEKDAYS, ensure_ascii=False)};

__APP_JS_PLACEHOLDER__
</script>
<script>if('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js');</script>
</body>
</html>""".replace("__APP_JS_PLACEHOLDER__", APP_JS)


CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #faf9f5; --card: #fff; --border: #eae8e0; --text: #1a1614;
  --sub: #8a8680; --accent: #1a1614; --tag-bg: #f0ede6; --radius: 14px;
  --safe-bottom: env(safe-area-inset-bottom, 0px);
}
body { font-family: -apple-system, BlinkMacSystemFont, 'Pretendard', sans-serif; background: var(--bg); color: var(--text); line-height: 1.65; -webkit-font-smoothing: antialiased; }
#app { min-height: 100vh; padding-bottom: calc(64px + var(--safe-bottom)); }

/* Top bar */
.top-bar { position: sticky; top: 0; z-index: 100; background: var(--bg); border-bottom: 1px solid var(--border); }
.top-bar-inner { max-width: 680px; margin: 0 auto; padding: 10px 16px; display: flex; align-items: center; gap: 10px; }
.top-left { display: flex; align-items: center; gap: 10px; flex: 1; }
.logo { width: 34px; height: 34px; background: var(--accent); color: #fff; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 18px; font-family: 'Noto Serif KR', serif; flex-shrink: 0; }
.search-box { flex: 1; padding: 8px 14px; border: 1px solid var(--border); border-radius: 10px; font-size: 14px; background: var(--card); outline: none; color: var(--text); }
.search-box:focus { border-color: var(--accent); }
.top-right { display: flex; gap: 6px; }
.icon-btn { width: 36px; height: 36px; border: 1px solid var(--border); border-radius: 10px; background: var(--card); display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--sub); transition: all .15s; }
.icon-btn:hover { border-color: var(--accent); color: var(--accent); }

/* Bottom nav */
.bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: var(--bg); border-top: 1px solid var(--border); display: flex; justify-content: space-around; padding: 6px 0 calc(6px + var(--safe-bottom)); z-index: 100; }
.nav-btn { background: none; border: none; display: flex; flex-direction: column; align-items: center; gap: 2px; font-size: 10px; color: var(--sub); cursor: pointer; padding: 4px 12px; }
.nav-btn.active { color: var(--accent); }
.nav-btn svg { stroke: currentColor; }

/* Main content */
main { max-width: 680px; margin: 0 auto; padding: 0 16px; }

/* Home hero */
.hero { padding: 32px 0 24px; }
.hero-label { font-size: 12px; color: var(--sub); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }
.hero h1 { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
.hero-sub { color: var(--sub); font-size: 13px; margin-top: 4px; }

/* Sector grid */
.sector-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; padding-bottom: 32px; }
.sector-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; cursor: pointer; transition: all .2s; display: flex; flex-direction: column; gap: 4px; }
.sector-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.08); transform: translateY(-2px); }
.sector-emoji { font-size: 28px; margin-bottom: 4px; }
.sector-name { font-size: 15px; font-weight: 700; }
.sector-sub { font-size: 12px; color: var(--sub); }
.sector-count { font-size: 12px; color: var(--sub); margin-top: 4px; font-weight: 600; }

/* Sector detail banner */
.sector-banner { padding: 28px 0 20px; }
.sector-banner .back-link { font-size: 12px; color: var(--sub); cursor: pointer; margin-bottom: 8px; display: inline-block; }
.sector-banner .back-link:hover { color: var(--accent); }
.sector-banner h2 { font-size: 20px; font-weight: 800; }
.sector-banner .count { font-size: 13px; color: var(--sub); }

/* Date group */
.date-header { display: flex; align-items: baseline; gap: 8px; padding: 20px 0 10px; }
.date-header .date-text { font-size: 14px; font-weight: 700; color: var(--text); }
.date-header .date-weekday { font-size: 12px; color: var(--sub); }
.date-header .date-count { font-size: 11px; color: var(--sub); margin-left: auto; }

/* Article card */
.article { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 10px; overflow: hidden; transition: box-shadow .2s; }
.article:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.article-head { padding: 16px 18px; cursor: pointer; display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.article-head-left { flex: 1; min-width: 0; }
.article-title { font-size: 15px; font-weight: 700; line-height: 1.5; letter-spacing: -0.3px; }
.article-intro { font-size: 13px; color: var(--sub); margin-top: 6px; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.article-tags { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 5px; }
.tag { font-size: 11px; background: var(--tag-bg); color: #666; padding: 2px 8px; border-radius: 20px; }
.bookmark-btn { width: 32px; height: 32px; border: none; background: none; cursor: pointer; color: var(--sub); flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 8px; transition: all .15s; }
.bookmark-btn:hover { background: var(--tag-bg); }
.bookmark-btn.active { color: #e8a020; }
.bookmark-btn.active svg { fill: #e8a020; }

/* Detail panel */
.detail { display: none; border-top: 1px solid var(--border); padding: 20px 18px; }
.article.open .detail { display: block; }
.detail-close { font-size: 12px; color: var(--sub); cursor: pointer; float: right; padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border); background: var(--card); }
.detail-close:hover { background: var(--tag-bg); }
.detail-sector { font-size: 11px; color: var(--sub); margin-bottom: 6px; }
.detail h2 { font-size: 17px; font-weight: 800; margin-bottom: 12px; line-height: 1.5; }
.detail-meta { font-size: 11px; color: var(--sub); margin-top: 16px; }

.section-label { font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: var(--sub); margin-bottom: 8px; margin-top: 20px; }
.intro-text { font-size: 14px; color: #333; line-height: 1.8; }
.para { margin-bottom: 14px; }
.para-title { font-size: 13px; font-weight: 700; color: var(--text); padding-left: 10px; border-left: 3px solid var(--accent); margin-bottom: 5px; }
.para-body { font-size: 13.5px; color: #444; line-height: 1.8; }
.ann { font-size: 12px; background: #f7f5ef; border-radius: 8px; padding: 8px 12px; color: #666; line-height: 1.6; margin-top: 6px; }
.ann-type { font-weight: 700; color: #999; margin-right: 5px; font-size: 11px; }
.ann-target { font-weight: 700; color: #444; margin-right: 4px; }

.q-box { background: var(--accent); color: #fff; border-radius: 12px; padding: 14px 18px; margin-top: 20px; }
.q-box .label { font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #888; margin-bottom: 5px; }
.q-box .text { font-size: 14px; line-height: 1.6; }
.a-box { background: #f7f5ef; border-radius: 12px; padding: 14px 18px; margin-top: 8px; }
.a-box .label { font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #aaa; margin-bottom: 5px; }
.a-box .text { font-size: 14px; color: #333; line-height: 1.6; }
.source { margin-top: 14px; font-size: 12px; }
.source a { color: var(--sub); text-decoration: underline; }
.source a:hover { color: var(--accent); }

/* Empty state */
.empty { text-align: center; padding: 60px 20px; color: var(--sub); font-size: 14px; }

/* Search results */
.search-results-label { font-size: 13px; color: var(--sub); padding: 16px 0 8px; }

/* Settings */
.settings-section { padding: 20px 0; }
.settings-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid var(--border); }
.settings-item label { font-size: 14px; font-weight: 600; }
.font-size-btns { display: flex; gap: 6px; }
.font-size-btns button { width: 36px; height: 36px; border: 1px solid var(--border); border-radius: 8px; background: var(--card); cursor: pointer; font-size: 14px; font-weight: 700; }
.font-size-btns button.active { background: var(--accent); color: #fff; border-color: var(--accent); }

@media (max-width: 480px) {
  .sector-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .article-intro { -webkit-line-clamp: 1; }
}
"""

APP_JS = """
// State
let currentView = 'home';
let currentFolder = null;
let bookmarks = JSON.parse(localStorage.getItem('mer_bookmarks') || '[]');
let fontSize = localStorage.getItem('mer_fontsize') || 'medium';

const main = document.getElementById('mainContent');
const searchInput = document.getElementById('searchInput');
const navBtns = document.querySelectorAll('.nav-btn');

// Utils
function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

function dateInfo(dateStr) {
  if (!dateStr) return { display: '', weekday: '' };
  const [y, m, d] = dateStr.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  const weekday = WEEKDAYS[dt.getDay() === 0 ? 6 : dt.getDay() - 1];
  return { display: y + '\\ub144 ' + m + '\\uc6d4 ' + d + '\\uc77c', weekday };
}

function groupByDate(items) {
  const groups = {};
  items.forEach(item => {
    const d = item.date || '';
    if (!groups[d]) groups[d] = [];
    groups[d].push(item);
  });
  return groups;
}

function isBookmarked(id) { return bookmarks.includes(id); }
function toggleBookmark(id) {
  const idx = bookmarks.indexOf(id);
  if (idx >= 0) bookmarks.splice(idx, 1);
  else bookmarks.push(id);
  localStorage.setItem('mer_bookmarks', JSON.stringify(bookmarks));
}

function renderAnns(anns) {
  if (!anns || !anns.length) return '';
  return anns.map(function(a) {
    if (a["\\uc720\\ud615"] === "\\uc6a9\\uc5b4\\ud480\\uc774") return '<div class="ann"><span class="ann-type">\\uc6a9\\uc5b4</span><span class="ann-target">' + esc(a["\\ub300\\uc0c1"]||'') + '</span>' + esc(a["\\ub0b4\\uc6a9"]||'') + '</div>';
    return '<div class="ann"><span class="ann-type">\\ub9e5\\ub77d</span>' + esc(a["\\ub0b4\\uc6a9"]||'') + '</div>';
  }).join('');
}

function renderArticle(d) {
  var bm = isBookmarked(d.id);
  var tagsHtml = d.tags.map(function(t) { return '<span class="tag">' + esc(t) + '</span>'; }).join('');
  var parasHtml = (d.paras||[]).map(function(p) {
    return '<div class="para"><div class="para-title">' + esc(p.t||'') + '</div><div class="para-body">' + esc(p.b||'') + '</div>' + renderAnns(p.a) + '</div>';
  }).join('');
  var di = dateInfo(d.date);
  var bmFill = bm ? '#e8a020' : 'none';

  return '<div class="article" data-id="' + d.id + '">' +
    '<div class="article-head" data-action="toggle">' +
      '<div class="article-head-left">' +
        '<div class="article-title">' + esc(d.title) + '</div>' +
        '<div class="article-intro">' + esc(d.intro) + '</div>' +
        '<div class="article-tags">' + tagsHtml + '</div>' +
      '</div>' +
      '<button class="bookmark-btn' + (bm ? ' active' : '') + '" data-action="bookmark" data-bid="' + d.id + '" title="\\ubd81\\ub9c8\\ud06c">' +
        '<svg width="18" height="18" fill="' + bmFill + '" stroke="currentColor" stroke-width="2"><path d="M5 3h8a1 1 0 011 1v12l-5-3-5 3V4a1 1 0 011-1z"/></svg>' +
      '</button>' +
    '</div>' +
    '<div class="detail">' +
      '<button class="detail-close" data-action="close">\\ub2eb\\uae30</button>' +
      '<div class="detail-sector">' + esc(d.folder) + '</div>' +
      '<h2>' + esc(d.title) + '</h2>' +
      '<div class="section-label">\\ubcf8\\ubb38</div>' +
      '<div class="intro-text">' + esc(d.intro) + '</div>' +
      renderAnns(d.intro_a) +
      '<div style="margin-top:12px">' + parasHtml + '</div>' +
      (d.q ? '<div class="q-box"><div class="label">\\uba54\\ub974\\uac00 \\ub358\\uc9c0\\ub294 \\uc9c8\\ubb38</div><div class="text">' + esc(d.q) + '</div></div>' : '') +
      (d.ans ? '<div class="a-box"><div class="label">\\ub098\\uc758 \\ub2f5</div><div class="text">' + esc(d.ans) + '</div></div>' : '') +
      (d.link ? '<div class="source"><a href="' + d.link + '" target="_blank">\\uc6d0\\ubb38 \\ubcf4\\uae30 \\u2192</a></div>' : '') +
      '<div class="detail-meta">\\u00b6 ' + (di.display || d.date) + ' \\u00b7 ' + esc(d.folder) + '</div>' +
    '</div>' +
  '</div>';
}

function renderDateGroups(items) {
  var groups = groupByDate(items);
  var dates = Object.keys(groups).sort().reverse();
  if (!dates.length) return '<div class="empty">\\uae00\\uc774 \\uc5c6\\uc2b5\\ub2c8\\ub2e4.</div>';
  return dates.map(function(date) {
    var di = dateInfo(date);
    var cards = groups[date];
    return '<div class="date-header"><span class="date-text">' + di.display + '</span><span class="date-weekday">' + di.weekday + '</span><span class="date-count">' + cards.length + '\\ud3b8</span></div>' +
      cards.map(renderArticle).join('');
  }).join('');
}

// Views
function showHome() {
  currentView = 'home'; currentFolder = null;
  var html = '<div class="hero"><div class="hero-label">Sectors</div><h1>\\uc139\\ud130\\ubcc4\\ub85c \\ubcf4\\uae30</h1><div class="hero-sub">' + FOLDERS.length + '\\uac1c \\uc8fc\\uc81c\\ub85c \\ubd84\\ub958\\ub41c \\uba54\\ub974\\uc758 \\uae00</div></div>';
  html += '<div class="sector-grid">';
  FOLDERS.forEach(function(f) {
    var m = META[f] || {};
    var cnt = COUNTS[f] || 0;
    html += '<div class="sector-card" data-action="sector" data-folder="' + f + '">' +
      '<div class="sector-emoji">' + (m.emoji||'') + '</div>' +
      '<div class="sector-name">' + esc(f) + '</div>' +
      '<div class="sector-sub">' + esc(m.sub||'') + '</div>' +
      '<div class="sector-count">' + cnt + '\\ud3b8</div>' +
    '</div>';
  });
  html += '</div>';
  main.innerHTML = html;
  setActiveNav('home');
}

function showSector(folder) {
  currentView = 'sector'; currentFolder = folder;
  var m = META[folder] || {};
  var items = DATA.filter(function(d) { return d.folder === folder; });
  var html = '<div class="sector-banner"><span class="back-link" data-action="home">\\u2190 \\uc804\\uccb4 \\uc139\\ud130</span><h2>' + (m.emoji||'') + ' ' + esc(folder) + '</h2><div class="count">' + items.length + '\\ud3b8</div></div>';
  html += renderDateGroups(items);
  main.innerHTML = html;
  setActiveNav('sectors');
  window.scrollTo(0, 0);
}

function showBookmarks() {
  currentView = 'bookmarks'; currentFolder = null;
  var items = DATA.filter(function(d) { return isBookmarked(d.id); });
  var html = '<div class="sector-banner"><h2>\\ubd81\\ub9c8\\ud06c</h2><div class="count">' + items.length + '\\ud3b8</div></div>';
  if (!items.length) html += '<div class="empty">\\ubd81\\ub9c8\\ud06c\\ud55c \\uae00\\uc774 \\uc5c6\\uc2b5\\ub2c8\\ub2e4.</div>';
  else html += renderDateGroups(items);
  main.innerHTML = html;
  setActiveNav('bookmarks');
}

function showSettings() {
  currentView = 'settings'; currentFolder = null;
  var html = '<div class="sector-banner"><h2>\\uc124\\uc815</h2></div>';
  html += '<div class="settings-section">';
  html += '<div class="settings-item"><label>\\uae00\\uc790 \\ud06c\\uae30</label><div class="font-size-btns">' +
    '<button style="font-size:12px" data-action="fontsize" data-size="small" class="' + (fontSize==='small'?'active':'') + '">\\uac00</button>' +
    '<button style="font-size:15px" data-action="fontsize" data-size="medium" class="' + (fontSize==='medium'?'active':'') + '">\\uac00</button>' +
    '<button style="font-size:18px" data-action="fontsize" data-size="large" class="' + (fontSize==='large'?'active':'') + '">\\uac00</button>' +
  '</div></div>';
  html += '<div class="settings-item"><label>\\ucd1d \\uae00 \\uc218</label><span>' + TOTAL + '\\ud3b8</span></div>';
  html += '<div class="settings-item"><label>\\ubd81\\ub9c8\\ud06c</label><span>' + bookmarks.length + '\\uac1c</span></div>';
  html += '</div>';
  main.innerHTML = html;
  setActiveNav('settings');
}

function showSearch(query) {
  var q = query.toLowerCase();
  var items = DATA.filter(function(d) {
    return d.title.toLowerCase().includes(q) ||
      d.tags.join(' ').toLowerCase().includes(q) ||
      d.intro.toLowerCase().includes(q) ||
      (d.paras||[]).some(function(p) { return (p.b||'').toLowerCase().includes(q); });
  });
  var html = '<div class="search-results-label">"' + esc(query) + '" \\uac80\\uc0c9 \\uacb0\\uacfc ' + items.length + '\\uac74</div>';
  if (!items.length) html += '<div class="empty">\\uac80\\uc0c9 \\uacb0\\uacfc\\uac00 \\uc5c6\\uc2b5\\ub2c8\\ub2e4.</div>';
  else html += renderDateGroups(items);
  main.innerHTML = html;
}

function setActiveNav(view) {
  navBtns.forEach(function(btn) { btn.classList.toggle('active', btn.dataset.view === view); });
}

// Event delegation
document.addEventListener('click', function(e) {
  var el = e.target.closest('[data-action]');
  if (!el) return;
  var action = el.dataset.action;
  if (action === 'toggle') {
    el.closest('.article').classList.toggle('open');
  } else if (action === 'bookmark') {
    e.stopPropagation();
    var id = el.dataset.bid;
    toggleBookmark(id);
    var active = isBookmarked(id);
    el.classList.toggle('active', active);
    el.querySelector('svg').setAttribute('fill', active ? '#e8a020' : 'none');
  } else if (action === 'close') {
    e.stopPropagation();
    el.closest('.article').classList.remove('open');
  } else if (action === 'sector') {
    showSector(el.dataset.folder);
  } else if (action === 'home') {
    showHome();
  } else if (action === 'fontsize') {
    fontSize = el.dataset.size;
    localStorage.setItem('mer_fontsize', fontSize);
    var map = {small: '13px', medium: '15px', large: '17px'};
    document.body.style.fontSize = map[fontSize] || '15px';
    showSettings();
  }
});

// Nav
navBtns.forEach(function(btn) {
  btn.addEventListener('click', function() {
    var v = btn.dataset.view;
    searchInput.value = '';
    if (v === 'home') showHome();
    else if (v === 'sectors') showHome();
    else if (v === 'bookmarks') showBookmarks();
    else if (v === 'settings') showSettings();
  });
});

document.getElementById('btnBookmarkNav').addEventListener('click', showBookmarks);

// Search
var searchTimer;
searchInput.addEventListener('input', function() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(function() {
    var q = searchInput.value.trim();
    if (q) showSearch(q);
    else if (currentFolder) showSector(currentFolder);
    else showHome();
  }, 300);
});

// Font size init
(function() {
  var map = {small: '13px', medium: '15px', large: '17px'};
  document.body.style.fontSize = map[fontSize] || '15px';
})();

// Start
showHome();
"""


def main():
    OUTPUT.mkdir(exist_ok=True)

    all_cards, folder_counts = build_all_data()
    print(f"총 {sum(folder_counts.values())}개 글 로드")

    html = render_html(all_cards, folder_counts)
    (OUTPUT / "index.html").write_text(html, encoding="utf-8")
    print(f"→ {OUTPUT}/index.html 생성")

    # PWA
    manifest = {
        "name": "메르 리더",
        "short_name": "메르 리더",
        "description": "메르 블로그 경제 분석 리더",
        "start_url": ".",
        "display": "standalone",
        "background_color": "#faf9f5",
        "theme_color": "#faf9f5",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    sw_js = """const CACHE = 'mer-v2';
self.addEventListener('install', e => { self.skipWaiting(); });
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
    print("완료")


if __name__ == "__main__":
    main()
