import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, ArrowLeft, ClipboardList, MapPin, ShieldCheck, Star } from 'lucide-react'

import {
  Alert,
  Badge,
  Button,
  EmptyState,
  Modal,
  SkeletonCard,
  StarPicker,
  Textarea,
} from '@/components/ui'
import { BookingTimeline } from '@/features/bookings/BookingTimeline'
import { EscrowPaymentModal } from '@/features/bookings/EscrowPaymentModal'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/useToast'
import { api, ApiError } from '@/lib/api'
import { BOOKING_STATUS, ESCROW_STATUS, formatDateTime, formatKes } from '@/lib/format'
import type { Booking, BookingStatus } from '@/lib/types'

export function BookingDetailPage() {
  const { bookingId = '' } = useParams()
  const { user } = useAuth()
  const { notify } = useToast()
  const queryClient = useQueryClient()

  const [paying, setPaying] = useState(false)
  const [reviewing, setReviewing] = useState(false)
  const [disputing, setDisputing] = useState(false)

  const { data: booking, isPending } = useQuery({
    queryKey: ['booking', bookingId],
    queryFn: () => api.bookings.detail(bookingId),
    enabled: Boolean(bookingId),
  })

  const { data: escrow } = useQuery({
    queryKey: ['escrow', bookingId],
    queryFn: () => api.escrow.forBooking(bookingId),
    enabled: Boolean(bookingId),
  })

  function invalidate() {
    void queryClient.invalidateQueries({ queryKey: ['booking', bookingId] })
    void queryClient.invalidateQueries({ queryKey: ['escrow', bookingId] })
    void queryClient.invalidateQueries({ queryKey: ['bookings'] })
    void queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }

  const transition = useMutation({
    mutationFn: (status: BookingStatus) => api.bookings.updateStatus(bookingId, status),
    onSuccess: () => {
      notify('Booking updated', 'success')
      invalidate()
    },
    onError: (error) =>
      notify(error instanceof ApiError ? error.message : 'Could not update the booking', 'error'),
  })

  const confirmCompletion = useMutation({
    mutationFn: () => api.bookings.confirmCompletion(bookingId),
    onSuccess: () => {
      notify('Payment released to the fundi', 'success')
      invalidate()
      setReviewing(true)
    },
    onError: (error) =>
      notify(error instanceof ApiError ? error.message : 'Could not release the payment', 'error'),
  })

  if (isPending) return <SkeletonCard />
  if (!booking) {
    return (
      <EmptyState
        icon={<ClipboardList size={20} />}
        title="Booking not found"
        action={
          <Link to="/bookings">
            <Button>Back to bookings</Button>
          </Link>
        }
      />
    )
  }

  const isCustomer = user?.id === booking.customer_id
  const isFundi = user?.id === booking.fundi_id
  const status = BOOKING_STATUS[booking.status]
  const escrowState = escrow ? ESCROW_STATUS[escrow.status] : null

  return (
    <div className="stack-lg">
      <Link to={isFundi ? '/jobs' : '/bookings'} className="row subtle" style={{ width: 'fit-content' }}>
        <ArrowLeft size={15} /> Back
      </Link>

      <div className="split">
        <div className="stack-lg">
          <section className="card stack">
            <div className="row-between wrap">
              <div>
                <h1 style={{ fontSize: 'var(--text-2xl)' }}>{booking.title}</h1>
                <p className="muted">
                  {isFundi ? `For ${booking.customer_name}` : `With ${booking.fundi_name}`}
                </p>
              </div>
              <Badge tone={status.tone}>{status.label}</Badge>
            </div>

            {booking.description && <p>{booking.description}</p>}

            <div className="fundi-meta">
              <span>
                <MapPin size={13} aria-hidden /> {booking.location_name}
              </span>
              <span>Requested {formatDateTime(booking.created_at)}</span>
              {booking.completed_at && <span>Completed {formatDateTime(booking.completed_at)}</span>}
            </div>
          </section>

          <section className="card">
            <div className="section-title">
              <h2>Progress</h2>
            </div>
            <BookingTimeline booking={booking} />
          </section>

          {booking.status === 'disputed' && (
            <Alert tone="danger">
              This job is in dispute. Funds stay frozen in escrow until an admin decides the outcome.
            </Alert>
          )}
        </div>

        <aside className="stack">
          <div className="card stack">
            <h2 style={{ fontSize: 'var(--text-base)' }}>Escrow</h2>

            <div className="money-rows">
              <div className="money-row">
                <span className="muted">Agreed price</span>
                <span className="numeric">{formatKes(booking.agreed_amount_cents)}</span>
              </div>
              <div className="money-row">
                <span className="muted">Platform fee</span>
                <span className="numeric">{formatKes(booking.platform_fee_cents)}</span>
              </div>
              <div className="money-row total">
                <span>Fundi receives</span>
                <span className="numeric">{formatKes(booking.fundi_amount_cents)}</span>
              </div>
            </div>

            {escrowState && (
              <div className="row-between">
                <span className="subtle">Status</span>
                <Badge tone={escrowState.tone}>{escrowState.label}</Badge>
              </div>
            )}

            {escrow?.mpesa_receipt_number && (
              <div className="row-between">
                <span className="subtle">M-PESA receipt</span>
                <code className="numeric" style={{ fontSize: 'var(--text-xs)' }}>
                  {escrow.mpesa_receipt_number}
                </code>
              </div>
            )}

            <BookingActions
              booking={booking}
              isCustomer={isCustomer}
              isFundi={isFundi}
              onPay={() => setPaying(true)}
              onReview={() => setReviewing(true)}
              onDispute={() => setDisputing(true)}
              onTransition={(next) => transition.mutate(next)}
              onConfirm={() => confirmCompletion.mutate()}
              busy={transition.isPending || confirmCompletion.isPending}
            />

            {booking.status === 'escrow_funded' && (
              <div className="alert alert-info">
                <ShieldCheck size={16} aria-hidden />
                <div>Money is locked. It only moves when you confirm — or an admin resolves a dispute.</div>
              </div>
            )}
          </div>
        </aside>
      </div>

      {paying && (
        <EscrowPaymentModal
          booking={booking}
          defaultPhone={user?.phone ?? ''}
          onClose={() => setPaying(false)}
        />
      )}
      {reviewing && !booking.has_review && isCustomer && (
        <ReviewModal bookingId={booking.id} onClose={() => setReviewing(false)} onDone={invalidate} />
      )}
      {disputing && (
        <DisputeModal bookingId={booking.id} onClose={() => setDisputing(false)} onDone={invalidate} />
      )}
    </div>
  )
}

function BookingActions({
  booking,
  isCustomer,
  isFundi,
  onPay,
  onReview,
  onDispute,
  onTransition,
  onConfirm,
  busy,
}: {
  booking: Booking
  isCustomer: boolean
  isFundi: boolean
  onPay: () => void
  onReview: () => void
  onDispute: () => void
  onTransition: (status: BookingStatus) => void
  onConfirm: () => void
  busy: boolean
}) {
  const { status } = booking
  const actions: React.ReactNode[] = []

  if (isFundi && status === 'pending') {
    actions.push(
      <Button key="accept" variant="primary" block disabled={busy} onClick={() => onTransition('accepted_unpaid')}>
        Accept job
      </Button>,
      <Button key="decline" variant="ghost" block disabled={busy} onClick={() => onTransition('declined')}>
        Decline
      </Button>,
    )
  }

  if (isCustomer && (status === 'pending' || status === 'accepted_unpaid')) {
    actions.push(
      <Button key="pay" variant="primary" block onClick={onPay}>
        Pay into escrow
      </Button>,
    )
  }

  if (isFundi && status === 'escrow_funded') {
    actions.push(
      <Button key="start" variant="primary" block disabled={busy} onClick={() => onTransition('in_progress')}>
        Start work
      </Button>,
    )
  }

  if (isFundi && status === 'in_progress') {
    actions.push(
      <Button key="finish" variant="primary" block disabled={busy} onClick={() => onTransition('awaiting_confirm')}>
        Mark as finished
      </Button>,
    )
  }

  if (isCustomer && status === 'awaiting_confirm') {
    actions.push(
      <Button key="confirm" variant="primary" block disabled={busy} onClick={onConfirm}>
        Confirm & release payment
      </Button>,
    )
  }

  if (isCustomer && status === 'completed' && !booking.has_review) {
    actions.push(
      <Button key="review" variant="primary" block onClick={onReview}>
        <Star size={15} /> Leave a review
      </Button>,
    )
  }

  const canDispute =
    !booking.has_dispute &&
    ['escrow_funded', 'in_progress', 'awaiting_confirm'].includes(status) &&
    (isCustomer || isFundi)

  if (canDispute) {
    actions.push(
      <Button key="dispute" variant="ghost" block onClick={onDispute}>
        <AlertTriangle size={15} /> Open a dispute
      </Button>,
    )
  }

  if (isCustomer && ['pending', 'accepted_unpaid', 'escrow_funded'].includes(status)) {
    actions.push(
      <Button key="cancel" variant="ghost" block disabled={busy} onClick={() => onTransition('cancelled')}>
        Cancel booking
      </Button>,
    )
  }

  if (actions.length === 0) return null
  return <div className="stack-sm">{actions}</div>
}

function ReviewModal({
  bookingId,
  onClose,
  onDone,
}: {
  bookingId: string
  onClose: () => void
  onDone: () => void
}) {
  const { notify } = useToast()
  const [rating, setRating] = useState(5)
  const [text, setText] = useState('')

  const submit = useMutation({
    mutationFn: () =>
      api.reviews.create({ booking_id: bookingId, rating, review_text: text.trim() || undefined }),
    onSuccess: () => {
      notify('Thanks for rating your fundi', 'success')
      onDone()
      onClose()
    },
    onError: (error) =>
      notify(error instanceof ApiError ? error.message : 'Could not submit that review', 'error'),
  })

  return (
    <Modal
      title="How did it go?"
      description="Your rating helps the next customer choose well."
      onClose={onClose}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Skip
          </Button>
          <Button variant="primary" loading={submit.isPending} onClick={() => submit.mutate()}>
            Submit review
          </Button>
        </>
      }
    >
      <div className="stack">
        <div className="field">
          <label>Rating</label>
          <StarPicker value={rating} onChange={setRating} />
        </div>
        <Textarea
          label="Anything to add?"
          placeholder="Turned up on time, clean work, fair price…"
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
      </div>
    </Modal>
  )
}

function DisputeModal({
  bookingId,
  onClose,
  onDone,
}: {
  bookingId: string
  onClose: () => void
  onDone: () => void
}) {
  const { notify } = useToast()
  const [reason, setReason] = useState('')
  const [statement, setStatement] = useState('')
  const [error, setError] = useState<string | null>(null)

  const submit = useMutation({
    mutationFn: () =>
      api.disputes.create({
        booking_id: bookingId,
        reason: reason.trim(),
        customer_statement: statement.trim(),
      }),
    onSuccess: () => {
      notify('Dispute opened — funds stay in escrow', 'success')
      onDone()
      onClose()
    },
    onError: (mutationError) =>
      setError(
        mutationError instanceof ApiError ? mutationError.message : 'Could not open that dispute.',
      ),
  })

  return (
    <Modal
      title="Open a dispute"
      description="An admin will review both sides before any money moves."
      onClose={onClose}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="danger"
            loading={submit.isPending}
            onClick={() => {
              setError(null)
              if (reason.trim().length < 5) return setError('Summarise the problem in a few words.')
              if (statement.trim().length < 10) return setError('Explain what happened.')
              submit.mutate()
            }}
          >
            Open dispute
          </Button>
        </>
      }
    >
      <div className="stack">
        {error && <Alert tone="danger">{error}</Alert>}
        <Textarea
          label="What went wrong?"
          placeholder="Work incomplete"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          style={{ minHeight: 60 }}
        />
        <Textarea
          label="Your statement"
          placeholder="Describe what was agreed and what actually happened."
          value={statement}
          onChange={(event) => setStatement(event.target.value)}
        />
      </div>
    </Modal>
  )
}
