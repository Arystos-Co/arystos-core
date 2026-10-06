import { ArrowUpRight } from 'lucide-react'

import { PaymentBadge } from '@/components/PaymentBadge'
import { RelativeTime } from '@/components/RelativeTime'
import { StatusBadge } from '@/components/StatusBadge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { ClientSummary } from '@/types'

interface ClientsTableProps {
  clients: ClientSummary[]
  onRowClick?: (slug: string) => void
}

export function ClientsTable({ clients, onRowClick }: ClientsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Slug</TableHead>
          <TableHead>Business name</TableHead>
          <TableHead>Tier</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>App version</TableHead>
          <TableHead>Last sync</TableHead>
          <TableHead>Payment</TableHead>
        </TableRow>
      </TableHeader>

      <TableBody>
        {clients.map((client) => (
          <TableRow key={client.slug} className="cursor-pointer" onClick={() => onRowClick?.(client.slug)}>
            <TableCell className="font-mono text-xs text-muted-foreground">{client.slug}</TableCell>
            <TableCell className="font-medium">{client.business_name}</TableCell>
            <TableCell className="capitalize">{client.tier}</TableCell>
            <TableCell>
              <StatusBadge value={client.status} />
            </TableCell>
            <TableCell>{client.app_version ?? '—'}</TableCell>
            <TableCell>
              <RelativeTime value={client.last_sync_at} />
            </TableCell>
            <TableCell className="flex items-center justify-between gap-2">
              <PaymentBadge value={client.payment_status} />
              <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
