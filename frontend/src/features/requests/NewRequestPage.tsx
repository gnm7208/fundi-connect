import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'

import { Alert, Button, Input, MoneyInput, Select, Textarea } from '@/components/ui'
import { useToast } from '@/hooks/useToast'
import { api, ApiError } from '@/lib/api'

export function NewRequestPage() {
  const navigate = useNavigate()
  const { notify } = useToast()

  const [categoryId, setCategoryId] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [location, setLocation] = useState('')
  const [minCents, setMinCents] = useState<number | ''>('')
  const [maxCents, setMaxCents] = useState<number | ''>('')
  const [error, setError] = useState<string | null>(null)

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => api.categories.list(),
    staleTime: 5 * 60_000,
  })

  const create = useMutation({
    mutationFn: () =>
      api.serviceRequests.create({
        category_id: categoryId,
        title: title.trim(),
        description: description.trim(),
        location_name: location.trim(),
        budget_min_cents: minCents === '' ? undefined : minCents,
        budget_max_cents: maxCents === '' ? undefined : maxCents,
      }),
    onSuccess: (request) => {
      notify('Job posted — fundis can now quote', 'success')
      navigate(`/requests/${request.id}`)
    },
    onError: (mutationError) =>
      setError(mutationError instanceof ApiError ? mutationError.message : 'Could not post that job.'),
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!categoryId) return setError('Choose the kind of work you need.')
    if (title.trim().length < 5) return setError('Give the job a clear title.')
    if (description.trim().length < 10) return setError('Describe the job in a bit more detail.')
    if (!location.trim()) return setError('Where is the job?')
    if (minCents !== '' && maxCents !== '' && minCents > maxCents) {
      return setError('The minimum budget cannot be above the maximum.')
    }
    create.mutate()
  }

  return (
    <div style={{ maxWidth: 620, margin: '0 auto' }} className="stack">
      <Link to="/requests" className="row subtle" style={{ width: 'fit-content' }}>
        <ArrowLeft size={15} /> Back to jobs
      </Link>

      <div className="page-head">
        <h1>Post a job</h1>
        <p className="muted">Describe the work and let verified fundis send you quotes.</p>
      </div>

      <form className="card stack" onSubmit={handleSubmit} noValidate>
        {error && <Alert tone="danger">{error}</Alert>}

        <Select
          label="Kind of work"
          value={categoryId}
          onChange={(event) => setCategoryId(event.target.value)}
          required
        >
          <option value="">Choose a trade…</option>
          {categories?.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </Select>

        <Input
          label="Job title"
          placeholder="Rewire two bedroom sockets"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
        />

        <Textarea
          label="Describe the job"
          placeholder="What needs doing, what's already there, and when you'd like it done."
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          required
        />

        <Input
          label="Location"
          placeholder="Roysambu, Nairobi"
          value={location}
          onChange={(event) => setLocation(event.target.value)}
          required
        />

        <div className="field-row">
          <MoneyInput
            label="Budget from (KES)"
            valueCents={minCents}
            onChangeCents={setMinCents}
            hint="Optional"
          />
          <MoneyInput
            label="Budget to (KES)"
            valueCents={maxCents}
            onChangeCents={setMaxCents}
            hint="Optional"
          />
        </div>

        <Button type="submit" variant="primary" loading={create.isPending} block>
          Post job
        </Button>
      </form>
    </div>
  )
}
