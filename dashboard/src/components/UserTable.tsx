import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { RelativeTime } from '@/components/RelativeTime'
import type { User } from '@/types'

interface UserTableProps {
  users: User[]
  onRoleChange: (id: string, role: User['role']) => void
  onDeactivate: (id: string) => void
}

export function UserTable({ users, onRoleChange, onDeactivate }: UserTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Username</TableHead>
          <TableHead>Role</TableHead>
          <TableHead>Active</TableHead>
          <TableHead>Last login</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.map((user) => (
          <TableRow key={user.id}>
            <TableCell className="font-medium">{user.username}</TableCell>
            <TableCell>
              <select
                value={user.role}
                onChange={(event) => onRoleChange(user.id, event.target.value as User['role'])}
                className="rounded-md border border-border bg-panel px-2 py-1 text-sm text-foreground"
              >
                <option value="owner">owner</option>
                <option value="operator">operator</option>
                <option value="read_only">read_only</option>
              </select>
            </TableCell>
            <TableCell>
              <Badge variant={user.active === 1 ? 'active' : 'offboarded'}>{user.active === 1 ? 'active' : 'inactive'}</Badge>
            </TableCell>
            <TableCell>
              <RelativeTime value={user.last_login_at} />
            </TableCell>
            <TableCell>
              <RelativeTime value={user.created_at} />
            </TableCell>
            <TableCell>
              <Button variant="secondary" onClick={() => onDeactivate(user.id)}>
                Deactivate
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
