import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowDownLeft, ArrowUpRight, Receipt, Wallet as WalletIcon } from 'lucide-react'

import { Alert, Button, EmptyState, Input, Modal, MoneyInput } from '@/components/ui'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/useToast'
import { api, ApiError } from '@/lib/api'
import { formatDateTime, formatKes, isValidKenyanPhone } from '@/lib/format'

const MIN_PAYOUT_CENTS = 10000

export function WalletPage() {
  const [withdrawing, setWithdrawing] = useState(false)

  const { data: wallet } = useQuery({ queryKey: ['wallet'], queryFn: () => api.wallet.me() })
  const { data: ledger, isPending } = useQuery({
    queryKey: ['wallet', 'transactions'],
    queryFn: () => api.wallet.transactions(),
  })

  const transactions = ledger?.transactions ?? []
  const balance = wallet?.balance_cents ?? 0

  return (
    <div className="stack-lg">
      <div className="page-head">
        <h1>Wallet</h1>
        <p className="muted">Earnings released from escrow, ready to send to M-PESA.</p>
      </div>

      <section className="card stack">
        <span className="label subtle">Available balance</span>
        <p className="balance-amount">{formatKes(balance)}</p>

        {wallet?.is_frozen ? (
          <Alert tone="danger">
            This wallet is frozen. Contact support before requesting a withdrawal.
          </Alert>
        ) : (
          <Button
            variant="primary"
            onClick={() => setWithdrawing(true)}
            disabled={balance < MIN_PAYOUT_CENTS}
            style={{ width: 'fit-content' }}
          >
            <ArrowUpRight size={15} /> Withdraw to M-PESA
          </Button>
        )}

        {balance < MIN_PAYOUT_CENTS && !wallet?.is_frozen && (
          <p className="subtle">Minimum withdrawal is {formatKes(MIN_PAYOUT_CENTS)}.</p>
        )}
      </section>

      <section className="card">
        <div className="section-title">
          <h2>Transactions</h2>
          <span className="subtle">{ledger?.pagination.total_items ?? 0} entries</span>
        </div>

        {isPending ? (
          <div className="stack-sm" aria-hidden>
            {[0, 1, 2].map((row) => (
              <div key={row} className="skeleton" style={{ height: 46 }} />
            ))}
          </div>
        ) : transactions.length === 0 ? (
          <EmptyState
            icon={<Receipt size={20} />}
            title="No transactions yet"
            description="Completed jobs will show up here as escrow payouts."
          />
        ) : (
          <div className="ledger">
            {transactions.map((transaction) => {
              const credit = transaction.amount_cents > 0
              return (
                <div className="ledger-row" key={transaction.id}>
                  <span
                    className="ledger-icon"
                    style={{
                      background: credit ? 'var(--success-100)' : 'var(--surface-sunken)',
                      color: credit ? 'var(--success-500)' : 'var(--text-muted)',
                    }}
                  >
                    {credit ? <ArrowDownLeft size={16} /> : <ArrowUpRight size={16} />}
                  </span>

                  <div style={{ minWidth: 0 }}>
                    <strong style={{ fontSize: 'var(--text-sm)' }}>
                      {credit ? 'Escrow payout' : 'M-PESA withdrawal'}
                    </strong>
                    <p className="subtle">
                      {transaction.description ?? transaction.reference ?? '—'}
                    </p>
                    <p className="subtle" style={{ fontSize: 10 }}>
                      {formatDateTime(transaction.created_at)}
                    </p>
                  </div>

                  <span className="ledger-amount" data-credit={credit}>
                    {credit ? '+' : ''}
                    {formatKes(transaction.amount_cents)}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </section>

      {withdrawing && (
        <WithdrawModal balanceCents={balance} onClose={() => setWithdrawing(false)} />
      )}
    </div>
  )
}

function WithdrawModal({ balanceCents, onClose }: { balanceCents: number; onClose: () => void }) {
  const { user } = useAuth()
  const { notify } = useToast()
  const queryClient = useQueryClient()

  const [amountCents, setAmountCents] = useState<number | ''>(balanceCents)
  const [phone, setPhone] = useState(user?.phone ?? '')
  const [error, setError] = useState<string | null>(null)

  const withdraw = useMutation({
    mutationFn: () => api.wallet.requestPayout(amountCents === '' ? 0 : amountCents, phone.trim()),
    onSuccess: () => {
      notify('Payout sent to your M-PESA', 'success')
      void queryClient.invalidateQueries({ queryKey: ['wallet'] })
      onClose()
    },
    onError: (mutationError) =>
      setError(
        mutationError instanceof ApiError
          ? mutationError.fieldError('amount_cents') ?? mutationError.message
          : 'Could not process that withdrawal.',
      ),
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (amountCents === '' || amountCents < MIN_PAYOUT_CENTS) {
      return setError(`Minimum withdrawal is ${formatKes(MIN_PAYOUT_CENTS)}.`)
    }
    if (amountCents > balanceCents) return setError('That is more than your available balance.')
    if (!isValidKenyanPhone(phone)) return setError('Enter a valid Kenyan M-PESA number.')
    withdraw.mutate()
  }

  return (
    <Modal
      title="Withdraw earnings"
      description="Sent straight to your M-PESA via Daraja B2C."
      onClose={onClose}
    >
      <form className="stack" onSubmit={handleSubmit} noValidate>
        {error && <Alert tone="danger">{error}</Alert>}

        <MoneyInput
          label="Amount (KES)"
          valueCents={amountCents}
          onChangeCents={setAmountCents}
          hint={`Available: ${formatKes(balanceCents)}`}
        />
        <Input
          label="M-PESA number"
          type="tel"
          placeholder="0712 345 678"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
        />

        <div className="modal-actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={withdraw.isPending}>
            <WalletIcon size={15} /> Withdraw
          </Button>
        </div>
      </form>
    </Modal>
  )
}
