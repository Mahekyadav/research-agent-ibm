import React, { useState } from 'react'
import { searchPapers } from '../api'
import { LoadingBlock, Alert, PaperCard, SectionHeader } from '../components/Shared'

const SOURCES = ['arxiv', 'semantic_scholar', 'crossref']

export default function Search() {
  const [query,    setQuery]    = useState('')
  const [sources,  setSources]  = useState(['arxiv', 'semantic_scholar', 'crossref'])
  const [maxPer,   setMaxPer]   = useState(8)
  const [ingest,   setIngest]   = useState(true)
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [error,    setError]    = useState(null)

  const toggle = (src) =>
    setSources(prev => prev.includes(src) ? prev.filter(s => s !== src) : [...prev, src])

  const run = async () => {
    if (!query.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const { data } = await searchPapers({ query, sources, max_per_source: maxPer, ingest_immediately: ingest })
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <SectionHeader title="Search Academic Papers"
        subtitle="Aggregate from arXiv, Semantic Scholar, and CrossRef simultaneously." />

      <div className="card" style={{ marginBottom: 20 }}>
        {/* Query */}
        <div className="field">
          <label>Research Query</label>
          <input className="input" placeholder="e.g. transformer models for protein folding"
            value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && run()} />
        </div>

        {/* Sources */}
        <div className="field">
          <label>Sources</label>
          <div style={{ display: 'flex', gap: 10 }}>
            {SOURCES.map(src => (
              <button key={src}
                className={`btn btn-sm ${sources.includes(src) ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => toggle(src)}
              >
                {src.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Options row */}
        <div className="field-row" style={{ alignItems: 'flex-end', marginBottom: 0 }}>
          <div className="field" style={{ marginBottom: 0 }}>
            <label>Max per source</label>
            <select className="select" value={maxPer} onChange={e => setMaxPer(+e.target.value)}>
              {[5, 8, 10, 15, 20, 25].map(n => <option key={n}>{n}</option>)}
            </select>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label>Auto-ingest into KB</label>
            <button
              className={`btn btn-sm ${ingest ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setIngest(v => !v)}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {ingest ? '✓ Enabled' : 'Disabled'}
            </button>
          </div>
        </div>

        <button className="btn btn-primary" style={{ marginTop: 16, width: '100%' }}
          onClick={run} disabled={loading || !query.trim()}>
          {loading ? 'Searching…' : `Search Across ${sources.length} Sources`}
        </button>
      </div>

      {loading && <LoadingBlock text="Querying academic sources…" />}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <div>
          {/* Summary bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>{result.papers_found} papers found</span>
            {result.ingestion && (
              <>
                <span className="badge badge-green">{result.ingestion.ingested} ingested</span>
                <span className="badge badge-gray">{result.ingestion.skipped} skipped (already indexed)</span>
                <span className="badge badge-blue">{result.ingestion.chunks_added} chunks added to KB</span>
              </>
            )}
          </div>

          {/* Papers */}
          {result.papers.map((p, i) => <PaperCard key={i} paper={p} />)}
        </div>
      )}
    </div>
  )
}
