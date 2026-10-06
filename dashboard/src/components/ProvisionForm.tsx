import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { Tier } from '@/types'

interface ProvisionFormProps {
  onSubmit: (value: {
    slug: string
    business_name: string
    contact_name: string
    contact_phone: string
    tier: Tier
  }) => void | Promise<void>
  submitLabel?: string
}

const defaultValues = {
  slug: '',
  business_name: '',
  contact_name: '',
  contact_phone: '',
  tier: 'core' as Tier,
}

export function ProvisionForm({ onSubmit, submitLabel = 'Create client' }: ProvisionFormProps) {
  const [form, setForm] = useState(defaultValues)

  const handleChange = (field: keyof typeof defaultValues, value: string) => {
    setForm((current) => ({ ...current, [field]: field === 'tier' ? (value as Tier) : value }))
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await onSubmit(form)
    setForm(defaultValues)
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="slug">Slug</Label>
          <Input id="slug" value={form.slug} onChange={(event) => handleChange('slug', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="tier">Tier</Label>
          <Select value={form.tier} onValueChange={(value) => handleChange('tier', value)}>
            <SelectTrigger id="tier">
              <SelectValue placeholder="Select tier" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="core">core</SelectItem>
              <SelectItem value="growth">growth</SelectItem>
              <SelectItem value="advanced">advanced</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="business_name">Business name</Label>
        <Input id="business_name" value={form.business_name} onChange={(event) => handleChange('business_name', event.target.value)} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="contact_name">Contact name</Label>
          <Input id="contact_name" value={form.contact_name} onChange={(event) => handleChange('contact_name', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="contact_phone">Contact phone</Label>
          <Input id="contact_phone" value={form.contact_phone} onChange={(event) => handleChange('contact_phone', event.target.value)} />
        </div>
      </div>

      <Button type="submit" className="w-full">{submitLabel}</Button>
    </form>
  )
}
