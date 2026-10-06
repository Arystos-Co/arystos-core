import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { login, loginWithAdminToken } from '@/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ThemeToggle } from '@/components/ThemeToggle'

export function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [useAdminToken, setUseAdminToken] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (sessionStorage.getItem('session_token') || sessionStorage.getItem('admin_token')) {
      navigate('/clients', { replace: true })
    }
  }, [navigate])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    try {
      if (useAdminToken) {
        await loginWithAdminToken(password)
      } else {
        await login(username, password)
      }
      navigate('/clients', { replace: true })
    } catch {
      setError('Authentication failed. Please check your credentials.')
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background px-4">
      <div className="absolute right-4 top-4">
        <ThemeToggle />
      </div>
      <Card className="w-full max-w-md border-border bg-panel">
        <CardHeader className="space-y-2 text-center">
          <div className="text-2xl font-medium tracking-tight">ARYSTOS</div>
          <CardTitle>Sign in</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            {!useAdminToken ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input id="username" value={username} onChange={(event) => setUsername(event.target.value)} autoFocus />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
                </div>
              </>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="admin-token">Admin token</Label>
                <Input
                  id="admin-token"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoFocus
                />
              </div>
            )}

            {error ? <div className="rounded-md border border-status-overdue/40 bg-status-overdue/5 px-3 py-2 text-sm text-status-overdue">{error}</div> : null}

            <Button type="submit" className="w-full">
              {useAdminToken ? 'Use admin token' : 'Sign in'}
            </Button>
          </form>

          <div className="mt-4 text-center text-sm text-muted-foreground">
            <button type="button" className="underline" onClick={() => setUseAdminToken((current) => !current)}>
              {useAdminToken ? 'Use user login instead' : 'Use admin token instead'}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
