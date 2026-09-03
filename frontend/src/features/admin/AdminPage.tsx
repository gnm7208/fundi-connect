import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart3, Gavel, ShieldCheck } from 'lucide-react'

import { api } from '@/lib/api'
import { formatKesCompact } from '@/lib/format'
import { AdminDisputes } from '@/features/admin/AdminDisputes'
import { AdminVerifications } from '@/features/admin/AdminVerifications'

const TABS = [
  { key: 'overview', label: 'Overview', icon: BarChart3 },
  { key: 'verifications', label: 'Verifications', icon: ShieldCheck },
  { key: 'disputes', label: 'Disputes', icon: Gavel },
] as const

export function AdminPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]['key']>('overview')

  const { data: metrics, isPending } = useQuery({
    queryKey: ['admin', 'metrics'],
    queryFn: () => api.admin.metrics(),
  })

  return (
    <div className="stack-lg">
      <div className="page-head">
        <h1>Admin console</h1>
        <p className="muted">Platform health, fundi verification and dispute arbitration.</p>
      </div>

      <div className="tabs" role="tablist">
        {TABS.map((item) => {
          const pending =
            item.key === 'verifications'
              ? metrics?.users.pending_verifications
              : item.key === 'disputes'
                ? metrics?.bookings.open_disputes
                : undefined
          return (
            <button
              key={item.key}
              className="tab"
              role="tab"
              aria-selected={tab === item.key}
              onClick={() => setTab(item.key)}
            >
              {item.label}
              {pending ? ` (${pending})` : ''}
            </button>
          )
        })}
      </div>

      {tab === 'overview' && (
        <div className="stack-lg">
          <section>
            <div className="section-title">
              <h2>Money</h2>
              <span className="subtle">All figures in KES</span>
            </div>
            <div className="grid-stats">
              <div className="stat">
                <span className="label">Completed GMV</span>
                <p className="value numeric">
                  {isPending ? '—' : formatKesCompact((metrics?.financials.total_gmv_kes ?? 0) * 100)}
                </p>
              </div>
              <div className="stat">
                <span className="label">Commission earned</span>
                <p className="value brand numeric">
                  {isPending
                    ? '—'
                    : formatKesCompact((metrics?.financials.total_revenue_commission_kes ?? 0) * 100)}
                </p>
              </div>
              <div className="stat">
                <span className="label">Held in escrow</span>
                <p className="value numeric">
                  {isPending
                    ? '—'
                    : formatKesCompact((metrics?.financials.funds_held_in_escrow_kes ?? 0) * 100)}
                </p>
              </div>
            </div>
          </section>

          <section>
            <div className="section-title">
              <h2>People</h2>
            </div>
            <div className="grid-stats">
              <div className="stat">
                <span className="label">Total users</span>
                <p className="value numeric">{metrics?.users.total ?? '—'}</p>
              </div>
              <div className="stat">
                <span className="label">Customers</span>
                <p className="value numeric">{metrics?.users.customers ?? '—'}</p>
              </div>
              <div className="stat">
                <span className="label">Fundis</span>
                <p className="value numeric">{metrics?.users.fundis ?? '—'}</p>
              </div>
              <div className="stat">
                <span className="label">Verified fundis</span>
                <p className="value numeric">{metrics?.users.verified_fundis ?? '—'}</p>
              </div>
            </div>
          </section>

          <section>
            <div className="section-title">
              <h2>Jobs</h2>
            </div>
            <div className="grid-stats">
              <div className="stat">
                <span className="label">Total bookings</span>
                <p className="value numeric">{metrics?.bookings.total ?? '—'}</p>
              </div>
              <div className="stat">
                <span className="label">Completed</span>
                <p className="value numeric">{metrics?.bookings.completed ?? '—'}</p>
              </div>
              <div className="stat">
                <span className="label">Open disputes</span>
                <p className="value numeric" style={{ color: metrics?.bookings.open_disputes ? 'var(--danger-500)' : undefined }}>
                  {metrics?.bookings.open_disputes ?? '—'}
                </p>
              </div>
              <div className="stat">
                <span className="label">Awaiting verification</span>
                <p className="value numeric">{metrics?.users.pending_verifications ?? '—'}</p>
              </div>
            </div>
          </section>
        </div>
      )}

      {tab === 'verifications' && <AdminVerifications />}
      {tab === 'disputes' && <AdminDisputes />}
    </div>
  )
}
