/* global React, ReactDOM, MR */
const { useState, useEffect, useMemo, useRef, useCallback } = React;
const { sectorMap, Ico, fmtDate, decodeEntities } = window.MR;

/* ---------- Generic localStorage list hook ---------- */
function useStorageList(key) {
  const [items, setItems] = useState(() => {
    try { return JSON.parse(localStorage.getItem(key) || '[]'); }
    catch { return []; }
  });
  const persist = (next) => { localStorage.setItem(key, JSON.stringify(next)); };
  const add = useCallback((item) => {
    setItems(prev => {
      const next = [{...item, id: Date.now()+Math.random(), createdAt: Date.now()}, ...prev];
      persist(next);
      return next;
    });
  }, [key]);
  const remove = useCallback((id) => {
    setItems(prev => {
      const next = prev.filter(c => c.id !== id);
      persist(next);
      return next;
    });
  }, [key]);
  const clear = useCallback(() => { setItems([]); persist([]); }, [key]);
  const update = useCallback((id, patch) => {
    setItems(prev => {
      const next = prev.map(c => c.id === id ? {...c, ...patch} : c);
      persist(next);
      return next;
    });
  }, [key]);
  const setAll = useCallback((arr) => { setItems(arr); persist(arr); }, [key]);
  return { items, add, remove, clear, update, setAll };
}

function useClips() {
  const { items: clips, add, remove, clear, setAll } = useStorageList('meru_clips');
  return { clips, add, remove, clear, setAll };
}
function useHighlights() {
  const { items: highlights, add, remove, clear, setAll } = useStorageList('meru_highlights');
  return { highlights, add, remove, clear, setAll };
}
function useMemos() {
  const { items: memos, add, remove, clear, update, setAll } = useStorageList('meru_memos');
  return { memos, add, remove, clear, update, setAll };
}
function useLookups() {
  const { items: lookups, add, remove, clear, setAll } = useStorageList('meru_lookups');
  return { lookups, add, remove, clear, setAll };
}

/* ---------- Drag-to-clip popover ---------- */
function ClipPopover({ container, onClip, onHighlight, onMemo, onLookup }) {
  const [pop, setPop] = useState(null);
  const [memoMode, setMemoMode] = useState(false);
  const [memoText, setMemoText] = useState('');
  const memoRef = useRef(null);
  const timerRef = useRef(null);

  const checkSelection = useCallback(() => {
    if (!container) return;
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;
    const text = sel.toString().trim();
    if (text.length < 4) return;
    const range = sel.getRangeAt(0);
    if (!container.contains(range.commonAncestorContainer)) return;
    const rect = range.getBoundingClientRect();
    const cRect = container.getBoundingClientRect();
    setPop({
      x: Math.max(20, Math.min(rect.left + rect.width/2 - cRect.left, cRect.width - 20)),
      y: rect.top - cRect.top,
      text,
    });
    setMemoMode(false);
    setMemoText('');
  }, [container]);

  useEffect(() => {
    if (!container) return;
    const onMouseUp = () => { checkSelection(); };
    const onSelChange = () => {
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(checkSelection, 300);
    };
    const onDown = (e) => {
      if (e.target.closest('.clip-popover')) return;
      setPop(null); setMemoMode(false); setMemoText('');
    };
    document.addEventListener('mouseup', onMouseUp);
    document.addEventListener('selectionchange', onSelChange);
    document.addEventListener('mousedown', onDown);
    document.addEventListener('touchstart', onDown);
    return () => {
      clearTimeout(timerRef.current);
      document.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('selectionchange', onSelChange);
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('touchstart', onDown);
    };
  }, [container, checkSelection]);

  useEffect(() => {
    if (memoMode && memoRef.current) memoRef.current.focus();
  }, [memoMode]);

  const dismiss = () => { setPop(null); setMemoMode(false); setMemoText(''); window.getSelection().removeAllRanges(); };

  if (!pop) return null;
  return (
    <div className="clip-popover" style={{left: pop.x, top: pop.y}}
         onTouchStart={e => e.stopPropagation()}>
      {!memoMode ? (
        <>
          <button onClick={() => { onHighlight(pop.text); dismiss(); }} title="형광펜">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
            형광펜
          </button>
          <button onClick={() => setMemoMode(true)} title="메모">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            메모
          </button>
          <button onClick={() => { onLookup(pop.text); dismiss(); }} title="나중에 찾아볼 것">
            <span style={{fontWeight:700, fontSize:'0.95rem', display:'inline-block', width:14, textAlign:'center'}}>?</span>
            모름
          </button>
          <button onClick={() => { onClip(pop.text); dismiss(); }} title="클립">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M5 12l5 5L20 7"/></svg>
            클립
          </button>
          <button onClick={() => { navigator.clipboard?.writeText(pop.text); dismiss(); }} title="복사">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            복사
          </button>
        </>
      ) : (
        <div className="memo-input-row" onTouchStart={e => e.stopPropagation()}>
          <input ref={memoRef} className="memo-input" type="text" placeholder="메모 입력…"
            value={memoText} onChange={e => setMemoText(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && memoText.trim()) { onMemo(pop.text, memoText.trim()); dismiss(); } }}
          />
          <button className="memo-save" onClick={() => { if (memoText.trim()) { onMemo(pop.text, memoText.trim()); dismiss(); } }}>
            저장
          </button>
          <button className="memo-cancel" onClick={() => setMemoMode(false)}>취소</button>
        </div>
      )}
    </div>
  );
}

/* ---------- Highlight markers inside body ---------- */
function highlightAll(text, clipTexts, highlightTexts, memoItems, lookupTexts, onUpdateMemo) {
  if (!text) return decodeEntities(text);
  const decoded = decodeEntities(text);
  const markers = [];
  (clipTexts || []).forEach(t => markers.push({text: t, type: 'clip'}));
  (highlightTexts || []).forEach(t => markers.push({text: t, type: 'highlight'}));
  (memoItems || []).forEach(m => markers.push({text: m.text, type: 'memo', memo: m.memo, id: m.id, pos: m.pos}));
  (lookupTexts || []).forEach(t => markers.push({text: t, type: 'lookup'}));
  if (!markers.length) return decoded;
  const prio = {memo: 0, lookup: 1, highlight: 2, clip: 3};
  markers.sort((a,b) => b.text.length - a.text.length || prio[a.type] - prio[b.type]);
  const seen = new Set();
  const unique = markers.filter(m => { if (seen.has(m.text)) return false; seen.add(m.text); return true; });

  let parts = [decoded];
  for (const marker of unique) {
    const next = [];
    for (const p of parts) {
      if (typeof p !== 'string') { next.push(p); continue; }
      const idx = p.indexOf(marker.text);
      if (idx === -1) { next.push(p); continue; }
      if (idx > 0) next.push(p.slice(0, idx));
      next.push({...marker});
      const rest = p.slice(idx + marker.text.length);
      if (rest) next.push(rest);
    }
    parts = next;
  }
  return parts.map((p, i) => {
    if (typeof p === 'string') return p;
    if (p.type === 'memo') return <MemoMark key={i} id={p.id} text={p.text} memo={p.memo} pos={p.pos} onUpdate={onUpdateMemo}/>;
    if (p.type === 'lookup') return <LookupMark key={i} text={p.text}/>;
    const cls = p.type === 'highlight' ? 'highlight-mark' : 'clip-mark';
    return <mark key={i} className={cls}>{p.text}</mark>;
  });
}

function highlightClips(text, clips) { return highlightAll(text, clips, [], [], [], null); }

/* ---------- Lookup mark (?) ---------- */
function LookupMark({ text }) {
  return (
    <mark className="lookup-mark" title="나중에 찾아볼 것">
      {text}
      <span className="lookup-icon">?</span>
    </mark>
  );
}

/* ---------- Memo mark with hover tooltip ---------- */
function MemoMark({ text, memo }) {
  const [hover, setHover] = useState(false);
  return (
    <span className="memo-mark-wrap" style={{position:'relative', display:'inline'}}
          onMouseEnter={() => setHover(true)}
          onMouseLeave={() => setHover(false)}>
      <mark className="memo-mark">
        {text}
        <span className="memo-icon">💬</span>
      </mark>
      {hover && (
        <span className="memo-tooltip">{memo}</span>
      )}
    </span>
  );
}

/* ---------- Inline article ---------- */
function InlineArticle({ post, onClose, onClip, clipsForPost, onHighlight, highlightsForPost,
                        onMemo, memosForPost, onUpdateMemo, onLookup, lookupsForPost }) {
  const ref = useRef(null);
  const [containerEl, setContainerEl] = useState(null);
  const sec = sectorMap[post.folder];
  const clipTexts = clipsForPost.map(c => c.text);
  const hlTexts = (highlightsForPost || []).map(h => h.text);
  const memoItems = (memosForPost || []).map(m => ({id: m.id, text: m.text, memo: m.memo, pos: m.pos}));
  const lookupTexts = (lookupsForPost || []).map(l => l.text);

  const setContainer = useCallback((node) => {
    ref.current = node;
    setContainerEl(node);
  }, []);

  const postMeta = { title: post.title, folder: post.folder, date: post.date, link: post.link };
  const handleClip = (text) => onClip({text, ...postMeta});
  const handleHL = (text) => onHighlight({text, ...postMeta});
  const handleMemo = (text, memo) => onMemo({text, memo, ...postMeta});
  const handleLookup = (text) => onLookup({text, ...postMeta});

  const hl = (text) => highlightAll(text, clipTexts, hlTexts, memoItems, lookupTexts, onUpdateMemo);

  return (
    <div className="inline-article" ref={setContainer} style={sec ? {'--c': `var(${sec.cssVar})`} : {}}>
      <button className="ia-close" onClick={onClose} aria-label="닫기"><Ico.Close/></button>
      <div className="ia-kicker">
        <span className="dot" style={sec ? {background: `var(${sec.cssVar})`} : {}}/>
        {post.folder}
      </div>
      <h2 className="ia-title">{decodeEntities(post.title)}</h2>
      <div className="ia-byline">
        <span>{fmtDate(post.date)}</span>
        <span className="sep"/>
        <span>{(post.paras||[]).length + 1}분 읽기</span>
      </div>

      <p className="ia-lede dropcap">{hl(post.intro)}</p>

      {(post.intro_anns || []).map((a, i) => <AnnotationInline key={'ia'+i} a={a}/>)}

      {(post.paras||[]).length > 0 && (
        <>
          <div className="ia-section-h">본문</div>
          {post.paras.map((p, i) => (
            <div className="ia-para" key={i}>
              {p.title && <h3 className="ia-para-title">{hl(p.title)}</h3>}
              <p className="ia-para-body">{hl(p.body)}</p>
              {(p.anns || []).map((a, j) => <AnnotationInline key={'pa'+i+'_'+j} a={a}/>)}
            </div>
          ))}
        </>
      )}

      {(post.question || post.answer) && (
        <div>
          {post.question && <div className="ia-pull-q">{hl(post.question)}</div>}
          {post.answer && <div className="ia-pull-a">{hl(post.answer)}</div>}
        </div>
      )}

      <div className="ia-foot">
        <div className="src" style={{fontSize:'0.78rem', color:'var(--muted)'}}>
          ¶ {fmtDate(post.date)} · {post.folder || '미분류'}
        </div>
      </div>

      <ClipPopover container={containerEl} onClip={handleClip} onHighlight={handleHL}
                   onMemo={handleMemo} onLookup={handleLookup}/>
    </div>
  );
}

function AnnotationInline({ a }) {
  const isTerm = a.유형 === '용어풀이';
  return (
    <div className="annotation-inline">
      <span className="ann-type">{isTerm ? '용어' : '맥락'}</span>
      {isTerm && a.대상 && <span className="ann-target">{a.대상}</span>}
      {decodeEntities(a.내용)}
    </div>
  );
}

/* ---------- Clips drawer (4 tabs) ---------- */
function ClipsDrawer({ clips, onClose, onRemove, onClear, onJump,
                       highlights, onRemoveHL, onClearHL,
                       memos, onRemoveMemo, onClearMemo,
                       lookups, onRemoveLookup, onClearLookup }) {
  const [tab, setTab] = useState('clips');
  const lookupsArr = lookups || [];
  const tabData = tab === 'clips' ? clips
                : tab === 'highlights' ? highlights
                : tab === 'memos' ? memos
                : lookupsArr;
  const tabLabels = {clips: '클립', highlights: '형광펜', memos: '메모', lookups: '모름'};
  const tabCounts = {clips: clips.length, highlights: (highlights||[]).length,
                     memos: (memos||[]).length, lookups: lookupsArr.length};
  const total = clips.length + (highlights||[]).length + (memos||[]).length + lookupsArr.length;

  const handleClear = () => {
    const labelMap = {clips: '발췌', highlights: '형광펜', memos: '메모', lookups: '모름 표시'};
    if (!confirm(`모든 ${labelMap[tab]}을(를) 삭제할까요?`)) return;
    if (tab === 'clips') onClear();
    else if (tab === 'highlights') onClearHL?.();
    else if (tab === 'memos') onClearMemo?.();
    else onClearLookup?.();
  };
  const handleRemove = (id) => {
    if (tab === 'clips') onRemove(id);
    else if (tab === 'highlights') onRemoveHL?.(id);
    else if (tab === 'memos') onRemoveMemo?.(id);
    else onRemoveLookup?.(id);
  };

  useEffect(() => {
    document.body.classList.add('drawer-open');
    return () => document.body.classList.remove('drawer-open');
  }, []);

  return (
    <>
      <aside className="clips-drawer">
        <div className="cd-head">
          <h2>내 서랍</h2>
          <span className="cd-count">{total}개</span>
          <button className="icon-btn" onClick={onClose} aria-label="닫기"><Ico.Close/></button>
        </div>
        <div className="cd-tabs">
          {['clips','highlights','memos','lookups'].map(t => (
            <button key={t} className={'cd-tab' + (tab===t?' active':'')} onClick={() => setTab(t)}>
              {tabLabels[t]} <span className="cd-tab-n">{tabCounts[t]}</span>
            </button>
          ))}
        </div>
        {tabData.length > 0 && (
          <div className="cd-actions">
            <button className="chip" onClick={() => {
              const text = tabData.map(c =>
                tab === 'memos'
                  ? `"${c.text}"\n📝 ${c.memo}\n— ${c.title} (${c.date})`
                  : tab === 'lookups'
                    ? `? ${c.text}\n— ${c.title} (${c.date})`
                    : `"${c.text}"\n— ${c.title} (${c.date})`
              ).join('\n\n');
              navigator.clipboard?.writeText(text);
            }}>전체 복사</button>
            <button className="chip" onClick={handleClear} style={{marginLeft:'auto'}}>모두 삭제</button>
          </div>
        )}
        <div className="cd-list">
          {tabData.length === 0 ? (
            <div className="cd-empty">
              <div className="e-mark">{tab === 'clips' ? '¶' : tab === 'highlights' ? '🖍' : tab === 'memos' ? '💬' : '?'}</div>
              <div>{tab === 'clips' ? '본문에서 텍스트를 드래그하면\n여기에 모입니다.' :
                     tab === 'highlights' ? '형광펜으로 칠한 텍스트가\n여기에 모입니다.' :
                     tab === 'memos' ? '메모를 추가하면\n여기에 모입니다.' :
                     '모르는 표현에 ? 표시하면\n여기에 모입니다.'}</div>
            </div>
          ) : tabData.map(c => {
            const sec = sectorMap[c.folder];
            const itemCls = 'clip-item' +
              (tab === 'highlights' ? ' hl-item' :
               tab === 'memos' ? ' memo-item' :
               tab === 'lookups' ? ' lookup-item' : '');
            return (
              <div className={itemCls} key={c.id}>
                <div className="ci-meta">
                  {sec && <span className="sec" style={{color: `var(${sec.cssVar})`}}>{c.folder}</span>}
                  <span>·</span>
                  <span style={{fontVariantNumeric:'tabular-nums'}}>{c.date}</span>
                </div>
                <div className="ci-source" onClick={() => onJump(c)}>{decodeEntities(c.title)}</div>
                <div className="ci-text">{c.text}</div>
                {tab === 'memos' && c.memo && <div className="ci-memo">💬 {c.memo}</div>}
                <div className="ci-tools">
                  <button onClick={() => navigator.clipboard?.writeText(tab === 'memos' ? `${c.text}\n📝 ${c.memo}` : c.text)}>복사</button>
                  <button onClick={() => onJump(c)}>해당 글 보기</button>
                  <button className="del" onClick={() => handleRemove(c.id)}>삭제</button>
                </div>
              </div>
            );
          })}
        </div>
      </aside>
    </>
  );
}

window.MR.useClips = useClips;
window.MR.useHighlights = useHighlights;
window.MR.useMemos = useMemos;
window.MR.useLookups = useLookups;
window.MR.InlineArticle = InlineArticle;
window.MR.ClipsDrawer = ClipsDrawer;
window.MR.ClipPopover = ClipPopover;
window.MR.highlightAll = highlightAll;
