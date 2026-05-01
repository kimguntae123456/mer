/* global React, MR */
const { useState, useEffect, useMemo, useRef, useCallback } = React;
const { sectorMap, Ico, fmtDate, decodeEntities } = window.MR;

/* ---------- Clips storage hook ---------- */
function useClips() {
  const [clips, setClips] = useState(() => {
    try { return JSON.parse(localStorage.getItem('meru_clips') || '[]'); }
    catch { return []; }
  });
  const persist = (next) => {
    setClips(next);
    localStorage.setItem('meru_clips', JSON.stringify(next));
  };
  const add = useCallback((clip) => {
    setClips(prev => {
      const next = [{...clip, id: Date.now()+Math.random(), createdAt: Date.now()}, ...prev];
      localStorage.setItem('meru_clips', JSON.stringify(next));
      return next;
    });
  }, []);
  const remove = useCallback((id) => {
    setClips(prev => {
      const next = prev.filter(c => c.id !== id);
      localStorage.setItem('meru_clips', JSON.stringify(next));
      return next;
    });
  }, []);
  const clear = useCallback(() => persist([]), []);
  return { clips, add, remove, clear };
}

/* ---------- Drag-to-clip popover ---------- */
function ClipPopover({ container, onClip }) {
  const [pop, setPop] = useState(null); // {x, y, text}

  useEffect(() => {
    if (!container) return;
    const onUp = () => {
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed) { setPop(null); return; }
      const text = sel.toString().trim();
      if (text.length < 4) { setPop(null); return; }
      // Ensure selection is within container
      const range = sel.getRangeAt(0);
      if (!container.contains(range.commonAncestorContainer)) { setPop(null); return; }
      const rect = range.getBoundingClientRect();
      const cRect = container.getBoundingClientRect();
      setPop({
        x: rect.left + rect.width/2 - cRect.left,
        y: rect.top - cRect.top,
        text,
      });
    };
    const onDown = (e) => {
      // Hide popover when starting new selection
      if (e.target.closest('.clip-popover')) return;
      setPop(null);
    };
    document.addEventListener('mouseup', onUp);
    document.addEventListener('touchend', onUp);
    document.addEventListener('mousedown', onDown);
    document.addEventListener('touchstart', onDown);
    return () => {
      document.removeEventListener('mouseup', onUp);
      document.removeEventListener('touchend', onUp);
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('touchstart', onDown);
    };
  }, [container]);

  if (!pop) return null;
  return (
    <div className="clip-popover" style={{left: pop.x, top: pop.y}}>
      <button onClick={() => { onClip(pop.text); setPop(null); window.getSelection().removeAllRanges(); }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M5 12l5 5L20 7"/></svg>
        클립
      </button>
      <button onClick={() => {
        navigator.clipboard?.writeText(pop.text);
        setPop(null);
        window.getSelection().removeAllRanges();
      }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        복사
      </button>
    </div>
  );
}

/* ---------- Highlight clipped text inside body ---------- */
function highlightClips(text, clips) {
  if (!clips || !clips.length || !text) return decodeEntities(text);
  const decoded = decodeEntities(text);
  // Sort by length desc to handle overlaps
  const sorted = [...clips].sort((a,b) => b.length - a.length);
  let parts = [decoded];
  for (const clip of sorted) {
    const next = [];
    for (const p of parts) {
      if (typeof p !== 'string') { next.push(p); continue; }
      const idx = p.indexOf(clip);
      if (idx === -1) { next.push(p); continue; }
      if (idx > 0) next.push(p.slice(0, idx));
      next.push({type: 'mark', text: clip});
      const rest = p.slice(idx + clip.length);
      if (rest) next.push(rest);
    }
    parts = next;
  }
  return parts.map((p, i) => typeof p === 'string'
    ? p
    : <mark key={i} className="clip-mark">{p.text}</mark>);
}

/* ---------- Inline article (shown when row is expanded) ---------- */
function InlineArticle({ post, onClose, onClip, clipsForPost }) {
  const ref = useRef(null);
  const [containerEl, setContainerEl] = useState(null);
  const sec = sectorMap[post.folder];
  const clipTexts = clipsForPost.map(c => c.text);

  const setContainer = useCallback((node) => {
    ref.current = node;
    setContainerEl(node);
  }, []);

  const handleClip = (text) => {
    onClip({
      text,
      title: post.title,
      folder: post.folder,
      date: post.date,
      link: post.link,
    });
  };

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

      <p className="ia-lede dropcap">{highlightClips(post.intro, clipTexts)}</p>

      {(post.intro_anns || []).map((a, i) => <AnnotationInline key={'ia'+i} a={a}/>)}

      {(post.paras||[]).length > 0 && (
        <>
          <div className="ia-section-h">본문</div>
          {post.paras.map((p, i) => (
            <div className="ia-para" key={i}>
              {p.title && <h3 className="ia-para-title">{highlightClips(p.title, clipTexts)}</h3>}
              <p className="ia-para-body">{highlightClips(p.body, clipTexts)}</p>
              {(p.anns || []).map((a, j) => <AnnotationInline key={'pa'+i+'_'+j} a={a}/>)}
            </div>
          ))}
        </>
      )}

      {(post.question || post.answer) && (
        <div>
          {post.question && <div className="ia-pull-q">{highlightClips(post.question, clipTexts)}</div>}
          {post.answer && <div className="ia-pull-a">{highlightClips(post.answer, clipTexts)}</div>}
        </div>
      )}

      <div className="ia-foot">
        <div className="src" style={{fontSize:'0.78rem', color:'var(--muted)'}}>
          ¶ {fmtDate(post.date)} · {post.folder || '미분류'}
        </div>
      </div>

      <ClipPopover container={containerEl} onClip={handleClip}/>
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

/* ---------- Clips drawer ---------- */
function ClipsDrawer({ clips, onClose, onRemove, onClear, onJump }) {
  return (
    <>
      <div className="clips-drawer-overlay" onClick={onClose}/>
      <aside className="clips-drawer">
        <div className="cd-head">
          <h2>발췌</h2>
          <span className="cd-count">{clips.length}개</span>
          <button className="icon-btn" onClick={onClose} aria-label="닫기"><Ico.Close/></button>
        </div>
        {clips.length > 0 && (
          <div className="cd-actions">
            <button
              className="chip"
              onClick={() => {
                const text = clips.map(c => `“${c.text}”\n— ${c.title} (${c.date})`).join('\n\n');
                navigator.clipboard?.writeText(text);
              }}
            >
              전체 복사
            </button>
            <button
              className="chip"
              onClick={() => {
                if (confirm('모든 발췌를 삭제할까요?')) onClear();
              }}
              style={{marginLeft:'auto'}}
            >
              모두 삭제
            </button>
          </div>
        )}
        <div className="cd-list">
          {clips.length === 0 ? (
            <div className="cd-empty">
              <div className="e-mark">¶</div>
              <div>본문에서 텍스트를 드래그하면<br/>여기에 모입니다.</div>
            </div>
          ) : clips.map(c => {
            const sec = sectorMap[c.folder];
            return (
              <div className="clip-item" key={c.id}>
                <div className="ci-meta">
                  {sec && <span className="sec" style={{color: `var(${sec.cssVar})`}}>{c.folder}</span>}
                  <span>·</span>
                  <span style={{fontVariantNumeric:'tabular-nums'}}>{c.date}</span>
                </div>
                <div className="ci-source" onClick={() => onJump(c)}>{decodeEntities(c.title)}</div>
                <div className="ci-text">{c.text}</div>
                <div className="ci-tools">
                  <button onClick={() => navigator.clipboard?.writeText(c.text)}>복사</button>
                  <button onClick={() => onJump(c)}>해당 글 보기</button>
                  <button className="del" onClick={() => onRemove(c.id)}>삭제</button>
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
window.MR.InlineArticle = InlineArticle;
window.MR.ClipsDrawer = ClipsDrawer;
window.MR.ClipPopover = ClipPopover;
