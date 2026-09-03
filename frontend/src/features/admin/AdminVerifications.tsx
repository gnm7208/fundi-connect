import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ExternalLink, ShieldCheck } from 'lucide-react'

import { Avatar, Badge, Button, EmptyState, Modal, Textarea } from '@/components/ui'
import { useToast } from '@/hooks/useToast'
import { api, ApiError } from '@/lib/api'
import { formatKes } from '@/lib/format'
import type { PendingFundi } from '@/lib/types'

export function AdminVerifications() {
  const queryClient = useQueryClient()
  const { notify } = useToast()
  const [rejecting, setRejecting] = useState<PendingFundi | null>(null)

  const { data: pending, isPending } = useQuery({
    queryKey: ['admin', 'verifications'],
    queryFn: () => api.admin.pendingVerifications(),
  })

  const review = useMutation({
    mutationFn: ({
      fundiId,
      status,
      notes,
    }: {
      fundiId: string
      status: 'verified' | 'rejected'
      notes?: string
    }) => api.admin.reviewVerification(fundiId, status, notes),
    onSuccess: (_result, variables) => {
      notify(variables.status === 'verified' ? 'Fundi verified' : 'Verification rejected', 'success')
      void queryClient.invalidateQueries({ queryKey: ['admin'] })
      setRejecting(null)
    },
    onError: (error) =>
      notify(error instanceof ApiError ? error.message : 'Could not update verification', 'error'),
  })

  if (isPending) {
    return <div className="skeleton" style={{ height: 180, borderRadius: 'var(--radius-lg)' }} />
  }

  if (!pending || pending.length === 0) {
    return (
      <EmptyState
        icon={<ShieldCheck size={20} />}
        title="No fundis waiting"
        description="Verification requests will appear here as fundis submit their IDs."
      />
    )
  }

  return (
    <>
      <div className="stack stagger">
        {pending.map((fundi) => (
          <div key={fundi.id} className="card stack">
            <div className="row-between wrap">
              <div className="row">
                <Avatar name={fundi.user_name} />
                <div>
                  <strong>{fundi.user_name}</strong>
                  <p className="subtle">
                    {fundi.business_name} · {fundi.location_name ?? 'No location'}
                  </p>
                </div>
              </div>
              <Badge tone="warning">Pending review</Badge>
            </div>

            <div className="table-scroll">
              <table className="data">
                <tbody>
                  <tr>
                    <th>Email</th>
                    <td>{fundi.email}</td>
                    <th>Phone</th>
                    <td className="numeric">{fundi.phone}</td>
                  </tr>
                  <tr>
                    <th>Experience</th>
                    <td>{fundi.experience_years} years</td>
                    <th>Rate</th>
                    <td className="numeric">
                      {fundi.hourly_rate_cents ? formatKes(fundi.hourly_rate_cents) : '—'}
                    </td>
                  </tr>
                  <tr>
                    <th>ID number</th>
                    <td className="numeric">{fundi.id_number ?? 'Not submitted'}</td>
                    <th>Trades</th>
                    <td>
                      {fundi.skills?.map((skill) => skill.skill_name).join(', ') || 'None listed'}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="row-between wrap">
              {fundi.id_document_url ? (
                <a
                  className="btn btn-secondary btn-sm"
                  href={fundi.id_document_url}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  <ExternalLink size={14} /> View ID document
                </a>
              ) : (
                <span className="subtle">No ID document uploaded yet</span>
              )}

              <div className="row">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setRejecting(fundi)}
                  disabled={review.isPending}
                >
                  Reject
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  disabled={review.isPending}
                  onClick={() =>
                    review.mutate({
                      fundiId: fundi.id,
                      status: 'verified',
                      notes: 'ID verified by admin.',
                    })
                  }
                >
                  <ShieldCheck size={14} /> Approve
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {rejecting && (
        <RejectModal
          fundi={rejecting}
          busy={review.isPending}
          onClose={() => setRejecting(null)}
          onConfirm={(notes) =>
            review.mutate({ fundiId: rejecting.id, status: 'rejected', notes })
          }
        />
      )}
    </>
  )
}

function RejectModal({
  fundi,
  busy,
  onClose,
  onConfirm,
}: {
  fundi: PendingFundi
  busy: boolean
  onClose: () => void
  onConfirm: (notes: string) => void
}) {
  const [notes, setNotes] = useState('')

  return (
    <Modal
      title={`Reject ${fundi.user_name}?`}
      description="They will see your reason and can resubmit."
      onClose={onClose}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="danger"
            loading={busy}
            onClick={() => onConfirm(notes.trim() || 'ID document could not be verified.')}
          >
            Reject verification
          </Button>
        </>
      }
    >
      <Textarea
        label="Reason"
        placeholder="The ID photo was blurry — please upload a clearer image."
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
      />
    </Modal>
  )
}
