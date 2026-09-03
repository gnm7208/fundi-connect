import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '@/hooks/useAuth'
import type { Role } from '@/lib/types'

function FullPageLoader() {
  return (
    <div className="stack" style={{ padding: 'var(--space-6) 0' }} aria-busy="true">
      <div className="skeleton" style={{ height: 28, width: 220 }} />
      <div className="skeleton" style={{ height: 160, borderRadius: 'var(--radius-lg)' }} />
    </div>
  )
}

/** Requires a session; optionally restricts to specific roles. */
export function Protected({ roles, children }: { roles?: Role[]; children: ReactNode }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <FullPageLoader />
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />

  return <>{children}</>
}

/** Keeps signed-in users off the marketing and auth pages. */
export function GuestOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <FullPageLoader />
  if (user) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}
