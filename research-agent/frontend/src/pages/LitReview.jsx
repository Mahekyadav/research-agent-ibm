import React, { useState } from 'react'
import { literatureReview } from '../api'
import { LoadingBlock, Alert, MdOutput, SourceList, SectionHeader } from '../components/Shared'

export default function LitReview() {
  const [query,   setQuery]   = useState('')
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [error,   setError]   = useState(null)

  const run = async () => {
    if (!query.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const { data } = await literatureReview(query)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <SectionHeader title="Literature Review Synthesis"
        subtitle="IBM Granite generates a structured review from your indexed research corpus." />

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="field">
          <label>Research Topic or Query</label>
          <textarea className="textarea" rows={3}
            placeholder="e.g. deep learning approaches for medical image segmentation"
            value={query} onChange={e => setQuery(e.target.value)} />
        </div>
        <button className="btn btn-primary" style={{ width: '100%' }}
          onClick={run} disabled={loading || !query.trim()}>
          {loading ? 'Generating Review…' : 'Generate Literature Review'}
        </button>
      </div>

      {loading && <LoadingBlock text="IBM Granite is synthesizing your literature…" />}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <div>
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="card-title">Structured Literature Review</div>
            <MdOutput content={result.review} />
          </div>
          <SourceList sources={result.sources} />
        </div>
      )}
    </div>
  )
}
