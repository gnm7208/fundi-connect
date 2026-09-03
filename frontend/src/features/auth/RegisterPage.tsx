import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Alert, Button, Input, MoneyInput, Select } from '@/components/ui'
import { useAuth } from '@/hooks/useAuth'
import { api, ApiError } from '@/lib/api'
import { isValidKenyanPhone } from '@/lib/format'
import type { Role } from '@/lib/types'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [role, setRole] = useState<Role>(searchParams.get('role') === 'fundi' ? 'fundi' : 'customer')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [businessName, setBusinessName] = useState('')
  const [locationName, setLocationName] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [rateCents, setRateCents] = useState<number | ''>(150000)

  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => api.categories.list(),
    staleTime: 5 * 60_000,
  })

  function validate(): boolean {
    const next: Record<string, string> = {}
    if (fullName.trim().length < 2) next.full_name = 'Tell us your name.'
    if (!email.includes('@')) next.email = 'Enter a valid email address.'
    if (!isValidKenyanPhone(phone)) next.phone = 'Use a Kenyan number, e.g. 0712 345 678.'
    if (password.length < 6) next.password = 'At least 6 characters.'
    if (role === 'fundi' && !locationName.trim()) next.location_name = 'Where do you work?'
    setFieldErrors(next)
    return Object.keys(next).length === 0
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!validate()) return

    setBusy(true)
    try {
      await register({
        role,
        full_name: fullName.trim(),
        email: email.trim(),
        phone: phone.trim(),
        password,
        ...(role === 'fundi'
          ? {
              business_name: businessName.trim() || undefined,
              location_name: locationName.trim(),
              category_id: categoryId || undefined,
              hourly_rate_cents: rateCents === '' ? undefined : rateCents,
            }
          : {}),
      })
      navigate(role === 'fundi' ? '/profile' : '/find', { replace: true })
    } catch (registerError) {
      if (registerError instanceof ApiError) {
        setError(registerError.message)
        setFieldErrors(
          Object.fromEntries(
            Object.entries(registerError.fields).map(([key, messages]) => [key, messages[0]]),
          ),
        )
      } else {
        setError('Could not reach the server. Check your connection.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ maxWidth: 520, margin: '0 auto' }}>
      <div className="page-head">
        <h1>Create your account</h1>
        <p className="muted">
          {role === 'fundi'
            ? 'Get discovered by customers nearby and get paid safely.'
            : 'Book verified fundis and pay only when the work is done.'}
        </p>
      </div>

      <form className="card stack" onSubmit={handleSubmit} noValidate>
        {error && <Alert tone="danger">{error}</Alert>}

        <div className="field">
          <label>I want to</label>
          <div className="segmented">
            <button type="button" aria-pressed={role === 'customer'} onClick={() => setRole('customer')}>
              Hire a fundi
            </button>
            <button type="button" aria-pressed={role === 'fundi'} onClick={() => setRole('fundi')}>
              Work as a fundi
            </button>
          </div>
        </div>

        <Input
          label="Full name"
          autoComplete="name"
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          error={fieldErrors.full_name}
          required
        />

        <div className="field-row">
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            error={fieldErrors.email}
            required
          />
          <Input
            label="Phone"
            type="tel"
            autoComplete="tel"
            placeholder="0712 345 678"
            hint="Used for M-PESA prompts"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            error={fieldErrors.phone}
            required
          />
        </div>

        <Input
          label="Password"
          type="password"
          autoComplete="new-password"
          hint="At least 6 characters"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={fieldErrors.password}
          required
        />

        {role === 'fundi' && (
          <>
            <div className="field-row">
              <Input
                label="Business name"
                hint="Optional — shown on your profile"
                value={businessName}
                onChange={(event) => setBusinessName(event.target.value)}
              />
              <Input
                label="Where you work"
                placeholder="Kilimani, Nairobi"
                value={locationName}
                onChange={(event) => setLocationName(event.target.value)}
                error={fieldErrors.location_name}
                required
              />
            </div>

            <div className="field-row">
              <Select
                label="Main trade"
                value={categoryId}
                onChange={(event) => setCategoryId(event.target.value)}
              >
                <option value="">Choose a trade…</option>
                {categories?.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </Select>
              <MoneyInput
                label="Hourly rate (KES)"
                valueCents={rateCents}
                onChangeCents={setRateCents}
                hint="You can change this later"
              />
            </div>
          </>
        )}

        <Button type="submit" variant="primary" loading={busy} block>
          Create account
        </Button>

        <p className="subtle" style={{ textAlign: 'center' }}>
          Already registered?{' '}
          <Link to="/login" style={{ color: 'var(--brand-500)', fontWeight: 560 }}>
            Log in
          </Link>
        </p>
      </form>
    </div>
  )
}
