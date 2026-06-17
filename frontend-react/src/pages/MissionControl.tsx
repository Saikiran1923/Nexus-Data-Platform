import { useEffect, useState } from 'react'
import { apiGet } from '../api/client'

interface KPIs {
  business_objectives: number
  running_projects: number
  completed_projects: number
  active_agents: number
  quality_score: number
  hours_saved: number
  cost_savings_usd: number
  revenue_impact_usd: number
}

interface Dashboard {
  kpis: KPIs
  subscription: { plan_name: string; minutes_remaining: number }
  open_risks: number
  recent_objectives: Array<{ id: string; title: string; status: string; category: string; phase: string }>
}

export default function MissionControl() {
  const [data, setData] = useState<Dashboard | null>(null)
  const [workforce, setWorkforce] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    apiGet<Dashboard>('/api/v1/mission-control/dashboard').then(setData).catch(console.error)
    apiGet<Record<string, unknown>>('/api/v1/mission-control/workforce').then(setWorkforce).catch(console.error)
  }, [])

  if (!data) return <p style={{ color: 'var(--text-muted)' }}>Loading Mission Control...</p>

  const kpis = [
    { label: 'Business Objectives', value: data.kpis.business_objectives, cls: 'accent' },
    { label: 'Running Projects', value: data.kpis.running_projects, cls: 'warning' },
    { label: 'Completed Projects', value: data.kpis.completed_projects, cls: 'success' },
    { label: 'Active Agents', value: data.kpis.active_agents, cls: 'purple' },
    { label: 'Quality Score', value: `${data.kpis.quality_score}%`, cls: 'success' },
    { label: 'Hours Saved', value: data.kpis.hours_saved, cls: 'accent' },
    { label: 'Cost Savings', value: `$${data.kpis.cost_savings_usd.toLocaleString()}`, cls: 'success' },
    { label: 'Revenue Impact', value: `$${data.kpis.revenue_impact_usd.toLocaleString()}`, cls: 'purple' },
  ]

  const departments = workforce?.departments as Record<string, { department: string; agents: Array<{ name: string }> }> | undefined

  return (
    <div>
      <div className="page-header">
        <h1>Mission Control</h1>
        <p>{data.subscription.plan_name} plan · {data.open_risks} open risks · {data.subscription.minutes_remaining} min runtime remaining</p>
      </div>

      <div className="kpi-grid">
        {kpis.map((k) => (
          <div key={k.label} className="kpi-card">
            <div className="kpi-label">{k.label}</div>
            <div className={`kpi-value ${k.cls}`}>{k.value}</div>
          </div>
        ))}
      </div>

      <div className="section-grid">
        <div className="card">
          <h3>Recent Objectives</h3>
          {data.recent_objectives.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No objectives yet. Create one in Objective Center.</p>}
          {data.recent_objectives.map((o) => (
            <div key={o.id} className="list-item">
              <div>
                <strong>{o.title}</strong>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{o.category}</div>
              </div>
              <span className={`badge badge-${o.status === 'completed' ? 'success' : 'info'}`}>{o.status}</span>
            </div>
          ))}
        </div>

        <div className="card">
          <h3>AI Workforce Board</h3>
          {departments && Object.entries(departments).map(([key, dept]) => (
            <div key={key} className="workforce-dept">
              <h4>{dept.department}</h4>
              {dept.agents.map((a) => (
                <span key={a.name} className="agent-chip">{a.name}</span>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
