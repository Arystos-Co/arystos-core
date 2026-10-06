import { useEffect, useState } from 'react'

import { listAudit } from '@/api'
import { RelativeTime } from '@/components/RelativeTime'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { AuditEntry } from '@/types'

export function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const rows = await listAudit()
        setEntries(rows)
      } finally {
        setLoading(false)
      }
    }

    void load()
  }, [])

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-medium text-foreground">Audit log</h1>

      <Card>
        <CardHeader>
          <CardTitle>Recent activity</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((row) => (
                <div key={row} className="h-12 animate-pulse rounded-md bg-panel/80" />
              ))}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Client</TableHead>
                  <TableHead>Change</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>
                      <RelativeTime value={entry.timestamp} />
                    </TableCell>
                    <TableCell>{entry.actor}</TableCell>
                    <TableCell>{entry.action}</TableCell>
                    <TableCell>
                      <a href={`/dashboard/clients/${entry.target_slug}`} className="text-accent">
                        {entry.target_slug}
                      </a>
                    </TableCell>
                    <TableCell>
                      {entry.old_value ?? '—'} → {entry.new_value ?? '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
