import type {
  AuditEntry,
  ClientDetail,
  ClientSummary,
  LoginResponse,
  TokenRegenerationResponse,
  User,
} from '@/types'

const AUTH_TOKEN_KEY = 'session_token'
const ADMIN_TOKEN_KEY = 'admin_token'

function clearAuthTokens(): void {
  sessionStorage.removeItem(AUTH_TOKEN_KEY)
  sessionStorage.removeItem(ADMIN_TOKEN_KEY)
}

function redirectToLogin(): void {
  const pathname = window.location.pathname
  if (!pathname.endsWith('/login') && !pathname.endsWith('/dashboard/login')) {
    window.location.assign('/dashboard/login')
  }
}

function getPreferredToken(): string | null {
  return sessionStorage.getItem(AUTH_TOKEN_KEY) ?? sessionStorage.getItem(ADMIN_TOKEN_KEY)
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getPreferredToken()
  const headers = new Headers(init.headers)

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(path, {
    ...init,
    headers,
  })

  if (response.status === 401) {
    clearAuthTokens()
    redirectToLogin()
    throw new Error('Unauthorized')
  }

  if (!response.ok) {
    let detail = 'Request failed'
    try {
      const payload = (await response.json()) as { detail?: string; error?: string }
      detail = payload.detail ?? payload.error ?? detail
    } catch {
      detail = response.statusText || detail
    }
    throw new Error(detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const payload = await request<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })

  sessionStorage.setItem(AUTH_TOKEN_KEY, payload.token)
  sessionStorage.removeItem(ADMIN_TOKEN_KEY)
  return payload
}

export async function loginWithAdminToken(token: string): Promise<void> {
  const response = await fetch('/api/v1/admin/clients', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Unauthorized')
  }

  sessionStorage.setItem(ADMIN_TOKEN_KEY, token)
  sessionStorage.removeItem(AUTH_TOKEN_KEY)
}

export async function logout(): Promise<void> {
  const token = sessionStorage.getItem(AUTH_TOKEN_KEY)
  if (token) {
    try {
      await request('/api/v1/auth/logout', { method: 'POST' })
    } catch {
      // Ignore logout errors and clear state.
    }
  }
  clearAuthTokens()
}

export async function me(): Promise<User> {
  return request<User>('/api/v1/auth/me')
}

export async function listClients(): Promise<ClientSummary[]> {
  return request<ClientSummary[]>('/api/v1/admin/clients')
}

export async function getClient(slug: string): Promise<ClientDetail> {
  return request<ClientDetail>(`/api/v1/admin/clients/${slug}`)
}

export async function provisionClient(data: {
  slug: string
  business_name: string
  contact_name?: string | null
  contact_phone?: string | null
  tier: 'core' | 'growth' | 'advanced'
}): Promise<{ client_id: string; slug: string; raw_token: string; download_url: string }> {
  return request<{ client_id: string; slug: string; raw_token: string; download_url: string }>('/api/v1/admin/clients', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateClientStatus(
  slug: string,
  status: 'active' | 'suspended' | 'offboarded',
): Promise<{ slug: string; status: string }> {
  return request<{ slug: string; status: string }>(`/api/v1/admin/clients/${slug}/status`, {
    method: 'POST',
    body: JSON.stringify({ status }),
  })
}

export async function updateClientPayment(
  slug: string,
  paymentStatus: 'paid' | 'pending' | 'overdue',
): Promise<{ slug: string; payment_status: string }> {
  return request<{ slug: string; payment_status: string }>(`/api/v1/admin/clients/${slug}/payment`, {
    method: 'POST',
    body: JSON.stringify({ payment_status: paymentStatus }),
  })
}

export async function regenerateToken(slug: string): Promise<TokenRegenerationResponse> {
  return request<TokenRegenerationResponse>(`/api/v1/admin/clients/${slug}/regenerate-token`, {
    method: 'POST',
  })
}

export async function getClientAudit(slug: string): Promise<AuditEntry[]> {
  return request<AuditEntry[]>(`/api/v1/admin/clients/${slug}/audit`)
}

export async function listAudit(): Promise<AuditEntry[]> {
  return request<AuditEntry[]>('/api/v1/admin/audit')
}

export async function listUsers(): Promise<User[]> {
  return request<User[]>('/api/v1/admin/users')
}

export async function createUser(data: {
  username: string
  password: string
  role: 'owner' | 'operator' | 'read_only'
}): Promise<User> {
  return request<User>('/api/v1/admin/users', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateUser(
  id: string,
  data: { role?: 'owner' | 'operator' | 'read_only'; active?: number },
): Promise<User> {
  return request<User>(`/api/v1/admin/users/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function deactivateUser(id: string): Promise<void> {
  await request<void>(`/api/v1/admin/users/${id}`, { method: 'DELETE' })
}

export { clearAuthTokens, getPreferredToken }
