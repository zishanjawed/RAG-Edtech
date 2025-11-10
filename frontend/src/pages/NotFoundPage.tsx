/**
 * NotFoundPage
 * 404 Not Found page
 */
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui'
import { Home } from 'lucide-react'

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-primary-600">404</h1>
        <h2 className="mt-4 text-3xl font-bold text-slate-900">Page Not Found</h2>
        <p className="mt-2 text-lg text-slate-600">
          The page you're looking for doesn't exist.
        </p>
        <Link to="/">
          <Button className="mt-8" size="lg" leftIcon={<Home className="h-5 w-5" />}>
            Back to Home
          </Button>
        </Link>
      </div>
    </div>
  )
}

