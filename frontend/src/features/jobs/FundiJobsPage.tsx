import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ClipboardList } from 'lucide-react'

import { Button, EmptyState, SkeletonList } from '@/components/ui'
import { BookingRow } from '@/features/bookings/BookingsPage'
import { api } from '@/lib/api'

const TABS = [
  { key: 'requests', label: 'New requests', statuses: ['pending'] },
  { key: 'working', label: 'In progress', statuses: ['escrow_funded', 'in_progress', 'awaiting_confirm'] },
  { key: 'waiting', label: 'Awaiting payment', statuses: ['accepted_unpaid'] },
  { key: 'done', label: 'Completed', statuses: ['completed'] },
] as const

export function FundiJobsPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]['key']>('requests')

  const { data, isPending } = useQuery({
    queryKey: ['bookings'],
    queryFn: () => api.bookings.list(),
  })

  const statuses = TABS.find((item) => item.key === tab)!.statuses as readonly string[]
  const jobs = (data?.bookings ?? []).filter((booking) => statuses.includes(booking.status))

  return (
    <div className="stack-lg">
      <div className="page-head row-between wrap">
        <div>
          <h1>My jobs</h1>
          <p className="muted">Accept work, update progress and get paid from escrow.</p>
        </div>
        <Link to="/requests">
          <Button variant="primary">Browse open requests</Button>
        </Link>
      </div>

      <div className="tabs" role="tablist">
        {TABS.map((item) => {
          const count = (data?.bookings ?? []).filter((booking) =>
            (item.statuses as readonly string[]).includes(booking.status),
          ).length
          return (
            <button
              key={item.key}
              className="tab"
              role="tab"
              aria-selected={tab === item.key}
              onClick={() => setTab(item.key)}
            >
              {item.label}
              {count > 0 ? ` (${count})` : ''}
            </button>
          )
        })}
      </div>

      {isPending ? (
        <SkeletonList count={3} />
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={<ClipboardList size={20} />}
          title="Nothing in this list"
          description="Quote on open service requests to win more work."
          action={
            <Link to="/requests">
              <Button variant="primary">Browse requests</Button>
            </Link>
          }
        />
      ) : (
        <div className="stack stagger">
          {jobs.map((booking) => (
            <BookingRow key={booking.id} booking={booking} />
          ))}
        </div>
      )}
    </div>
  )
}
