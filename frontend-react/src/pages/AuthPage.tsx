import { useState } from 'react'
import { login, signup } from './api/client'

interface Props {
  onAuth: () => void
}

export default function AuthPage({ onAuth }: Props) {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    email: '',
    password: '',
    tenant_slug: '',
    tenant_name: '',
    full_name: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(form.email, form.password, form.tenant_slug)
      } else {
        await signup({
          email: form.email,
          password: form.password,
          tenant_slug: form.tenant_slug,
          tenant_name: form.tenant_name,
          full_name: form.full_name,
        })
      }
      onAuth()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Nexus One</h1>
        <p className="subtitle">Enterprise Autonomous Execution Operating System</p>
        {error && <p className="error-msg">{error}</p>}
        <form onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <>
              <input className="input" placeholder="Full Name" value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
              <input className="input" placeholder="Organization Name" required value={form.tenant_name}
                onChange={(e) => setForm({ ...form, tenant_name: e.target.value })} />
            </>
          )}
          <input className="input" type="email" placeholder="Email" required value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="input" type="password" placeholder="Password" required value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <input className="input" placeholder="Tenant Slug (e.g. acme-corp)" required value={form.tenant_slug}
            onChange={(e) => setForm({ ...form, tenant_slug: e.target.value })} />
          <button className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem' }} disabled={loading}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Organization'}
          </button>
        </form>
        <p style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center' }}>
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button className="nav-item" style={{ display: 'inline', padding: 0, color: 'var(--accent)' }}
            onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}>
            {mode === 'login' ? 'Sign up' : 'Sign in'}
          </button>
        </p>
      </div>
    </div>
  )
}
