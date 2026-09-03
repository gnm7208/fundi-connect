import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { Alert, Button, Input } from '@/components/ui'
import { useAuth } from '@/hooks/useAuth'
import { ApiError } from '@/lib/api'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await login(identifier, password)
      const from = (location.state as { from?: string } | null)?.from
      navigate(from ?? '/dashboard', { replace: true })
    } catch (loginError) {
      setError(
        loginError instanceof ApiError
          ? loginError.message
          : 'Could not reach the server. Check your connection.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: '0 auto' }}>
      <div className="page-head">
        <h1>Welcome back</h1>
        <p className="muted">Log in to manage your jobs and payments.</p>
      </div>

      <form className="card stack" onSubmit={handleSubmit} noValidate>
        {error && <Alert tone="danger">{error}</Alert>}

        <Input
          label="Email or phone"
          autoComplete="username"
          placeholder="you@example.com or 07xx xxx xxx"
          value={identifier}
          onChange={(event) => setIdentifier(event.target.value)}
          required
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        <Button type="submit" variant="primary" loading={busy} block>
          Log in
        </Button>

        <p className="subtle" style={{ textAlign: 'center' }}>
          New here?{' '}
          <Link to="/register" style={{ color: 'var(--brand-500)', fontWeight: 560 }}>
            Create an account
          </Link>
        </p>
      </form>
    </div>
  )
}
