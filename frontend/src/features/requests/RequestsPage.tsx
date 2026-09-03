import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { FileText, MapPin, Plus } from 'lucide-react'

import { Badge, Button, EmptyState, SkeletonList } from '@/components/ui'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import { formatKes, formatRelative } from '@/lib/format'

export function RequestsPage() {
  const { user } = useAuth()
  const isFundi = user?.role === 'fundi'

  const { data, isPending } = useQuery({
    queryKey: ['service-requests', 'open'],
    queryFn: () => api.serviceRequests.list({ status: 'open' }),
  })

  const requests = data?.service_requests ?? []

  return (
    <div className="stack-lg">
      <div className="page-head row-between wrap">
        <div>
          <h1>{isFundi ? 'Open jobs' : 'My job posts'}</h1>
          <p className="muted">
            {isFundi
              ? 'Customers waiting for a quote. Win the job by pricing it well.'
              : 'Post a job once and let verified fundis quote for it.'}
          </p>
        </div>
        {!isFundi && (
          <Link to="/requests/new">
            <Button variant="primary">
              <Plus size={15} /> Post a job
            </Button>
          </Link>
        )}
      </div>

      {isPending ? (
        <SkeletonList count={3} />
      ) : requests.length === 0 ? (
        <EmptyState
          icon={<FileText size={20} />}
          title="No open requests"
          description={
            isFundi
              ? 'Check back soon — new jobs are posted daily.'
              : 'Post a job and compare quotes from verified fundis.'
          }
          action={
            !isFundi && (
              <Link to="/requests/new">
                <Button variant="primary">Post a job</Button>
              </Link>
            )
          }
        />
      ) : (
        <div className="grid-cards stagger">
          {requests.map((request) => (
            <Link
              key={request.id}
              to={`/requests/${request.id}`}
              className="card card-interactive stack-sm"
            >
              <div className="row-between wrap">
                <strong>{request.title}</strong>
                <Badge tone={request.quote_count > 0 ? 'progress' : 'neutral'}>
                  {request.quote_count} quote{request.quote_count === 1 ? '' : 's'}
                </Badge>
              </div>

              <p
                className="subtle"
                style={{
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}
              >
                {request.description}
              </p>

              <div className="fundi-meta">
                <span>
                  <MapPin size={13} aria-hidden /> {request.location_name}
                </span>
                {request.category_name && <span>{request.category_name}</span>}
                <span>{formatRelative(request.created_at)}</span>
              </div>

              {(request.budget_min_cents || request.budget_max_cents) && (
                <div className="row-between">
                  <span className="subtle">Budget</span>
                  <strong className="numeric">
                    {formatKes(request.budget_min_cents)} – {formatKes(request.budget_max_cents)}
                  </strong>
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
