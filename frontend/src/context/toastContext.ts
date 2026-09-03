import { createContext } from 'react'

export type ToastTone = 'success' | 'error' | 'info'

export interface ToastValue {
  notify: (message: string, tone?: ToastTone) => void
}

export const ToastContext = createContext<ToastValue | null>(null)
