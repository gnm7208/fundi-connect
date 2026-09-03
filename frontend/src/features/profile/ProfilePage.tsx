import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BadgeCheck, Plus, ShieldCheck, Trash2 } from 'lucide-react'

import { AvatarUploader } from '@/components/AvatarUploader'
import {
  Alert,
  Badge,
  Button,
  Input,
  Modal,
  MoneyInput,
  Select,
  Textarea,
} from '@/components/ui'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/useToast'
import { api, ApiError } from '@/lib/api'
import { formatKes } from '@/lib/format'

export function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const { notify } = useToast()
  const queryClient = useQueryClient()

  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url ?? null)
  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [verifying, setVerifying] = useState(false)
  const [addingSkill, setAddingSkill] = useState(false)

  const profile = user?.fundi_profile
  const isFundi = user?.role === 'fundi'

  const [bio, setBio] = useState(profile?.bio ?? '')
  const [businessName, setBusinessName] = useState(profile?.business_name ?? '')
  const [locationName, setLocationName] = useState(profile?.location_name ?? '')
  const [experience, setExperience] = useState(String(profile?.experience_years ?? 1))
  const [rateCents, setRateCents] = useState<number | ''>(profile?.hourly_rate_cents ?? '')
  const [radius, setRadius] = useState(String(profile?.service_radius_km ?? 15))
  const [available, setAvailable] = useState(profile?.is_available ?? true)

  const saveAccount = useMutation({
    mutationFn: () =>
      api.auth.updateProfile({ full_name: fullName.trim(), avatar_url: avatarUrl ?? '' }),
    onSuccess: async () => {
      await refreshUser()
      notify('Profile updated', 'success')
    },
    onError: (error) =>
      notify(error instanceof ApiError ? error.message : 'Could not save your profile', 'error'),
  })

  const saveFundi = useMutation({
    mutationFn: () =>
      api.fundis.updateProfile({
        business_name: businessName.trim() || null,
        bio: bio.trim() || null,
        location_name: locationName.trim() || null,
        experience_years: Number(experience) || 0,
        hourly_rate_cents: rateCents === '' ? undefined : rateCents,
        service_radius_km: Number(radius) || 15,
        is_available: available,
      }),
    onSuccess: async () => {
      await refreshUser()
      notify('Fundi profile updated', 'success')
    },
    onError: (error) =>
      notify(error instanceof ApiError ? error.message : 'Could not save your fundi profile', 'error'),
  })

  const removeSkill = useMutation({
    mutationFn: (skillId: string) => api.fundis.removeSkill(skillId),
    onSuccess: async () => {
      await refreshUser()
      void queryClient.invalidateQueries({ queryKey: ['fundi'] })
    },
  })

  if (!user) return null

  return (
    <div className="stack-lg" style={{ maxWidth: 720, margin: '0 auto' }}>
      <div className="page-head">
        <h1>My profile</h1>
        <p className="muted">
          {isFundi
            ? 'This is what customers see when they find you.'
            : 'Personalise your account so fundis know who they are working for.'}
        </p>
      </div>

      <section className="card stack">
        <h2 style={{ fontSize: 'var(--text-base)' }}>Photo &amp; name</h2>
        <AvatarUploader name={fullName} value={avatarUrl} onChange={setAvatarUrl} />
        <Input
          label="Full name"
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
        />
        <Button
          variant="primary"
          style={{ width: 'fit-content' }}
          loading={saveAccount.isPending}
          onClick={() => saveAccount.mutate()}
        >
          Save
        </Button>
      </section>

      {isFundi && (
        <>
          <section className="card stack">
            <div className="row-between wrap">
              <h2 style={{ fontSize: 'var(--text-base)' }}>Verification</h2>
              {profile?.verification_status === 'verified' ? (
                <Badge tone="success">
                  <BadgeCheck size={13} /> Verified
                </Badge>
              ) : profile?.verification_status === 'rejected' ? (
                <Badge tone="danger">Rejected</Badge>
              ) : (
                <Badge tone="warning">Pending review</Badge>
              )}
            </div>

            {profile?.verification_status === 'verified' ? (
              <p className="subtle">
                Your national ID has been verified. Customers see the badge on your profile.
              </p>
            ) : (
              <>
                <Alert tone="info">
                  <ShieldCheck size={15} style={{ display: 'inline', verticalAlign: -2 }} /> Verified
                  fundis get significantly more bookings. Submit your national ID to be reviewed.
                </Alert>
                {profile?.verification_notes && (
                  <p className="subtle">Admin note: {profile.verification_notes}</p>
                )}
                <Button
                  variant="primary"
                  style={{ width: 'fit-content' }}
                  onClick={() => setVerifying(true)}
                >
                  Submit ID for verification
                </Button>
              </>
            )}
          </section>

          <section className="card stack">
            <h2 style={{ fontSize: 'var(--text-base)' }}>Your work</h2>

            <Input
              label="Business name"
              placeholder="Mwangi Fast Fixes"
              value={businessName}
              onChange={(event) => setBusinessName(event.target.value)}
            />

            <Textarea
              label="About you"
              placeholder="What you do, the jobs you're best at, and how you work."
              value={bio}
              onChange={(event) => setBio(event.target.value)}
            />

            <div className="field-row">
              <Input
                label="Where you work"
                placeholder="Kilimani, Nairobi"
                value={locationName}
                onChange={(event) => setLocationName(event.target.value)}
              />
              <MoneyInput
                label="Hourly rate (KES)"
                valueCents={rateCents}
                onChangeCents={setRateCents}
              />
            </div>

            <div className="field-row">
              <div className="field">
                <label>Years of experience</label>
                <input
                  className="input numeric"
                  type="number"
                  min={0}
                  max={60}
                  value={experience}
                  onChange={(event) => setExperience(event.target.value)}
                />
              </div>
              <div className="field">
                <label>Travel radius (km)</label>
                <input
                  className="input numeric"
                  type="number"
                  min={1}
                  max={100}
                  value={radius}
                  onChange={(event) => setRadius(event.target.value)}
                />
              </div>
            </div>

            <div className="field">
              <label>Availability</label>
              <div className="segmented">
                <button type="button" aria-pressed={available} onClick={() => setAvailable(true)}>
                  Taking jobs
                </button>
                <button type="button" aria-pressed={!available} onClick={() => setAvailable(false)}>
                  Busy
                </button>
              </div>
            </div>

            <Button
              variant="primary"
              style={{ width: 'fit-content' }}
              loading={saveFundi.isPending}
              onClick={() => saveFundi.mutate()}
            >
              Save fundi profile
            </Button>
          </section>

          <section className="card stack">
            <div className="row-between">
              <h2 style={{ fontSize: 'var(--text-base)' }}>Skills &amp; trades</h2>
              <Button size="sm" onClick={() => setAddingSkill(true)}>
                <Plus size={14} /> Add skill
              </Button>
            </div>

            {!profile?.skills || profile.skills.length === 0 ? (
              <p className="subtle">
                Add the trades you work in so customers can find you by category.
              </p>
            ) : (
              <div className="stack-sm">
                {profile.skills.map((skill) => (
                  <div key={skill.id} className="row-between card card-tight">
                    <div>
                      <strong style={{ fontSize: 'var(--text-sm)' }}>{skill.skill_name}</strong>
                      <p className="subtle">
                        {skill.category_name} · {skill.experience_years} years
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      aria-label={`Remove ${skill.skill_name}`}
                      onClick={() => removeSkill.mutate(skill.id)}
                    >
                      <Trash2 size={14} />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {profile?.hourly_rate_cents ? (
              <p className="subtle">
                Customers see your rate as {formatKes(profile.hourly_rate_cents)} per hour.
              </p>
            ) : null}
          </section>
        </>
      )}

      {verifying && <VerificationModal onClose={() => setVerifying(false)} />}
      {addingSkill && <AddSkillModal onClose={() => setAddingSkill(false)} />}
    </div>
  )
}

function VerificationModal({ onClose }: { onClose: () => void }) {
  const { refreshUser } = useAuth()
  const { notify } = useToast()
  const [idNumber, setIdNumber] = useState('')
  const [documentUrl, setDocumentUrl] = useState('')
  const [error, setError] = useState<string | null>(null)

  const submit = useMutation({
    mutationFn: () =>
      api.fundis.submitVerification({ id_number: idNumber.trim(), id_document_url: documentUrl.trim() }),
    onSuccess: async () => {
      await refreshUser()
      notify('ID submitted — an admin will review it shortly', 'success')
      onClose()
    },
    onError: (mutationError) =>
      setError(mutationError instanceof ApiError ? mutationError.message : 'Could not submit that.'),
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (idNumber.trim().length < 5) return setError('Enter your national ID number.')
    if (documentUrl.trim().length < 5) return setError('Add a link to a photo of your ID.')
    submit.mutate()
  }

  return (
    <Modal
      title="Verify your identity"
      description="Only admins see these details. They are never shown to customers."
      onClose={onClose}
    >
      <form className="stack" onSubmit={handleSubmit} noValidate>
        {error && <Alert tone="danger">{error}</Alert>}
        <Input
          label="National ID number"
          value={idNumber}
          onChange={(event) => setIdNumber(event.target.value)}
        />
        <Input
          label="Link to ID photo"
          placeholder="https://…"
          hint="Upload the photo to a service you trust and paste the link."
          value={documentUrl}
          onChange={(event) => setDocumentUrl(event.target.value)}
        />
        <div className="modal-actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={submit.isPending}>
            Submit for review
          </Button>
        </div>
      </form>
    </Modal>
  )
}

function AddSkillModal({ onClose }: { onClose: () => void }) {
  const { refreshUser } = useAuth()
  const { notify } = useToast()
  const [categoryId, setCategoryId] = useState('')
  const [skillName, setSkillName] = useState('')
  const [years, setYears] = useState('1')
  const [error, setError] = useState<string | null>(null)

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => api.categories.list(),
    staleTime: 5 * 60_000,
  })

  const submit = useMutation({
    mutationFn: () =>
      api.fundis.addSkill({
        category_id: categoryId,
        skill_name: skillName.trim(),
        experience_years: Number(years) || 1,
      }),
    onSuccess: async () => {
      await refreshUser()
      notify('Skill added', 'success')
      onClose()
    },
    onError: (mutationError) =>
      setError(mutationError instanceof ApiError ? mutationError.message : 'Could not add that skill.'),
  })

  return (
    <Modal title="Add a skill" onClose={onClose}>
      <form
        className="stack"
        onSubmit={(event) => {
          event.preventDefault()
          setError(null)
          if (!categoryId) return setError('Choose a trade category.')
          if (skillName.trim().length < 2) return setError('Name the skill.')
          submit.mutate()
        }}
        noValidate
      >
        {error && <Alert tone="danger">{error}</Alert>}

        <Select
          label="Trade category"
          value={categoryId}
          onChange={(event) => {
            setCategoryId(event.target.value)
            const match = categories?.find((category) => category.id === event.target.value)
            if (match && !skillName) setSkillName(match.name)
          }}
        >
          <option value="">Choose…</option>
          {categories?.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </Select>

        <Input
          label="Skill name"
          placeholder="Pipe fitting"
          value={skillName}
          onChange={(event) => setSkillName(event.target.value)}
        />

        <div className="field">
          <label>Years doing this</label>
          <input
            className="input numeric"
            type="number"
            min={0}
            max={60}
            value={years}
            onChange={(event) => setYears(event.target.value)}
          />
        </div>

        <div className="modal-actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={submit.isPending}>
            Add skill
          </Button>
        </div>
      </form>
    </Modal>
  )
}
