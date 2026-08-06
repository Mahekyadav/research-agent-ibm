import React, { useState } from 'react'
import { topicClusters } from '../api'
import { LoadingBlock, Alert, SectionHeader } from '../components/Shared'

const CLUSTER_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444',
  '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1']

export default function Clusters() {
  const [domain,    setDomain]    = useState('')
  const [nClusters, setNClusters] = useState(5)
  const [loading,   setLoading]   = useState(false)
  const [result,    setResult]    = useState(null)
  const [error,     setError]     = useState(null)

  const run = async () => {
    if (!domain.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const { data } = await topicClusters(domain, nClusters)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  const clusters = result?.clusters || []

  // Compute max size for bar scaling
  const maxSize = clusters.reduce((m, c) => Math.max(m, c.size), 0)

  return (
    <div>
      <SectionHeader title="Topic Clustering"
        subtitle="K-Means clustering over IBM Slate embedding space groups papers by semantic similarity." />

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="field-row">
          <div className="field" style={{ marginBottom: 0 }}>
            <label>Research Domain</label>
            <input className="input" placeholder="e.g. deep learning, NLP, drug discovery"
              value={domain} onChange={e => setDomain(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && run()} />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label>Number of Clusters (k)</label>
            <select className="select" value={nClusters} onChange={e => setNClusters(+e.target.value)}>
              {[2, 3, 4, 5, 6, 7, 8, 10].map(n => <option key={n}>{n}</option>)}
            </select>
          </div>
        </div>
        <button className="btn btn-primary" style={{ width: '100%', marginTop: 14 }}
          onClick={run} disabled={loading || !domain.trim()}>
          {loading ? 'Clustering…' : `Cluster into ${nClusters} Topics`}
        </button>
      </div>

      {loading && <LoadingBlock text={`Clustering papers into ${nClusters} topic groups…`} />}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <div>
          {/* Overview */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
            <span className="badge badge-blue">{result.total_papers} papers clustered</span>
            <span className="badge badge-purple">{result.n_clusters} clusters</span>
            <span className="badge badge-gray">{result.domain}</span>
          </div>

          {/* Bar chart */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-title">Cluster Size Distribution</div>
            {clusters.map((cl, i) => (
              <div key={i} style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: CLUSTER_COLORS[i % CLUSTER_COLORS.length], flexShrink: 0 }} />
                  <span style={{ fontSize: 12, fontWeight: 600, minWidth: 80 }}>Cluster {cl.cluster_id}</span>
                  <div style={{ flex: 1, background: 'var(--bg)', borderRadius: 4, height: 16, overflow: 'hidden', position: 'relative' }}>
                    <div style={{
                      width: `${Math.max(2, (cl.size / maxSize) * 100)}%`,
                      background: CLUSTER_COLORS[i % CLUSTER_COLORS.length] + '66',
                      borderRight: `2px solid ${CLUSTER_COLORS[i % CLUSTER_COLORS.length]}`,
                      height: '100%', transition: 'width .5s',
                    }} />
                  </div>
                  <span style={{ fontSize: 12, color: 'var(--text2)', minWidth: 50, textAlign: 'right' }}>{cl.size} papers</span>
                </div>
                {/* Sample papers */}
                <div style={{ paddingLeft: 24, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {cl.sample_papers?.map((p, j) => (
                    <span key={j} style={{
                      fontSize: 11, color: 'var(--text3)', background: 'var(--bg)',
                      border: '1px solid var(--border)', borderRadius: 4,
                      padding: '2px 6px', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }} title={p}>{p}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
