import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { UserRole } from '@/types'

interface ProvisionUserFormProps {
  onSubmit: (value: { username: string; password: string; role: UserRole }) => void | Promise<void>
}

const defaultValues = {
  username: '',
  password: '',
  role: 'operator' as UserRole,
}

export function ProvisionUserForm({ onSubmit }: ProvisionUserFormProps) {
  const [form, setForm] = useState(defaultValues)

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await onSubmit(form)
    setForm(defaultValues)
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="space-y-2">
        <Label htmlFor="username">Username</Label>
        <Input id="username" value={form.username} onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input id="password" type="password" value={form.password} onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="role">Role</Label>
        <Select value={form.role} onValueChange={(value) => setForm((current) => ({ ...current, role: value as UserRole }))}>
          <SelectTrigger id="role">
            <SelectValue placeholder="Select role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="owner">owner</SelectItem>
            <SelectItem value="operator">operator</SelectItem>
            <SelectItem value="read_only">read_only</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Button type="submit" className="w-full">Create user</Button>
    </form>
  )
}
