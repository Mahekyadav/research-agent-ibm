import React, { useState, useRef, useEffect } from 'react'
import { buildKG } from '../api'
import { LoadingBlock, Alert, SectionHeader } from '../components/Shared'

const TYPE_COLOR = {
  concept: '#3b82f6', method: '#8b5cf6', paper: '#10b981',
  author: '#f59e0b', institution: '#ef4444', dataset: '#06b6d4', default: '#64748b',
}

function KGCanvas({ graph }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    if (!graph || !canvasRef.current) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const W = canvas.width, H = canvas.height
    ctx.clearRect(0, 0, W, H)

    const entities = graph.entities || []
    const rels = graph.relationships || []
    if (!entities.length) return

    // Assign positions in a circle
    const cx = W / 2, cy = H / 2
    const r  = Math.min(W, H) * 0.36
    const pos = {}
    entities.forEach((e, i) => {
      const angle = (2 * Math.PI * i) / entities.length - Math.PI / 2
      pos[e.id] = {
        x: i === 0 ? cx : cx + r * Math.cos(angle),
        y: i === 0 ? cy : cy + r * Math.sin(angle),
      }
    })

    // Draw edges
    rels.forEach(rel => {
      const s = pos[rel.source], t = pos[rel.target]
      if (!s || !t) return
      ctx.beginPath()
      ctx.moveTo(s.x, s.y)
      ctx.lineTo(t.x, t.y)
      ctx.strokeStyle = 'rgba(100,116,139,.5)'
      ctx.lineWidth = Math.max(1, (rel.weight || 1))
      ctx.setLineDash([4, 3])
      ctx.stroke()
      ctx.setLineDash([])
      // Relation label
      const mx = (s.x + t.x) / 2, my = (s.y + t.y) / 2
      ctx.fillStyle = '#64748b'
      ctx.font = '10px system-ui'
      ctx.textAlign = 'center'
      ctx.fillText(rel.relation || '', mx, my - 3)
    })

    // Draw nodes
    entities.forEach((e) => {
      const { x, y } = pos[e.id]
      const nr = 22 + (e.weight || 1) * 1.5
      const col = TYPE_COLOR[e.type] || TYPE_COLOR.default
      // Shadow
      ctx.shadowColor = col
      ctx.shadowBlur  = 10
      // Node circle
      ctx.beginPath()
      ctx.arc(x, y, nr, 0, 2 * Math.PI)
      ctx.fillStyle = col + '33'
      ctx.fill()
      ctx.strokeStyle = col
      ctx.lineWidth = 2
      ctx.stroke()
      ctx.shadowBlur = 0
      // Label
      const label = e.label?.length > 14 ? e.label.slice(0, 13) + '…' : e.label
      ctx.fillStyle = '#f1f5f9'
      ctx.font = `${e.id === entities[0]?.id ? 'bold ' : ''}11px system-ui`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(label || e.id, x, y)
    })
  }, [graph])

  return (
    <canvas ref={canvasRef} width={680} height={420}
      style={{ width: '100%', borderRadius: 8, background: 'var(--bg)', display: 'block' }} />
  )
}

export default function KnowledgeGraph() {
  const [topic,   setTopic]   = useState('')
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [error,   setError]   = useState(null)
  const [viewRaw, setViewRaw] = useState(false)

  const run = async () => {
    if (!topic.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const { data } = await buildKG(topic)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  const graph = result?.graph || {}

  return (
    <div>
      <SectionHeader title="Knowledge Graph"
        subtitle="Extract entities and relationships from your research corpus as an interactive graph." />

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="field">
          <label>Research Topic</label>
          <input className="input" placeholder="e.g. graph neural networks"
            value={topic} onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && run()} />
        </div>
        <button className="btn btn-primary" style={{ width: '100%' }}
          onClick={run} disabled={loading || !topic.trim()}>
          {loading ? 'Building Graph…' : 'Build Knowledge Graph'}
        </button>
      </div>

      {loading && <LoadingBlock text="Extracting entities and relationships…" />}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <div>
          {/* Stats */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
            <span className="badge badge-blue">{graph.entities?.length || 0} entities</span>
            <span className="badge badge-purple">{graph.relationships?.length || 0} relationships</span>
            <span className="badge badge-green">{graph.clusters?.length || 0} clusters</span>
            <span className="badge badge-gray">{result.papers_used} papers used</span>
            <button className="btn btn-sm btn-ghost" style={{ marginLeft: 'auto' }}
              onClick={() => setViewRaw(v => !v)}>
              {viewRaw ? 'Show Graph' : 'View JSON'}
            </button>
          </div>

          {/* Canvas graph */}
          {!viewRaw && (
            <div className="card" style={{ marginBottom: 14 }}>
              <div className="card-title">Knowledge Graph — {result.topic}</div>
              <KGCanvas graph={graph} />
              {/* Legend */}
              <div style={{ display: 'flex', gap: 12, marginTop: 12, flexWrap: 'wrap' }}>
                {Object.entries(TYPE_COLOR).filter(([k]) => k !== 'default').map(([type, col]) => (
                  <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--text2)' }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: col }} />
                    {type}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Raw JSON */}
          {viewRaw && (
            <div className="card">
              <pre style={{ fontSize: 11, color: 'var(--text2)', overflow: 'auto', maxHeight: 420 }}>
                {JSON.stringify(graph, null, 2)}
              </pre>
            </div>
          )}

          {/* Clusters */}
          {graph.clusters?.length > 0 && (
            <div className="card" style={{ marginTop: 14 }}>
              <div className="card-title">Clusters</div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {graph.clusters.map((cl, i) => (
                  <div key={i} style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, padding: '8px 12px', fontSize: 12 }}>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>{cl.name || `Cluster ${cl.id}`}</div>
                    <div style={{ color: 'var(--text3)', fontSize: 11 }}>{cl.entities?.join(', ')}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
