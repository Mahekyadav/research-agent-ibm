import axios from 'axios'

// In dev: Vite proxy forwards /api/* → http://localhost:8000/*
// In prod: FastAPI serves the SPA and all routes are on the same origin
const BASE = import.meta.env.VITE_API_URL || ''

const http = axios.create({ baseURL: BASE, timeout: 120000 })

/* ── Health ── */
export const getHealth = () => http.get('/health')
export const getStats  = () => http.get('/stats')

/* ── Search & Ingest ── */
export const searchPapers = (payload) => http.post('/search', payload)
export const searchArxiv  = (query, max_results = 10) =>
  http.get('/search/arxiv', { params: { query, max_results } })
export const searchS2 = (query, limit = 10) =>
  http.get('/search/semantic-scholar', { params: { query, limit } })
export const searchCrossref = (query, rows = 10) =>
  http.get('/search/crossref', { params: { query, rows } })

export const ingestFile = (file, force = false) => {
  const fd = new FormData()
  fd.append('file', file)
  return http.post(`/ingest/file?force=${force}`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const ingestUrl  = (url)            => http.post('/ingest/url',  { url })
export const ingestText = (text, source_name) => http.post('/ingest/text', { text, source_name })

/* ── Intelligence ── */
export const literatureReview = (query)        => http.post('/research/literature-review', { query })
export const trendAnalysis    = (domain)       => http.post('/research/trends',            { domain })
export const citationGaps     = (topic)        => http.post('/research/citation-gaps',     { topic })
export const researchAsk      = (question, session_id) =>
  http.post('/research/ask', { question, session_id })
export const buildKG          = (topic)        => http.post('/research/knowledge-graph',   { topic })
export const critiquePaper    = (paper_title)  => http.post('/research/critique',          { paper_title })
export const topicClusters    = (domain, n_clusters) =>
  http.post('/research/clusters', { domain, n_clusters })

/* ── Conversation ── */
export const newSession     = ()           => http.post('/chat/session/new')
export const chat           = (message, session_id) => http.post('/chat', { message, session_id })
export const getHistory     = (sid)        => http.get(`/chat/session/${sid}/history`)
export const endSession     = (sid)        => http.delete(`/chat/session/${sid}`)
export const listSessions   = ()           => http.get('/chat/sessions')
