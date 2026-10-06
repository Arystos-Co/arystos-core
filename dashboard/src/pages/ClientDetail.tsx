import { ArrowLeft } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import * as api from '@/api'
import { ClientActionsPanel } from '@/components/ClientActionsPanel'
import { ClientInfoPanel } from '@/components/ClientInfoPanel'
import { RelativeTime } from '@/components/RelativeTime'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import type { AuditEntry, ClientDetail as ClientDetailType, PaymentStatus, UserRole } from '@/types'

export function ClientDetailPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const [client, setClient] = useState<ClientDetailType | null>(null)
  const [audit, setAudit] = useState<AuditEntry[]>([])
  const [currentRole, setCurrentRole] = useState<UserRole>('read_only')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!slug) {
      return
    }

    const load = async () => {
      try {
        setIsLoading(true)
        const [detail, entries, user] = await Promise.all([
          api.getClient(slug),
          api.getClientAudit(slug),
          api.me(),
        ])
        setClient(detail)
        setAudit(entries.slice(0, 10))
        setCurrentRole(user.role)
      } finally {
        setIsLoading(false)
      }
    }

    void load()
  }, [slug])

  const handleStatusChange = async (status: 'active' | 'suspended' | 'offboarded') => {
    if (!slug) {
      return
    }
    const result = await api.updateClientStatus(slug, status)
    if (client) {
      setClient({ ...client, status: result.status as ClientDetailType['status'] })
    }
  }

  const handlePaymentChange = async (paymentStatus: PaymentStatus) => {
    if (!slug) {
      return
    }
    const result = await api.updateClientPayment(slug, paymentStatus)
    if (client) {
      setClient({ ...client, payment_status: result.payment_status as ClientDetailType['payment_status'] })
    }
  }

  const handleRegenerateToken = async () => {
    if (!slug) {
      return
    }
    const result = await api.regenerateToken(slug)
    if (result.raw_token) {
      window.alert(`New client token: ${result.raw_token}`)
    }
  }

  if (isLoading || !client) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-10 w-40" />
        <div className="grid gap-6 lg:grid-cols-[1.6fr_0.9fr]">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={() => navigate('/clients')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <div>
            <div className="text-sm uppercase tracking-wide text-muted-foreground">Client</div>
            <h1 className="text-2xl font-medium">{client.business_name}</h1>
          </div>
        </div>
        <div className="text-right text-sm text-muted-foreground">
          <div className="font-mono">{client.slug}</div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.6fr_0.9fr]">
        <ClientInfoPanel client={client} />
        <ClientActionsPanel
          client={client}
          currentRole={currentRole}
          onStatusChange={handleStatusChange}
          onPaymentChange={handlePaymentChange}
          onRegenerateToken={handleRegenerateToken}
        />
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2">
          <CardTitle>Recent audit</CardTitle>
          <Link to="/audit" className="text-sm text-accent">
            View all in Audit
          </Link>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {audit.length === 0 ? (
              <div className="text-sm text-muted-foreground">No audit entries yet.</div>
            ) : (
              audit.map((entry) => (
                <div key={entry.id} className="flex items-center justify-between gap-3 border-b border-border pb-2 last:border-0 last:pb-0">
                  <div>
                    <div className="text-sm font-medium text-foreground">{entry.action}</div>
                    <div className="text-xs text-muted-foreground">
                      {entry.actor} · {entry.old_value ?? '—'} → {entry.new_value ?? '—'}
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    <RelativeTime value={entry.timestamp} />
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
