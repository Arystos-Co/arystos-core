import type { UserRole } from '@/types'

export function canProvision(role: UserRole): boolean {
  return role === 'owner' || role === 'operator'
}

export function canOffboard(role: UserRole): boolean {
  return role === 'owner' || role === 'operator'
}

export function canManageUsers(role: UserRole): boolean {
  return role === 'owner'
}

export function canRegenerateToken(role: UserRole): boolean {
  return role === 'owner'
}
