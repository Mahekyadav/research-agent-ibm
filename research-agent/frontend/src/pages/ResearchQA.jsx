import React, { useState } from 'react'
import { researchAsk } from '../api'
import { LoadingBlock, Alert, MdOutput, SourceList, SectionHeader } from '../components/Shared'

export default function ResearchQA() {
  const [question, setQuestion] = useState('')
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [error,    setError]    = useState(null)
  const [history,  setHistory]  = useState([])

  const run = async () => {
    if (!question.trim()) return
    setLoading(true); setError(null)
    const q = question
    setQuestion('')
    try {
      const { data } = await researchAsk(q)
      setResult(data)
      setHistory(h => [...h, { q, a: data.answer, sources: data.sources }])
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  const EXAMPLES = [
    'What are the main limitations of BERT?',
    'How does attention mechanism work in transformers?',
    'What datasets are used for named entity recognition?',
    'What are the most cited papers on continual learning?',
  ]

  return (
    <div>
      <SectionHeader title="Research Q&A"
        subtitle="Ask precise questions about your indexed knowledge base. Answers include confidence level and suggested follow-ups." />

      {/* Example chips */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        {EXAMPLES.map(ex => (
          <button key={ex} className="btn btn-sm btn-ghost"
            onClick={() => setQuestion(ex)}
            style={{ fontSize: 11 }}>
            {ex}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="field">
          <label>Research Question</label>
          <textarea className="textarea" rows={3}
            placeholder="Ask anything about your research corpus…"
            value={question} onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) run() }} />
          <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 4 }}>Ctrl+Enter to submit</div>
        </div>
        <button className="btn btn-primary" style={{ width: '100%' }}
          onClick={run} disabled={loading || !question.trim()}>
          {loading ? 'Retrieving answer…' : 'Get Research Answer'}
        </button>
      </div>

      {loading && <LoadingBlock text="Retrieving and synthesizing answer…" />}
      {error   && <Alert type="error">{error}</Alert>}

      {/* Latest result */}
      {result && (
        <div className="card" style={{ marginBottom: 14 }}>
          <div className="card-title">Answer</div>
          <MdOutput content={result.answer} />
          <SourceList sources={result.sources} />
        </div>
      )}

      {/* History */}
      {history.length > 1 && (
        <div>
          <h3 style={{ marginBottom: 10, fontSize: 13, color: 'var(--text2)' }}>Previous Questions</h3>
          {[...history].reverse().slice(1).map((h, i) => (
            <div key={i} className="card card-sm" style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent2)', marginBottom: 6 }}>Q: {h.q}</div>
              <div style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.5 }}>
                {h.a?.slice(0, 200)}{h.a?.length > 200 ? '…' : ''}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
