/**
 * Student Dashboard - 2025 Edition
 * Clean analytics page with subtle design and soft shadows
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, MessageSquare, Clock, TrendingUp } from 'lucide-react'
import { motion } from 'framer-motion'
import { TextReveal } from '@/components/animated/TextReveal'
import { Card, CardHeader, CardBody, CardContent } from '@/components/ui/Card'
import { analyticsService } from '@/api/analytics.service'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { cn } from '@/lib/utils'
import { PageShell } from '@/components/layout/PageShell'
import { PageHeader } from '@/components/layout/PageHeader'
import { useNavigate } from 'react-router-dom'
import { AnalyticsDashboardSkeleton } from '../components/AnalyticsSkeleton'

// Clean Metric Card Component (2025)
interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  accentColor?: string
  trend?: string
}

function formatCompactNumber(n: number | string) {
  const num = typeof n === 'string' ? Number(n) : n
  if (Number.isNaN(num)) return n
  return new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(num as number)
}

function MetricCard({ title, value, subtitle, icon, accentColor = 'from-blue-500 to-cyan-500', trend }: MetricCardProps) {
  return (
    <Card className="shadow-soft-md" animated>
      {/* Subtle gradient accent bar */}
      <motion.div 
        className={cn('absolute top-0 left-0 right-0 h-1 bg-gradient-to-r', accentColor)}
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      />
      
      {/* Background gradient on hover */}
      <motion.div 
        className={cn('absolute inset-0 opacity-0 bg-gradient-to-br', accentColor)}
        whileHover={{ opacity: 0.03 }}
        transition={{ duration: 0.3 }}
      />
      
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <h3 className="text-sm font-medium text-muted-foreground">
          {title}
        </h3>
        <motion.div 
          whileHover={{ rotate: 5, scale: 1.1 }}
          className="text-muted-foreground"
        >
          {icon}
        </motion.div>
      </CardHeader>
      <CardContent>
        <motion.div 
          className="text-3xl font-bold"
          initial={{ scale: 1 }}
          whileHover={{ scale: 1.05 }}
        >
          {typeof value === 'number' ? formatCompactNumber(value) : value}
        </motion.div>
        {(subtitle || trend) && (
          <p className="text-xs text-muted-foreground mt-1">
            {trend && <span className="text-green-600">{trend}</span>}
            {trend && subtitle && ' • '}
            {subtitle}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export function StudentDashboard() {
  const { user } = useAuth()
  const [studentId] = useState(user?.id || '')
  const navigate = useNavigate()

  const { data: engagement, isLoading, error } = useQuery({
    queryKey: ['student-engagement', studentId],
    queryFn: () => analyticsService.getStudentEngagement(studentId),
    enabled: !!studentId,
  })

  const formatDate = (dateString: string) => {
    const d = new Date(dateString)
    if (isNaN(d.getTime())) return '—'
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  if (isLoading) {
    return <AnalyticsDashboardSkeleton />
  }

  if (error || !engagement) {
    return (
      <div className="p-6">
        <Card className="flex flex-col items-center justify-center p-12 shadow-soft-md">
          <TrendingUp className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-semibold">No Analytics Available</h3>
          <p className="text-sm text-muted-foreground mt-2 text-center max-w-sm">
            Start asking questions to see your learning analytics
          </p>
        </Card>
      </div>
    )
  }

  return (
    <PageShell className="py-6 space-y-8">
      {/* Header */}
      <TextReveal>
        <PageHeader
          title="Analytics"
          description={`Track your learning progress and activity • ${user?.email ?? ''}`}
        />
      </TextReveal>

      {/* Metrics Grid with staggered animation */}
      <motion.div 
        className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
        variants={{
          hidden: { opacity: 0 },
          show: {
            opacity: 1,
            transition: {
              staggerChildren: 0.1
            }
          }
        }}
        initial="hidden"
        animate="show"
      >
        {[
          {
            title: "Questions Asked",
            value: engagement.total_questions,
            subtitle: "Total questions",
            icon: <MessageSquare className="h-4 w-4" />,
            accentColor: "from-blue-500 to-cyan-500",
            trend: "+12%"
          },
          {
            title: "Content Accessed",
            value: engagement.unique_content_accessed,
            subtitle: "Unique documents",
            icon: <BookOpen className="h-4 w-4" />,
            accentColor: "from-violet-500 to-purple-500"
          },
          {
            title: "Avg Response Time",
            value: `${Math.round(engagement.avg_response_time_ms)}ms`,
            subtitle: "Average AI response",
            icon: <Clock className="h-4 w-4" />,
            accentColor: "from-emerald-500 to-teal-500"
          },
          {
            title: "Last Activity",
            value: formatDate(engagement.last_activity),
            subtitle: engagement.first_activity ? `Since ${formatDate(engagement.first_activity)}` : undefined,
            icon: <TrendingUp className="h-4 w-4" />,
            accentColor: "from-orange-500 to-red-500"
          }
        ].map((metric) => (
          <motion.div
            key={metric.title}
            variants={{
              hidden: { opacity: 0, y: 20 },
              show: { opacity: 1, y: 0 }
            }}
          >
            <MetricCard {...metric} />
          </motion.div>
        ))}
      </motion.div>

      {/* Recent Questions */}
      {engagement.recent_questions && engagement.recent_questions.length > 0 && (
        <Card className="shadow-soft-md">
          <CardHeader>
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-primary" />
              <h2 className="text-xl font-semibold tracking-tight">Recent Questions</h2>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Your latest activity and interactions
            </p>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {engagement.recent_questions.map((q) => (
                <div
                  key={q.question_id}
                  className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-primary/10 p-2">
                      <MessageSquare className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">
                        Question ID: {q.question_id.slice(0, 8)}...
                      </p>
                      <p className="text-xs text-muted-foreground">{formatDate(q.timestamp)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <BookOpen className="h-5 w-5 text-muted-foreground" />
                    <button
                      onClick={() => navigate(`/chat/${q.content_id}`)}
                      className="inline-flex items-center rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90 transition"
                    >
                      Open Chat
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </PageShell>
  )
}
