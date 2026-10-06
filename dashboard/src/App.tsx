import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Outlet, Route, Routes, useNavigate } from 'react-router-dom'

import { logout, me } from '@/api'
import { Sidebar } from '@/components/Sidebar'
import { AuditPage } from '@/pages/Audit'
import { ClientDetailPage } from '@/pages/ClientDetail'
import { ClientsList } from '@/pages/ClientsList'
import { Login } from '@/pages/Login'
import { UsersPage } from '@/pages/Users'
import type { User } from '@/types'

function ProtectedLayout() {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const token = sessionStorage.getItem('session_token') || sessionStorage.getItem('admin_token')
    if (!token) {
      navigate('/login', { replace: true })
      return
    }

    void me()
      .then((currentUser) => setUser(currentUser))
      .catch(() => {
        sessionStorage.removeItem('session_token')
        sessionStorage.removeItem('admin_token')
        navigate('/login', { replace: true })
      })
      .finally(() => setReady(true))
  }, [navigate])

  if (!ready) {
    return <div className="min-h-screen bg-background" />
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar user={user} onLogout={handleLogout} />
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter basename="/dashboard">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedLayout />}>
          <Route path="/" element={<Navigate to="/clients" replace />} />
          <Route path="/clients" element={<ClientsList />} />
          <Route path="/clients/:slug" element={<ClientDetailPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/users" element={<UsersPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
