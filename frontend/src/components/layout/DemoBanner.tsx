import { useQuery } from '@tanstack/react-query'
import { FlaskConical } from 'lucide-react'

import { api } from '@/lib/api'

/** Shown when the API reports simulated payments, so nobody mistakes the demo for
 *  an instance that actually moves money. Silent on a live deployment. */
export function DemoBanner() {
  const { data } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.health(),
    staleTime: 10 * 60_000,
    retry: false,
  })

  if (data?.payments !== 'simulated') return null

  return (
    <div className="demo-banner" role="status">
      <FlaskConical size={14} aria-hidden />
      <span>
        <strong>Demo mode.</strong> M-PESA payments are simulated — no real money moves.
      </span>
    </div>
  )
}
