import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, CheckCheck } from 'lucide-react'

import { EmptyState } from '@/components/ui'
import { api } from '@/lib/api'
import { formatRelative } from '@/lib/format'

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const wrap = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.notifications.list(),
    refetchInterval: 60_000,
  })

  const markAll = useMutation({
    mutationFn: () => api.notifications.markAllRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  })

  const markOne = useMutation({
    mutationFn: (id: string) => api.notifications.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  })

  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: MouseEvent) => {
      if (!wrap.current?.contains(event.target as Node)) setOpen(false)
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  const unread = data?.unread_count ?? 0
  const notifications = data?.notifications ?? []

  return (
    <div className="menu-wrap" ref={wrap}>
      <button
        className="icon-btn"
        onClick={() => setOpen((value) => !value)}
        aria-label={unread > 0 ? `Notifications, ${unread} unread` : 'Notifications'}
        aria-expanded={open}
      >
        <Bell size={18} />
        {unread > 0 && <span className="dot">{unread > 9 ? '9+' : unread}</span>}
      </button>

      {open && (
        <div className="menu" style={{ width: 320 }}>
          <div className="menu-head row-between">
            <strong style={{ fontSize: 'var(--text-sm)' }}>Notifications</strong>
            {unread > 0 && (
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => markAll.mutate()}
                disabled={markAll.isPending}
              >
                <CheckCheck size={13} /> Mark all read
              </button>
            )}
          </div>

          <div className="notif-list">
            {notifications.length === 0 ? (
              <EmptyState
                icon={<Bell size={20} />}
                title="Nothing yet"
                description="Booking and payment updates will show up here."
              />
            ) : (
              notifications.map((notification) => (
                <button
                  key={notification.id}
                  className="notif"
                  data-unread={!notification.is_read}
                  onClick={() => !notification.is_read && markOne.mutate(notification.id)}
                >
                  <strong>{notification.title}</strong>
                  <p>{notification.message}</p>
                  <span className="subtle" style={{ fontSize: 10 }}>
                    {formatRelative(notification.created_at)}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
