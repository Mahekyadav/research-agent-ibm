import React, { useState, useEffect } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Search, Upload, BookOpen, TrendingUp,
  AlertCircle, Network, MessageSquare, MessageCircle,
  FileSearch, Grid3X3, Atom, ChevronLeft, ChevronRight
} from 'lucide-react'
import { getHealth } from '../api'

const NAV = [
  { to: '/dashboard',      icon: LayoutDashboard, label: 'Dashboard',       group: 'Overview' },
  { to: '/search',         icon: Search,          label: 'Search Papers',   group: 'Sources' },
  { to: '/ingest',         icon: Upload,          label: 'Ingest / Upload', group: 'Sources' },
  { to: '/lit-review',     icon: BookOpen,        label: 'Literature Review',group: 'Intelligence' },
  { to: '/trends',         icon: TrendingUp,      label: 'Trend Analysis',  group: 'Intelligence' },
  { to: '/citation-gaps',  icon: AlertCircle,     label: 'Citation Gaps',   group: 'Intelligence' },
  { to: '/knowledge-graph',icon: Network,         label: 'Knowledge Graph', group: 'Visualize' },
  { to: '/clusters',       icon: Grid3X3,         label: 'Topic Clusters',  group: 'Visualize' },
  { to: '/research-qa',    icon: MessageSquare,   label: 'Research Q&A',    group: 'Query' },
  { to: '/chat',           icon: MessageCircle,   label: 'AI Chat',         group: 'Query' },
  { to: '/critique',       icon: FileSearch,      label: 'Paper Critique',  group: 'Analysis' },
]

const GROUPS = ['Overview', 'Sources', 'Intelligence', 'Visualize', 'Query', 'Analysis']

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const [online, setOnline] = useState(null)
  const location = useLocation()

  useEffect(() => {
    getHealth()
      .then(() => setOnline(true))
      .catch(() => setOnline(false))
  }, [])

  const pageLabel = NAV.find(n => location.pathname.startsWith(n.to))?.label || 'ResearchMind'

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <aside style={{
        width: collapsed ? 56 : 240,
        background: 'var(--bg2)',
        borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column',
        transition: 'width .2s', flexShrink: 0, overflow: 'hidden',
      }}>
        {/* Logo */}
        <div style={{
          height: 'var(--topbar-h)', display: 'flex', alignItems: 'center',
          gap: 10, padding: collapsed ? '0 16px' : '0 18px',
          borderBottom: '1px solid var(--border)', flexShrink: 0,
        }}>
          <div style={{
            width: 28, height: 28, borderRadius: 6, background: 'var(--accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <Atom size={16} color="#fff" />
          </div>
          {!collapsed && (
            <div>
              <div style={{ fontWeight: 800, fontSize: 13, letterSpacing: '-.3px' }}>ResearchMind</div>
              <div style={{ fontSize: 10, color: 'var(--text3)' }}>IBM WatsonX</div>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
          {GROUPS.map(group => {
            const items = NAV.filter(n => n.group === group)
            return (
              <div key={group} style={{ marginBottom: 4 }}>
                {!collapsed && (
                  <div style={{
                    fontSize: 10, fontWeight: 700, color: 'var(--text3)',
                    textTransform: 'uppercase', letterSpacing: '.8px',
                    padding: '8px 18px 4px',
                  }}>{group}</div>
                )}
                {items.map(({ to, icon: Icon, label }) => (
                  <NavLink key={to} to={to} style={{ textDecoration: 'none' }}>
                    {({ isActive }) => (
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: 10,
                        padding: collapsed ? '9px 16px' : '9px 18px',
                        borderRadius: 6, margin: '1px 8px',
                        background: isActive ? 'var(--accent-bg)' : 'transparent',
                        color: isActive ? 'var(--accent2)' : 'var(--text2)',
                        cursor: 'pointer', transition: 'background .12s, color .12s',
                        whiteSpace: 'nowrap',
                      }}
                        onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = 'rgba(255,255,255,.04)' }}
                        onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent' }}
                      >
                        <Icon size={16} style={{ flexShrink: 0 }} />
                        {!collapsed && <span style={{ fontSize: 13 }}>{label}</span>}
                      </div>
                    )}
                  </NavLink>
                ))}
              </div>
            )
          })}
        </nav>

        {/* Status + collapse */}
        <div style={{
          borderTop: '1px solid var(--border)', padding: '10px 12px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          {!collapsed && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
              <div style={{
                width: 7, height: 7, borderRadius: '50%',
                background: online === true ? 'var(--green)' : online === false ? 'var(--red)' : 'var(--text3)',
              }} />
              <span style={{ color: 'var(--text3)' }}>
                {online === true ? 'API Online' : online === false ? 'API Offline' : 'Checking…'}
              </span>
            </div>
          )}
          <button
            onClick={() => setCollapsed(c => !c)}
            className="btn btn-icon btn-secondary"
            style={{ marginLeft: collapsed ? 'auto' : 0 }}
          >
            {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Topbar */}
        <header style={{
          height: 'var(--topbar-h)', background: 'var(--bg2)',
          borderBottom: '1px solid var(--border)', display: 'flex',
          alignItems: 'center', padding: '0 24px', flexShrink: 0,
          gap: 10,
        }}>
          <h2 style={{ fontSize: 15, fontWeight: 600 }}>{pageLabel}</h2>
          <div style={{ flex: 1 }} />
          <span className="badge badge-blue" style={{ fontSize: 10 }}>IBM Granite 13B</span>
          <span className="badge badge-purple" style={{ fontSize: 10 }}>Slate 125M</span>
        </header>

        {/* Page content */}
        <main style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
