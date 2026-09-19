import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { LogOut, Mail, Phone, ShieldCheck, Trash2 } from 'lucide-react'

import { Alert, Badge, Button, Input } from '@/components/ui'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/useToast'
import { api, ApiError } from '@/lib/api'
import { formatDate, isValidKenyanPhone } from '@/lib/format'

export function SettingsPage() {
  const { user, refreshUser, logout, deleteAccount } = useAuth()
  const { notify } = useToast()
  const navigate = useNavigate()

  const [phone, setPhone] = useState(user?.phone ?? '')
  const [error, setError] = useState<string | null>(null)
  const [deletePassword, setDeletePassword] = useState('')
  const [deleteArmed, setDeleteArmed] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const removeAccount = useMutation({
    mutationFn: () => deleteAccount(deletePassword),
    onSuccess: () => {
      notify('Your account has been deleted', 'success')
      navigate('/', { replace: true })
    },
    onError: (mutationError) => {
      setDeleteArmed(false)
      if (mutationError instanceof ApiError && mutationError.status === 403) {
        setDeleteError('That password is not right.')
      } else if (mutationError instanceof ApiError) {
        // 409s explain exactly what is still in flight (active job, escrow, wallet balance).
        setDeleteError(mutationError.message)
      } else {
        setDeleteError('Could not delete your account. Check your connection and try again.')
      }
    },
  })

  const savePhone = useMutation({
    mutationFn: () => api.auth.updateProfile({ phone: phone.trim() }),
    onSuccess: async () => {
      await refreshUser()
      notify('Phone number updated', 'success')
    },
    onError: (mutationError) =>
      setError(
        mutationError instanceof ApiError
          ? mutationError.message
          : 'Could not update your phone number.',
      ),
  })

  if (!user) return null

  return (
    <div className="stack-lg" style={{ maxWidth: 620, margin: '0 auto' }}>
      <div className="page-head">
        <h1>Account settings</h1>
        <p className="muted">Your contact details and account status.</p>
      </div>

      <section className="card stack">
        <h2 style={{ fontSize: 'var(--text-base)' }}>Contact</h2>

        <div className="row-between">
          <div className="row">
            <Mail size={16} className="muted" aria-hidden />
            <div>
              <strong style={{ fontSize: 'var(--text-sm)' }}>{user.email}</strong>
              <p className="subtle">Your login email cannot be changed here.</p>
            </div>
          </div>
        </div>

        {error && <Alert tone="danger">{error}</Alert>}

        <Input
          label="Phone number"
          type="tel"
          hint="Used for M-PESA prompts and payouts."
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
        />
        <Button
          variant="primary"
          style={{ width: 'fit-content' }}
          loading={savePhone.isPending}
          disabled={phone === user.phone}
          onClick={() => {
            setError(null)
            if (!isValidKenyanPhone(phone)) {
              setError('Enter a valid Kenyan number, e.g. 0712 345 678.')
              return
            }
            savePhone.mutate()
          }}
        >
          <Phone size={15} /> Update number
        </Button>
      </section>

      <section className="card stack">
        <h2 style={{ fontSize: 'var(--text-base)' }}>Account</h2>

        <div className="row-between">
          <span className="muted">Role</span>
          <Badge tone="brand" >{user.role}</Badge>
        </div>
        <div className="row-between">
          <span className="muted">Member since</span>
          <span>{formatDate(user.created_at)}</span>
        </div>
        <div className="row-between">
          <span className="muted">Status</span>
          <Badge tone={user.is_active ? 'success' : 'danger'}>
            {user.is_active ? 'Active' : 'Disabled'}
          </Badge>
        </div>

        <div className="alert alert-info">
          <ShieldCheck size={16} aria-hidden />
          <div>
            Money you send is held by Fundi Connect in escrow, never handed straight to a fundi.
          </div>
        </div>
      </section>

      <section className="card stack">
        <h2 style={{ fontSize: 'var(--text-base)' }}>Session</h2>
        <Button
          variant="danger"
          style={{ width: 'fit-content' }}
          onClick={async () => {
            await logout()
            navigate('/')
          }}
        >
          <LogOut size={15} /> Log out
        </Button>
      </section>

      <section className="card stack" aria-labelledby="delete-account-heading">
        <h2 id="delete-account-heading" style={{ fontSize: 'var(--text-base)' }}>
          Delete my account
        </h2>
        <p className="muted" style={{ fontSize: 'var(--text-sm)' }}>
          Permanently removes your login, profile, messages, requests and finished job history.
          It is refused while you have an active job, money held in escrow or a wallet balance —
          finish or cancel those first. This cannot be undone.
        </p>
        {deleteError && <Alert tone="danger">{deleteError}</Alert>}
        <form
          className="stack"
          onSubmit={(event) => {
            event.preventDefault()
            setDeleteError(null)
            if (!deleteArmed) {
              // First submit only arms the button, so one stray tap cannot erase an account.
              setDeleteArmed(true)
              return
            }
            removeAccount.mutate()
          }}
        >
          <Input
            label="Confirm with your password"
            type="password"
            autoComplete="current-password"
            value={deletePassword}
            onChange={(event) => {
              setDeletePassword(event.target.value)
              setDeleteArmed(false)
            }}
            required
          />
          <div className="row">
            <Button
              type="submit"
              variant="danger"
              style={{ width: 'fit-content' }}
              loading={removeAccount.isPending}
              disabled={!deletePassword}
            >
              <Trash2 size={15} /> {deleteArmed ? 'Yes, delete my account' : 'Delete my account'}
            </Button>
            {deleteArmed && !removeAccount.isPending && (
              <Button type="button" variant="ghost" onClick={() => setDeleteArmed(false)}>
                Cancel
              </Button>
            )}
          </div>
        </form>
      </section>
    </div>
  )
}
