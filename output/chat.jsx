/* global React, MR */
const { useState, useEffect, useRef, useCallback } = React;

const KEY_STORAGE = 'meru_oai_key';
const PROMPT_STORAGE = 'meru_oai_prompt';
const MODEL = 'gpt-4o-mini';

const PRESETS = {
  '기본 (학습 도우미)': '너는 한국 금융·경제 학습 도우미. 사용자가 보고 있는 메르 블로그 글을 함께 읽으며 모르는 용어·맥락·인과를 짧고 정확하게 설명. 추측 금지, 한국어, 핵심만.',
  '비전공자 풀어쓰기': '너는 금융·경제 비전공자에게 설명하는 도우미. 모든 답을 다음 3단계로 한다. 1) 일상 비유 한 줄로 직관 잡아주기 2) 정확한 정의·메커니즘을 평이한 한국어로 풀어쓰기 (전문용어 나오면 즉시 괄호 안에 한 줄 풀이) 3) "왜 중요한가" 한 줄. 어려운 한자어·영어 약자는 가능하면 우리말로 바꾸고, 못 바꾸면 그 자리에서 풀어준다. 한국어 반말체 OK, 친근하게.',
  '깐깐한 교수': '너는 한국 금융·경제학 박사 교수. 학생이 묻는 개념의 정의·전제·반례를 엄격하게 짚어준다. 두루뭉술한 답 금지, 모르면 모른다고 말한다. 한국어 격식체.',
  '메르 스타일': '너는 메르처럼 답한다. 짧은 문장, 번호 매기기(1. 2. 3.), 직설적 어조, 비유 적극 사용. "~다", "~네", "~지" 같은 평어 섞고, 핵심 숫자·고유명사 굵게 살림. 양시론·뭉개기 절대 금지.',
  '면접 코치': '너는 공기업·금융권 면접 코치. 사용자가 묻는 내용을 면접 답변 구조(두괄식 결론 → 근거 2개 → 시사점)로 30초 분량으로 정리해 답한다. 한국어 격식체.',
  '쉬운 비유': '너는 어려운 금융·경제 개념을 일상 비유로 풀어주는 도우미. 전문용어가 나오면 반드시 일상 사례에 빗대 1문장 비유 먼저, 그다음 정확한 정의. 한국어 반말체 OK.',
  '간결 (한 줄)': '한국어로 한 문장(최대 2문장)만으로 답한다. 군더더기 금지. 정의·핵심만.',
};

function getPrompt() {
  return localStorage.getItem(PROMPT_STORAGE) || PRESETS['기본 (학습 도우미)'];
}
function savePrompt(p) {
  if (p) localStorage.setItem(PROMPT_STORAGE, p);
  else localStorage.removeItem(PROMPT_STORAGE);
}

function getKey() { return localStorage.getItem(KEY_STORAGE) || ''; }
function setKey(k) {
  if (k) localStorage.setItem(KEY_STORAGE, k);
  else localStorage.removeItem(KEY_STORAGE);
}

function buildContext(post) {
  if (!post) return '';
  const lines = [];
  lines.push(`# 글 제목: ${post.title}`);
  if (post.folder) lines.push(`섹터: ${post.folder}`);
  if (post.date) lines.push(`날짜: ${post.date}`);
  lines.push('');
  if (post.intro) lines.push(post.intro);
  (post.paras || []).forEach(p => {
    if (p.title) lines.push(`\n## ${p.title}`);
    if (p.body) lines.push(p.body);
  });
  if (post.question) lines.push(`\n메르 질문: ${post.question}`);
  if (post.answer) lines.push(`나의 답: ${post.answer}`);
  const txt = lines.join('\n');
  return txt.length > 6000 ? txt.slice(0, 6000) + '…' : txt;
}

function ChatPanel({ open, onClose, currentPost, onSaveClip, onSaveLookup }) {
  const [apiKey, setApiKey] = useState(() => getKey());
  const [keyInput, setKeyInput] = useState('');
  const [messages, setMessages] = useState([]); // {role, content}
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const [useContext, setUseContext] = useState(true);
  const [systemPrompt, setSystemPrompt] = useState(() => getPrompt());
  const [showStyle, setShowStyle] = useState(false);
  const [panelW, setPanelW] = useState(() => {
    const v = parseInt(localStorage.getItem('meru_oai_panel_w'), 10);
    return Number.isFinite(v) && v >= 320 ? v : 460;
  });

  useEffect(() => {
    document.documentElement.style.setProperty('--chat-w', panelW + 'px');
  }, [panelW]);

  const onPanelResize = (e) => {
    e.preventDefault();
    const startX = e.clientX;
    const startW = panelW;
    const onMove = (ev) => {
      const w = Math.min(900, Math.max(320, startW + (startX - ev.clientX)));
      setPanelW(w);
    };
    const onUp = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      try { localStorage.setItem('meru_oai_panel_w', String(panelW)); } catch {}
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  };

  // persist width on change
  useEffect(() => {
    try { localStorage.setItem('meru_oai_panel_w', String(panelW)); } catch {}
  }, [panelW]);

  // textarea auto-grow
  const autoGrow = (el) => {
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(240, el.scrollHeight) + 'px';
  };
  useEffect(() => { autoGrow(inputRef.current); }, [input]);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open && apiKey && inputRef.current) inputRef.current.focus();
  }, [open, apiKey]);

  useEffect(() => {
    document.body.classList.toggle('chat-open', !!open);
    return () => document.body.classList.remove('chat-open');
  }, [open]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading]);

  // grab selection on open
  const grabSelection = useCallback(() => {
    const sel = window.getSelection?.();
    const t = sel?.toString().trim();
    if (t && t.length >= 4) setInput(prev => prev ? prev : `다음 부분 설명해줘:\n"${t}"\n\n`);
  }, []);
  useEffect(() => { if (open) grabSelection(); }, [open, grabSelection]);

  const saveKey = () => {
    const k = keyInput.replace(/\s+/g, '').trim();
    if (!k.startsWith('sk-')) { setErr('OpenAI 키 형식 아님 (sk-…)'); return; }
    setKey(k);
    setApiKey(k);
    setKeyInput('');
    setErr('');
  };

  const clearKey = () => {
    if (!confirm('저장된 키를 지울까요?')) return;
    setKey('');
    setApiKey('');
  };

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setErr('');
    const userMsg = {role: 'user', content: text};
    const next = [...messages, userMsg];
    setMessages(next);
    setInput('');
    setLoading(true);

    const ctx = useContext ? buildContext(currentPost) : '';
    const base = systemPrompt.trim() || PRESETS['기본 (학습 도우미)'];
    const sys = ctx
      ? `${base}\n\n사용자가 묻는 표현이 아래 글 안에 있으면 글 맥락에 맞춰 답해.\n\n--- 현재 보는 글 ---\n${ctx}`
      : base;

    try {
      const cleanKey = apiKey.replace(/\s+/g, '').trim();
      const res = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        cache: 'no-store',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + cleanKey,
        },
        body: JSON.stringify({
          model: MODEL,
          messages: [{role: 'system', content: sys}, ...next.map(m => ({role: m.role, content: m.content}))],
          temperature: 0.3,
        }),
      });
      if (!res.ok) {
        let body = '';
        try { body = await res.text(); } catch {}
        throw new Error(`HTTP ${res.status} — ${body.slice(0,300)}`);
      }
      const data = await res.json();
      const reply = data.choices?.[0]?.message?.content || '(빈 응답)';
      setMessages(m => [...m, {role: 'assistant', content: reply}]);
    } catch (e) {
      const msg = String(e.message || e);
      const hint = msg === 'Failed to fetch'
        ? 'Failed to fetch — 키가 폐기됐거나(잘 가능성 큼), 브라우저 확장이 차단, 또는 SW 캐시 문제. 시크릿 창에서 재시도해보고, OpenAI 대시보드에서 키 상태 확인.'
        : msg;
      setErr(hint);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const reset = () => { setMessages([]); setErr(''); };

  if (!open) return null;
  return (
    <>
      <aside className="chat-panel" style={{width: panelW + 'px'}}>
        <div className="chat-resize-handle" onMouseDown={onPanelResize} title="드래그하여 너비 조절"/>
        <div className="chat-head">
          <h2>AI 도움말</h2>
          <span className="chat-model">{MODEL}</span>
          <button className="icon-btn" onClick={onClose} aria-label="닫기">×</button>
        </div>

        {!apiKey ? (
          <div className="chat-keygate">
            <p style={{fontSize:'0.9rem', lineHeight:1.6}}>
              OpenAI API 키를 한 번만 입력하면 이 브라우저에 저장됩니다.<br/>
              키는 서버로 보내지지 않고 localStorage에만 저장됩니다.
            </p>
            <input
              type="password"
              className="chat-key-input"
              placeholder="sk-..."
              value={keyInput}
              onChange={e => setKeyInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') saveKey(); }}
            />
            <button className="chat-key-save" onClick={saveKey}>저장하고 시작</button>
            {err && <div className="chat-err">{err}</div>}
            <p style={{fontSize:'0.75rem', color:'var(--muted)', marginTop:12}}>
              키 발급: platform.openai.com/api-keys
            </p>
          </div>
        ) : (
          <>
            <div className="chat-toolbar">
              <label className="chat-ctx">
                <input type="checkbox" checked={useContext} onChange={e => setUseContext(e.target.checked)}/>
                <span>현재 글 맥락 포함 {currentPost ? '✓' : '(없음)'}</span>
              </label>
              <button className="chip" onClick={() => setShowStyle(s => !s)}>스타일</button>
              <button className="chip" onClick={reset}>초기화</button>
              <button className="chip" onClick={clearKey}>키</button>
            </div>

            {showStyle && (
              <div className="chat-style-editor">
                <div className="chat-style-presets">
                  {Object.entries(PRESETS).map(([name, prompt]) => (
                    <button key={name} className="chip preset"
                      onClick={() => { setSystemPrompt(prompt); savePrompt(prompt); }}>
                      {name}
                    </button>
                  ))}
                </div>
                <textarea
                  className="chat-style-text"
                  rows={5}
                  value={systemPrompt}
                  onChange={e => setSystemPrompt(e.target.value)}
                  onBlur={() => savePrompt(systemPrompt)}
                  placeholder="여기에 직접 시스템 프롬프트를 적으면 그대로 적용됩니다…"
                />
                <div style={{display:'flex', gap:8, fontSize:'0.72rem', color:'var(--muted)', alignItems:'center'}}>
                  <span>저장됨 (자동) · 다음 메시지부터 적용</span>
                  <button className="chip" style={{marginLeft:'auto'}}
                    onClick={() => { const def = PRESETS['기본 (학습 도우미)']; setSystemPrompt(def); savePrompt(def); }}>
                    기본값 복원
                  </button>
                </div>
              </div>
            )}

            <div className="chat-msgs" ref={scrollRef}>
              {messages.length === 0 && (
                <div className="chat-empty">
                  본문에서 모르는 부분 드래그 후 열면<br/>
                  자동으로 질문에 들어갑니다.<br/><br/>
                  <small>예: "이 단락에서 캐리트레이드가 왜 영향을 줘?"</small>
                </div>
              )}
              {messages.map((m, i) => {
                const meta = currentPost
                  ? {title: currentPost.title, folder: currentPost.folder, date: currentPost.date, link: currentPost.link}
                  : {title: 'AI 답변', folder: '', date: new Date().toISOString().slice(0,10), link: ''};
                return (
                  <div key={i} className={'chat-msg ' + m.role}>
                    <div className="chat-role">{m.role === 'user' ? '나' : 'AI'}</div>
                    <div className="chat-body">{m.content}</div>
                    {m.role === 'assistant' && (
                      <div className="chat-msg-tools">
                        <button onClick={() => navigator.clipboard?.writeText(m.content)}>복사</button>
                        <button onClick={() => onSaveClip?.({text: m.content, ...meta})}>클립에 저장</button>
                        <button onClick={() => onSaveLookup?.({text: m.content, ...meta})}>모름에 저장</button>
                      </div>
                    )}
                  </div>
                );
              })}
              {loading && <div className="chat-msg assistant"><div className="chat-role">AI</div><div className="chat-body chat-typing">…생각 중</div></div>}
              {err && <div className="chat-err">⚠ {err}</div>}
            </div>

            <div className="chat-input-row">
              <textarea
                ref={inputRef}
                className="chat-input"
                placeholder="질문… (Enter 전송, Shift+Enter 줄바꿈)"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                rows={1}
              />
              <button className="chat-send" onClick={send} disabled={loading || !input.trim()}>
                전송
              </button>
            </div>
          </>
        )}
      </aside>
    </>
  );
}

window.MR.ChatPanel = ChatPanel;
