import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard    from './pages/Dashboard'
import Search       from './pages/Search'
import LitReview    from './pages/LitReview'
import Trends       from './pages/Trends'
import CitationGaps from './pages/CitationGaps'
import KnowledgeGraph from './pages/KnowledgeGraph'
import ResearchQA   from './pages/ResearchQA'
import Chat         from './pages/Chat'
import Critique     from './pages/Critique'
import Clusters     from './pages/Clusters'
import Ingest       from './pages/Ingest'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"     element={<Dashboard />} />
          <Route path="search"        element={<Search />} />
          <Route path="ingest"        element={<Ingest />} />
          <Route path="lit-review"    element={<LitReview />} />
          <Route path="trends"        element={<Trends />} />
          <Route path="citation-gaps" element={<CitationGaps />} />
          <Route path="knowledge-graph" element={<KnowledgeGraph />} />
          <Route path="research-qa"   element={<ResearchQA />} />
          <Route path="chat"          element={<Chat />} />
          <Route path="critique"      element={<Critique />} />
          <Route path="clusters"      element={<Clusters />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
