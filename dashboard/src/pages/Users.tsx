import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import * as api from '@/api'
import { ProvisionUserForm } from '@/components/ProvisionUserForm'
import { UserTable } from '@/components/UserTable'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Sheet, SheetContent } from '@/components/ui/sheet'
import type { User, UserRole } from '@/types'

export function UsersPage() {
  const navigate = useNavigate()
  const [users, setUsers] = useState<User[]>([])
  const [sheetOpen, setSheetOpen] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const current = await api.me()
        if (current.role !== 'owner') {
          navigate('/clients', { replace: true })
          return
        }
        const rows = await api.listUsers()
        setUsers(rows)
      } catch {
        navigate('/login', { replace: true })
      }
    }

    void load()
  }, [navigate])

  const handleCreate = async (data: { username: string; password: string; role: UserRole }) => {
    await api.createUser(data)
    const rows = await api.listUsers()
    setUsers(rows)
    setSheetOpen(false)
  }

  const handleRoleChange = async (id: string, nextRole: User['role']) => {
    const updated = await api.updateUser(id, { role: nextRole })
    setUsers((current) => current.map((user) => (user.id === updated.id ? updated : user)))
  }

  const handleDeactivate = async (id: string) => {
    const confirmed = window.confirm('Deactivate this user?')
    if (!confirmed) {
      return
    }
    await api.deactivateUser(id)
    const rows = await api.listUsers()
    setUsers(rows)
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-medium text-foreground">Users</h1>
        <Button onClick={() => setSheetOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New user
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Team access</CardTitle>
        </CardHeader>
        <CardContent>
          <UserTable users={users} onRoleChange={handleRoleChange} onDeactivate={handleDeactivate} />
        </CardContent>
      </Card>

      <Sheet>
        {sheetOpen ? (
          <SheetContent className="z-50">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-xl font-medium text-foreground">Create user</h2>
              <Button variant="ghost" onClick={() => setSheetOpen(false)}>
                Close
              </Button>
            </div>
            <ProvisionUserForm onSubmit={handleCreate} />
          </SheetContent>
        ) : null}
      </Sheet>
    </div>
  )
}
