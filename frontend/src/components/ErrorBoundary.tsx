/**
 * ErrorBoundary Component
 * Catches React errors and displays user-friendly message
 */
import { Component, ReactNode, ErrorInfo } from 'react'
import { Card } from './ui/Card'
import { Button } from './ui/Button'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
          <Card className="max-w-md">
            <Card.Body className="text-center space-y-4">
              <div className="flex justify-center">
                <div className="rounded-full bg-red-100 p-3">
                  <AlertTriangle className="h-8 w-8 text-red-600" />
                </div>
              </div>
              
              <div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">
                  Something went wrong
                </h2>
                <p className="text-sm text-slate-600">
                  We encountered an error while loading this page.
                </p>
              </div>

              {this.state.error && (
                <details className="text-left">
                  <summary className="text-sm font-medium text-slate-700 cursor-pointer">
                    Error details
                  </summary>
                  <pre className="mt-2 text-xs text-slate-600 bg-slate-100 p-3 rounded overflow-auto">
                    {this.state.error.message}
                  </pre>
                </details>
              )}

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => window.history.back()}
                >
                  Go Back
                </Button>
                <Button
                  className="flex-1"
                  onClick={this.handleReset}
                >
                  Reload App
                </Button>
              </div>
            </Card.Body>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

