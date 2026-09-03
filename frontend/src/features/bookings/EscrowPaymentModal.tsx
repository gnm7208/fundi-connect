import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Lock, Smartphone } from 'lucide-react'

import { Alert, Button, Input, Modal } from '@/components/ui'
import { useToast } from '@/hooks/useToast'
import { api, ApiError } from '@/lib/api'
import { formatKes, isValidKenyanPhone } from '@/lib/format'
import type { Booking } from '@/lib/types'

type Stage = 'enter-phone' | 'awaiting-pin' | 'done'

const POLL_MS = 3000

export function EscrowPaymentModal({
  booking,
  defaultPhone,
  onClose,
}: {
  booking: Booking
  defaultPhone: string
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const { notify } = useToast()

  const [stage, setStage] = useState<Stage>('enter-phone')
  const [phone, setPhone] = useState(defaultPhone)
  const [checkoutId, setCheckoutId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const push = useMutation({
    mutationFn: () => api.payments.initiateStkPush(booking.id, phone.trim()),
    onSuccess: (result) => {
      setCheckoutId(result.checkout_request_id)
      setStage('awaiting-pin')
    },
    onError: (pushError) => {
      setError(pushError instanceof ApiError ? pushError.message : 'Could not send the M-PESA prompt.')
    },
  })

  // The customer completes the payment on their handset, so the browser learns
  // about it by polling the escrow record rather than from the request itself.
  useEffect(() => {
    if (stage !== 'awaiting-pin' || !checkoutId) return

    const timer = setInterval(async () => {
      try {
        const escrow = await api.payments.status(checkoutId)
        if (escrow.status === 'held_in_escrow') {
          clearInterval(timer)
          setStage('done')
          notify('Payment secured in escrow', 'success')
          void queryClient.invalidateQueries({ queryKey: ['booking', booking.id] })
          void queryClient.invalidateQueries({ queryKey: ['bookings'] })
        } else if (escrow.status === 'failed') {
          clearInterval(timer)
          setStage('enter-phone')
          setError('That payment did not go through. Try again.')
        }
      } catch {
        // A transient poll failure is not worth surfacing; the next tick retries.
      }
    }, POLL_MS)

    return () => clearInterval(timer)
  }, [stage, checkoutId, booking.id, notify, queryClient])

  const confirmDemo = useMutation({
    mutationFn: () => api.payments.simulateConfirmation(checkoutId!),
    onError: () => setError('Simulation failed. Is the API in simulation mode?'),
  })

  function handleSend() {
    setError(null)
    if (!isValidKenyanPhone(phone)) {
      setError('Enter a valid Kenyan number, e.g. 0712 345 678.')
      return
    }
    push.mutate()
  }

  return (
    <Modal
      title="Pay into escrow"
      description="Your money is held by Fundi Connect until you confirm the job."
      onClose={onClose}
    >
      <div className="stack">
        {error && <Alert tone="danger">{error}</Alert>}

        <div className="escrow-panel money-rows">
          <div className="money-row">
            <span>{booking.title}</span>
            <span className="numeric">{formatKes(booking.agreed_amount_cents)}</span>
          </div>
          <div className="money-row muted">
            <span>Fundi receives on completion</span>
            <span className="numeric">{formatKes(booking.fundi_amount_cents)}</span>
          </div>
          <div className="money-row muted">
            <span>Platform fee</span>
            <span className="numeric">{formatKes(booking.platform_fee_cents)}</span>
          </div>
          <div className="money-row total">
            <span>You pay now</span>
            <span className="numeric">{formatKes(booking.agreed_amount_cents)}</span>
          </div>
        </div>

        {stage === 'enter-phone' && (
          <>
            <Input
              label="M-PESA number"
              type="tel"
              placeholder="0712 345 678"
              hint="You will get a PIN prompt on this phone."
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
            />
            <Button variant="primary" block loading={push.isPending} onClick={handleSend}>
              <Smartphone size={15} /> Send M-PESA prompt
            </Button>
          </>
        )}

        {stage === 'awaiting-pin' && (
          <div className="stack">
            <div className="alert alert-info">
              <Loader2 size={16} className="spin" aria-hidden />
              <div>
                <strong>Check your phone</strong>
                <p className="subtle">
                  Enter your M-PESA PIN to lock {formatKes(booking.agreed_amount_cents)} in escrow.
                  This page updates itself.
                </p>
              </div>
            </div>

            {/* Demo affordance: stands in for the handset when Daraja runs in simulation mode. */}
            <Button
              variant="ghost"
              block
              loading={confirmDemo.isPending}
              onClick={() => confirmDemo.mutate()}
            >
              Simulate entering my PIN (demo)
            </Button>
          </div>
        )}

        {stage === 'done' && (
          <div className="stack">
            <div className="alert alert-success">
              <Lock size={16} aria-hidden />
              <div>
                <strong>Money secured</strong>
                <p className="subtle">
                  The fundi can start work. Nothing is paid out until you confirm.
                </p>
              </div>
            </div>
            <Button variant="primary" block onClick={onClose}>
              Done
            </Button>
          </div>
        )}
      </div>
    </Modal>
  )
}
