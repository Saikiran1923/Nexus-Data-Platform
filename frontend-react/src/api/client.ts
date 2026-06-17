const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export interface APIResponse<T> {
  success: boolean
  message: string
  data: T
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('nexus_token')
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' }
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: authHeaders() })
  const body = await res.json()
  if (!res.ok) throw new Error(body.message || 'Request failed')
  return body.data
}

export async function apiPost<T>(path: string, payload?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: authHeaders(),
    body: payload ? JSON.stringify(payload) : undefined,
  })
  const body = await res.json()
  if (!res.ok) throw new Error(body.message || 'Request failed')
  return body.data
}

export async function login(email: string, password: string, tenantSlug: string) {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, tenant_slug: tenantSlug }),
  })
  const body = await res.json()
  if (!res.ok) throw new Error(body.message || 'Login failed')
  localStorage.setItem('nexus_token', body.data.access_token)
  return body.data
}

export async function signup(data: {
  email: string
  password: string
  tenant_name: string
  tenant_slug: string
  full_name?: string
}) {
  const res = await fetch(`${API_BASE}/api/v1/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  const body = await res.json()
  if (!res.ok) throw new Error(body.message || 'Signup failed')
  localStorage.setItem('nexus_token', body.data.access_token)
  return body.data
}
