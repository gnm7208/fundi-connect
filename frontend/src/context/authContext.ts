import { createContext } from 'react'

import type { RegisterPayload } from '@/lib/api'
import type { User } from '@/lib/types'

export interface AuthValue {
  user: User | null
  /** True until the initial session probe settles, so guards don't redirect early. */
  loading: boolean
  login: (emailOrPhone: string, password: string) => Promise<User>
  register: (payload: RegisterPayload) => Promise<User>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  setUser: (user: User) => void
}

export const AuthContext = createContext<AuthValue | null>(null)
