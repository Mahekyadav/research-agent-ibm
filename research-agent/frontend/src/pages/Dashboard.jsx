import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getStats, getHealth } from '../api'
import { StatCard, Alert, Spinner } from '../components/Shared'
import {
  BookOpen, TrendingUp, AlertCircle, Network,
  MessageCircle, Search, ArrowRight
} from 'lucide-react'

const QUICK = [
  { to: '/search',          icon: Search,       label: 'Search Papers',      color: 'var(--accent)',  desc: 'Aggregate from arXiv, S2, CrossRef' },
  { to: '/lit-review',      icon: BookOpen,     label: 'Literature Review',  color: 'var(--purple)',  desc: 'Synthesize indexed knowledge' },
  { to: '/trends',          icon: TrendingUp,   label: 'Trend Analysis',     color: 'var(--green)',   desc: 'Emerging directions & forecasts' },
  { to: '/citation-gaps',   icon: AlertCircle,  label: 'Citation Gaps',      color: 'var(--yellow)',  desc: 'Find understudied research areas' },
  { to: '/knowledge-graph', icon: Network,      label: 'Knowledge Graph',    color: 'var(--accent)',  desc: 'Entity & relation extraction' },
  { to: '/chat',            icon: MessageCircle,label: 'AI Chat',            color: 'var(--purple)',  desc: 'Multi-turn research conversation' },
]

export default function Dashboard() {
  const [stats, setStats]     = useState(null)
  const [health, setHealth]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    Promise.all([getStats(), getHealth()])
      .then(([s, h]) => { setStats(s.data); setHealth(h.data) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      {/* Hero */}
      <div className="card" style={{
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        border: '1px solid var(--border)', marginBottom: 24, position: 'relative', overflow: 'hidden'
      }}>
        <div style={{ position: 'absolute', top: -40, right: -40, width: 200, height: 200, borderRadius: '50%', background: 'rgba(59,130,246,.06)' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 10 }}>
          <div style={{ background: 'var(--accent)', width: 36, height: 36, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#fff', fontSize: 18 }}>🔬</span>
          </div>
          <div>
            <h1 style={{ fontSize: 20 }}>ResearchMind</h1>
            <p style={{ fontSize: 12, marginTop: 1 }}>IBM WatsonX Granite + Slate · Intelligent Research Companion</p>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <span className="badge badge-blue">Granite 13B</span>
            <span className="badge badge-purple">Slate 125M</span>
            {health && <span className="badge badge-green">API Online</span>}
          </div>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text2)', maxWidth: 560 }}>
          Aggregate papers from arXiv · Semantic Scholar · CrossRef, synthesize literature,
          detect citation gaps, predict trends, build knowledge graphs, and chat with your research corpus.
        </p>
      </div>

      {/* Stats */}
      {loading && <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}><Spinner large /></div>}
      {error   && <Alert type="error">Could not connect to API — {error}. Start the backend with <code>python main.py</code></Alert>}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 24 }}>
          <StatCard label="Documents Indexed"   value={stats.documents_indexed}  color="var(--accent)" />
          <StatCard label="Total Chunks"         value={stats.total_chunks}       color="var(--purple)" />
          <StatCard label="Collection"           value={stats.collection ? '✓' : '—'}
            sub={stats.collection || ''} color="var(--green)" />
        </div>
      )}

      {/* Source breakdown */}
      {stats?.sources_breakdown && Object.keys(stats.sources_breakdown).length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-title">Source Breakdown</div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {Object.entries(stats.sources_breakdown).map(([src, cnt]) => (
              <div key={src} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'var(--bg)', padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)' }}>
                <span style={{ fontSize: 12, fontWeight: 600 }}>{src}</span>
                <span className="badge badge-gray">{cnt}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div style={{ marginBottom: 8 }}>
        <h2 style={{ fontSize: 14, marginBottom: 14 }}>Quick Actions</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {QUICK.map(({ to, icon: Icon, label, color, desc }) => (
            <Link key={to} to={to} style={{ textDecoration: 'none' }}>
              <div className="card card-sm" style={{ cursor: 'pointer', transition: 'border-color .15s' }}
                onMouseEnter={e => e.currentTarget.style.borderColor = color}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <div style={{ background: `${color}22`, width: 30, height: 30, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Icon size={15} style={{ color }} />
                  </div>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{label}</span>
                  <ArrowRight size={13} style={{ marginLeft: 'auto', color: 'var(--text3)' }} />
                </div>
                <p style={{ fontSize: 12 }}>{desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
