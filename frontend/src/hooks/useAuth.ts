import { useContext } from 'react'

import { AuthContext, type AuthValue } from '@/context/authContext'

export function useAuth(): AuthValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
