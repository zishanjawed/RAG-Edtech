/**
 * Question Type Chart Component
 * Visualizes question type distribution with pie chart
 */
import { useQuery } from '@tanstack/react-query'
import { PieChart as PieChartIcon } from 'lucide-react'
import { PieChart } from '@/components/charts'
import { Spinner, EmptyState, Card, CardBody } from '@/components/ui'
import { analyticsService } from '@/api/analytics.service'

interface QuestionTypeChartProps {
  contentId: string
}

export function QuestionTypeChart({ contentId }: QuestionTypeChartProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['question-types', contentId],
    queryFn: () => analyticsService.getQuestionTypes(contentId),
    enabled: !!contentId,
  })

  if (isLoading) {
    return (
      <Card>
        <CardBody>
          <div className="flex h-64 items-center justify-center">
            <Spinner size="lg" />
          </div>
        </CardBody>
      </Card>
    )
  }

  if (error || !data || data.question_types.length === 0) {
    return (
      <Card>
        <CardBody>
          <EmptyState
            icon={PieChartIcon}
            title="No Question Data"
            description="Question type distribution will appear after questions are asked."
          />
        </CardBody>
      </Card>
    )
  }

  const chartData = data.question_types.map((qt) => ({
    name: qt.type.charAt(0).toUpperCase() + qt.type.slice(1),
    value: qt.count,
  }))

  return (
    <Card>
      <CardBody>
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Question Types</h3>
            <p className="text-sm text-slate-600">Distribution of {data.total_questions} questions</p>
          </div>

          <PieChart data={chartData} height={300} />

          <div className="mt-4 space-y-2">
            {data.question_types.map((qt) => (
              <div
                key={qt.type}
                className="flex items-center justify-between rounded-lg border border-slate-100 p-3"
              >
                <div>
                  <span className="font-medium text-slate-900">
                    {qt.type.charAt(0).toUpperCase() + qt.type.slice(1)}
                  </span>
                  <span className="ml-2 text-sm text-slate-600">({qt.percentage}%)</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-slate-900">{qt.count} questions</p>
                  <p className="text-xs text-slate-500">Avg: {qt.avg_response_time_ms}ms</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardBody>
    </Card>
  )
}

