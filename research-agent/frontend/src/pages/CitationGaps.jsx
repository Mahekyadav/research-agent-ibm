import React, { useState } from 'react'
import { citationGaps } from '../api'
import { LoadingBlock, Alert, MdOutput, SourceList, SectionHeader } from '../components/Shared'

export default function CitationGaps() {
  const [topic,   setTopic]   = useState('')
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [error,   setError]   = useState(null)

  const run = async () => {
    if (!topic.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const { data } = await citationGaps(topic)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <SectionHeader title="Citation Gap Detection"
        subtitle="Find understudied sub-topics, missing research connections, and priority research directions." />

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="field">
          <label>Research Topic</label>
          <input className="input" placeholder="e.g. explainability in federated learning"
            value={topic} onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && run()} />
        </div>
        <button className="btn btn-primary" style={{ width: '100%' }}
          onClick={run} disabled={loading || !topic.trim()}>
          {loading ? 'Detecting Gaps…' : 'Detect Citation Gaps'}
        </button>
      </div>

      {loading && <LoadingBlock text="Scanning for citation gaps and research opportunities…" />}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
            <span className="badge badge-yellow">{result.papers_analyzed} papers scanned</span>
            {result.avg_citation_count > 0 && (
              <span className="badge badge-gray">Avg citations: {result.avg_citation_count}</span>
            )}
          </div>
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Citation Gap Analysis — {result.topic}</div>
            <MdOutput content={result.gaps} />
          </div>
          <SourceList sources={result.sources} />
        </div>
      )}
    </div>
  )
}
