import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BadgeCheck, ClipboardList, Plus, Search, ShieldAlert, Wallet as WalletIcon } from 'lucide-react'

import { Alert, Badge, Button, EmptyState, SkeletonList } from '@/components/ui'
import { BookingRow } from '@/features/bookings/BookingsPage'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import { formatKes } from '@/lib/format'

const OPEN_STATUSES = new Set([
  'pending',
  'accepted_unpaid',
  'escrow_funded',
  'in_progress',
  'awaiting_confirm',
  'disputed',
])

export function DashboardPage() {
  const { user } = useAuth()
  const isFundi = user?.role === 'fundi'

  const { data: bookingsData, isPending } = useQuery({
    queryKey: ['bookings'],
    queryFn: () => api.bookings.list(),
  })

  const { data: wallet } = useQuery({
    queryKey: ['wallet'],
    queryFn: () => api.wallet.me(),
    enabled: isFundi,
  })

  const bookings = bookingsData?.bookings ?? []
  const active = bookings.filter((booking) => OPEN_STATUSES.has(booking.status))
  const completed = bookings.filter((booking) => booking.status === 'completed')
  const needsAction = bookings.filter((booking) =>
    isFundi
      ? ['pending', 'escrow_funded', 'in_progress'].includes(booking.status)
      : ['accepted_unpaid', 'awaiting_confirm'].includes(booking.status),
  )

  const verification = user?.fundi_profile?.verification_status

  return (
    <div className="stack-lg">
      <div className="page-head row-between wrap">
        <div>
          <h1>Habari, {user?.full_name.split(' ')[0]}</h1>
          <p className="muted">
            {isFundi
              ? 'Your jobs, earnings and verification at a glance.'
              : 'Your bookings and escrow payments at a glance.'}
          </p>
        </div>
        <Link to={isFundi ? '/requests' : '/find'}>
          <Button variant="primary">
            {isFundi ? (
              <>
                <Search size={15} /> Browse open jobs
              </>
            ) : (
              <>
                <Plus size={15} /> Book a fundi
              </>
            )}
          </Button>
        </Link>
      </div>

      {isFundi && verification !== 'verified' && (
        <Alert tone={verification === 'rejected' ? 'danger' : 'warning'}>
          {verification === 'rejected'
            ? 'Your verification was rejected. Update your ID details to try again — '
            : 'Customers trust verified fundis far more. Submit your national ID to get the badge — '}
          <Link to="/profile" style={{ fontWeight: 600, textDecoration: 'underline' }}>
            finish verification
          </Link>
          .
        </Alert>
      )}

      <div className="grid-stats">
        <div className="stat">
          <span className="label">Active jobs</span>
          <p className="value">{active.length}</p>
        </div>
        <div className="stat">
          <span className="label">Completed</span>
          <p className="value">{completed.length}</p>
        </div>
        {isFundi ? (
          <>
            <div className="stat">
              <span className="label">Wallet balance</span>
              <p className="value brand numeric">{formatKes(wallet?.balance_cents ?? 0)}</p>
            </div>
            <div className="stat">
              <span className="label">Verification</span>
              <p className="value" style={{ fontSize: 'var(--text-lg)', marginTop: 6 }}>
                {verification === 'verified' ? (
                  <Badge tone="success">
                    <BadgeCheck size={13} /> Verified
                  </Badge>
                ) : verification === 'rejected' ? (
                  <Badge tone="danger">
                    <ShieldAlert size={13} /> Rejected
                  </Badge>
                ) : (
                  <Badge tone="warning">Pending</Badge>
                )}
              </p>
            </div>
          </>
        ) : (
          <div className="stat">
            <span className="label">Held in escrow</span>
            <p className="value brand numeric">
              {formatKes(
                bookings
                  .filter((booking) => booking.escrow_status === 'held_in_escrow')
                  .reduce((total, booking) => total + booking.agreed_amount_cents, 0),
              )}
            </p>
          </div>
        )}
      </div>

      <section>
        <div className="section-title">
          <h2>{needsAction.length > 0 ? 'Needs your attention' : 'Active jobs'}</h2>
          <Link to={isFundi ? '/jobs' : '/bookings'} className="subtle">
            View all
          </Link>
        </div>

        {isPending ? (
          <SkeletonList count={2} />
        ) : (needsAction.length > 0 ? needsAction : active).length === 0 ? (
          <EmptyState
            icon={<ClipboardList size={20} />}
            title="Nothing needs you right now"
            description={
              isFundi
                ? 'Browse open service requests and send a quote.'
                : 'Find a fundi and book your first job.'
            }
            action={
              <Link to={isFundi ? '/requests' : '/find'}>
                <Button variant="primary">{isFundi ? 'Browse jobs' : 'Find a fundi'}</Button>
              </Link>
            }
          />
        ) : (
          <div className="stack stagger">
            {(needsAction.length > 0 ? needsAction : active).slice(0, 5).map((booking) => (
              <BookingRow key={booking.id} booking={booking} />
            ))}
          </div>
        )}
      </section>

      {isFundi && wallet && wallet.balance_cents > 0 && (
        <Link to="/wallet" className="card card-interactive row-between">
          <div className="row">
            <WalletIcon size={18} className="muted" aria-hidden />
            <div>
              <strong>Withdraw your earnings</strong>
              <p className="subtle">{formatKes(wallet.balance_cents)} ready to send to M-PESA</p>
            </div>
          </div>
          <Button variant="primary" size="sm">
            Go to wallet
          </Button>
        </Link>
      )}
    </div>
  )
}
