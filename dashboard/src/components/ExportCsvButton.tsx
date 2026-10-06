import type { ClientSummary } from '@/types'

import { Button } from '@/components/ui/button'

export function ExportCsvButton({ clients }: { clients: ClientSummary[] }) {
  const handleExport = () => {
    const headers = ['slug', 'business_name', 'tier', 'status', 'app_version', 'last_sync_at', 'payment_status']
    const rows = clients.map((client) => [
      client.slug,
      client.business_name,
      client.tier,
      client.status,
      client.app_version ?? '',
      client.last_sync_at ?? '',
      client.payment_status,
    ])

    const csv = [headers, ...rows]
      .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\n')

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    const date = new Date().toISOString().slice(0, 10)
    link.href = url
    link.download = `arystos-clients-${date}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return <Button variant="secondary" onClick={handleExport}>Export CSV</Button>
}
