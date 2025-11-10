/**
 * Content Engagement Page
 * Detailed analytics for specific content
 */
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, TrendingUp, Users, PieChart as PieChartIcon } from 'lucide-react'
import { Button, MetricCard, Spinner, EmptyState, Card, CardBody } from '@/components/ui'
import { LineChart, PieChart } from '@/components/charts'
import { teacherService } from '@/api/teacher.service'

export function ContentEngagementPage() {
  const { contentId } = useParams<{ contentId: string }>()
  const navigate = useNavigate()

  const { data: engagement, isLoading, error } = useQuery({
    queryKey: ['content-engagement', contentId],
    queryFn: () => teacherService.getContentEngagement(contentId!),
    enabled: !!contentId,
  })

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error || !engagement) {
    return (
      <EmptyState
        icon={TrendingUp}
        title="No Engagement Data"
        description="Content engagement analytics will appear after students interact with the content."
        action={{
          label: 'Go Back',
          onClick: () => navigate(-1),
        }}
      />
    )
  }

  const getEngagementColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'bg-emerald-100 text-emerald-700'
      case 'medium':
        return 'bg-amber-100 text-amber-700'
      case 'low':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-slate-100 text-slate-700'
    }
  }

  const questionTypesData = engagement.question_types.map((qt) => ({
    name: qt.type.charAt(0).toUpperCase() + qt.type.slice(1),
    value: qt.count,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            leftIcon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => navigate(-1)}
          >
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Content Engagement</h1>
            <p className="mt-1 text-slate-600">ID: {contentId}</p>
          </div>
        </div>
        <span
          className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${getEngagementColor(
            engagement.engagement_level
          )}`}
        >
          {engagement.engagement_level.charAt(0).toUpperCase() + engagement.engagement_level.slice(1)} Engagement
        </span>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          title="Total Questions"
          value={engagement.total_questions}
          icon={<TrendingUp className="h-6 w-6" />}
        />
        <MetricCard
          title="Unique Students"
          value={engagement.unique_students}
          icon={<Users className="h-6 w-6" />}
        />
        <MetricCard
          title="Engagement Level"
          value={engagement.engagement_level}
          icon={<PieChartIcon className="h-6 w-6" />}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardBody>
            <h2 className="text-xl font-semibold text-slate-900">Question Trends</h2>
            <p className="text-sm text-slate-600">Activity over time</p>
            <div className="mt-4">
              <LineChart
                data={engagement.question_trends}
                xKey="date"
                lines={[
                  { key: 'count', color: '#4f46e5', name: 'Questions' },
                ]}
                height={300}
              />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <h2 className="text-xl font-semibold text-slate-900">Question Types</h2>
            <p className="text-sm text-slate-600">Distribution by category</p>
            <div className="mt-4">
              <PieChart data={questionTypesData} height={300} />
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardBody>
          <h2 className="text-xl font-semibold text-slate-900">Top Students</h2>
          <p className="text-sm text-slate-600">Most active learners for this content</p>
          <div className="mt-4 space-y-3">
            {engagement.top_students.map((student, index) => (
              <div
                key={student.student_id}
                className="flex items-center justify-between rounded-lg border border-slate-100 p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-primary-600 font-semibold">
                    #{index + 1}
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">
                      Student {student.student_id.slice(0, 12)}...
                    </p>
                    <p className="text-xs text-slate-500">
                      Avg response: {Math.round(student.avg_response_time)}ms
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-slate-900">{student.question_count}</p>
                  <p className="text-xs text-slate-500">questions</p>
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </div>
  )
}

