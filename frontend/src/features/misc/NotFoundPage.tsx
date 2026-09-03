import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'

import { Button, EmptyState } from '@/components/ui'

export function NotFoundPage() {
  return (
    <EmptyState
      icon={<Compass size={20} />}
      title="Page not found"
      description="That link does not lead anywhere on Fundi Connect."
      action={
        <Link to="/">
          <Button variant="primary">Go home</Button>
        </Link>
      }
    />
  )
}
