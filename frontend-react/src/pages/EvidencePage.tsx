import { useEffect, useState } from 'react'
import { apiGet } from '../api/client'

interface Evidence {
  id: string
  agent_name: string
  action: string
  reason: string
  impact: string
  created_at: string
}

interface Risk {
  id: string
  risk_type: string
  severity: string
  description: string
  mitigation: string
}

interface Insight {
  id: string
  summary: string
  recommendations: string[]
  roi_analysis: Record<string, number>
}

export default function EvidencePage() {
  const [evidence, setEvidence] = useState<Evidence[]>([])
  const [risks, setRisks] = useState<Risk[]>([])
  const [insights, setInsights] = useState<Insight[]>([])

  useEffect(() => {
    apiGet<Evidence[]>('/api/v1/mission-control/evidence').then(setEvidence).catch(console.error)
    apiGet<Risk[]>('/api/v1/mission-control/risks').then(setRisks).catch(console.error)
    apiGet<Insight[]>('/api/v1/mission-control/executive-insights').then(setInsights).catch(console.error)
  }, [])

  return (
    <div>
      <div className="page-header">
        <h1>Evidence & Insights</h1>
        <p>Every action is traceable. Executive insights and risk intelligence in one view.</p>
      </div>

      <div className="section-grid">
        <div className="card">
          <h3>Evidence Center</h3>
          {evidence.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No evidence yet. Execute an objective to generate traceable evidence.</p>}
          {evidence.map((e) => (
            <div key={e.id} className="evidence-row">
              <strong>{e.agent_name}</strong>
              <div style={{ fontSize: '0.85rem', margin: '0.25rem 0' }}>{e.action}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Reason: {e.reason}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--success)' }}>Impact: {e.impact}</div>
            </div>
          ))}
        </div>

        <div className="card">
          <h3>Risk Center</h3>
          {risks.map((r) => (
            <div key={r.id} className="list-item" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
              <span className={`badge badge-${r.severity === 'high' ? 'danger' : 'warning'}`}>{r.severity}</span>
              <strong style={{ marginTop: '0.25rem' }}>{r.risk_type}</strong>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{r.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginTop: '1.5rem' }}>
        <h3>Executive Insights</h3>
        {insights.map((i) => (
          <div key={i.id} style={{ padding: '1rem 0', borderBottom: '1px solid var(--border)' }}>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem', color: 'var(--text-secondary)', fontFamily: 'inherit' }}>{i.summary}</pre>
            {i.roi_analysis && (
              <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--success)' }}>
                ROI: {i.roi_analysis.roi_percentage}% · Payback: {i.roi_analysis.payback_period_months} months
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
