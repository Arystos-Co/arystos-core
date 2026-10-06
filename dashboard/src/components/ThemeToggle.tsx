import { Moon, Sun } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'

type Theme = 'dark' | 'light'

function getStoredTheme(): Theme {
  return localStorage.getItem('dashboard-theme') === 'light' ? 'light' : 'dark'
}

export function initializeTheme(): void {
  document.documentElement.dataset.theme = getStoredTheme()
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(getStoredTheme)
  const nextTheme: Theme = theme === 'dark' ? 'light' : 'dark'

  const toggleTheme = () => {
    document.documentElement.dataset.theme = nextTheme
    localStorage.setItem('dashboard-theme', nextTheme)
    setTheme(nextTheme)
  }

  return (
    <Button
      type="button"
      variant="secondary"
      size="sm"
      onClick={toggleTheme}
      aria-label={`Switch to ${nextTheme} mode`}
      title={`Switch to ${nextTheme} mode`}
    >
      {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      {theme === 'dark' ? 'Light mode' : 'Dark mode'}
    </Button>
  )
}
