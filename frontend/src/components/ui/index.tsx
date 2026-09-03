import {
  useEffect,
  useRef,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from 'react'
import { AlertCircle, Loader2, Star, X } from 'lucide-react'

import { initials } from '@/lib/format'

/* ---------- Button ---------- */

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  block?: boolean
}

export function Button({
  variant = 'secondary',
  size = 'md',
  loading = false,
  block = false,
  className = '',
  children,
  disabled,
  ...rest
}: ButtonProps) {
  const classes = [
    'btn',
    `btn-${variant}`,
    size !== 'md' ? `btn-${size}` : '',
    block ? 'btn-block' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <button className={classes} disabled={disabled || loading} {...rest}>
      {loading && <Loader2 size={15} className="spin" aria-hidden />}
      {children}
    </button>
  )
}

/* ---------- Form fields ---------- */

interface FieldWrapProps {
  label: string
  hint?: string
  error?: string
  children: ReactNode
}

function FieldWrap({ label, hint, error, children }: FieldWrapProps) {
  return (
    <div className="field">
      <label>{label}</label>
      {children}
      {error ? <span className="error-text">{error}</span> : hint ? <span className="hint">{hint}</span> : null}
    </div>
  )
}

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  hint?: string
  error?: string
}

export function Input({ label, hint, error, ...rest }: InputProps) {
  return (
    <FieldWrap label={label} hint={hint} error={error}>
      <input className="input" aria-invalid={error ? true : undefined} {...rest} />
    </FieldWrap>
  )
}

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string
  hint?: string
  error?: string
}

export function Textarea({ label, hint, error, ...rest }: TextareaProps) {
  return (
    <FieldWrap label={label} hint={hint} error={error}>
      <textarea className="textarea" aria-invalid={error ? true : undefined} {...rest} />
    </FieldWrap>
  )
}

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label: string
  hint?: string
  error?: string
}

export function Select({ label, hint, error, children, ...rest }: SelectProps) {
  return (
    <FieldWrap label={label} hint={hint} error={error}>
      <select className="select" {...rest}>
        {children}
      </select>
    </FieldWrap>
  )
}

/** Money input in shillings that reports whole-shilling minor units upward. */
export function MoneyInput({
  label,
  valueCents,
  onChangeCents,
  hint,
  error,
  ...rest
}: {
  label: string
  valueCents: number | ''
  onChangeCents: (cents: number | '') => void
  hint?: string
  error?: string
} & Omit<InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'>) {
  return (
    <FieldWrap label={label} hint={hint} error={error}>
      <input
        className="input numeric"
        type="number"
        inputMode="numeric"
        min={0}
        step={1}
        aria-invalid={error ? true : undefined}
        value={valueCents === '' ? '' : valueCents / 100}
        onChange={(event) => {
          const shillings = event.target.value
          onChangeCents(shillings === '' ? '' : Math.round(Number(shillings)) * 100)
        }}
        {...rest}
      />
    </FieldWrap>
  )
}

/* ---------- Badge ---------- */

export function Badge({
  tone = 'neutral',
  children,
}: {
  tone?: 'neutral' | 'progress' | 'success' | 'warning' | 'danger' | 'brand'
  children: ReactNode
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

/* ---------- Avatar ---------- */

export function Avatar({
  name,
  src,
  size = 'md',
}: {
  name: string | null | undefined
  src?: string | null
  size?: 'sm' | 'md' | 'lg' | 'xl'
}) {
  const className = `avatar${size === 'md' ? '' : ` avatar-${size}`}`
  return (
    <div className={className} aria-hidden>
      {src ? <img src={src} alt="" loading="lazy" /> : initials(name)}
    </div>
  )
}

/* ---------- Stars ---------- */

export function Stars({ rating, count }: { rating: number; count?: number }) {
  const rounded = Math.round(rating)
  return (
    <span className="stars" title={`${rating.toFixed(1)} out of 5`}>
      {[1, 2, 3, 4, 5].map((value) => (
        <Star
          key={value}
          size={13}
          fill={value <= rounded ? 'currentColor' : 'none'}
          strokeWidth={value <= rounded ? 0 : 1.6}
          aria-hidden
        />
      ))}
      <span className="subtle" style={{ marginLeft: 4 }}>
        {rating > 0 ? rating.toFixed(1) : 'New'}
        {count !== undefined && count > 0 ? ` (${count})` : ''}
      </span>
    </span>
  )
}

export function StarPicker({
  value,
  onChange,
}: {
  value: number
  onChange: (rating: number) => void
}) {
  return (
    <div className="stars stars-input" role="radiogroup" aria-label="Rating">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          role="radio"
          aria-checked={value === star}
          aria-label={`${star} star${star > 1 ? 's' : ''}`}
          data-on={star <= value}
          onClick={() => onChange(star)}
        >
          <Star size={26} fill={star <= value ? 'currentColor' : 'none'} strokeWidth={1.6} />
        </button>
      ))}
    </div>
  )
}

/* ---------- Feedback ---------- */

export function Alert({
  tone = 'info',
  children,
}: {
  tone?: 'info' | 'danger' | 'success' | 'warning'
  children: ReactNode
}) {
  return (
    <div className={`alert alert-${tone}`} role={tone === 'danger' ? 'alert' : undefined}>
      <AlertCircle size={16} aria-hidden />
      <div>{children}</div>
    </div>
  )
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: ReactNode
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <div>
        <strong>{title}</strong>
        {description && <p className="subtle">{description}</p>}
      </div>
      {action}
    </div>
  )
}

export function SkeletonCard() {
  return (
    <div className="card stack-sm" aria-hidden>
      <div className="row">
        <div className="skeleton" style={{ width: 40, height: 40, borderRadius: 999 }} />
        <div className="stack-sm" style={{ flex: 1 }}>
          <div className="skeleton" style={{ height: 12, width: '55%' }} />
          <div className="skeleton" style={{ height: 10, width: '35%' }} />
        </div>
      </div>
      <div className="skeleton" style={{ height: 10, width: '90%' }} />
      <div className="skeleton" style={{ height: 10, width: '70%' }} />
    </div>
  )
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="grid-cards">
      {Array.from({ length: count }, (_, index) => (
        <SkeletonCard key={index} />
      ))}
    </div>
  )
}

/* ---------- Modal ---------- */

export function Modal({
  title,
  description,
  onClose,
  children,
  footer,
}: {
  title: string
  description?: string
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
}) {
  const panel = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)

    const { overflow } = document.body.style
    document.body.style.overflow = 'hidden'
    panel.current?.focus()

    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = overflow
    }
  }, [onClose])

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        ref={panel}
      >
        <div className="modal-head">
          <div>
            <h2>{title}</h2>
            {description && <p className="subtle">{description}</p>}
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>
        {children}
        {footer && <div className="modal-actions">{footer}</div>}
      </div>
    </div>
  )
}
