/* global React, MR */
const { useState, useEffect, useRef, useCallback } = React;

const KEY_STORAGE = 'meru_oai_key';
const MODEL = 'gpt-4o-mini';

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

function ChatPanel({ open, onClose, currentPost }) {
  const [apiKey, setApiKey] = useState(() => getKey());
  const [keyInput, setKeyInput] = useState('');
  const [messages, setMessages] = useState([]); // {role, content}
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const [useContext, setUseContext] = useState(true);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open && apiKey && inputRef.current) inputRef.current.focus();
  }, [open, apiKey]);

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
    const sys = ctx
      ? `너는 한국 금융·경제 학습 도우미. 사용자가 보고 있는 메르 블로그 글을 함께 읽으며 모르는 용어·맥락·인과를 짧고 정확하게 설명. 추측 금지, 한국어, 핵심만. 사용자가 묻는 표현이 아래 글 안에 있으면 글 맥락에 맞춰 답해.\n\n--- 현재 보는 글 ---\n${ctx}`
      : '너는 한국 금융·경제 학습 도우미. 짧고 정확하게, 한국어, 추측 금지.';

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
      <div className="chat-overlay" onClick={onClose}/>
      <aside className="chat-panel">
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
              <button className="chip" onClick={reset}>대화 초기화</button>
              <button className="chip" onClick={clearKey}>키 변경</button>
            </div>

            <div className="chat-msgs" ref={scrollRef}>
              {messages.length === 0 && (
                <div className="chat-empty">
                  본문에서 모르는 부분 드래그 후 열면<br/>
                  자동으로 질문에 들어갑니다.<br/><br/>
                  <small>예: "이 단락에서 캐리트레이드가 왜 영향을 줘?"</small>
                </div>
              )}
              {messages.map((m, i) => (
                <div key={i} className={'chat-msg ' + m.role}>
                  <div className="chat-role">{m.role === 'user' ? '나' : 'AI'}</div>
                  <div className="chat-body">{m.content}</div>
                </div>
              ))}
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
                rows={2}
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
