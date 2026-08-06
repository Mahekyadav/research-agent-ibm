import React, { useState } from 'react'
import { trendAnalysis } from '../api'
import { LoadingBlock, Alert, MdOutput, SectionHeader } from '../components/Shared'

export default function Trends() {
  const [domain,  setDomain]  = useState('')
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [error,   setError]   = useState(null)

  const run = async () => {
    if (!domain.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const { data } = await trendAnalysis(domain)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <SectionHeader title="Trend Analysis & Future Prediction"
        subtitle="Identify emerging topics, declining areas, and IBM Granite's 3–5 year research forecasts." />

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="field">
          <label>Research Domain</label>
          <input className="input" placeholder="e.g. large language models, federated learning, quantum computing"
            value={domain} onChange={e => setDomain(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && run()} />
        </div>
        <button className="btn btn-primary" style={{ width: '100%' }}
          onClick={run} disabled={loading || !domain.trim()}>
          {loading ? 'Analyzing…' : 'Analyze Trends'}
        </button>
      </div>

      {loading && <LoadingBlock text="Analyzing trends across your corpus…" />}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <div>
          {/* Meta stats */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
            <span className="badge badge-blue">{result.papers_analyzed} papers analyzed</span>
            {Object.entries(result.year_distribution || {}).slice(0, 5).map(([y, c]) => (
              <span key={y} className="badge badge-gray">{y}: {c}</span>
            ))}
            {Object.entries(result.source_distribution || {}).map(([s, c]) => (
              <span key={s} className="badge badge-purple">{s}: {c}</span>
            ))}
          </div>

          <div className="card">
            <div className="card-title">Trend Analysis — {result.domain}</div>
            <MdOutput content={result.analysis} />
          </div>
        </div>
      )}
    </div>
  )
}
