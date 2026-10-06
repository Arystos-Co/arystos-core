import { LogOut, ShieldCheck, Users } from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/ThemeToggle'
import type { UserRole } from '@/types'

interface SidebarProps {
  user?: {
    username: string
    role: UserRole
  } | null
  onLogout: () => void
}

const navItems = [
  { to: '/clients', label: 'Clients' },
  { to: '/audit', label: 'Audit' },
  { to: '/users', label: 'Users', ownerOnly: true },
]

export function Sidebar({ user, onLogout }: SidebarProps) {
  return (
    <aside className="flex w-60 flex-col border-r border-border bg-panel">
      <div className="border-b border-border px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-accent text-sm font-semibold text-white">
            A
          </div>
          <div>
            <div className="text-lg font-medium">ARYSTOS</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-2 px-3 py-5">
        {navItems.map((item) => {
          if (item.ownerOnly && user?.role !== 'owner') {
            return null
          }

          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive ? 'bg-accent/10 text-foreground' : 'text-muted-foreground hover:bg-panel/80 hover:text-foreground'
                }`
              }
            >
              {item.label === 'Users' ? <Users className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
              {item.label}
            </NavLink>
          )
        })}
      </nav>

      <div className="border-t border-border p-4">
        <div className="mb-4">
          <ThemeToggle />
        </div>
        <div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-status-active" />
          <span>{user?.username ?? 'admin'}</span>
        </div>
        <div className="mb-4 text-xs uppercase tracking-wide text-muted-foreground">
          {user?.role ?? 'owner'}
        </div>
        <Button variant="secondary" className="w-full justify-center" onClick={onLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          Logout
        </Button>
      </div>
    </aside>
  )
}
