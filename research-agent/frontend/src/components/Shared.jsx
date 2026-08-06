import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function Spinner({ large }) {
  return <div className={`spinner${large ? ' spinner-lg' : ''}`} />
}

export function LoadingBlock({ text = 'Running…' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '60px 20px', gap: 16 }}>
      <Spinner large />
      <p style={{ color: 'var(--text3)', fontSize: 13 }}>{text}</p>
    </div>
  )
}

export function Alert({ type = 'error', children }) {
  return <div className={`alert alert-${type}`}>{children}</div>
}

export function MdOutput({ content }) {
  if (!content) return null
  return (
    <div className="md-output">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  )
}

export function SourceList({ sources }) {
  if (!sources?.length) return null
  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '.5px', marginBottom: 8 }}>
        Sources ({sources.length})
      </div>
      {sources.map((s, i) => (
        <div key={i} className="source-card">
          <div className="sc-title">{s.title || s.source}</div>
          <div className="sc-meta">
            {s.authors && <span>{s.authors}</span>}
            {s.year    && <span>{s.year}</span>}
            {s.citation_count > 0 && <span>Cited {s.citation_count}×</span>}
            {s.source_type && <span className="badge badge-gray" style={{ fontSize: 10 }}>{s.source_type}</span>}
          </div>
        </div>
      ))}
    </div>
  )
}

export function PaperCard({ paper, onIngest }) {
  const authors = Array.isArray(paper.authors) ? paper.authors.slice(0, 3).join(', ') : paper.authors || ''
  return (
    <div className="paper-card">
      <div className="pc-title">
        {paper.url || paper.doi ? (
          <a href={paper.url || `https://doi.org/${paper.doi}`} target="_blank" rel="noreferrer"
            style={{ color: 'var(--accent2)', textDecoration: 'none' }}>
            {paper.title}
          </a>
        ) : paper.title}
      </div>
      <div className="pc-author">{authors}{paper.published ? ` · ${paper.published?.slice(0,4)}` : paper.year ? ` · ${paper.year}` : ''}</div>
      {paper.abstract && <div className="pc-abstract">{paper.abstract}</div>}
      <div className="pc-footer">
        <span className="badge badge-gray">{paper.source}</span>
        {paper.citation_count > 0 && (
          <span className="badge badge-yellow">{paper.citation_count} citations</span>
        )}
        {paper.categories?.length > 0 && (
          <span className="badge badge-purple">{paper.categories[0]}</span>
        )}
        {onIngest && (
          <button className="btn btn-sm btn-ghost" style={{ marginLeft: 'auto' }} onClick={() => onIngest(paper)}>
            + Ingest
          </button>
        )}
      </div>
    </div>
  )
}

export function StatCard({ label, value, sub, color = 'var(--accent)' }) {
  return (
    <div className="card" style={{ textAlign: 'center' }}>
      <div style={{ fontSize: 28, fontWeight: 800, color }}>{value ?? '—'}</div>
      <div style={{ fontSize: 13, fontWeight: 600, marginTop: 4 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

export function SectionHeader({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <h1 style={{ fontSize: 19, fontWeight: 700 }}>{title}</h1>
      {subtitle && <p style={{ fontSize: 13, marginTop: 4 }}>{subtitle}</p>}
    </div>
  )
}

export function Empty({ icon: Icon, message }) {
  return (
    <div className="empty">
      {Icon && <Icon size={40} style={{ display: 'block', margin: '0 auto 12px', opacity: .3 }} />}
      <p>{message || 'Nothing here yet.'}</p>
    </div>
  )
}
