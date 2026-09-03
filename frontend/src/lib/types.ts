// Mirrors the `to_dict()` serializers in server/models/. Money always arrives as
// integer minor units (`*_cents`); the `*_kes` fields are convenience only and are
// never used for arithmetic on this side either.

export type Role = 'customer' | 'fundi' | 'admin'

export type VerificationStatus = 'pending' | 'verified' | 'rejected'

export type BookingStatus =
  | 'pending'
  | 'accepted_unpaid'
  | 'escrow_funded'
  | 'in_progress'
  | 'awaiting_confirm'
  | 'completed'
  | 'declined'
  | 'cancelled'
  | 'disputed'

export type EscrowStatus = 'pending' | 'held_in_escrow' | 'released' | 'refunded' | 'disputed' | 'failed'

export type ServiceRequestStatus = 'open' | 'matched' | 'cancelled' | 'closed'

export type QuoteStatus = 'pending' | 'accepted' | 'declined'

export type DisputeStatus = 'open' | 'under_review' | 'resolved_refund' | 'resolved_payout'

export interface Pagination {
  page: number
  per_page: number
  total_items: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface Skill {
  id: string
  category_id: string
  category_name: string | null
  category_slug: string | null
  skill_name: string
  experience_years: number
  certification_url: string | null
}

export interface FundiProfile {
  id: string
  user_id: string
  business_name: string | null
  bio: string | null
  experience_years: number
  verification_status: VerificationStatus
  verified_at: string | null
  location_name: string | null
  latitude: number | null
  longitude: number | null
  service_radius_km: number
  hourly_rate_cents: number | null
  hourly_rate_kes: number | null
  is_available: boolean
  rating_avg: number
  rating_count: number
  jobs_completed: number
  created_at: string | null
  skills?: Skill[]
  /** Owner/admin-only fields — returned by /auth/me and admin review, never publicly. */
  verification_notes?: string | null
  id_number?: string | null
  id_document_url?: string | null
}

/** A search hit: a fundi profile plus the joined user fields and computed distance. */
export interface FundiSearchResult extends FundiProfile {
  fundi_name: string | null
  avatar_url: string | null
  distance_km: number | null
}

/** The public detail view, which merges user fields and recent reviews into the profile. */
export interface FundiDetail extends FundiProfile {
  full_name: string
  phone: string
  avatar_url: string | null
  recent_reviews: Review[]
}

export interface User {
  id: string
  email: string
  phone: string
  role: Role
  full_name: string
  avatar_url: string | null
  is_active: boolean
  created_at: string | null
  fundi_profile?: FundiProfile
}

export interface Category {
  id: string
  name: string
  slug: string
  description: string | null
  icon: string | null
  is_active: boolean
}

export interface Booking {
  id: string
  customer_id: string
  customer_name: string | null
  customer_phone: string | null
  fundi_id: string
  fundi_name: string | null
  fundi_phone: string | null
  service_request_id: string | null
  title: string
  description: string | null
  agreed_amount_cents: number
  platform_fee_cents: number
  fundi_amount_cents: number
  status: BookingStatus
  location_name: string
  latitude: number | null
  longitude: number | null
  scheduled_for: string | null
  started_at: string | null
  completed_at: string | null
  cancelled_at: string | null
  created_at: string | null
  has_review: boolean
  has_dispute: boolean
  escrow_status: EscrowStatus | null
}

export interface Escrow {
  id: string
  booking_id: string
  customer_id: string
  fundi_id: string
  amount_cents: number
  platform_fee_cents: number
  fundi_payout_cents: number
  status: EscrowStatus
  mpesa_receipt_number: string | null
  payment_phone: string | null
  funded_at: string | null
  released_at: string | null
  refunded_at: string | null
  created_at: string | null
}

export interface Quote {
  id: string
  service_request_id: string
  fundi_id: string
  fundi_name: string | null
  fundi_rating: number | null
  amount_cents: number
  estimated_hours: number | null
  notes: string | null
  status: QuoteStatus
  created_at: string | null
}

export interface ServiceRequest {
  id: string
  customer_id: string
  customer_name: string | null
  customer_phone: string | null
  category_id: string
  category_name: string | null
  title: string
  description: string
  location_name: string
  latitude: number | null
  longitude: number | null
  budget_min_cents: number | null
  budget_max_cents: number | null
  preferred_date: string | null
  status: ServiceRequestStatus
  created_at: string | null
  quote_count: number
  quotes?: Quote[]
}

export interface Review {
  id: string
  booking_id: string
  customer_id: string
  customer_name: string | null
  fundi_id: string
  rating: number
  review_text: string | null
  created_at: string | null
}

export interface Dispute {
  id: string
  booking_id: string
  initiated_by_id: string
  initiator_name: string | null
  reason: string
  customer_statement: string | null
  fundi_statement: string | null
  resolution: string | null
  resolved_by_id: string | null
  status: DisputeStatus
  created_at: string | null
  resolved_at: string | null
}

export interface Wallet {
  id: string
  user_id: string
  balance_cents: number
  currency: string
  is_frozen: boolean
  updated_at: string | null
}

export interface WalletTransaction {
  id: string
  wallet_id: string
  type: 'escrow_payout' | 'withdrawal' | 'refund' | 'adjustment'
  amount_cents: number
  balance_after_cents: number
  reference: string | null
  status: 'completed' | 'pending' | 'failed'
  description: string | null
  created_at: string | null
}

export interface Message {
  id: string
  conversation_id: string
  sender_id: string
  sender_name: string | null
  content: string
  read_at: string | null
  created_at: string | null
}

export interface Conversation {
  id: string
  customer_id: string
  customer_name: string | null
  fundi_id: string
  fundi_name: string | null
  booking_id: string | null
  last_message_at: string | null
  created_at: string | null
  messages?: Message[]
}

export interface Notification {
  id: string
  user_id: string
  title: string
  message: string
  type: 'booking' | 'escrow' | 'dispute' | 'message' | 'system'
  data_json: string | null
  is_read: boolean
  created_at: string | null
}

export interface AdminMetrics {
  users: {
    total: number
    customers: number
    fundis: number
    verified_fundis: number
    pending_verifications: number
  }
  bookings: { total: number; completed: number; open_disputes: number }
  financials: {
    total_gmv_kes: number
    total_revenue_commission_kes: number
    funds_held_in_escrow_kes: number
  }
}

export interface PendingFundi extends FundiProfile {
  user_name: string | null
  email: string | null
  phone: string | null
}
