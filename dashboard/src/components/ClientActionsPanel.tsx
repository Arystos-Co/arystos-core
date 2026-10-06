import { ShieldAlert } from 'lucide-react'

import { PaymentBadge } from '@/components/PaymentBadge'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { canRegenerateToken } from '@/lib/roles'
import type { ClientDetail, ClientStatus, PaymentStatus, UserRole } from '@/types'

interface ClientActionsPanelProps {
  client: ClientDetail
  currentRole: UserRole
  onStatusChange: (status: ClientStatus) => void
  onPaymentChange: (status: PaymentStatus) => void
  onRegenerateToken: () => void
}

export function ClientActionsPanel({
  client,
  currentRole,
  onStatusChange,
  onPaymentChange,
  onRegenerateToken,
}: ClientActionsPanelProps) {
  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <StatusBadge value={client.status} />
          <div className="grid gap-2 md:grid-cols-3">
            <Button variant={client.status === 'active' ? 'secondary' : 'default'} onClick={() => onStatusChange('active')} disabled={client.status === 'active'}>
              Activate
            </Button>
            <Button variant={client.status === 'suspended' ? 'secondary' : 'default'} onClick={() => onStatusChange('suspended')}>
              Suspend
            </Button>
            <Button variant={client.status === 'offboarded' ? 'secondary' : 'default'} onClick={() => onStatusChange('offboarded')}>
              Offboard
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Payment</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <PaymentBadge value={client.payment_status} />
          <div className="grid gap-2 md:grid-cols-3">
            <Button variant="secondary" onClick={() => onPaymentChange('paid')}>Paid</Button>
            <Button variant="secondary" onClick={() => onPaymentChange('pending')}>Pending</Button>
            <Button variant="secondary" onClick={() => onPaymentChange('overdue')}>Overdue</Button>
          </div>
        </CardContent>
      </Card>

      {canRegenerateToken(currentRole) ? (
        <Card>
          <CardHeader>
            <CardTitle>Danger zone</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border border-status-overdue/40 bg-status-overdue/5 p-3 text-sm text-foreground">
              <div className="mb-2 flex items-center gap-2 font-medium text-status-overdue">
                <ShieldAlert className="h-4 w-4" />
                Regenerate token
              </div>
              <p className="text-muted-foreground">This invalidates the current client token and issues a new one.</p>
            </div>
            <Button variant="destructive" onClick={onRegenerateToken}>
              Regenerate token
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <Separator className="my-4" />
    </div>
  )
}
