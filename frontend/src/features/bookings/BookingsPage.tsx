import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ClipboardList, MapPin } from 'lucide-react'

import { Badge, Button, EmptyState, SkeletonList } from '@/components/ui'
import { api } from '@/lib/api'
import { BOOKING_STATUS, formatKes, formatRelative } from '@/lib/format'
import type { Booking } from '@/lib/types'

const TABS = [
  { key: 'active', label: 'Active' },
  { key: 'completed', label: 'Completed' },
  { key: 'all', label: 'All' },
] as const

const ACTIVE_STATUSES = new Set([
  'pending',
  'accepted_unpaid',
  'escrow_funded',
  'in_progress',
  'awaiting_confirm',
  'disputed',
])

export function BookingsPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]['key']>('active')

  const { data, isPending } = useQuery({
    queryKey: ['bookings'],
    queryFn: () => api.bookings.list({ per_page: 50 }),
  })

  const all = data?.bookings ?? []
  const bookings = all.filter((booking) => {
    if (tab === 'active') return ACTIVE_STATUSES.has(booking.status)
    if (tab === 'completed') return booking.status === 'completed'
    return true
  })

  return (
    <div className="stack-lg">
      <div className="page-head row-between wrap">
        <div>
          <h1>My bookings</h1>
          <p className="muted">Track every job and its escrow status.</p>
        </div>
        <Link to="/find">
          <Button variant="primary">Book a fundi</Button>
        </Link>
      </div>

      <div className="tabs" role="tablist">
        {TABS.map((item) => (
          <button
            key={item.key}
            className="tab"
            role="tab"
            aria-selected={tab === item.key}
            onClick={() => setTab(item.key)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {isPending ? (
        <SkeletonList count={3} />
      ) : bookings.length === 0 ? (
        <EmptyState
          icon={<ClipboardList size={20} />}
          title={tab === 'active' ? 'No active bookings' : 'Nothing here yet'}
          description="When you book a fundi, the job and its escrow will appear here."
          action={
            <Link to="/find">
              <Button variant="primary">Find a fundi</Button>
            </Link>
          }
        />
      ) : (
        <div className="stack stagger">
          {bookings.map((booking) => (
            <BookingRow key={booking.id} booking={booking} />
          ))}
        </div>
      )}
    </div>
  )
}

export function BookingRow({ booking }: { booking: Booking }) {
  const status = BOOKING_STATUS[booking.status]

  return (
    <Link to={`/bookings/${booking.id}`} className="card card-tight card-interactive stack-sm">
      <div className="row-between wrap">
        <strong>{booking.title}</strong>
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>

      <div className="fundi-meta">
        <span>
          <MapPin size={13} aria-hidden /> {booking.location_name}
        </span>
        <span>with {booking.fundi_name ?? booking.customer_name}</span>
        <span>{formatRelative(booking.created_at)}</span>
      </div>

      <div className="row-between">
        <span className="subtle">Agreed price</span>
        <strong className="numeric">{formatKes(booking.agreed_amount_cents)}</strong>
      </div>
    </Link>
  )
}
