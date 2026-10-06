import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import type { ClientDetail } from '@/types'

export function ClientInfoPanel({ client }: { client: ClientDetail }) {
  const detailItems = [
    ['Business name', client.business_name],
    ['Slug', client.slug],
    ['Tier', client.tier],
    ['Contact name', client.contact_name ?? '—'],
    ['Contact phone', client.contact_phone ?? '—'],
    ['Contract start', client.contract_start ?? '—'],
    ['Created at', client.created_at],
    ['Last sync', client.last_sync_at ?? '—'],
    ['App version', client.app_version ?? '—'],
    ['Offboarded at', client.offboarded_at ?? '—'],
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Client details</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {detailItems.map(([label, value]) => (
            <div key={label} className="space-y-1">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
              <div className="text-sm text-foreground">{String(value)}</div>
            </div>
          ))}
        </div>
        <Separator className="my-5" />
        <div className="text-xs text-muted-foreground">Updated at {client.updated_at}</div>
      </CardContent>
    </Card>
  )
}
