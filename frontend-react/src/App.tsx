import { useState } from 'react'
import AuthPage from './pages/AuthPage'
import MissionControl from './pages/MissionControl'
import ObjectiveCenter from './pages/ObjectiveCenter'
import EvidencePage from './pages/EvidencePage'

type Page = 'mission' | 'objectives' | 'evidence' | 'workforce' | 'portfolio'

const NAV: { id: Page; label: string }[] = [
  { id: 'mission', label: 'Mission Control' },
  { id: 'objectives', label: 'Objective Center' },
  { id: 'evidence', label: 'Evidence & Insights' },
  { id: 'workforce', label: 'AI Workforce' },
  { id: 'portfolio', label: 'Portfolio' },
]

export default function App() {
  const [authed, setAuthed] = useState(!!localStorage.getItem('nexus_token'))
  const [page, setPage] = useState<Page>('mission')

  if (!authed) return <AuthPage onAuth={() => setAuthed(true)} />

  const renderPage = () => {
    switch (page) {
      case 'mission': return <MissionControl />
      case 'objectives': return <ObjectiveCenter />
      case 'evidence': return <EvidencePage />
      case 'workforce': return <MissionControl />
      case 'portfolio': return <MissionControl />
      default: return <MissionControl />
    }
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          Nexus One
          <span>Autonomous Execution OS</span>
        </div>
        {NAV.map((n) => (
          <button key={n.id} className={`nav-item ${page === n.id ? 'active' : ''}`} onClick={() => setPage(n.id)}>
            {n.label}
          </button>
        ))}
        <button className="nav-item" style={{ marginTop: 'auto', color: 'var(--danger)' }}
          onClick={() => { localStorage.removeItem('nexus_token'); setAuthed(false); }}>
          Sign Out
        </button>
      </aside>
      <main className="main-content">{renderPage()}</main>
    </div>
  )
}
