import { useRef, useState } from 'react'
import { Camera, Link2, Trash2 } from 'lucide-react'

import { Avatar, Button, Input } from '@/components/ui'
import { uploadImage, uploadsEnabled, UploadError } from '@/lib/uploads'

interface AvatarUploaderProps {
  name: string | null | undefined
  value: string | null
  onChange: (avatarUrl: string | null) => void
}

export function AvatarUploader({ name, value, onChange }: AvatarUploaderProps) {
  const fileInput = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [linkMode, setLinkMode] = useState(false)
  const [link, setLink] = useState('')

  async function handleFile(file: File | undefined) {
    if (!file) return
    setError(null)
    setBusy(true)
    try {
      onChange(await uploadImage(file))
    } catch (uploadError) {
      setError(
        uploadError instanceof UploadError
          ? uploadError.message
          : 'Could not upload that image. Try again.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="stack-sm">
      <div className="avatar-picker">
        <div
          className="avatar-drop"
          onClick={() => uploadsEnabled && fileInput.current?.click()}
          role={uploadsEnabled ? 'button' : undefined}
          tabIndex={uploadsEnabled ? 0 : undefined}
          aria-label={uploadsEnabled ? 'Change profile photo' : undefined}
          onKeyDown={(event) => {
            if (uploadsEnabled && (event.key === 'Enter' || event.key === ' ')) {
              event.preventDefault()
              fileInput.current?.click()
            }
          }}
        >
          <Avatar name={name} src={value} size="xl" />
          {uploadsEnabled && (
            <span className="overlay">
              <Camera size={20} />
            </span>
          )}
        </div>

        <div className="stack-sm">
          <div className="row wrap">
            {uploadsEnabled && (
              <Button
                type="button"
                size="sm"
                loading={busy}
                onClick={() => fileInput.current?.click()}
              >
                <Camera size={14} /> Upload photo
              </Button>
            )}
            <Button type="button" size="sm" variant="ghost" onClick={() => setLinkMode((on) => !on)}>
              <Link2 size={14} /> {linkMode ? 'Cancel link' : 'Use a link'}
            </Button>
            {value && (
              <Button type="button" size="sm" variant="ghost" onClick={() => onChange(null)}>
                <Trash2 size={14} /> Remove
              </Button>
            )}
          </div>
          <p className="hint">
            {uploadsEnabled
              ? 'JPG, PNG or WebP up to 5MB. Square photos look best.'
              : 'Paste a link to a photo of yourself or your work.'}
          </p>
        </div>
      </div>

      {linkMode && (
        <div className="row" style={{ alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <Input
              label="Image link"
              placeholder="https://…"
              value={link}
              onChange={(event) => setLink(event.target.value)}
            />
          </div>
          <Button
            type="button"
            onClick={() => {
              if (!link.trim()) return
              onChange(link.trim())
              setLink('')
              setLinkMode(false)
            }}
          >
            Use
          </Button>
        </div>
      )}

      {error && <span className="error-text">{error}</span>}

      <input
        ref={fileInput}
        type="file"
        accept="image/*"
        className="visually-hidden"
        onChange={(event) => {
          void handleFile(event.target.files?.[0])
          event.target.value = ''
        }}
      />
    </div>
  )
}
