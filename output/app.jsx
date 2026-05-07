/* global React, ReactDOM, MR */
const { useState, useEffect, useMemo, useCallback, useRef } = React;
const { SECTORS, sectorMap, Ico, fmtDate, decodeEntities,
        useBookmarks, useHidden, searchPosts, ArticleView, DayGroup, PostRow,
        useClips, useHighlights, useMemos, useLookups, InlineArticle, ClipsDrawer, ChatPanel } = window.MR;

/* ---------- Tweak defaults ---------- */
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "density": "magazine",
  "mode": "magazine",
  "fontSize": "m",
  "theme": "white",
  "showSectorAccent": true,
  "showRelated": true
}/*EDITMODE-END*/;

const FS_LABELS = { s: '작게', m: '보통', l: '크게', xl: '아주 크게' };

/* ---------- Sidebar (desktop) ---------- */
function Sidebar({ filter, setFilter, counts, total, currentBookmarks, hiddenCount }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="mark">메르 리더</div>
        <div className="sub">Meru Reader</div>
        <div className="meta">{total}편 · 2024–2026</div>
      </div>

      <div className="nav-list">
        <div
          className={'nav-item' + (filter.kind === 'all' ? ' active' : '')}
          onClick={() => setFilter({kind: 'all'})}
        >
          <span>전체 글</span>
          <span className="count">{total}</span>
        </div>
        <div
          className={'nav-item' + (filter.kind === 'bookmarks' ? ' active' : '')}
          onClick={() => setFilter({kind: 'bookmarks'})}
        >
          <span>북마크</span>
          <span className="count">{currentBookmarks}</span>
        </div>
        <div
          className={'nav-item' + (filter.kind === 'sectors' ? ' active' : '')}
          onClick={() => setFilter({kind: 'sectors'})}
        >
          <span>섹터 보기</span>
          <span className="count">{SECTORS.length}</span>
        </div>
        <div
          className={'nav-item' + (filter.kind === 'trash' ? ' active' : '')}
          onClick={() => setFilter({kind: 'trash'})}
        >
          <span>휴지통</span>
          <span className="count">{hiddenCount}</span>
        </div>
      </div>

      <div className="nav-list">
        <div className="nav-section-title">섹터</div>
        {SECTORS.map(s => (
          <div
            key={s.name}
            className={'nav-item' + (filter.kind === 'sector' && filter.sector === s.name ? ' active' : '')}
            onClick={() => setFilter({kind: 'sector', sector: s.name})}
            style={{'--c': `var(${s.cssVar})`}}
          >
            <span style={{display:'inline-flex', alignItems:'center', gap:8}}>
              <span style={{fontSize:'0.95rem', lineHeight:1}}>{s.emoji}</span>
              {s.name}
            </span>
            <span className="count">{counts[s.name] || 0}</span>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        2024년 1월부터 2026년 4월까지 메르 블로그<br/>전체 글을 섹터별로 정리한 리더입니다.
      </div>
    </aside>
  );
}

/* ---------- Topbar ---------- */
function Topbar({ q, setQ, fontSize, setFontSize, density, setDensity, openSettings, bookmarkCount, openBookmarks }) {
  const densityIcons = {
    compact: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M3 6h18M3 10h18M3 14h18M3 18h18"/></svg>,
    grid: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>,
    magazine: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M4 6h16M4 11h10M4 11v9M4 16h10M4 20h10M16 11v9M16 11l4 0M16 16l4 0M16 20l4 0"/></svg>,
  };
  const cycleDensity = () => {
    const order = ['compact','grid','magazine'];
    const i = order.indexOf(density);
    setDensity(order[(i+1) % order.length]);
  };
  return (
    <div className="topbar">
      <div className="search">
        <span className="ico"><Ico.Search/></span>
        <input
          type="text"
          placeholder="제목·태그·본문 검색…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      <div className="actions">
        <button
          className="icon-btn"
          title={`보기 방식: ${density === 'compact' ? '컴팩트' : density === 'grid' ? '그리드' : '매거진'}`}
          onClick={cycleDensity}
        >
          {densityIcons[density] || densityIcons.compact}
        </button>
        <button
          className="icon-btn"
          title="글자 크기"
          onClick={() => {
            const order = ['s','m','l','xl'];
            const i = order.indexOf(fontSize);
            setFontSize(order[(i+1) % order.length]);
          }}
        >
          <Ico.Type/>
        </button>
        <button
          className="icon-btn"
          title="북마크"
          onClick={openBookmarks}
        >
          <Ico.Bookmark/>
          {bookmarkCount > 0 && <span className="badge">{bookmarkCount}</span>}
        </button>
        <button className="icon-btn" title="설정" onClick={openSettings}>
          <Ico.Settings/>
        </button>
      </div>
    </div>
  );
}

/* ---------- Mobile bottom tabs ---------- */
function MobileTabs({ filter, setFilter, openSettings }) {
  const at = (k) => filter.kind === k ? ' active' : '';
  return (
    <nav className="mobile-tabs">
      <button className={'tab' + at('all')} onClick={() => setFilter({kind:'all'})}>
        <Ico.Home/><span className="lab">홈</span>
      </button>
      <button className={'tab' + at('sectors')} onClick={() => setFilter({kind:'sectors'})}>
        <Ico.Grid/><span className="lab">섹터</span>
      </button>
      <button className={'tab' + at('bookmarks')} onClick={() => setFilter({kind:'bookmarks'})}>
        <Ico.Bookmark/><span className="lab">북마크</span>
      </button>
      <button className="tab" onClick={openSettings}>
        <Ico.Settings/><span className="lab">설정</span>
      </button>
    </nav>
  );
}

/* ---------- Sector grid (homepage card view) ---------- */
function SectorGrid({ counts, setFilter }) {
  return (
    <>
      <div className="page-head">
        <div className="eyebrow">Sectors</div>
        <h2>섹터별로 보기</h2>
        <div className="ph-sub">9개 주제로 분류된 메르의 글 — 관심 있는 분야부터 골라 읽어보세요.</div>
      </div>
      <div className="sector-grid">
        {SECTORS.map(s => (
          <div
            key={s.name}
            className="sector-card"
            onClick={() => setFilter({kind:'sector', sector: s.name})}
            style={{'--c': `var(${s.cssVar})`}}
          >
            <div className="emoji">{s.emoji}</div>
            <div className="name">{s.name}</div>
            <div className="sub">{s.sub}</div>
            <div className="num">{counts[s.name] || 0}<small>편</small></div>
          </div>
        ))}
      </div>
    </>
  );
}

/* ---------- Masthead (home) ---------- */
function Masthead({ total, sectorCount, bookmarkCount }) {
  return (
    <header className="masthead">
      <div className="eyebrow">메르 블로그 · 2024 — 2026</div>
      <h1>읽고, 잇고, 남기는<br/>경제·산업 일지</h1>
      <p className="lede">
        지정학에서 반도체, 한화의 인적분할까지 — 메르가 풀어낸 한 시대의 흐름을
        한 권의 책처럼 펼쳐 읽습니다.
      </p>
      <div className="stats">
        <div className="stat"><div className="n">{total}</div><div className="l">총 글</div></div>
        <div className="stat"><div className="n">{sectorCount}</div><div className="l">섹터</div></div>
        <div className="stat"><div className="n">{bookmarkCount}</div><div className="l">내 북마크</div></div>
      </div>
    </header>
  );
}

/* ---------- Page-head (sector / bookmark) ---------- */
function PageHead({ eyebrow, title, sub }) {
  return (
    <header className="page-head">
      <div className="eyebrow">{eyebrow}</div>
      <h2>{title}</h2>
      {sub && <div className="ph-sub">{sub}</div>}
    </header>
  );
}

/* ---------- Group posts by date ---------- */
function groupByDate(posts) {
  const map = new Map();
  for (const p of posts) {
    if (!map.has(p.date)) map.set(p.date, []);
    map.get(p.date).push(p);
  }
  return [...map.entries()].sort((a,b) => b[0].localeCompare(a[0]));
}

/* ---------- App ---------- */
function App() {
  const data = window.MERU_DATA;

  const [tweaks, setTweak] = window.useTweaks
    ? window.useTweaks(TWEAK_DEFAULTS)
    : [TWEAK_DEFAULTS, () => {}];

  const [filter, setFilter] = useState(() => {
    const saved = sessionStorage.getItem('meru_filter');
    if (saved) try { return JSON.parse(saved); } catch {}
    return { kind: 'sectors' };
  });
  const [q, setQ] = useState('');
  const [expandedTitle, setExpandedTitle] = useState(null);
  const [showClips, setShowClips] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [marks, toggleMark] = useBookmarks();
  const { hidden, hide: hidePost, restore: restorePost, restoreAll: restoreAllPosts } = useHidden();
  const { clips, add: addClipRaw, remove: removeClipRaw, clear: clearClipsRaw, setAll: setAllClips } = useClips();
  const { highlights, add: addHLRaw, remove: removeHLRaw, clear: clearHLRaw, setAll: setAllHL } = useHighlights();
  const { memos, add: addMemoRaw, remove: removeMemoRaw, clear: clearMemoRaw, update: updateMemoRaw, setAll: setAllMemos } = useMemos();
  const { lookups, add: addLookupRaw, remove: removeLookupRaw, clear: clearLookupRaw, setAll: setAllLookups } = useLookups();

  // Undo stack: snapshots of prev state per key
  const undoRef = useRef([]);
  const settersRef = useRef({});
  settersRef.current = { clips: setAllClips, highlights: setAllHL, memos: setAllMemos, lookups: setAllLookups };
  const snapshotsRef = useRef({});
  snapshotsRef.current = { clips, highlights, memos, lookups };

  const pushUndo = (key) => {
    const prev = snapshotsRef.current[key];
    undoRef.current.push({key, prev: [...prev]});
    if (undoRef.current.length > 30) undoRef.current.shift();
  };
  const undo = useCallback(() => {
    const last = undoRef.current.pop();
    if (!last) return;
    settersRef.current[last.key]?.(last.prev);
  }, []);

  const addClip = useCallback((item) => { pushUndo('clips'); addClipRaw(item); }, [addClipRaw]);
  const removeClip = useCallback((id) => { pushUndo('clips'); removeClipRaw(id); }, [removeClipRaw]);
  const clearClips = useCallback(() => { pushUndo('clips'); clearClipsRaw(); }, [clearClipsRaw]);
  const addHL = useCallback((item) => { pushUndo('highlights'); addHLRaw(item); }, [addHLRaw]);
  const removeHL = useCallback((id) => { pushUndo('highlights'); removeHLRaw(id); }, [removeHLRaw]);
  const clearHL = useCallback(() => { pushUndo('highlights'); clearHLRaw(); }, [clearHLRaw]);
  const addMemo = useCallback((item) => { pushUndo('memos'); addMemoRaw(item); }, [addMemoRaw]);
  const removeMemo = useCallback((id) => { pushUndo('memos'); removeMemoRaw(id); }, [removeMemoRaw]);
  const clearMemo = useCallback(() => { pushUndo('memos'); clearMemoRaw(); }, [clearMemoRaw]);
  const addLookup = useCallback((item) => { pushUndo('lookups'); addLookupRaw(item); }, [addLookupRaw]);
  const removeLookup = useCallback((id) => { pushUndo('lookups'); removeLookupRaw(id); }, [removeLookupRaw]);
  const clearLookup = useCallback(() => { pushUndo('lookups'); clearLookupRaw(); }, [clearLookupRaw]);
  // memo position update — not undoable
  const updateMemo = updateMemoRaw;

  // Global Ctrl/Cmd+Z undo
  useEffect(() => {
    const onKey = (e) => {
      if (!(e.metaKey || e.ctrlKey)) return;
      if (e.key.toLowerCase() !== 'z' || e.shiftKey) return;
      const tag = (e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) return;
      e.preventDefault();
      undo();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [undo]);

  // persist filter
  useEffect(() => {
    sessionStorage.setItem('meru_filter', JSON.stringify(filter));
  }, [filter]);

  // apply mode + font-size + density to body
  useEffect(() => {
    document.body.classList.remove('mode-magazine','mode-newspaper','mode-minimal');
    document.body.classList.add('mode-' + (tweaks.mode || 'magazine'));
    document.body.classList.remove('density-compact','density-grid','density-magazine');
    document.body.classList.add('density-' + (tweaks.density || 'compact'));
    document.body.classList.remove('theme-paper','theme-white');
    document.body.classList.add('theme-' + (tweaks.theme || 'white'));
    document.body.dataset.fs = tweaks.fontSize || 'm';
  }, [tweaks.mode, tweaks.fontSize, tweaks.density, tweaks.theme]);

  // counts per sector (excluding hidden)
  const counts = useMemo(() => {
    const c = {};
    data.forEach(d => { if (!hidden.has(d.title)) c[d.folder] = (c[d.folder] || 0) + 1; });
    return c;
  }, [data, hidden]);
  const visibleTotal = useMemo(() => data.filter(d => !hidden.has(d.title)).length, [data, hidden]);
  const visibleBookmarks = useMemo(() => [...marks].filter(t => !hidden.has(t)).length, [marks, hidden]);

  // filter pipeline
  const filteredPosts = useMemo(() => {
    let posts = data;
    if (filter.kind === 'trash') {
      posts = posts.filter(p => hidden.has(p.title));
    } else {
      posts = posts.filter(p => !hidden.has(p.title));
      if (filter.kind === 'sector') posts = posts.filter(p => p.folder === filter.sector);
      else if (filter.kind === 'bookmarks') posts = posts.filter(p => marks.has(p.title));
    }
    posts = searchPosts(posts, q);
    posts = [...posts].sort((a,b) => b.date.localeCompare(a.date));
    return posts;
  }, [data, filter, q, marks, hidden]);

  const grouped = useMemo(() => groupByDate(filteredPosts), [filteredPosts]);

  const handleOpen = useCallback((p) => {
    setExpandedTitle(prev => prev === p.title ? null : p.title);
    // smooth scroll to row after a tick
    setTimeout(() => {
      const el = document.querySelector('.row.expanded');
      if (el) {
        const top = el.getBoundingClientRect().top + window.scrollY - 80;
        window.scrollTo({top, behavior: 'smooth'});
      }
    }, 50);
  }, []);
  const handleClose = useCallback(() => setExpandedTitle(null), []);

  const handleJumpToClip = useCallback((clip) => {
    setShowClips(false);
    const post = data.find(p => p.title === clip.title);
    if (post) {
      setFilter({kind: 'all'});
      setQ('');
      setExpandedTitle(post.title);
      setTimeout(() => {
        const el = document.querySelector('.row.expanded');
        if (el) {
          const top = el.getBoundingClientRect().top + window.scrollY - 60;
          window.scrollTo({top, behavior: 'smooth'});
        }
      }, 200);
    }
  }, [data]);

  // settings panel toggle (just opens tweaks if available, otherwise font cycle)
  const openSettings = () => {
    window.parent.postMessage({type:'__edit_mode_request'}, '*');
  };

  // Build inline article slot for the currently expanded row
  const expandedPost = expandedTitle ? data.find(p => p.title === expandedTitle) : null;
  const clipsForPost = expandedPost ? clips.filter(c => c.title === expandedPost.title) : [];
  const hlForPost = expandedPost ? highlights.filter(h => h.title === expandedPost.title) : [];
  const memosForPost = expandedPost ? memos.filter(m => m.title === expandedPost.title) : [];
  const lookupsForPost = expandedPost ? lookups.filter(l => l.title === expandedPost.title) : [];
  const expandedSlot = expandedPost ? (
    <InlineArticle
      post={expandedPost}
      onClose={handleClose}
      onClip={addClip}
      clipsForPost={clipsForPost}
      onHighlight={addHL}
      highlightsForPost={hlForPost}
      onMemo={addMemo}
      memosForPost={memosForPost}
      onUpdateMemo={updateMemo}
      onLookup={addLookup}
      lookupsForPost={lookupsForPost}
    />
  ) : null;

  /* render content area */
  let body;
  if (filter.kind === 'sectors') {
    body = <SectorGrid counts={counts} setFilter={setFilter}/>;
  } else if (filter.kind === 'bookmarks') {
    body = (
      <>
        <PageHead eyebrow="My Library" title="북마크"
          sub={`저장한 글 ${visibleBookmarks}편${q ? ` · 검색 결과 ${filteredPosts.length}편` : ''}`}/>
        <Timeline grouped={grouped} q={q} onOpen={handleOpen} marks={marks} toggleMark={toggleMark}
          expandedTitle={expandedTitle} expandedSlot={expandedSlot}
          onHide={hidePost} hidden={hidden}
          emptyMsg={visibleBookmarks === 0 ? '아직 저장한 글이 없습니다.' : '검색 결과가 없습니다.'}/>
      </>
    );
  } else if (filter.kind === 'trash') {
    body = (
      <>
        <PageHead eyebrow="Trash" title="휴지통"
          sub={`숨긴 글 ${hidden.size}편${q ? ` · 검색 결과 ${filteredPosts.length}편` : ''}`}/>
        {hidden.size > 0 && (
          <div style={{padding:'0 36px 12px'}}>
            <button
              className="icon-btn"
              style={{padding:'8px 14px', fontSize:'0.85rem'}}
              onClick={() => { if (confirm(`숨긴 글 ${hidden.size}편을 모두 복원할까요?`)) restoreAllPosts(); }}
            >전체 복원</button>
          </div>
        )}
        <Timeline grouped={grouped} q={q} onOpen={handleOpen} marks={marks} toggleMark={toggleMark}
          expandedTitle={expandedTitle} expandedSlot={expandedSlot}
          onRestore={restorePost} hidden={hidden}
          emptyMsg={hidden.size === 0 ? '휴지통이 비어 있습니다.' : '검색 결과가 없습니다.'}/>
      </>
    );
  } else if (filter.kind === 'sector') {
    const sec = sectorMap[filter.sector];
    body = (
      <>
        <PageHead eyebrow={sec?.sub || ''} title={filter.sector}
          sub={`${counts[filter.sector] || 0}편${q ? ` · 검색 결과 ${filteredPosts.length}편` : ''}`}/>
        <Timeline grouped={grouped} q={q} onOpen={handleOpen} marks={marks} toggleMark={toggleMark}
          expandedTitle={expandedTitle} expandedSlot={expandedSlot}
          onHide={hidePost} hidden={hidden}/>
      </>
    );
  } else {
    body = (
      <>
        <Masthead total={visibleTotal} sectorCount={SECTORS.length} bookmarkCount={visibleBookmarks}/>
        {q && <div style={{padding:'0 36px 16px', fontSize:'0.85rem', color:'var(--muted)'}}>
          검색 “{q}” — {filteredPosts.length}편
        </div>}
        <Timeline grouped={grouped} q={q} onOpen={handleOpen} marks={marks} toggleMark={toggleMark}
          expandedTitle={expandedTitle} expandedSlot={expandedSlot}
          onHide={hidePost} hidden={hidden}/>
      </>
    );
  }

  return (
    <>
      <div className="app">
        <Sidebar filter={filter} setFilter={setFilter} counts={counts}
          total={visibleTotal} currentBookmarks={visibleBookmarks} hiddenCount={hidden.size}/>
        <div className="content">
          <Topbar q={q} setQ={setQ}
            fontSize={tweaks.fontSize}
            setFontSize={(v) => setTweak('fontSize', v)}
            density={tweaks.density}
            setDensity={(v) => setTweak('density', v)}
            openSettings={openSettings}
            bookmarkCount={marks.size}
            openBookmarks={() => setFilter({kind:'bookmarks'})}/>
          {body}
        </div>
      </div>

      <MobileTabs filter={filter} setFilter={setFilter} openSettings={openSettings}/>

      {(clips.length + highlights.length + memos.length + lookups.length) > 0 && (
        <button className="clips-fab" onClick={() => setShowClips(true)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          내 서랍
          <span className="num">{clips.length + highlights.length + memos.length + lookups.length}</span>
        </button>
      )}

      <button className="chat-fab" onClick={() => setShowChat(true)} title="AI 도움말">
        AI
      </button>

      <ChatPanel open={showChat} onClose={() => setShowChat(false)} currentPost={expandedPost}
        onSaveClip={addClip} onSaveLookup={addLookup}/>

      {showClips && (
        <ClipsDrawer
          clips={clips}
          onClose={() => setShowClips(false)}
          onRemove={removeClip}
          onClear={clearClips}
          onJump={handleJumpToClip}
          highlights={highlights}
          onRemoveHL={removeHL}
          onClearHL={clearHL}
          memos={memos}
          onRemoveMemo={removeMemo}
          onClearMemo={clearMemo}
          lookups={lookups}
          onRemoveLookup={removeLookup}
          onClearLookup={clearLookup}
        />
      )}
    </>
  );
}

/* ---------- Timeline ---------- */
function Timeline({ grouped, q, onOpen, marks, toggleMark, emptyMsg, expandedTitle, expandedSlot, onHide, onRestore, hidden }) {
  if (grouped.length === 0) {
    return (
      <div className="empty">
        <div className="e-mark">¶</div>
        <div className="e-msg">{emptyMsg || '결과가 없습니다.'}</div>
      </div>
    );
  }
  return (
    <div className="timeline">
      {grouped.map(([date, posts]) => (
        <DayGroup key={date} date={date} posts={posts} onOpen={onOpen}
          marks={marks} toggleMark={toggleMark}
          expandedTitle={expandedTitle} expandedSlot={expandedSlot}
          onHide={onHide} onRestore={onRestore} hidden={hidden}/>
      ))}
    </div>
  );
}

/* ---------- Tweaks Panel ---------- */
function TweaksUI() {
  if (!window.TweaksPanel) return null;
  const { TweaksPanel, useTweaks, TweakSection, TweakRadio, TweakSelect } = window;
  const [tw, setTw] = useTweaks(TWEAK_DEFAULTS);

  return (
    <TweaksPanel title="Tweaks">
      <TweakSection label="배경 톤">
        <TweakRadio
          label="Theme"
          value={tw.theme}
          onChange={(v) => setTw('theme', v)}
          options={[
            {value: 'white', label: '화이트'},
            {value: 'paper', label: '종이'},
          ]}
        />
      </TweakSection>
      <TweakSection label="목록 밀도">
        <TweakRadio
          label="Density"
          value={tw.density}
          onChange={(v) => setTw('density', v)}
          options={[
            {value: 'compact', label: '컴팩트'},
            {value: 'grid', label: '그리드'},
            {value: 'magazine', label: '매거진'},
          ]}
        />
      </TweakSection>
      <TweakSection label="아티클 스타일">
        <TweakRadio
          label="Mode"
          value={tw.mode}
          onChange={(v) => setTw('mode', v)}
          options={[
            {value: 'magazine', label: '매거진'},
            {value: 'newspaper', label: '신문'},
            {value: 'minimal', label: '미니멀'},
          ]}
        />
      </TweakSection>
      <TweakSection label="글자 크기">
        <TweakRadio
          label="Size"
          value={tw.fontSize}
          onChange={(v) => setTw('fontSize', v)}
          options={[
            {value:'s', label:'S'},
            {value:'m', label:'M'},
            {value:'l', label:'L'},
            {value:'xl', label:'XL'},
          ]}
        />
      </TweakSection>
    </TweaksPanel>
  );
}

/* ---------- mount ---------- */
ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
ReactDOM.createRoot(document.getElementById('tweaks-root')).render(<TweaksUI/>);
