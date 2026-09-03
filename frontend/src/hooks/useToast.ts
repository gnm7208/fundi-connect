import { useContext } from 'react'

import { ToastContext, type ToastValue } from '@/context/toastContext'

export function useToast(): ToastValue {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used inside <ToastProvider>')
  return context
}
