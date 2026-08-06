import React, { useState } from 'react'
import { ingestFile, ingestUrl, ingestText } from '../api'
import { Alert, SectionHeader } from '../components/Shared'
import { Upload, Link2, FileText, CheckCircle } from 'lucide-react'

function ResultBadge({ result }) {
  if (!result) return null
  return (
    <div className="alert alert-success" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <CheckCircle size={16} />
      <span>
        {result.status === 'success' || result.chunks
          ? `Ingested successfully — ${result.chunks} chunks added`
          : result.status === 'skipped'
          ? 'Already in knowledge base (skipped)'
          : JSON.stringify(result)}
      </span>
    </div>
  )
}

export default function Ingest() {
  // File tab
  const [file, setFile] = useState(null)
  const [force, setForce] = useState(false)
  const [fileRes, setFileRes] = useState(null)
  const [fileErr, setFileErr] = useState(null)
  const [fileLoading, setFileLoading] = useState(false)

  // URL tab
  const [url, setUrl] = useState('')
  const [urlRes, setUrlRes] = useState(null)
  const [urlErr, setUrlErr] = useState(null)
  const [urlLoading, setUrlLoading] = useState(false)

  // Text tab
  const [text, setText] = useState('')
  const [srcName, setSrcName] = useState('user_note')
  const [textRes, setTextRes] = useState(null)
  const [textErr, setTextErr] = useState(null)
  const [textLoading, setTextLoading] = useState(false)

  const [tab, setTab] = useState(0)

  const submitFile = async () => {
    if (!file) return
    setFileLoading(true); setFileErr(null); setFileRes(null)
    try {
      const { data } = await ingestFile(file, force)
      setFileRes(data)
    } catch (e) { setFileErr(e.response?.data?.detail || e.message) }
    finally { setFileLoading(false) }
  }

  const submitUrl = async () => {
    if (!url.trim()) return
    setUrlLoading(true); setUrlErr(null); setUrlRes(null)
    try {
      const { data } = await ingestUrl(url)
      setUrlRes(data)
    } catch (e) { setUrlErr(e.response?.data?.detail || e.message) }
    finally { setUrlLoading(false) }
  }

  const submitText = async () => {
    if (text.trim().length < 20) return
    setTextLoading(true); setTextErr(null); setTextRes(null)
    try {
      const { data } = await ingestText(text, srcName)
      setTextRes(data)
    } catch (e) { setTextErr(e.response?.data?.detail || e.message) }
    finally { setTextLoading(false) }
  }

  const TABS = ['File Upload', 'URL', 'Paste Text']

  return (
    <div>
      <SectionHeader title="Ingest Research Content"
        subtitle="Add PDFs, URLs, or pasted abstracts directly into the knowledge base." />

      <div className="tabs">
        {TABS.map((t, i) => (
          <button key={t} className={`tab ${tab === i ? 'active' : ''}`} onClick={() => setTab(i)}>{t}</button>
        ))}
      </div>

      {/* File Upload */}
      {tab === 0 && (
        <div className="card">
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12,
            border: '2px dashed var(--border)', borderRadius: 10, padding: '32px 20px',
            cursor: 'pointer', marginBottom: 16, transition: 'border-color .15s' }}
            onClick={() => document.getElementById('fi').click()}
            onDragOver={e => { e.preventDefault(); e.currentTarget.style.borderColor = 'var(--accent)' }}
            onDragLeave={e => { e.currentTarget.style.borderColor = 'var(--border)' }}
            onDrop={e => { e.preventDefault(); setFile(e.dataTransfer.files[0]); e.currentTarget.style.borderColor = 'var(--border)' }}
          >
            <Upload size={32} style={{ color: 'var(--text3)' }} />
            <p style={{ fontSize: 13 }}>{file ? file.name : 'Click or drag & drop a PDF, DOCX, or TXT file'}</p>
            {file && <span className="badge badge-green">{(file.size / 1024).toFixed(0)} KB</span>}
            <input id="fi" type="file" accept=".pdf,.docx,.txt,.md" style={{ display: 'none' }}
              onChange={e => setFile(e.target.files[0])} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <label style={{ margin: 0 }}>Force re-ingest if already indexed</label>
            <button className={`btn btn-sm ${force ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setForce(v => !v)}>{force ? 'On' : 'Off'}</button>
          </div>
          {fileErr && <Alert type="error">{fileErr}</Alert>}
          <ResultBadge result={fileRes} />
          <button className="btn btn-primary" style={{ width: '100%' }}
            onClick={submitFile} disabled={!file || fileLoading}>
            {fileLoading ? 'Ingesting…' : 'Ingest File'}
          </button>
        </div>
      )}

      {/* URL */}
      {tab === 1 && (
        <div className="card">
          <div className="field">
            <label>Paper or Preprint URL</label>
            <div style={{ display: 'flex', gap: 8 }}>
              <Link2 size={16} style={{ color: 'var(--text3)', alignSelf: 'center', flexShrink: 0 }} />
              <input className="input" placeholder="https://arxiv.org/abs/2310.12345"
                value={url} onChange={e => setUrl(e.target.value)} />
            </div>
          </div>
          {urlErr && <Alert type="error">{urlErr}</Alert>}
          <ResultBadge result={urlRes} />
          <button className="btn btn-primary" style={{ width: '100%' }}
            onClick={submitUrl} disabled={!url.trim() || urlLoading}>
            {urlLoading ? 'Ingesting…' : 'Ingest from URL'}
          </button>
        </div>
      )}

      {/* Text */}
      {tab === 2 && (
        <div className="card">
          <div className="field">
            <label>Source Name</label>
            <input className="input" placeholder="my_research_note" value={srcName}
              onChange={e => setSrcName(e.target.value)} />
          </div>
          <div className="field">
            <label>Research Text / Abstract</label>
            <textarea className="textarea" rows={8}
              placeholder="Paste your abstract, research notes, or paper excerpt here…"
              value={text} onChange={e => setText(e.target.value)} />
          </div>
          <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 12 }}>
            {text.length} characters · min 20 required
          </div>
          {textErr && <Alert type="error">{textErr}</Alert>}
          <ResultBadge result={textRes} />
          <button className="btn btn-primary" style={{ width: '100%' }}
            onClick={submitText} disabled={text.trim().length < 20 || textLoading}>
            {textLoading ? 'Ingesting…' : 'Ingest Text'}
          </button>
        </div>
      )}
    </div>
  )
}
