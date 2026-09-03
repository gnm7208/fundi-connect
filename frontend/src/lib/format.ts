import type { BookingStatus, EscrowStatus } from './types'

const kes = new Intl.NumberFormat('en-KE', {
  style: 'currency',
  currency: 'KES',
  maximumFractionDigits: 0,
})

/** Format integer minor units as KES. Amounts are whole shillings by API contract. */
export function formatKes(cents: number | null | undefined): string {
  if (cents === null || cents === undefined) return '—'
  return kes.format(cents / 100)
}

/** Compact form for dense surfaces: KES 1.2M, KES 45K. */
export function formatKesCompact(cents: number | null | undefined): string {
  if (cents === null || cents === undefined) return '—'
  const shillings = cents / 100
  if (Math.abs(shillings) >= 1_000_000) return `KES ${(shillings / 1_000_000).toFixed(1)}M`
  if (Math.abs(shillings) >= 10_000) return `KES ${Math.round(shillings / 1000)}K`
  return kes.format(shillings)
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-KE', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-KE', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const relative = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return '—'
  const seconds = (new Date(iso).getTime() - Date.now()) / 1000
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ['year', 31_536_000],
    ['month', 2_592_000],
    ['week', 604_800],
    ['day', 86_400],
    ['hour', 3600],
    ['minute', 60],
  ]
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) return relative.format(Math.round(seconds / size), unit)
  }
  return 'just now'
}

export function formatDistance(km: number | null | undefined): string | null {
  if (km === null || km === undefined) return null
  if (km < 1) return `${Math.round(km * 1000)} m away`
  return `${km.toFixed(1)} km away`
}

type Tone = 'neutral' | 'progress' | 'success' | 'warning' | 'danger'

/** Plain-language labels — a customer should never read a raw enum like `accepted_unpaid`. */
export const BOOKING_STATUS: Record<BookingStatus, { label: string; tone: Tone }> = {
  pending: { label: 'Awaiting fundi', tone: 'neutral' },
  accepted_unpaid: { label: 'Accepted — pay to start', tone: 'warning' },
  escrow_funded: { label: 'Paid & secured', tone: 'progress' },
  in_progress: { label: 'Work in progress', tone: 'progress' },
  awaiting_confirm: { label: 'Confirm to release', tone: 'warning' },
  completed: { label: 'Completed', tone: 'success' },
  declined: { label: 'Declined', tone: 'neutral' },
  cancelled: { label: 'Cancelled', tone: 'neutral' },
  disputed: { label: 'In dispute', tone: 'danger' },
}

export const ESCROW_STATUS: Record<EscrowStatus, { label: string; tone: Tone }> = {
  pending: { label: 'Not funded', tone: 'neutral' },
  held_in_escrow: { label: 'Held in escrow', tone: 'progress' },
  released: { label: 'Released to fundi', tone: 'success' },
  refunded: { label: 'Refunded to you', tone: 'neutral' },
  disputed: { label: 'Frozen — in dispute', tone: 'danger' },
  failed: { label: 'Payment failed', tone: 'danger' },
}

export function initials(name: string | null | undefined): string {
  if (!name) return '?'
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

/** Kenyan mobile numbers, matching the server's normalizer. */
export function isValidKenyanPhone(phone: string): boolean {
  const cleaned = phone.replace(/[\s\-()+]/g, '')
  return (
    /^0[17]\d{8}$/.test(cleaned) || /^254[17]\d{8}$/.test(cleaned) || /^[17]\d{8}$/.test(cleaned)
  )
}
