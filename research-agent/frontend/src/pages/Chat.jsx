import React, { useState, useEffect, useRef } from 'react'
import { chat, newSession, getHistory, endSession } from '../api'
import { Spinner, Alert, MdOutput, SectionHeader } from '../components/Shared'
import { Send, Plus, Trash2, User, Bot } from 'lucide-react'

export default function Chat() {
  const [sessionId, setSessionId] = useState(null)
  const [messages,  setMessages]  = useState([])
  const [input,     setInput]     = useState('')
  const [loading,   setLoading]   = useState(false)
  const [error,     setError]     = useState(null)
  const [starting,  setStarting]  = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const startSession = async () => {
    setStarting(true); setError(null)
    try {
      const { data } = await newSession()
      setSessionId(data.session_id)
      setMessages([{
        role: 'assistant',
        content: "👋 Hello! I'm **ResearchMind**, your IBM WatsonX-powered research companion. Ask me anything about the papers in your knowledge base — I can discuss findings, compare methods, or help with follow-up questions.",
        sources: [],
      }])
    } catch (e) { setError(e.message) }
    finally { setStarting(false) }
  }

  const send = async () => {
    if (!input.trim() || !sessionId || loading) return
    const msg = input.trim()
    setInput('')
    setMessages(m => [...m, { role: 'user', content: msg }])
    setLoading(true); setError(null)
    try {
      const { data } = await chat(msg, sessionId)
      setMessages(m => [...m, { role: 'assistant', content: data.answer, sources: data.sources }])
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
      setMessages(m => [...m, { role: 'assistant', content: '⚠️ Error: ' + (e.response?.data?.detail || e.message), sources: [] }])
    } finally {
      setLoading(false)
    }
  }

  const clear = async () => {
    if (sessionId) await endSession(sessionId).catch(() => {})
    setSessionId(null); setMessages([]); setError(null)
  }

  const STARTERS = [
    'What papers are in my knowledge base?',
    'Summarize the main themes across all indexed papers.',
    'What are the most impactful recent contributions?',
    'What methodologies are most commonly used?',
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 56px - 48px)', maxHeight: 780 }}>
      <SectionHeader title="AI Research Chat"
        subtitle="Multi-turn conversation with session memory. Follow-up questions maintain full context." />

      {!sessionId ? (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
          <Bot size={52} style={{ color: 'var(--accent)', opacity: .6 }} />
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ marginBottom: 6 }}>Start a Research Session</h2>
            <p style={{ fontSize: 13, maxWidth: 400 }}>
              Each session maintains conversation memory across follow-up questions.
            </p>
          </div>
          {error && <Alert type="error">{error}</Alert>}
          <button className="btn btn-primary" onClick={startSession} disabled={starting}>
            {starting ? <><Spinner />&nbsp;Starting…</> : <><Plus size={15} /> New Chat Session</>}
          </button>
        </div>
      ) : (
        <>
          {/* Session header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{ fontSize: 11, color: 'var(--text3)', fontFamily: 'monospace' }}>
              Session: {sessionId.slice(0, 8)}…
            </span>
            <span className="badge badge-green">Active</span>
            <button className="btn btn-sm btn-danger" style={{ marginLeft: 'auto' }} onClick={clear}>
              <Trash2 size={12} /> End Session
            </button>
          </div>

          {/* Starter chips */}
          {messages.length <= 1 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
              {STARTERS.map(s => (
                <button key={s} className="btn btn-sm btn-ghost" style={{ fontSize: 11 }}
                  onClick={() => { setInput(s) }}>{s}</button>
              ))}
            </div>
          )}

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '4px 0', marginBottom: 12 }}>
            {messages.map((m, i) => (
              <div key={i} style={{
                display: 'flex', gap: 10, marginBottom: 14,
                flexDirection: m.role === 'user' ? 'row-reverse' : 'row',
                alignItems: 'flex-start',
              }}>
                {/* Avatar */}
                <div style={{
                  width: 30, height: 30, borderRadius: '50%', flexShrink: 0,
                  background: m.role === 'user' ? 'var(--bg3)' : 'var(--accent)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {m.role === 'user' ? <User size={15} color="#fff" /> : <Bot size={15} color="#fff" />}
                </div>

                {/* Bubble */}
                <div style={{ maxWidth: '75%' }}>
                  <div style={{
                    background: m.role === 'user' ? 'var(--bg3)' : 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: m.role === 'user' ? '12px 4px 12px 12px' : '4px 12px 12px 12px',
                    padding: '10px 14px',
                  }}>
                    {m.role === 'user'
                      ? <p style={{ fontSize: 13, color: 'var(--text)', margin: 0 }}>{m.content}</p>
                      : <MdOutput content={m.content} />
                    }
                  </div>
                  {/* Sources */}
                  {m.sources?.length > 0 && (
                    <div style={{ marginTop: 6 }}>
                      {m.sources.slice(0, 3).map((s, j) => (
                        <div key={j} style={{ fontSize: 11, color: 'var(--text3)', padding: '2px 0' }}>
                          📄 {s.title || s.source}{s.year ? ` (${s.year})` : ''}{s.citation_count > 0 ? ` · ${s.citation_count} citations` : ''}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <div style={{ width: 30, height: 30, borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot size={15} color="#fff" />
                </div>
                <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '4px 12px 12px 12px', padding: '12px 16px' }}>
                  <Spinner />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div style={{ display: 'flex', gap: 8 }}>
            <textarea className="textarea" rows={2}
              placeholder="Ask about your research corpus…"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
              style={{ flex: 1, resize: 'none' }}
            />
            <button className="btn btn-primary btn-icon" onClick={send}
              disabled={!input.trim() || loading}
              style={{ alignSelf: 'flex-end', padding: '10px 14px' }}>
              <Send size={16} />
            </button>
          </div>
        </>
      )}
    </div>
  )
}
