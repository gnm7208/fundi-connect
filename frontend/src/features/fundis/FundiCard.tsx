import { Link } from 'react-router-dom'
import { BadgeCheck, Briefcase, MapPin } from 'lucide-react'

import { Avatar, Stars } from '@/components/ui'
import { formatDistance, formatKes } from '@/lib/format'
import type { FundiSearchResult } from '@/lib/types'

export function FundiCard({ fundi }: { fundi: FundiSearchResult }) {
  const distance = formatDistance(fundi.distance_km)
  const trades = fundi.skills?.map((skill) => skill.category_name).filter(Boolean) ?? []

  return (
    <Link to={`/fundis/${fundi.user_id}`} className="card card-interactive fundi-card">
      <div className="fundi-card-head">
        <Avatar name={fundi.fundi_name} src={fundi.avatar_url} />
        <div style={{ minWidth: 0, flex: 1 }}>
          <h3>
            {fundi.fundi_name ?? fundi.business_name ?? 'Fundi'}
            {fundi.verification_status === 'verified' && (
              <BadgeCheck size={15} className="verified-tick" aria-label="Verified" />
            )}
          </h3>
          <p className="subtle">{fundi.business_name ?? trades[0] ?? 'General services'}</p>
        </div>
        <Stars rating={fundi.rating_avg} count={fundi.rating_count} />
      </div>

      {fundi.bio && (
        <p className="subtle" style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {fundi.bio}
        </p>
      )}

      <div className="fundi-meta">
        {fundi.location_name && (
          <span>
            <MapPin size={13} aria-hidden />
            {fundi.location_name}
            {distance ? ` · ${distance}` : ''}
          </span>
        )}
        <span>
          <Briefcase size={13} aria-hidden />
          {fundi.jobs_completed} job{fundi.jobs_completed === 1 ? '' : 's'} done
        </span>
      </div>

      <div className="fundi-card-foot">
        <span className="rate">
          {fundi.hourly_rate_cents ? formatKes(fundi.hourly_rate_cents) : 'Rate on request'}
          {fundi.hourly_rate_cents ? <small> /hr</small> : null}
        </span>
        <span className={`badge badge-${fundi.is_available ? 'success' : 'neutral'}`}>
          {fundi.is_available ? 'Available' : 'Busy'}
        </span>
      </div>
    </Link>
  )
}
