/* global React */
const { useState, useEffect, useMemo, useRef, useCallback } = React;

/* ---------- Sector metadata ---------- */
const SECTORS = [
  { name: '지정학', sub: '중동·중국', cssVar: '--c-geo', emoji: '🌍' },
  { name: '금융·통화', sub: '금리·환율', cssVar: '--c-fin', emoji: '💵' },
  { name: '미국·글로벌', sub: '미국경제·정책', cssVar: '--c-us', emoji: '🇺🇸' },
  { name: '부동산', sub: '건설·PF', cssVar: '--c-realty', emoji: '🏘️' },
  { name: '기술·산업', sub: '반도체·AI·배터리', cssVar: '--c-tech', emoji: '⚙️' },
  { name: '에너지·자원', sub: '원자재·기후', cssVar: '--c-energy', emoji: '⚡' },
  { name: '자본시장', sub: '주식·투자', cssVar: '--c-cap', emoji: '📈' },
  { name: '중후장대', sub: '조선·방산', cssVar: '--c-heavy', emoji: '🚢' },
  { name: '한국경제', sub: '국내정책', cssVar: '--c-kr', emoji: '🇰🇷' },
];
const sectorMap = Object.fromEntries(SECTORS.map(s => [s.name, s]));

/* ---------- Icons ---------- */
const Ico = {
  Search: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>,
  Bookmark: ({filled}) => <svg width="18" height="18" viewBox="0 0 24 24" fill={filled?'currentColor':'none'} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>,
  Settings: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h0a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h0a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v0a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
  Close: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>,
  Arrow: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="m9 18 6-6-6-6"/></svg>,
  Home: () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>,
  Grid: () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>,
  Type: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>,
  Back: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="m15 18-6-6 6-6"/></svg>,
  Trash: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>,
  Restore: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>,
};

/* ---------- Date helpers ---------- */
const WK = ['일','월','화','수','목','금','토'];
function fmtDate(s) {
  const d = new Date(s+'T00:00:00');
  return `${d.getFullYear()}년 ${d.getMonth()+1}월 ${d.getDate()}일`;
}
function fmtDateShort(s) {
  const d = new Date(s+'T00:00:00');
  return `${d.getMonth()+1}/${d.getDate()}`;
}
function dayWeek(s) {
  const d = new Date(s+'T00:00:00');
  return WK[d.getDay()] + '요일';
}
function decodeEntities(s) {
  if (!s) return '';
  return s.replace(/&#x27;/g,"'").replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&lt;/g,'<').replace(/&gt;/g,'>');
}

/* ---------- Bookmarks (localStorage) ---------- */
function useBookmarks() {
  const [marks, setMarks] = useState(() => {
    try { return new Set(JSON.parse(localStorage.getItem('meru_bookmarks') || '[]')); }
    catch { return new Set(); }
  });
  const toggle = useCallback((title) => {
    setMarks(prev => {
      const next = new Set(prev);
      if (next.has(title)) next.delete(title); else next.add(title);
      localStorage.setItem('meru_bookmarks', JSON.stringify([...next]));
      return next;
    });
  }, []);
  return [marks, toggle];
}

/* ---------- Hidden posts (localStorage) ---------- */
function useHidden() {
  const [hidden, setHidden] = useState(() => {
    try { return new Set(JSON.parse(localStorage.getItem('meru_hidden') || '[]')); }
    catch { return new Set(); }
  });
  const persist = (s) => localStorage.setItem('meru_hidden', JSON.stringify([...s]));
  const hide = useCallback((title) => {
    setHidden(prev => { const n = new Set(prev); n.add(title); persist(n); return n; });
  }, []);
  const restore = useCallback((title) => {
    setHidden(prev => { const n = new Set(prev); n.delete(title); persist(n); return n; });
  }, []);
  const restoreAll = useCallback(() => {
    setHidden(() => { const n = new Set(); persist(n); return n; });
  }, []);
  return { hidden, hide, restore, restoreAll };
}

/* ---------- Search ---------- */
function searchPosts(data, q) {
  if (!q || !q.trim()) return data;
  const ql = q.trim().toLowerCase();
  return data.filter(d => {
    if (d.title.toLowerCase().includes(ql)) return true;
    if (d.tags.some(t => t.toLowerCase().includes(ql))) return true;
    if (d.intro && d.intro.toLowerCase().includes(ql)) return true;
    if (d.paras && d.paras.some(p => (p.body||'').toLowerCase().includes(ql) || (p.title||'').toLowerCase().includes(ql))) return true;
    return false;
  });
}

/* ---------- Row ---------- */
function PostRow({ post, onOpen, isBookmarked, onToggleBookmark, showDate, isExpanded, expandedSlot, onHide, onRestore, isHidden }) {
  const sec = sectorMap[post.folder];
  const cssVar = sec?.cssVar;
  return (<>
    <div className={'row' + (isExpanded ? ' expanded' : '')} onClick={onOpen} style={cssVar ? {'--c': `var(${cssVar})`} : {}}>
      <div className="row-body">
        <h3 className="row-title">{decodeEntities(post.title)}</h3>
        <p className="row-excerpt">{decodeEntities(post.intro)}</p>
        <div className="row-meta-bottom">
          {showDate && <span className="row-date">{fmtDateShort(post.date)}</span>}
          <span className="row-sector"><span className="emoji">{sec?.emoji || '📰'}</span>{post.folder || '미분류'}</span>
          <div className="row-tags">
            {post.tags.slice(0, 3).map((t,i) => <span className="t" key={i}>{t}</span>)}
          </div>
        </div>
      </div>
      <div className="row-actions">
        <button
          className={'bookmark-btn' + (isBookmarked ? ' on' : '')}
          onClick={(e) => { e.stopPropagation(); onToggleBookmark(post.title); }}
          aria-label="북마크"
          title={isBookmarked ? '북마크 해제' : '북마크'}
        >
          <Ico.Bookmark filled={isBookmarked}/>
        </button>
        {isHidden ? (
          onRestore && (
            <button
              className="bookmark-btn"
              onClick={(e) => { e.stopPropagation(); onRestore(post.title); }}
              aria-label="복원"
              title="복원"
            ><Ico.Restore/></button>
          )
        ) : (
          onHide && (
            <button
              className="bookmark-btn"
              onClick={(e) => {
                e.stopPropagation();
                if (confirm('이 글을 숨길까요? 휴지통에서 다시 복원할 수 있습니다.')) onHide(post.title);
              }}
              aria-label="숨김"
              title="숨김 (휴지통으로 이동)"
            ><Ico.Trash/></button>
          )
        )}
      </div>
    </div>
    {isExpanded && expandedSlot}
  </>);
}

/* ---------- Day Group ---------- */
function DayGroup({ date, posts, onOpen, marks, toggleMark, expandedTitle, expandedSlot, onHide, onRestore, hidden }) {
  return (
    <div className="day-group">
      <div className="day-head">
        <span className="d">{fmtDate(date)}</span>
        <span className="w">{dayWeek(date)}</span>
        <span className="c">{posts.length}편</span>
      </div>
      <div className="row-list">
        {posts.map((p, i) => (
          <PostRow key={p.title+i} post={p} onOpen={() => onOpen(p)}
            isBookmarked={marks.has(p.title)} onToggleBookmark={toggleMark}
            showDate={true}
            isExpanded={expandedTitle === p.title}
            expandedSlot={expandedTitle === p.title ? expandedSlot : null}
            onHide={onHide} onRestore={onRestore}
            isHidden={hidden ? hidden.has(p.title) : false}/>
        ))}
      </div>
    </div>
  );
}

window.MR = { SECTORS, sectorMap, Ico, fmtDate, fmtDateShort, dayWeek, decodeEntities, useBookmarks, useHidden, searchPosts, PostRow, DayGroup };
