import type { ClientStatus } from '@/types'

import { Badge } from '@/components/ui/badge'

const statusStyles: Record<ClientStatus, 'active' | 'suspended' | 'offboarded'> = {
  active: 'active',
  suspended: 'suspended',
  offboarded: 'offboarded',
}

export function StatusBadge({ value }: { value: ClientStatus }) {
  return <Badge variant={statusStyles[value]}>{value}</Badge>
}
