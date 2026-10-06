import type { PaymentStatus } from '@/types'

import { Badge } from '@/components/ui/badge'

const paymentStyles: Record<PaymentStatus, 'active' | 'suspended' | 'overdue' | 'secondary'> = {
  paid: 'active',
  pending: 'secondary',
  overdue: 'overdue',
}

export function PaymentBadge({ value }: { value: PaymentStatus }) {
  return <Badge variant={paymentStyles[value]}>{value}</Badge>
}
