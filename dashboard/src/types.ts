export type Tier = 'core' | 'growth' | 'advanced'
export type ClientStatus = 'active' | 'suspended' | 'offboarded'
export type PaymentStatus = 'paid' | 'pending' | 'overdue'
export type UserRole = 'owner' | 'operator' | 'read_only'

export interface ClientSummary {
  slug: string
  business_name: string
  tier: Tier
  status: ClientStatus
  app_version: string | null
  last_sync_at: string | null
  payment_status: PaymentStatus
}

export interface ClientDetail extends ClientSummary {
  contact_name: string | null
  contact_phone: string | null
  contract_start: string | null
  offboarded_at: string | null
  created_at: string
  updated_at: string
}

export interface AuditEntry {
  id: string
  actor: string
  action: string
  target_slug: string
  old_value: string | null
  new_value: string | null
  reason: string | null
  timestamp: string
}

export interface ProvisionPayload {
  slug: string
  business_name: string
  contact_name?: string | null
  contact_phone?: string | null
  tier: Tier
}

export interface User {
  id: string
  username: string
  role: UserRole
  active: 0 | 1
  last_login_at: string | null
  created_at: string
}

export interface LoginResponse {
  token: string
  user: User
}

export interface TokenRegenerationResponse {
  slug: string
  raw_token: string
  download_url: string
}
