/* global React, MR */
const { useState, useEffect, useMemo, useRef, useCallback } = React;
const { SECTORS, sectorMap, Ico, fmtDate, decodeEntities } = window.MR;

/* ---------- Article view (full screen reader) ---------- */
function ArticleView({ post, allPosts, onClose, onOpen, isBookmarked, onToggleBookmark, fontSize }) {
  const scrollRef = useRef(null);
  const [progress, setProgress] = useState(0);

  // related: same sector + share at least one tag, sorted by overlap
  const related = useMemo(() => {
    const tagSet = new Set(post.tags);
    return allPosts
      .filter(p => p.title !== post.title)
      .map(p => {
        const overlap = p.tags.filter(t => tagSet.has(t)).length;
        const sameSector = p.folder === post.folder;
        return { p, score: overlap * 2 + (sameSector ? 1 : 0) };
      })
      .filter(x => x.score > 0)
      .sort((a,b) => b.score - a.score || b.p.date.localeCompare(a.p.date))
      .slice(0, 5)
      .map(x => x.p);
  }, [post, allPosts]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      const max = el.scrollHeight - el.clientHeight;
      setProgress(max > 0 ? el.scrollTop / max : 0);
    };
    el.addEventListener('scroll', onScroll);
    return () => el.removeEventListener('scroll', onScroll);
  }, [post]);

  // ESC to close
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  // scroll top on post change
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [post.title]);

  const sec = sectorMap[post.folder];

  return (
    <div className="article-view" ref={scrollRef}>
      <div className="article-topbar">
        <button className="icon-btn" onClick={onClose} aria-label="닫기"><Ico.Back/></button>
        <span className="crumb">
          {sec && <span className="sector-dot" style={{'--c': `var(${sec.cssVar})`}}/>}
          {post.folder}
        </span>
        <div style={{flex:1}}/>
        <button
          className={'icon-btn' + (isBookmarked ? ' active' : '')}
          onClick={() => onToggleBookmark(post.title)}
          aria-label="북마크"
          title={isBookmarked ? '북마크 해제' : '북마크'}
        >
          <Ico.Bookmark filled={isBookmarked}/>
        </button>
        <div className="progress" style={{transform: `scaleX(${progress})`}}/>
      </div>

      <article className="article">
        <div className="kicker">
          <span className="dot" style={sec ? {background: `var(${sec.cssVar})`} : {}}/>
          {post.folder}
        </div>
        <h1 className="title">{decodeEntities(post.title)}</h1>

        <div className="byline">
          <span>메르 블로그</span>
          <span className="sep"/>
          <span>{fmtDate(post.date)}</span>
          <span className="sep"/>
          <span>{(post.paras||[]).length + 1}분 읽기</span>
        </div>

        <p className="lede dropcap">{decodeEntities(post.intro)}</p>

        {(post.intro_anns || []).length > 0 && (
          <div className="annotations">
            {post.intro_anns.map((a, i) => <Annotation key={i} a={a}/>)}
          </div>
        )}

        {(post.paras||[]).length > 0 && (
          <>
            <div className="section-h">본문</div>
            {post.paras.map((p, i) => (
              <div className="para" key={i}>
                {p.title && <h2 className="para-title">{decodeEntities(p.title)}</h2>}
                <p className="para-body">{decodeEntities(p.body)}</p>
                {(p.anns || []).length > 0 && (
                  <div className="annotations">
                    {p.anns.map((a, j) => <Annotation key={j} a={a}/>)}
                  </div>
                )}
              </div>
            ))}
          </>
        )}

        {(post.question || post.answer) && (
          <div className="qa">
            {post.question && <div className="pull-q">{decodeEntities(post.question)}</div>}
            {post.answer && <div className="pull-a">{decodeEntities(post.answer)}</div>}
          </div>
        )}

        <div className="article-foot">
          <div className="ftags">
            {post.tags.map((t,i) => <span className="t" key={i}>{t}</span>)}
          </div>
        </div>

        {related.length > 0 && (
          <div className="related">
            <h2>관련 글</h2>
            {related.map((r, i) => (
              <div className="rel-row" key={i} onClick={() => onOpen(r)}>
                <div>
                  <div className="rel-title">{decodeEntities(r.title)}</div>
                  <div style={{fontSize:'0.74rem', color:'var(--muted)', marginTop:6, letterSpacing:'1px', textTransform:'uppercase', fontWeight:600}}>{r.folder}</div>
                </div>
                <div className="rel-date">{r.date}</div>
              </div>
            ))}
          </div>
        )}
      </article>
    </div>
  );
}

function Annotation({ a }) {
  const isTerm = a.유형 === '용어풀이';
  return (
    <div className="annotation">
      <span className="ann-type">{isTerm ? '용어' : '맥락'}</span>
      {isTerm && a.대상 && <span className="ann-target">{a.대상}</span>}
      {decodeEntities(a.내용)}
    </div>
  );
}

window.MR.ArticleView = ArticleView;
