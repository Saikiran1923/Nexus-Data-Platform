import { useEffect, useState } from 'react'
import { apiGet, apiPost } from '../api/client'

interface Objective {
  id: string
  title: string
  description: string
  category: string
  complexity: string
  status: string
  success_probability: number
  estimated_duration_hours: number
  predicted_risk_level: string
  selected_agents: string[]
  predicted_outputs: string[]
  current_phase: string
}

export default function ObjectiveCenter() {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [objectives, setObjectives] = useState<Objective[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = () => apiGet<Objective[]>('/api/v1/objectives').then(setObjectives).catch(console.error)
  useEffect(() => { load() }, [])

  const examples = [
    'Build Customer Analytics Dashboard',
    'Analyze Sales Performance',
    'Create Executive KPI Report',
    'Build Forecasting Model',
    'Improve Customer Retention',
  ]

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await apiPost('/api/v1/objectives', { title, description })
      setTitle('')
      setDescription('')
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create objective')
    } finally {
      setLoading(false)
    }
  }

  const handleExecute = async (id: string) => {
    await apiPost(`/api/v1/objectives/${id}/execute`)
    load()
  }

  return (
    <div>
      <div className="page-header">
        <h1>Objective Center</h1>
        <p>Define business objectives — Nexus One automatically plans, selects agents, and executes.</p>
      </div>

      <div className="section-grid">
        <div className="card">
          <h3>New Business Objective</h3>
          {error && <p className="error-msg">{error}</p>}
          <form onSubmit={handleCreate}>
            <input className="input" placeholder="Business Objective" required value={title}
              onChange={(e) => setTitle(e.target.value)} />
            <textarea className="input textarea" placeholder="Describe what you want to achieve..." required
              value={description} onChange={(e) => setDescription(e.target.value)} />
            <button className="btn btn-primary" disabled={loading}>
              {loading ? 'Analyzing...' : 'Analyze & Plan'}
            </button>
          </form>
          <div style={{ marginTop: '1rem' }}>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Examples:</p>
            {examples.map((ex) => (
              <button key={ex} className="agent-chip" style={{ cursor: 'pointer' }}
                onClick={() => { setTitle(ex); setDescription(`Execute: ${ex}. Deliver production-ready outputs with full evidence trail.`); }}>
                {ex}
              </button>
            ))}
          </div>
        </div>

        <div className="card">
          <h3>Your Objectives</h3>
          {objectives.map((o) => (
            <div key={o.id} className="list-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                <strong>{o.title}</strong>
                <span className={`badge badge-${o.status === 'completed' ? 'success' : 'info'}`}>{o.status}</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {o.category} · {o.complexity} · {o.success_probability}% success · {o.estimated_duration_hours}h
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Agents: {o.selected_agents?.slice(0, 4).join(', ')}{o.selected_agents?.length > 4 ? '...' : ''}
              </div>
              {o.status === 'analyzed' && (
                <button className="btn btn-secondary" onClick={() => handleExecute(o.id)}>Execute Now</button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
