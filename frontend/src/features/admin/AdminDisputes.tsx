import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Gavel, Scale } from 'lucide-react'

import { Alert, Badge, Button, EmptyState, Modal, Textarea } from '@/components/ui'
import { useToast } from '@/hooks/useToast'
import { api, ApiError } from '@/lib/api'
import { formatDateTime } from '@/lib/format'
import type { Dispute, DisputeStatus } from '@/lib/types'

const STATUS: Record<DisputeStatus, { label: string; tone: 'warning' | 'progress' | 'success' | 'neutral' }> = {
  open: { label: 'Open', tone: 'warning' },
  under_review: { label: 'Under review', tone: 'progress' },
  resolved_refund: { label: 'Refunded customer', tone: 'success' },
  resolved_payout: { label: 'Paid the fundi', tone: 'success' },
}

export function AdminDisputes() {
  const [resolving, setResolving] = useState<Dispute | null>(null)

  const { data: disputes, isPending } = useQuery({
    queryKey: ['admin', 'disputes'],
    queryFn: () => api.admin.disputes(),
  })

  if (isPending) {
    return <div className="skeleton" style={{ height: 180, borderRadius: 'var(--radius-lg)' }} />
  }

  if (!disputes || disputes.length === 0) {
    return (
      <EmptyState
        icon={<Scale size={20} />}
        title="No disputes"
        description="When a customer or fundi contests a job, it lands here for arbitration."
      />
    )
  }

  const open = disputes.filter((dispute) => ['open', 'under_review'].includes(dispute.status))
  const closed = disputes.filter((dispute) => !['open', 'under_review'].includes(dispute.status))

  return (
    <>
      <div className="stack-lg">
        {open.length > 0 && (
          <section className="stack">
            <div className="section-title">
              <h2>Needs a decision</h2>
              <span className="subtle">{open.length}</span>
            </div>
            {open.map((dispute) => (
              <DisputeCard key={dispute.id} dispute={dispute} onResolve={() => setResolving(dispute)} />
            ))}
          </section>
        )}

        {closed.length > 0 && (
          <section className="stack">
            <div className="section-title">
              <h2>Resolved</h2>
              <span className="subtle">{closed.length}</span>
            </div>
            {closed.map((dispute) => (
              <DisputeCard key={dispute.id} dispute={dispute} />
            ))}
          </section>
        )}
      </div>

      {resolving && <ResolveModal dispute={resolving} onClose={() => setResolving(null)} />}
    </>
  )
}

function DisputeCard({ dispute, onResolve }: { dispute: Dispute; onResolve?: () => void }) {
  const status = STATUS[dispute.status]

  return (
    <div className="card stack">
      <div className="row-between wrap">
        <div>
          <strong>{dispute.reason}</strong>
          <p className="subtle">
            Opened by {dispute.initiator_name} · {formatDateTime(dispute.created_at)}
          </p>
        </div>
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>

      <div className="stack-sm">
        <div>
          <span className="label subtle">Customer statement</span>
          <p>{dispute.customer_statement ?? '—'}</p>
        </div>
        <div>
          <span className="label subtle">Fundi statement</span>
          <p>{dispute.fundi_statement ?? 'Not yet submitted.'}</p>
        </div>
      </div>

      {dispute.resolution && (
        <Alert tone="success">
          <strong>Resolution:</strong> {dispute.resolution}
        </Alert>
      )}

      {onResolve && (
        <Button variant="primary" style={{ width: 'fit-content' }} onClick={onResolve}>
          <Gavel size={15} /> Arbitrate
        </Button>
      )}
    </div>
  )
}

function ResolveModal({ dispute, onClose }: { dispute: Dispute; onClose: () => void }) {
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const [action, setAction] = useState<'refund_customer' | 'payout_fundi'>('refund_customer')
  const [resolution, setResolution] = useState('')
  const [error, setError] = useState<string | null>(null)

  const resolve = useMutation({
    mutationFn: () => api.admin.resolveDispute(dispute.id, action, resolution.trim()),
    onSuccess: () => {
      notify('Dispute resolved and escrow settled', 'success')
      void queryClient.invalidateQueries({ queryKey: ['admin'] })
      onClose()
    },
    onError: (mutationError) =>
      setError(
        mutationError instanceof ApiError ? mutationError.message : 'Could not resolve that dispute.',
      ),
  })

  return (
    <Modal
      title="Arbitrate dispute"
      description="This decision moves real money out of escrow immediately."
      onClose={onClose}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            loading={resolve.isPending}
            onClick={() => {
              setError(null)
              if (resolution.trim().length < 5) {
                setError('Record why you decided this — both parties will see it.')
                return
              }
              resolve.mutate()
            }}
          >
            Resolve dispute
          </Button>
        </>
      }
    >
      <div className="stack">
        {error && <Alert tone="danger">{error}</Alert>}

        <div className="field">
          <label>Outcome</label>
          <div className="segmented">
            <button
              type="button"
              aria-pressed={action === 'refund_customer'}
              onClick={() => setAction('refund_customer')}
            >
              Refund customer
            </button>
            <button
              type="button"
              aria-pressed={action === 'payout_fundi'}
              onClick={() => setAction('payout_fundi')}
            >
              Pay the fundi
            </button>
          </div>
        </div>

        <Alert tone="warning">
          {action === 'refund_customer'
            ? 'The full escrow amount returns to the customer and the booking is cancelled.'
            : 'The fundi is credited their share and the booking is marked complete.'}
        </Alert>

        <Textarea
          label="Decision notes"
          placeholder="What the evidence showed and why you decided this way."
          value={resolution}
          onChange={(event) => setResolution(event.target.value)}
        />
      </div>
    </Modal>
  )
}
