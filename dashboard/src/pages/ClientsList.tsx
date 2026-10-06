import { useEffect, useMemo, useState } from 'react'
import { Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { listClients, provisionClient } from '@/api'
import { ClientsTable } from '@/components/ClientsTable'
import { ExportCsvButton } from '@/components/ExportCsvButton'
import { ProvisionForm } from '@/components/ProvisionForm'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Sheet, SheetContent } from '@/components/ui/sheet'
import type { ClientSummary } from '@/types'

export function ClientsList() {
  const navigate = useNavigate()
  const [clients, setClients] = useState<ClientSummary[]>([])
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sheetOpen, setSheetOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true)
        const rows = await listClients()
        setClients(rows)
      } finally {
        setIsLoading(false)
      }
    }

    void load()
  }, [])

  const filteredClients = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    return clients.filter((client) => {
      const matchesQuery =
        !normalized ||
        client.slug.toLowerCase().includes(normalized) ||
        client.business_name.toLowerCase().includes(normalized)
      const matchesStatus = statusFilter === 'all' || client.status === statusFilter
      return matchesQuery && matchesStatus
    })
  }, [clients, query, statusFilter])

  const handleCreate = async (data: {
    slug: string
    business_name: string
    contact_name: string
    contact_phone: string
    tier: 'core' | 'growth' | 'advanced'
  }) => {
    await provisionClient({
      slug: data.slug,
      business_name: data.business_name,
      contact_name: data.contact_name || null,
      contact_phone: data.contact_phone || null,
      tier: data.tier,
    })
    const rows = await listClients()
    setClients(rows)
    setSheetOpen(false)
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-medium text-foreground">Clients</h1>
        </div>
        <div className="flex gap-2">
          <ExportCsvButton clients={clients} />
          <Button onClick={() => setSheetOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New client
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Client directory</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <Input
              value={query}
              placeholder="Search by slug or business name"
              onChange={(event) => setQuery(event.target.value)}
              className="max-w-md"
            />

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full max-w-[180px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="suspended">Suspended</SelectItem>
                <SelectItem value="offboarded">Offboarded</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((row) => (
                <div key={row} className="h-12 animate-pulse rounded-md bg-panel/80" />
              ))}
            </div>
          ) : filteredClients.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border p-8 text-center">
              <p className="mb-4 text-muted-foreground">No clients yet. Create your first one.</p>
              <Button onClick={() => setSheetOpen(true)}>New client</Button>
            </div>
          ) : (
            <ClientsTable clients={filteredClients} onRowClick={(slug) => navigate(`/clients/${slug}`)} />
          )}
        </CardContent>
      </Card>

      <Sheet>
        {sheetOpen ? (
          <SheetContent className="z-50">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-xl font-medium text-foreground">Provision client</h2>
              <Button variant="ghost" onClick={() => setSheetOpen(false)}>
                Close
              </Button>
            </div>
            <ProvisionForm onSubmit={handleCreate} />
          </SheetContent>
        ) : null}
      </Sheet>
    </div>
  )
}
