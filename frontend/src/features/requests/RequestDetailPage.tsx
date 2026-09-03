import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FileText, MapPin } from 'lucide-react'

import {
  Alert,
  Badge,
  Button,
  EmptyState,
  Modal,
  MoneyInput,
  SkeletonCard,
  Stars,
  Textarea,
} from '@/components/ui'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/useToast'
import { api, ApiError } from '@/lib/api'
import { formatDateTime, formatKes } from '@/lib/format'
import type { Quote } from '@/lib/types'

export function RequestDetailPage() {
  const { requestId = '' } = useParams()
  const { user } = useAuth()
  const { notify } = useToast()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [quoting, setQuoting] = useState(false)

  const { data: request, isPending } = useQuery({
    queryKey: ['service-request', requestId],
    queryFn: () => api.serviceRequests.detail(requestId),
    enabled: Boolean(requestId),
  })

  const accept = useMutation({
    mutationFn: (quoteId: string) => api.serviceRequests.acceptQuote(requestId, quoteId),
    onSuccess: (booking) => {
      notify('Quote accepted — fund the escrow to start', 'success')
      void queryClient.invalidateQueries({ queryKey: ['service-requests'] })
      navigate(`/bookings/${booking.id}`)
    },
    onError: (error) =>
      notify(error instanceof ApiError ? error.message : 'Could not accept that quote', 'error'),
  })

  if (isPending) return <SkeletonCard />
  if (!request) {
    return (
      <EmptyState
        icon={<FileText size={20} />}
        title="Request not found"
        action={
          <Link to="/requests">
            <Button>Back to jobs</Button>
          </Link>
        }
      />
    )
  }

  const isOwner = user?.id === request.customer_id
  const isFundi = user?.role === 'fundi'
  const quotes = request.quotes ?? []

  return (
    <div className="stack-lg">
      <Link to="/requests" className="row subtle" style={{ width: 'fit-content' }}>
        <ArrowLeft size={15} /> Back to jobs
      </Link>

      <div className="split">
        <div className="stack-lg">
          <section className="card stack">
            <div className="row-between wrap">
              <h1 style={{ fontSize: 'var(--text-2xl)' }}>{request.title}</h1>
              <Badge tone={request.status === 'open' ? 'progress' : 'neutral'}>
                {request.status === 'open' ? 'Open for quotes' : 'Matched'}
              </Badge>
            </div>

            <p>{request.description}</p>

            <div className="fundi-meta">
              <span>
                <MapPin size={13} aria-hidden /> {request.location_name}
              </span>
              {request.category_name && <span>{request.category_name}</span>}
              <span>Posted {formatDateTime(request.created_at)}</span>
            </div>

            {(request.budget_min_cents || request.budget_max_cents) && (
              <div className="row-between">
                <span className="subtle">Customer budget</span>
                <strong className="numeric">
                  {formatKes(request.budget_min_cents)} – {formatKes(request.budget_max_cents)}
                </strong>
              </div>
            )}
          </section>

          {isOwner && (
            <section className="card">
              <div className="section-title">
                <h2>Quotes received</h2>
                <span className="subtle">{quotes.length}</span>
              </div>

              {quotes.length === 0 ? (
                <EmptyState
                  icon={<FileText size={20} />}
                  title="No quotes yet"
                  description="Fundis nearby will see this job and send their prices."
                />
              ) : (
                <div className="stack">
                  {quotes.map((quote) => (
                    <QuoteRow
                      key={quote.id}
                      quote={quote}
                      canAccept={request.status === 'open'}
                      busy={accept.isPending}
                      onAccept={() => accept.mutate(quote.id)}
                    />
                  ))}
                </div>
              )}
            </section>
          )}
        </div>

        <aside className="stack">
          {isFundi && request.status === 'open' && (
            <div className="card stack">
              <h2 style={{ fontSize: 'var(--text-base)' }}>Want this job?</h2>
              <p className="subtle">
                Send your price. If the customer accepts, they fund escrow before you start.
              </p>
              <Button variant="primary" block onClick={() => setQuoting(true)}>
                Send a quote
              </Button>
            </div>
          )}

          {isOwner && (
            <div className="card stack-sm">
              <h2 style={{ fontSize: 'var(--text-base)' }}>How this works</h2>
              <p className="subtle">
                Accepting a quote creates a booking. Your money is only taken once you fund the
                escrow, and only released when you confirm the work.
              </p>
            </div>
          )}
        </aside>
      </div>

      {quoting && (
        <QuoteModal
          requestId={request.id}
          onClose={() => setQuoting(false)}
          onDone={() => {
            void queryClient.invalidateQueries({ queryKey: ['service-request', requestId] })
          }}
        />
      )}
    </div>
  )
}

function QuoteRow({
  quote,
  canAccept,
  busy,
  onAccept,
}: {
  quote: Quote
  canAccept: boolean
  busy: boolean
  onAccept: () => void
}) {
  return (
    <div className="card card-tight row-between wrap">
      <div>
        <strong>{quote.fundi_name}</strong>
        <div className="row wrap" style={{ marginTop: 2 }}>
          {quote.fundi_rating !== null && <Stars rating={quote.fundi_rating} />}
          {quote.estimated_hours && <span className="subtle">~{quote.estimated_hours}h</span>}
        </div>
        {quote.notes && <p className="subtle" style={{ marginTop: 6 }}>{quote.notes}</p>}
      </div>

      <div className="stack-sm" style={{ textAlign: 'right' }}>
        <strong className="numeric" style={{ fontSize: 'var(--text-lg)' }}>
          {formatKes(quote.amount_cents)}
        </strong>
        {quote.status === 'accepted' ? (
          <Badge tone="success">Accepted</Badge>
        ) : quote.status === 'declined' ? (
          <Badge>Declined</Badge>
        ) : canAccept ? (
          <Button variant="primary" size="sm" disabled={busy} onClick={onAccept}>
            Accept quote
          </Button>
        ) : null}
      </div>
    </div>
  )
}

function QuoteModal({
  requestId,
  onClose,
  onDone,
}: {
  requestId: string
  onClose: () => void
  onDone: () => void
}) {
  const { notify } = useToast()
  const [amountCents, setAmountCents] = useState<number | ''>('')
  const [hours, setHours] = useState('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)

  const submit = useMutation({
    mutationFn: () =>
      api.serviceRequests.submitQuote(requestId, {
        amount_cents: amountCents === '' ? 0 : amountCents,
        estimated_hours: hours ? Number(hours) : undefined,
        notes: notes.trim() || undefined,
      }),
    onSuccess: () => {
      notify('Quote sent to the customer', 'success')
      onDone()
      onClose()
    },
    onError: (mutationError) =>
      setError(
        mutationError instanceof ApiError
          ? mutationError.fieldError('amount_cents') ?? mutationError.message
          : 'Could not send that quote.',
      ),
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (amountCents === '' || amountCents < 100) return setError('Enter your price in shillings.')
    submit.mutate()
  }

  return (
    <Modal
      title="Send a quote"
      description="Price the whole job. The customer funds escrow if they accept."
      onClose={onClose}
    >
      <form className="stack" onSubmit={handleSubmit} noValidate>
        {error && <Alert tone="danger">{error}</Alert>}

        <MoneyInput
          label="Your price (KES)"
          valueCents={amountCents}
          onChangeCents={setAmountCents}
          hint="Whole shillings. A 10% platform fee applies on completion."
        />

        <div className="field">
          <label>Estimated hours</label>
          <input
            className="input numeric"
            type="number"
            min={0}
            step={0.5}
            placeholder="3"
            value={hours}
            onChange={(event) => setHours(event.target.value)}
          />
        </div>

        <Textarea
          label="Message to the customer"
          placeholder="What's included, materials, when you can start."
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
        />

        <div className="modal-actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={submit.isPending}>
            Send quote
          </Button>
        </div>
      </form>
    </Modal>
  )
}
