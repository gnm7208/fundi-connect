import { Check, CircleDot, Lock, ShieldCheck, Wrench } from 'lucide-react'

import type { Booking } from '@/lib/types'

const STEPS = [
  {
    key: 'requested',
    icon: CircleDot,
    title: 'Job requested',
    body: 'Waiting for the fundi to accept.',
  },
  {
    key: 'accepted',
    icon: Check,
    title: 'Fundi accepted',
    body: 'Price agreed. Fund the escrow to start.',
  },
  { key: 'funded', icon: Lock, title: 'Money locked in escrow', body: 'Held safely — not yet paid out.' },
  { key: 'working', icon: Wrench, title: 'Work in progress', body: 'The fundi is on the job.' },
  {
    key: 'released',
    icon: ShieldCheck,
    title: 'Confirmed & paid out',
    body: 'Escrow released to the fundi.',
  },
] as const

/** How far along the five-step ladder a booking status sits. */
const REACHED: Record<Booking['status'], number> = {
  pending: 0,
  accepted_unpaid: 1,
  escrow_funded: 2,
  in_progress: 3,
  awaiting_confirm: 3,
  completed: 4,
  disputed: 3,
  declined: 0,
  cancelled: 0,
}

export function BookingTimeline({ booking }: { booking: Booking }) {
  const reached = REACHED[booking.status]
  const finished = booking.status === 'completed'

  return (
    <ol className="timeline">
      {STEPS.map((step, index) => {
        const done = index < reached || (finished && index === reached)
        const current = index === reached && !finished
        const Icon = step.icon

        return (
          <li key={step.key} data-done={done} data-current={current}>
            <span className="dot">
              <Icon size={12} strokeWidth={2.5} aria-hidden />
            </span>
            <div>
              <h4>{step.title}</h4>
              <p>
                {current && booking.status === 'awaiting_confirm'
                  ? 'The fundi says the job is done — confirm to release payment.'
                  : step.body}
              </p>
            </div>
          </li>
        )
      })}
    </ol>
  )
}
