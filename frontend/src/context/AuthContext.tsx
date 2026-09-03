import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { AuthContext } from '@/context/authContext'
import { api, tokenStore, type RegisterPayload } from '@/lib/api'
import type { User } from '@/lib/types'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    // The session may live in an httpOnly cookie we cannot read, so ask the API
    // rather than inferring from stored tokens.
    api.auth
      .me()
      .then((me) => {
        if (!cancelled) setUser(me)
      })
      .catch(() => {
        if (!cancelled) {
          tokenStore.clear()
          setUser(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (emailOrPhone: string, password: string) => {
    const me = await api.auth.login(emailOrPhone, password)
    setUser(me)
    return me
  }, [])

  const register = useCallback(async (payload: RegisterPayload) => {
    const me = await api.auth.register(payload)
    setUser(me)
    return me
  }, [])

  const logout = useCallback(async () => {
    await api.auth.logout()
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    setUser(await api.auth.me())
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser, setUser }),
    [user, loading, login, register, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
