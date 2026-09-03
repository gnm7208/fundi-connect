import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { AlertCircle, CheckCircle2, Info } from 'lucide-react'

import { ToastContext, type ToastTone } from '@/context/toastContext'

interface ToastItem {
  id: number
  message: string
  tone: ToastTone
  entered: boolean
}

const ICONS = { success: CheckCircle2, error: AlertCircle, info: Info }
const VISIBLE_MS = 4200

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const nextId = useRef(1)
  const timers = useRef<number[]>([])

  useEffect(() => () => timers.current.forEach(clearTimeout), [])

  const notify = useCallback((message: string, tone: ToastTone = 'info') => {
    const id = nextId.current++
    setToasts((current) => [...current, { id, message, tone, entered: false }])

    // Flip the enter flag on the next frame so the transition has a start state
    // to move from; transitions retarget cleanly when toasts stack up fast.
    requestAnimationFrame(() => {
      setToasts((current) => current.map((t) => (t.id === id ? { ...t, entered: true } : t)))
    })

    timers.current.push(
      window.setTimeout(() => {
        setToasts((current) => current.map((t) => (t.id === id ? { ...t, entered: false } : t)))
        timers.current.push(
          window.setTimeout(() => {
            setToasts((current) => current.filter((t) => t.id !== id))
          }, 240),
        )
      }, VISIBLE_MS),
    )
  }, [])

  const value = useMemo(() => ({ notify }), [notify])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-region" role="status" aria-live="polite">
        {toasts.map((toast) => {
          const Icon = ICONS[toast.tone]
          return (
            <div
              key={toast.id}
              className={`toast toast-${toast.tone}`}
              data-enter={toast.entered}
            >
              <Icon size={16} aria-hidden />
              <span>{toast.message}</span>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}
