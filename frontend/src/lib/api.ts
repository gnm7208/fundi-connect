import type {
  AdminMetrics,
  Booking,
  BookingStatus,
  Category,
  Conversation,
  Dispute,
  Escrow,
  FundiDetail,
  FundiSearchResult,
  Notification,
  Pagination,
  PendingFundi,
  Review,
  Role,
  ServiceRequest,
  User,
  Wallet,
  WalletTransaction,
} from './types'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

const ACCESS_TOKEN_KEY = 'fundi.access_token'
const REFRESH_TOKEN_KEY = 'fundi.refresh_token'

// The API also sets httpOnly cookies, which are what protect the session on a
// same-origin deploy. Bearer tokens are kept as well so the app still authenticates
// when the frontend is served from a different origin than the API, where the
// production cookie policy (SameSite=Strict) would drop them.
export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },
  set(access: string | null, refresh?: string | null) {
    if (access) localStorage.setItem(ACCESS_TOKEN_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

/** Field-level validation errors as returned by the Marshmallow boundary. */
export type FieldErrors = Record<string, string[]>

export class ApiError extends Error {
  status: number
  fields: FieldErrors

  constructor(message: string, status: number, fields: FieldErrors = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fields = fields
  }

  /** First validation message for a field, if the server rejected it. */
  fieldError(name: string): string | undefined {
    return this.fields[name]?.[0]
  }
}

type RequestOptions = {
  method?: string
  body?: unknown
  /** Set for the refresh call itself, so a failed refresh cannot recurse. */
  skipRefresh?: boolean
  auth?: 'access' | 'refresh'
}

let refreshInFlight: Promise<boolean> | null = null

async function attemptRefresh(): Promise<boolean> {
  if (!tokenStore.refresh) return false

  // Collapse parallel 401s into a single refresh so a dashboard firing five
  // queries at once does not fire five refreshes and race itself.
  refreshInFlight ??= (async () => {
    try {
      const data = await request<{ access_token: string }>('/auth/refresh', {
        method: 'POST',
        skipRefresh: true,
        auth: 'refresh',
      })
      tokenStore.set(data.access_token)
      return true
    } catch {
      tokenStore.clear()
      return false
    } finally {
      refreshInFlight = null
    }
  })()

  return refreshInFlight
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, skipRefresh = false, auth = 'access' } = options

  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  const token = auth === 'refresh' ? tokenStore.refresh : tokenStore.access
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  if (response.status === 401 && !skipRefresh) {
    if (await attemptRefresh()) {
      return request<T>(path, { ...options, skipRefresh: true })
    }
  }

  if (response.status === 204) return undefined as T

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      (payload && (payload.error || payload.message)) ||
      `Request failed (${response.status})`
    throw new ApiError(message, response.status, payload?.fields ?? {})
  }

  return payload as T
}

function query(params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value))
    }
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

export interface RegisterPayload {
  email: string
  phone: string
  password: string
  full_name: string
  role: Role
  business_name?: string
  location_name?: string
  category_id?: string
  hourly_rate_cents?: number
}

export interface FundiSearchParams {
  q?: string
  category?: string
  lat?: number
  lng?: number
  radius_km?: number
  verified_only?: boolean
  min_rating?: number
  sort?: 'rating' | 'distance' | 'jobs' | 'rate_asc' | 'rate_desc'
  page?: number
  per_page?: number
}

type SessionResponse = { user: User; access_token: string; refresh_token: string }

export interface HealthStatus {
  status: string
  service: string
  version: string
  database: string
  environment: string
  payments: 'simulated' | 'live'
}

export const api = {
  /** Unauthenticated; also tells the UI whether this instance moves real money. */
  async health() {
    const response = await fetch(`${API_BASE_URL.replace(/\/v1$/, '')}/health`, {
      headers: { Accept: 'application/json' },
    })
    if (!response.ok) throw new ApiError('Health check failed', response.status)
    return (await response.json()) as HealthStatus
  },

  auth: {
    async register(payload: RegisterPayload) {
      const data = await request<SessionResponse>('/auth/register', {
        method: 'POST',
        body: payload,
      })
      tokenStore.set(data.access_token, data.refresh_token)
      return data.user
    },
    async login(emailOrPhone: string, password: string) {
      const data = await request<SessionResponse>('/auth/login', {
        method: 'POST',
        body: { email_or_phone: emailOrPhone, password },
      })
      tokenStore.set(data.access_token, data.refresh_token)
      return data.user
    },
    async logout() {
      try {
        await request('/auth/logout', { method: 'POST' })
      } finally {
        tokenStore.clear()
      }
    },
    async me() {
      const data = await request<{ user: User }>('/auth/me')
      return data.user
    },
    async updateProfile(payload: { full_name?: string; phone?: string; avatar_url?: string }) {
      const data = await request<{ user: User }>('/auth/me', { method: 'PATCH', body: payload })
      return data.user
    },
    /** Erases the account; the server refuses (409) while jobs or money are in flight. */
    async deleteAccount(password: string) {
      await request('/auth/me', { method: 'DELETE', body: { password } })
      // Only once the server has actually deleted the account.
      tokenStore.clear()
    },
  },

  categories: {
    async list() {
      const data = await request<{ categories: Category[] }>('/categories')
      return data.categories
    },
  },

  fundis: {
    async search(params: FundiSearchParams) {
      return request<{ fundis: FundiSearchResult[]; count: number; pagination: Pagination }>(
        `/fundis/search${query({ ...params })}`,
      )
    },
    async detail(fundiId: string) {
      const data = await request<{ fundi: FundiDetail }>(`/fundis/${fundiId}`)
      return data.fundi
    },
    async updateProfile(payload: Record<string, unknown>) {
      const data = await request<{ fundi_profile: FundiDetail }>('/fundis/profile', {
        method: 'PATCH',
        body: payload,
      })
      return data.fundi_profile
    },
    async addSkill(payload: { category_id: string; skill_name: string; experience_years?: number }) {
      return request('/fundis/skills', { method: 'POST', body: payload })
    },
    async removeSkill(skillId: string) {
      return request(`/fundis/skills/${skillId}`, { method: 'DELETE' })
    },
    async submitVerification(payload: { id_number: string; id_document_url: string }) {
      return request<{ verification_status: string }>('/fundis/verify-id', {
        method: 'POST',
        body: payload,
      })
    },
    async reviews(fundiId: string) {
      return request<{ reviews: Review[]; rating_avg: number; rating_count: number }>(
        `/reviews/fundi/${fundiId}`,
      )
    },
  },

  serviceRequests: {
    async list(params: { status?: string; category_id?: string; page?: number } = {}) {
      return request<{ service_requests: ServiceRequest[]; pagination: Pagination }>(
        `/service-requests${query(params)}`,
      )
    },
    async detail(id: string) {
      const data = await request<{ service_request: ServiceRequest }>(`/service-requests/${id}`)
      return data.service_request
    },
    async create(payload: {
      category_id: string
      title: string
      description: string
      location_name: string
      budget_min_cents?: number
      budget_max_cents?: number
      preferred_date?: string
    }) {
      const data = await request<{ service_request: ServiceRequest }>('/service-requests', {
        method: 'POST',
        body: payload,
      })
      return data.service_request
    },
    async submitQuote(
      requestId: string,
      payload: { amount_cents: number; estimated_hours?: number; notes?: string },
    ) {
      return request(`/service-requests/${requestId}/quotes`, { method: 'POST', body: payload })
    },
    async acceptQuote(requestId: string, quoteId: string) {
      const data = await request<{ booking: Booking }>(
        `/service-requests/${requestId}/quotes/${quoteId}/accept`,
        { method: 'POST' },
      )
      return data.booking
    },
  },

  bookings: {
    async list(params: { status?: string; page?: number; per_page?: number } = {}) {
      return request<{ bookings: Booking[]; pagination: Pagination }>(`/bookings${query(params)}`)
    },
    async detail(id: string) {
      const data = await request<{ booking: Booking }>(`/bookings/${id}`)
      return data.booking
    },
    async create(payload: {
      fundi_id: string
      title: string
      description?: string
      agreed_amount_cents: number
      location_name: string
      scheduled_for?: string
    }) {
      const data = await request<{ booking: Booking }>('/bookings', { method: 'POST', body: payload })
      return data.booking
    },
    async updateStatus(id: string, status: BookingStatus, notes?: string) {
      const data = await request<{ booking: Booking }>(`/bookings/${id}/status`, {
        method: 'PATCH',
        body: { status, notes },
      })
      return data.booking
    },
    async confirmCompletion(id: string) {
      const data = await request<{ booking: Booking }>(`/bookings/${id}/confirm`, { method: 'POST' })
      return data.booking
    },
  },

  payments: {
    async initiateStkPush(bookingId: string, phoneNumber: string) {
      return request<{ message: string; checkout_request_id: string; escrow: Escrow }>(
        '/payments/stk-push',
        { method: 'POST', body: { booking_id: bookingId, phone_number: phoneNumber } },
      )
    },
    /** Demo-only: stands in for the customer entering their M-PESA PIN. */
    async simulateConfirmation(checkoutRequestId: string) {
      return request<{ escrow: Escrow; booking_status: BookingStatus }>(
        '/payments/simulate-callback',
        { method: 'POST', body: { checkout_request_id: checkoutRequestId } },
      )
    },
    async status(checkoutRequestId: string) {
      const data = await request<{ escrow: Escrow }>(`/payments/status/${checkoutRequestId}`)
      return data.escrow
    },
  },

  escrow: {
    async forBooking(bookingId: string) {
      const data = await request<{ escrow: Escrow }>(`/escrow/booking/${bookingId}`)
      return data.escrow
    },
  },

  reviews: {
    async create(payload: { booking_id: string; rating: number; review_text?: string }) {
      const data = await request<{ review: Review }>('/reviews', { method: 'POST', body: payload })
      return data.review
    },
  },

  disputes: {
    async create(payload: { booking_id: string; reason: string; customer_statement: string }) {
      const data = await request<{ dispute: Dispute }>('/disputes', { method: 'POST', body: payload })
      return data.dispute
    },
    async detail(id: string) {
      const data = await request<{ dispute: Dispute }>(`/disputes/${id}`)
      return data.dispute
    },
    async respond(id: string, fundiStatement: string) {
      return request(`/disputes/${id}/respond`, {
        method: 'POST',
        body: { fundi_statement: fundiStatement },
      })
    },
  },

  wallet: {
    async me() {
      const data = await request<{ wallet: Wallet }>('/wallets/me')
      return data.wallet
    },
    async transactions(page = 1) {
      return request<{
        transactions: WalletTransaction[]
        balance_kes: number
        pagination: Pagination
      }>(`/wallets/me/transactions${query({ page })}`)
    },
    async requestPayout(amountCents: number, phoneNumber: string) {
      return request<{ message: string }>('/wallets/payout-request', {
        method: 'POST',
        body: { amount_cents: amountCents, phone_number: phoneNumber },
      })
    },
  },

  conversations: {
    async list() {
      const data = await request<{ conversations: Conversation[] }>('/conversations')
      return data.conversations
    },
    async detail(id: string) {
      const data = await request<{ conversation: Conversation }>(`/conversations/${id}`)
      return data.conversation
    },
    async start(payload: { fundi_id: string; booking_id?: string; initial_message?: string }) {
      const data = await request<{ conversation: Conversation }>('/conversations', {
        method: 'POST',
        body: payload,
      })
      return data.conversation
    },
    async send(conversationId: string, content: string) {
      return request(`/conversations/${conversationId}/messages`, {
        method: 'POST',
        body: { content },
      })
    },
  },

  notifications: {
    async list(unreadOnly = false) {
      return request<{
        notifications: Notification[]
        unread_count: number
        pagination: Pagination
      }>(`/notifications${query({ unread_only: unreadOnly || undefined })}`)
    },
    async markRead(id: string) {
      return request(`/notifications/${id}/read`, { method: 'POST' })
    },
    async markAllRead() {
      return request('/notifications/read-all', { method: 'POST' })
    },
  },

  admin: {
    async metrics() {
      return request<AdminMetrics>('/admin/metrics')
    },
    async pendingVerifications() {
      const data = await request<{ pending_fundis: PendingFundi[] }>(
        '/admin/fundis/pending-verification',
      )
      return data.pending_fundis
    },
    async reviewVerification(fundiId: string, status: 'verified' | 'rejected', notes?: string) {
      return request(`/admin/fundis/${fundiId}/verify`, {
        method: 'PATCH',
        body: { status, notes },
      })
    },
    async disputes() {
      const data = await request<{ disputes: Dispute[] }>('/admin/disputes')
      return data.disputes
    },
    async resolveDispute(
      disputeId: string,
      action: 'refund_customer' | 'payout_fundi',
      resolution: string,
    ) {
      return request(`/admin/disputes/${disputeId}/resolve`, {
        method: 'POST',
        body: { action, resolution },
      })
    },
  },
}
