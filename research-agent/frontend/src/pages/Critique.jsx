import React, { useState } from 'react'
import { critiquePaper } from '../api'
import { LoadingBlock, Alert, MdOutput, SourceList, SectionHeader } from '../components/Shared'

const EXAMPLES = [
  'Attention Is All You Need',
  'BERT: Pre-training of Deep Bidirectional Transformers',
  'Deep Residual Learning for Image Recognition',
  'Generative Adversarial Networks',
]

export default function Critique() {
  const [title,   setTitle]   = useState('')
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [error,   setError]   = useState(null)

  const run = async () => {
    if (!title.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const { data } = await critiquePaper(title)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <SectionHeader title="Paper Critique"
        subtitle="In-depth critical analysis: strengths, limitations, novelty, reproducibility, and impact." />

      {/* Examples */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        {EXAMPLES.map(ex => (
          <button key={ex} className="btn btn-sm btn-ghost" style={{ fontSize: 11 }}
            onClick={() => setTitle(ex)}>{ex}</button>
        ))}
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="field">
          <label>Paper Title</label>
          <input className="input" placeholder="e.g. Attention Is All You Need"
            value={title} onChange={e => setTitle(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && run()} />
        </div>
        <button className="btn btn-primary" style={{ width: '100%' }}
          onClick={run} disabled={loading || !title.trim()}>
          {loading ? 'Analyzing…' : 'Critique This Paper'}
        </button>
      </div>

      {loading && <LoadingBlock text="Generating critical analysis…" />}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <div>
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Critical Analysis — {result.paper_title}</div>
            <MdOutput content={result.critique} />
          </div>
          <SourceList sources={result.sources} />
        </div>
      )}
    </div>
  )
}
