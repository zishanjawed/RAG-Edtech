/**
 * Teacher Dashboard - 2025 Edition
 * Clean professional dashboard with subtle design
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Users, MessageSquare, TrendingUp, BookOpen, Activity, Plus } from 'lucide-react'
import { TextReveal } from '@/components/animated/TextReveal'
import { Card, CardHeader, CardBody, CardContent, Button, Avatar } from '@/components/ui'
import { Skeleton } from '@/components/ui/skeleton'
import { BarChart } from '@/components/charts'
import { teacherService } from '@/api/teacher.service'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { cn } from '@/lib/utils'
import { PageShell } from '@/components/layout/PageShell'
import { PageHeader } from '@/components/layout/PageHeader'

// Clean Metric Card (2025)
interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  accentColor?: string
}

function formatCompactNumber(n: number | string) {
  const num = typeof n === 'string' ? Number(n) : n
  if (Number.isNaN(num)) return n
  return new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(num as number)
}

function MetricCard({ title, value, subtitle, icon, accentColor = 'from-blue-500 to-cyan-500' }: MetricCardProps) {
  return (
    <Card className="shadow-soft-md hover:shadow-soft-lg transition-all hover:-translate-y-1">
      {/* Subtle gradient accent bar */}
      <div className={cn('absolute top-0 left-0 right-0 h-1 bg-gradient-to-r', accentColor)} />
      
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <h3 className="text-sm font-medium text-muted-foreground">
          {title}
        </h3>
        <div className="text-muted-foreground">
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold">{typeof value === 'number' ? formatCompactNumber(value) : value}</div>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1">
            {subtitle}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export function TeacherDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [teacherId] = useState(user?.id || '')

  const { data: overview, isLoading, error } = useQuery({
    queryKey: ['teacher-overview', teacherId],
    queryFn: () => teacherService.getTeacherOverview(teacherId),
    enabled: !!teacherId,
  })

  const formatDate = (dateString: string) => {
    const d = new Date(dateString)
    if (isNaN(d.getTime())) return '—'
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getInitials = (id: string) => {
    return id.slice(0, 2).toUpperCase()
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-20 w-full" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="p-6">
              <Skeleton className="h-12 w-12 mb-4 rounded-xl" />
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-8 w-16" />
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error || !overview) {
    return (
      <div className="p-6">
        <Card className="flex flex-col items-center justify-center p-12 shadow-soft-md">
          <Users className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-semibold">No Data Available</h3>
          <p className="text-sm text-muted-foreground mt-2 text-center max-w-sm">
            Start by having students upload content and ask questions
          </p>
        </Card>
      </div>
    )
  }

  const chartData = (overview.top_contents || []).slice(0, 5).map((content) => ({
    name: content.content_title || `Content ${(content.content_id || '').slice(0, 8)}`,
    questions: content.question_count,
    students: content.student_count,
  }))

  return (
    <PageShell className="py-6 space-y-6">
      {/* Header */}
      <TextReveal>
        <PageHeader
          title="Dashboard"
          description={`Welcome back! Here's what's happening with your class • ${user?.email ?? ''}`}
          actions={
            <Button variant="default" className="gap-2">
              <Plus className="h-4 w-4" />
              New Assignment
            </Button>
          }
        />
      </TextReveal>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          title="Total Students"
          value={overview.overview.total_students}
          subtitle="Active learners"
          icon={<Users className="h-4 w-4" />}
          accentColor="from-blue-500 to-cyan-500"
        />
        
        <MetricCard
          title="Total Questions"
          value={overview.overview.total_questions}
          subtitle="Class engagement"
          icon={<MessageSquare className="h-4 w-4" />}
          accentColor="from-violet-500 to-purple-500"
        />
        
        <MetricCard
          title="Avg Questions"
          value={overview.overview.avg_questions_per_student.toFixed(1)}
          subtitle="Per student"
          icon={<TrendingUp className="h-4 w-4" />}
          accentColor="from-emerald-500 to-teal-500"
        />
      </div>

      {/* Charts & Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top Content Chart */}
        <Card className="shadow-soft-md">
          <CardHeader>
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-primary" />
              <h2 className="text-xl font-semibold tracking-tight">Top Content by Usage</h2>
            </div>
            <p className="text-sm text-muted-foreground mt-1">Most accessed learning materials</p>
          </CardHeader>
          <CardBody className="pt-4">
            <BarChart
              data={chartData}
              xKey="name"
              bars={[
                { key: 'questions', color: 'hsl(var(--primary))', name: 'Questions' },
                { key: 'students', color: '#10b981', name: 'Students' },
              ]}
              height={300}
            />
            <div className="mt-6 space-y-2">
              {(overview.top_contents || []).slice(0, 5).map((c) => (
                <div
                  key={c.content_id}
                  className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="rounded-md bg-primary/10 p-2">
                      <BookOpen className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">
                        {c.content_title || `Content ${(c.content_id || '').slice(0, 8)}`}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {c.question_count} questions • {c.student_count} students
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => navigate(`/chat/${c.content_id}`)}
                    className="inline-flex items-center rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90 transition"
                  >
                    Open Chat
                  </button>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Recent Activity */}
        <Card className="shadow-soft-md">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-semibold tracking-tight">Recent Activity</h2>
                </div>
                <p className="text-sm text-muted-foreground mt-1">Latest student interactions</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/teacher/students')}
              >
                View All
              </Button>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {(overview.recent_students || []).slice(0, 5).map((student) => (
                <div
                  key={student._id || student.student_id || Math.random()}
                  className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted/50 cursor-pointer"
                  onClick={() => navigate('/teacher/students')}
                >
                  <div className="flex items-center gap-3">
                    <Avatar
                      name={student.student_name || getInitials(student._id || student.student_id || 'U')}
                      size="md"
                      className="bg-primary/10 text-primary"
                    />
                    <div>
                      <p className="font-medium">
                        {student.student_name || `Student ${(student._id || student.student_id || '').slice(0, 8)}`}
                      </p>
                      <p className="text-xs text-muted-foreground">{formatDate(student.last_activity)}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-primary">{student.total_questions}</p>
                    <p className="text-xs text-muted-foreground">questions</p>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>
    </PageShell>
  )
}
