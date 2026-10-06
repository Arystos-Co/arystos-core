import type { UserRole } from '@/types'

import { Badge } from '@/components/ui/badge'

export function RoleBadge({ value }: { value: UserRole }) {
  const label = value === 'read_only' ? 'read only' : value

  return <Badge variant="secondary">{label}</Badge>
}
