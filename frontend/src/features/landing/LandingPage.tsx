import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BadgeCheck, HandCoins, Lock, ShieldCheck, Star } from 'lucide-react'

import { Button } from '@/components/ui'
import { api } from '@/lib/api'

const STEPS = [
  {
    title: 'Agree a price',
    body: 'Book a verified fundi directly, or post a job and compare quotes.',
  },
  {
    title: 'Pay into escrow',
    body: 'An M-PESA prompt locks your money with Fundi Connect — not with the fundi.',
  },
  {
    title: 'Work gets done',
    body: 'The fundi starts knowing the money is already there and cannot vanish.',
  },
  {
    title: 'You release payment',
    body: 'Happy with the job? One tap pays the fundi. Unhappy? Open a dispute.',
  },
]

export function LandingPage() {
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => api.categories.list(),
    staleTime: 5 * 60_000,
  })

  return (
    <div className="stack-lg">
      <section className="hero">
        <span className="badge badge-brand">
          <ShieldCheck size={13} /> M-PESA escrow protected
        </span>
        <h1 style={{ marginTop: 'var(--space-4)' }}>Find a fundi you can actually trust.</h1>
        <p>
          Plumbers, electricians, carpenters and mama fua near you — ID-verified, rated by real
          customers, and paid only once the job is done right.
        </p>
        <div className="hero-actions">
          <Link to="/register">
            <Button variant="primary" size="lg">
              Find a fundi
            </Button>
          </Link>
          <Link to="/register?role=fundi">
            <Button size="lg">Work as a fundi</Button>
          </Link>
        </div>

        <div className="trust-strip">
          <div className="trust-item">
            <Lock size={18} aria-hidden />
            <div>
              <h3>Your money is held, not sent</h3>
              <p>Funds sit in escrow until you confirm the work is complete.</p>
            </div>
          </div>
          <div className="trust-item">
            <BadgeCheck size={18} aria-hidden />
            <div>
              <h3>Every fundi is verified</h3>
              <p>National ID checks before a fundi can take escrow-backed jobs.</p>
            </div>
          </div>
          <div className="trust-item">
            <Star size={18} aria-hidden />
            <div>
              <h3>Reviews you can believe</h3>
              <p>Only customers who actually paid for a job can leave a rating.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="card">
        <div className="section-title">
          <h2>How the escrow works</h2>
          <span className="subtle">
            <HandCoins size={13} style={{ display: 'inline', verticalAlign: -2 }} /> 10% platform
            fee on completed jobs
          </span>
        </div>
        <div className="escrow-steps">
          {STEPS.map((step) => (
            <div className="escrow-step" key={step.title}>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      {categories && categories.length > 0 && (
        <section className="card">
          <div className="section-title">
            <h2>Trades on the platform</h2>
          </div>
          <div className="row wrap">
            {categories.map((category) => (
              <span className="chip" key={category.id} aria-pressed={false}>
                {category.name}
              </span>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
