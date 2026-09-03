import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  BadgeCheck,
  Briefcase,
  Clock,
  MapPin,
  MessageSquare,
  ShieldCheck,
  Star,
} from 'lucide-react'

import {
  Alert,
  Avatar,
  Badge,
  Button,
  EmptyState,
  Input,
  Modal,
  MoneyInput,
  SkeletonCard,
  Stars,
  Textarea,
} from '@/components/ui'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/useToast'
import { api, ApiError } from '@/lib/api'
import { formatDate, formatKes } from '@/lib/format'

export function FundiDetailPage() {
  const { fundiId = '' } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { notify } = useToast()
  const [booking, setBooking] = useState(false)

  const { data: fundi, isPending } = useQuery({
    queryKey: ['fundi', fundiId],
    queryFn: () => api.fundis.detail(fundiId),
    enabled: Boolean(fundiId),
  })

  const startChat = useMutation({
    mutationFn: () => api.conversations.start({ fundi_id: fundiId }),
    onSuccess: () => {
      notify('Conversation started', 'success')
      navigate('/messages')
    },
    onError: () => notify('Could not start that conversation', 'error'),
  })

  if (isPending) return <SkeletonCard />
  if (!fundi) {
    return (
      <EmptyState
        icon={<Briefcase size={20} />}
        title="Fundi not found"
        description="This profile may have been removed."
        action={<Link to="/find"><Button>Back to search</Button></Link>}
      />
    )
  }

  const isVerified = fundi.verification_status === 'verified'
  const canBook = user?.role === 'customer' || user?.role === 'admin'

  return (
    <div className="stack-lg">
      <Link to="/find" className="row subtle" style={{ width: 'fit-content' }}>
        <ArrowLeft size={15} /> Back to search
      </Link>

      <div className="split">
        <div className="stack-lg">
          <section className="card">
            <div className="profile-head">
              <Avatar name={fundi.full_name} src={fundi.avatar_url} size="lg" />
              <div style={{ flex: 1, minWidth: 0 }}>
                <h1>
                  {fundi.full_name}
                  {isVerified && (
                    <Badge tone="brand">
                      <BadgeCheck size={13} /> Verified
                    </Badge>
                  )}
                </h1>
                <p className="muted">{fundi.business_name}</p>
                <div className="row wrap" style={{ marginTop: 'var(--space-2)' }}>
                  <Stars rating={fundi.rating_avg} count={fundi.rating_count} />
                  <span className="subtle">·</span>
                  <span className="subtle">{fundi.jobs_completed} jobs completed</span>
                </div>
              </div>
            </div>

            {fundi.bio && <p style={{ marginTop: 'var(--space-4)' }}>{fundi.bio}</p>}

            <div className="fundi-meta" style={{ marginTop: 'var(--space-4)' }}>
              {fundi.location_name && (
                <span>
                  <MapPin size={14} aria-hidden /> {fundi.location_name}
                </span>
              )}
              <span>
                <Clock size={14} aria-hidden /> {fundi.experience_years} years experience
              </span>
              <span>
                <Briefcase size={14} aria-hidden /> Serves {fundi.service_radius_km} km radius
              </span>
            </div>

            {fundi.skills && fundi.skills.length > 0 && (
              <div className="row wrap" style={{ marginTop: 'var(--space-4)' }}>
                {fundi.skills.map((skill) => (
                  <Badge key={skill.id}>
                    {skill.skill_name}
                    {skill.experience_years ? ` · ${skill.experience_years}y` : ''}
                  </Badge>
                ))}
              </div>
            )}
          </section>

          <section className="card">
            <div className="section-title">
              <h2>Reviews</h2>
              <span className="subtle">{fundi.rating_count} verified</span>
            </div>

            {fundi.recent_reviews.length === 0 ? (
              <EmptyState
                icon={<Star size={20} />}
                title="No reviews yet"
                description="Only customers who paid through escrow can leave one."
              />
            ) : (
              <div className="stack">
                {fundi.recent_reviews.map((review) => (
                  <div key={review.id} className="stack-sm">
                    <div className="row-between">
                      <strong style={{ fontSize: 'var(--text-sm)' }}>
                        {review.customer_name ?? 'Customer'}
                      </strong>
                      <span className="subtle">{formatDate(review.created_at)}</span>
                    </div>
                    <Stars rating={review.rating} />
                    {review.review_text && <p className="muted">{review.review_text}</p>}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>

        <aside className="stack">
          <div className="card stack">
            <div>
              <span className="subtle">Hourly rate</span>
              <p style={{ fontSize: 'var(--text-2xl)', fontWeight: 660 }}>
                {fundi.hourly_rate_cents ? formatKes(fundi.hourly_rate_cents) : 'On request'}
              </p>
            </div>

            {!isVerified && (
              <Alert tone="warning">
                This fundi has not completed ID verification yet.
              </Alert>
            )}

            {canBook ? (
              <>
                <Button variant="primary" block onClick={() => setBooking(true)}>
                  Book this fundi
                </Button>
                <Button block onClick={() => startChat.mutate()} loading={startChat.isPending}>
                  <MessageSquare size={15} /> Message
                </Button>
              </>
            ) : (
              <p className="subtle">Log in as a customer to book this fundi.</p>
            )}

            <div className="alert alert-info" style={{ marginTop: 'var(--space-2)' }}>
              <ShieldCheck size={16} aria-hidden />
              <div>Your payment is held in escrow and only released when you confirm the job.</div>
            </div>
          </div>
        </aside>
      </div>

      {booking && (
        <BookingModal
          fundiId={fundi.user_id}
          fundiName={fundi.full_name}
          defaultLocation={fundi.location_name ?? ''}
          onClose={() => setBooking(false)}
        />
      )}
    </div>
  )
}

function BookingModal({
  fundiId,
  fundiName,
  defaultLocation,
  onClose,
}: {
  fundiId: string
  fundiName: string
  defaultLocation: string
  onClose: () => void
}) {
  const navigate = useNavigate()
  const { notify } = useToast()

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [amountCents, setAmountCents] = useState<number | ''>('')
  const [location, setLocation] = useState(defaultLocation)
  const [error, setError] = useState<string | null>(null)

  const create = useMutation({
    mutationFn: () =>
      api.bookings.create({
        fundi_id: fundiId,
        title: title.trim(),
        description: description.trim() || undefined,
        agreed_amount_cents: amountCents === '' ? 0 : amountCents,
        location_name: location.trim(),
      }),
    onSuccess: (created) => {
      notify('Booking request sent', 'success')
      navigate(`/bookings/${created.id}`)
    },
    onError: (mutationError) => {
      setError(
        mutationError instanceof ApiError
          ? mutationError.fieldError('agreed_amount_cents') ?? mutationError.message
          : 'Could not create that booking.',
      )
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (title.trim().length < 3) return setError('Give the job a short title.')
    if (amountCents === '' || amountCents < 5000) return setError('Minimum booking is KES 50.')
    if (!location.trim()) return setError('Where should the fundi come?')
    create.mutate()
  }

  return (
    <Modal
      title={`Book ${fundiName}`}
      description="Agree the job and price. You pay into escrow next."
      onClose={onClose}
    >
      <form className="stack" onSubmit={handleSubmit} noValidate>
        {error && <Alert tone="danger">{error}</Alert>}

        <Input
          label="What needs doing?"
          placeholder="Fix leaking kitchen sink"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
        />
        <Textarea
          label="Details"
          placeholder="Describe the problem, access, materials…"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
        <MoneyInput
          label="Agreed price (KES)"
          valueCents={amountCents}
          onChangeCents={setAmountCents}
          hint="Whole shillings. Held in escrow until you confirm the work."
        />
        <Input
          label="Location"
          placeholder="Kilimani, Nairobi"
          value={location}
          onChange={(event) => setLocation(event.target.value)}
          required
        />

        <div className="modal-actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={create.isPending}>
            Send request
          </Button>
        </div>
      </form>
    </Modal>
  )
}
