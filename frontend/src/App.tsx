import { useEffect, useMemo, useState, type Dispatch, type FormEvent, type ReactNode, type SetStateAction } from 'react'
import {
  Briefcase,
  Building2,
  CheckCircle2,
  CircleDollarSign,
  CreditCard,
  Landmark,
  LayoutGrid,
  MessageSquareText,
  Search,
  ShieldCheck,
  Star,
  UserRound,
  Wallet,
} from 'lucide-react'
import { NavLink, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { MOCK_BOOKINGS, type Booking, type FundiProfile } from './data/mockData'
import { fetchFundis, loginUser, type LoginRequest } from './lib/api'
import './App.css'

type UserSession = {
  id: number
  name: string
  email: string
  role: 'customer' | 'fundi' | 'admin'
}

type ServiceRequestForm = {
  title: string
  category: string
  location: string
  budget: string
}

const demoUsers: Record<UserSession['role'], UserSession> = {
  customer: {
    id: 1,
    name: 'Jane Customer',
    email: 'customer@fundiconnect.co.ke',
    role: 'customer',
  },
  fundi: {
    id: 2,
    name: 'Mwangi Fundi',
    email: 'fundi@fundiconnect.co.ke',
    role: 'fundi',
  },
  admin: {
    id: 3,
    name: 'Platform Admin',
    email: 'admin@fundiconnect.co.ke',
    role: 'admin',
  },
}

function App() {
  const [session, setSession] = useState<UserSession | null>(null)
  const [fundis, setFundis] = useState<FundiProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [bookings, setBookings] = useState<Booking[]>(MOCK_BOOKINGS)

  useEffect(() => {
    let ignore = false

    const loadFundis = async () => {
      try {
        const data = await fetchFundis()
        if (!ignore) {
          setFundis(data)
        }
      } finally {
        if (!ignore) {
          setLoading(false)
        }
      }
    }

    loadFundis()

    return () => {
      ignore = true
    }
  }, [])

  const handleLogin = async (payload: LoginRequest) => {
    const response = await loginUser(payload)
    const nextUser = (response.user as UserSession) ?? demoUsers[payload.role]
    setSession(nextUser)
    return nextUser
  }

  const handleLogout = () => {
    setSession(null)
  }

  const handleCreateBooking = (nextBooking: Booking) => {
    setBookings((current) => [nextBooking, ...current])
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-mark">F</div>
          <div>
            <p className="eyebrow">Trusted local helpers</p>
            <h1>Fundi Connect</h1>
          </div>
        </div>

        <nav className="main-nav" aria-label="Main navigation">
          <NavLink to="/">Home</NavLink>
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/bookings">Bookings</NavLink>
          <NavLink to="/wallet">Wallet</NavLink>
          {session?.role === 'admin' ? <NavLink to="/admin">Admin</NavLink> : null}
        </nav>

        <div className="topbar-actions">
          {session ? (
            <>
              <div className="user-pill">
                <UserRound size={16} />
                {session.name}
              </div>
              <button className="ghost-button" onClick={handleLogout} type="button">
                Log out
              </button>
            </>
          ) : (
            <NavLink className="primary-button" to="/login">
              Sign in
            </NavLink>
          )}
        </div>
      </header>

      <main className="page-content">
        <Routes>
          <Route
            path="/"
            element={<HomePage fundis={fundis} loading={loading} session={session} onCreateBooking={handleCreateBooking} />}
          />
          <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
          <Route path="/dashboard" element={session ? <DashboardPage session={session} /> : <Navigate to="/login" replace />} />
          <Route
            path="/bookings"
            element={
              session ? <BookingsPage session={session} bookings={bookings} onUpdateBooking={setBookings} /> : <Navigate to="/login" replace />
            }
          />
          <Route path="/wallet" element={session ? <WalletPage session={session} /> : <Navigate to="/login" replace />} />
          <Route path="/admin" element={session?.role === 'admin' ? <AdminPage session={session} /> : <Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

function HomePage({
  fundis,
  loading,
  session,
  onCreateBooking,
}: {
  fundis: FundiProfile[]
  loading: boolean
  session: UserSession | null
  onCreateBooking: (booking: Booking) => void
}) {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [requestOpen, setRequestOpen] = useState(false)
  const [selectedFundi, setSelectedFundi] = useState<FundiProfile | null>(null)
  const [requestForm, setRequestForm] = useState<ServiceRequestForm>({
    title: 'Bathroom pipe leak repair',
    category: 'Plumbing',
    location: 'Kilimani, Nairobi',
    budget: '6500',
  })

  const filteredFundis = useMemo(() => {
    const query = searchTerm.trim().toLowerCase()

    if (!query) {
      return fundis
    }

    return fundis.filter(
      (fundi) =>
        fundi.name.toLowerCase().includes(query) ||
        fundi.skill.toLowerCase().includes(query) ||
        fundi.estate.toLowerCase().includes(query),
    )
  }, [fundis, searchTerm])

  const handleCreateRequest = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!session) {
      navigate('/login')
      return
    }

    const title = requestForm.title.trim() || `${requestForm.category} service request`
    const budget = Number(requestForm.budget || 0)

    const nextBooking: Booking = {
      id: Date.now(),
      title,
      customer: session.name,
      date: 'Today, 9:00 AM',
      status: 'Requested',
      amount: `KES ${budget.toLocaleString()}`,
      fundi: 'Pending assignment',
    }

    onCreateBooking(nextBooking)
    setRequestOpen(false)
    navigate('/bookings')
  }

  const handleBookNow = (fundi: FundiProfile) => {
    if (!session) {
      navigate('/login')
      return
    }

    const nextBooking: Booking = {
      id: Date.now(),
      title: `${fundi.skill} service`,
      customer: session.name,
      date: 'Today, 2:00 PM',
      status: 'Requested',
      amount: `KES ${(fundi.hourlyRate * 2).toLocaleString()}`,
      fundi: fundi.name,
    }

    onCreateBooking(nextBooking)
    navigate('/bookings')
  }

  const handleBrowseCategories = () => {
    setSearchTerm('plumbing')
    document.getElementById('fundi-list')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const handleViewMatchingFundis = () => {
    document.getElementById('fundi-list')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <>
      {requestOpen ? (
        <div className="modal-backdrop" onClick={() => setRequestOpen(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="section-heading compact">
              <div>
                <p className="eyebrow">Create request</p>
                <h3>Post a service request</h3>
              </div>
              <button className="ghost-button" type="button" onClick={() => setRequestOpen(false)}>
                Close
              </button>
            </div>

            <form className="request-form" onSubmit={handleCreateRequest}>
              <div className="modal-grid">
                <div className="field-group full">
                  <label htmlFor="request-title">Job title</label>
                  <input
                    id="request-title"
                    value={requestForm.title}
                    onChange={(event) => setRequestForm((current) => ({ ...current, title: event.target.value }))}
                  />
                </div>

                <div className="field-group">
                  <label htmlFor="request-category">Category</label>
                  <select
                    id="request-category"
                    value={requestForm.category}
                    onChange={(event) => setRequestForm((current) => ({ ...current, category: event.target.value }))}
                  >
                    <option value="Plumbing">Plumbing</option>
                    <option value="Electrical">Electrical</option>
                    <option value="Carpentry">Carpentry</option>
                    <option value="Appliance Repair">Appliance Repair</option>
                  </select>
                </div>

                <div className="field-group">
                  <label htmlFor="request-budget">Budget (KES)</label>
                  <input
                    id="request-budget"
                    type="number"
                    value={requestForm.budget}
                    onChange={(event) => setRequestForm((current) => ({ ...current, budget: event.target.value }))}
                  />
                </div>

                <div className="field-group full">
                  <label htmlFor="request-location">Location</label>
                  <input
                    id="request-location"
                    value={requestForm.location}
                    onChange={(event) => setRequestForm((current) => ({ ...current, location: event.target.value }))}
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button className="secondary-button" type="button" onClick={() => setRequestOpen(false)}>
                  Cancel
                </button>
                <button className="primary-button" type="submit">
                  Submit request
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {selectedFundi ? (
        <div className="modal-backdrop" onClick={() => setSelectedFundi(null)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="section-heading compact">
              <div>
                <p className="eyebrow">Profile</p>
                <h3>{selectedFundi.name}</h3>
              </div>
              <button className="ghost-button" type="button" onClick={() => setSelectedFundi(null)}>
                Close
              </button>
            </div>

            <div className="profile-body">
              <p className="muted-text">{selectedFundi.businessName}</p>
              <div className="meta-grid">
                <span>
                  <Building2 size={14} /> {selectedFundi.estate}
                </span>
                <span>
                  <Briefcase size={14} /> {selectedFundi.skill}
                </span>
              </div>
              <p className="bio-copy">{selectedFundi.bio}</p>
              <div className="profile-stats">
                <div>
                  <strong>{selectedFundi.rating.toFixed(1)}</strong>
                  <span>rating</span>
                </div>
                <div>
                  <strong>{selectedFundi.jobsCompleted}</strong>
                  <span>jobs</span>
                </div>
                <div>
                  <strong>KES {selectedFundi.hourlyRate.toLocaleString()}</strong>
                  <span>/hour</span>
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button className="secondary-button" type="button" onClick={() => setSelectedFundi(null)}>
                Back
              </button>
              <button className="primary-button" type="button" onClick={() => handleBookNow(selectedFundi)}>
                Book this fundi
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow accent">Verified workers, secure payments</p>
          <h2>Find trusted help nearby without the guesswork.</h2>
          <p className="muted-text">
            Book plumbers, electricians, carpenters, and repair pros with escrow protection built in for every job.
          </p>

          <div className="action-row">
            <button className="primary-button" type="button" onClick={() => setRequestOpen(true)}>
              Post a service request
            </button>
            <button className="secondary-button" type="button" onClick={handleBrowseCategories}>
              Browse categories
            </button>
          </div>

          <div className="mini-stats">
            <div>
              <strong>3.2k+</strong>
              <span>verified workers</span>
            </div>
            <div>
              <strong>99.2%</strong>
              <span>job completion</span>
            </div>
            <div>
              <strong>KES 24M</strong>
              <span>escrow protected</span>
            </div>
          </div>
        </div>

        <div className="hero-card">
          <div className="card-header-row">
            <span className="status-dot" />
            <span>Open service request</span>
          </div>
          <h3>Emergency plumbing help</h3>
          <div className="job-meta">
            <span>Kilimani, Nairobi</span>
            <span>Within 30 mins</span>
          </div>
          <div className="job-box">
            <p>Estimated budget</p>
            <strong>KES 6,500</strong>
          </div>
          <button className="primary-button full-width" type="button" onClick={handleViewMatchingFundis}>
            View matching fundis
          </button>
        </div>
      </section>

      <section className="search-panel">
        <div className="search-label">
          <Search size={18} />
          <span>Search nearby experts</span>
        </div>
        <div className="search-row">
          <input
            type="text"
            placeholder="Plumber in Kilimani, electrician, carpentry..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
          <button className="primary-button" type="button" onClick={handleViewMatchingFundis}>
            Search
          </button>
        </div>
      </section>

      <section className="section-heading">
        <div>
          <p className="eyebrow">Recommended near you</p>
          <h3>Top-rated fundis</h3>
        </div>
        <button className="secondary-button" type="button" onClick={() => setSearchTerm('')}>
          View all
        </button>
      </section>

      <section id="fundi-list" className="card-grid">
        {loading ? (
          <div className="empty-state">Loading trusted fundis...</div>
        ) : filteredFundis.length === 0 ? (
          <div className="empty-state">No fundis match your current search.</div>
        ) : (
          filteredFundis.map((fundi) => (
            <article className="fundi-card" key={fundi.id}>
              <div className="card-top-row">
                <div>
                  <h4>{fundi.name}</h4>
                  <p>{fundi.businessName}</p>
                </div>
                {fundi.verified ? (
                  <span className="badge success">
                    <ShieldCheck size={14} /> Verified
                  </span>
                ) : (
                  <span className="badge neutral">New</span>
                )}
              </div>

              <div className="rating-row">
                <span className="rating">
                  <Star size={14} fill="currentColor" /> {fundi.rating.toFixed(1)}
                </span>
                <span>{fundi.jobsCompleted} jobs</span>
                <span>{fundi.distanceKm.toFixed(1)} km away</span>
              </div>

              <div className="meta-grid">
                <span>
                  <Building2 size={14} /> {fundi.estate}
                </span>
                <span>
                  <Briefcase size={14} /> {fundi.skill}
                </span>
              </div>

              <p className="bio-copy">{fundi.bio}</p>

              <div className="price-row">
                <div>
                  <small>From</small>
                  <strong>KES {fundi.hourlyRate.toLocaleString()}</strong>
                  <span>/ hour</span>
                </div>
                <span className="response-time">Responds in {fundi.responseTime}</span>
              </div>

              <div className="card-actions">
                <button className="secondary-button" type="button" onClick={() => setSelectedFundi(fundi)}>
                  View profile
                </button>
                <button className="primary-button" type="button" onClick={() => handleBookNow(fundi)}>
                  Book now
                </button>
              </div>
            </article>
          ))
        )}
      </section>
    </>
  )
}

function LoginPage({ onLogin }: { onLogin: (payload: LoginRequest) => Promise<UserSession> }) {
  const navigate = useNavigate()
  const [role, setRole] = useState<UserSession['role']>('customer')
  const [email, setEmail] = useState('customer@fundiconnect.co.ke')
  const [password, setPassword] = useState('password123')
  const [error, setError] = useState('')

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    if (!email || !password) {
      setError('Please provide both email and password.')
      return
    }

    const user = await onLogin({ email, password, role })
    if (user) {
      navigate('/dashboard')
    }
  }

  return (
    <div className="auth-layout">
      <div className="auth-panel">
        <p className="eyebrow accent">Welcome back</p>
        <h2>Sign in to your Fundi Connect account</h2>

        <div className="role-toggle" aria-label="Select role">
          {(['customer', 'fundi', 'admin'] as const).map((option) => (
            <button
              key={option}
              type="button"
              className={role === option ? 'active' : ''}
              onClick={() => setRole(option)}
            >
              {option}
            </button>
          ))}
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Email address
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>

          {error ? <p className="error-text">{error}</p> : null}

          <button className="primary-button full-width" type="submit">
            Sign in
          </button>
        </form>
      </div>

      <div className="auth-side-panel">
        <div className="trust-box">
          <CheckCircle2 size={18} />
          <span>Escrow protected payments</span>
        </div>
        <div className="trust-box">
          <Landmark size={18} />
          <span>Kenyan market-ready workflows</span>
        </div>
        <div className="trust-box">
          <MessageSquareText size={18} />
          <span>Direct chat and booking updates</span>
        </div>
      </div>
    </div>
  )
}

function DashboardPage({ session }: { session: UserSession }) {
  const stats = {
    jobs:
      session.role === 'fundi'
        ? '18 open jobs'
        : session.role === 'admin'
          ? '1,240 platform jobs'
          : '7 active bookings',
    payouts:
      session.role === 'fundi'
        ? 'KES 118,450'
        : session.role === 'admin'
          ? 'KES 4.86M GMV'
          : 'KES 26,300',
    score: session.role === 'admin' ? '98% trust score' : '4.9 service rating',
  }

  return (
    <div className="dashboard-grid">
      <section className="summary-card hero-card wide-card">
        <p className="eyebrow accent">{session.role.toUpperCase()} overview</p>
        <h2>Welcome back, {session.name.split(' ')[0]}.</h2>
        <p className="muted-text">
          {session.role === 'customer'
            ? 'Track your bookings, confirm work, and keep your home services protected by escrow.'
            : session.role === 'fundi'
              ? 'Manage incoming requests, update job status, and keep your wallet moving on schedule.'
              : 'Monitor platform quality, trust scores, and dispute resolution across the marketplace.'}
        </p>
      </section>

      <div className="stat-grid">
        <StatCard icon={<LayoutGrid size={18} />} label="Jobs" value={stats.jobs} />
        <StatCard icon={<Wallet size={18} />} label="Wallet" value={stats.payouts} />
        <StatCard icon={<Star size={18} />} label="Performance" value={stats.score} />
      </div>

      <section className="panel-block">
        <div className="section-heading compact">
          <h3>Recent activity</h3>
        </div>
        <ul className="activity-list">
          <li>
            <span>Leak repair request</span>
            <strong>Kilimani</strong>
          </li>
          <li>
            <span>Escrow marked active</span>
            <strong>KES 6,500</strong>
          </li>
          <li>
            <span>Customer review received</span>
            <strong>5.0 / 5</strong>
          </li>
        </ul>
      </section>

      {session.role === 'admin' ? <AdminPanel /> : null}
    </div>
  )
}

function BookingsPage({
  session,
  bookings,
  onUpdateBooking,
}: {
  session: UserSession
  bookings: Booking[]
  onUpdateBooking: Dispatch<SetStateAction<Booking[]>>
}) {
  const handleAdvanceStatus = (bookingId: number) => {
    onUpdateBooking((current) =>
      current.map((booking) => {
        if (booking.id !== bookingId) {
          return booking
        }

        const nextStatus = {
          Requested: 'Accepted',
          Accepted: 'In progress',
          'In progress': 'Completed',
          Completed: 'Completed',
        } as const

        return { ...booking, status: nextStatus[booking.status] }
      }),
    )
  }

  return (
    <div className="panel-block booking-page">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Bookings</p>
          <h3>
            {session.role === 'fundi'
              ? 'Your job board'
              : session.role === 'admin'
                ? 'Marketplace bookings'
                : 'Your appointments'}
          </h3>
        </div>
      </div>

      <div className="booking-list">
        {bookings.map((booking) => (
          <article className="booking-item" key={booking.id}>
            <div>
              <div className="booking-tag">{booking.status}</div>
              <h4>{booking.title}</h4>
              <p>
                {booking.customer} • {booking.date}
              </p>
            </div>
            <div className="booking-side">
              <strong>{booking.amount}</strong>
              <span>{booking.fundi}</span>
              {booking.status !== 'Completed' ? (
                <button className="secondary-button small-button" type="button" onClick={() => handleAdvanceStatus(booking.id)}>
                  Mark next step
                </button>
              ) : (
                <span className="done-note">Completed</span>
              )}
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}

function WalletPage({ session }: { session: UserSession }) {
  const balance =
    session.role === 'fundi'
      ? 'KES 156,200'
      : session.role === 'admin'
        ? 'KES 2.4M'
        : 'KES 46,900'

  return (
    <div className="wallet-layout">
      <section className="summary-card hero-card">
        <p className="eyebrow accent">
          {session.role === 'fundi' ? 'Earnings' : session.role === 'admin' ? 'Platform treasury' : 'Balance'}
        </p>
        <h2>{balance}</h2>
        <p className="muted-text">Available to approach or keep in escrow for active jobs.</p>
      </section>

      <section className="panel-block">
        <div className="section-heading compact">
          <h3>Quick actions</h3>
        </div>
        <div className="action-grid">
          <button className="secondary-button" type="button">
            <CircleDollarSign size={16} /> Request payout
          </button>
          <button className="secondary-button" type="button">
            <CreditCard size={16} /> View transactions
          </button>
          <button className="secondary-button" type="button">
            <ShieldCheck size={16} /> Escrow details
          </button>
        </div>
      </section>
    </div>
  )
}

function AdminPage({ session }: { session: UserSession }) {
  if (session.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="dashboard-grid">
      <section className="summary-card hero-card wide-card">
        <p className="eyebrow accent">Marketplace overview</p>
        <h2>Admin control center</h2>
        <p className="muted-text">Monitor verification, disputes, and earning activity across the platform.</p>
      </section>

      <div className="stat-grid">
        <StatCard icon={<LayoutGrid size={18} />} label="GMV" value="KES 4.86M" />
        <StatCard icon={<ShieldCheck size={18} />} label="Verified fundis" value="1,482" />
        <StatCard icon={<MessageSquareText size={18} />} label="Open disputes" value="12" />
      </div>

      <AdminPanel />
    </div>
  )
}

function AdminPanel() {
  return (
    <section className="panel-block admin-panel">
      <div className="section-heading compact">
        <h3>Operational review</h3>
      </div>

      <ul className="activity-list">
        <li>
          <span>Fundi verification approvals</span>
          <strong>24 pending</strong>
        </li>
        <li>
          <span>Disputes awaiting resolution</span>
          <strong>7 urgent</strong>
        </li>
        <li>
          <span>Escrow release confirmations</span>
          <strong>38 today</strong>
        </li>
      </ul>
    </section>
  )
}

function StatCard({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <p>{label}</p>
      <strong>{value}</strong>
    </div>
  )
}

export default App
