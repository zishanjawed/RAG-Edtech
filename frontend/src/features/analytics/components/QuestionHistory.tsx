/**
 * Question History Component
 * Shows list of previous questions with type classification
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MessageSquare, Clock, Tag } from 'lucide-react'
import { DataTable, Spinner, EmptyState } from '@/components/ui'
import type { Column } from '@/components/ui/DataTable'
import { analyticsService } from '@/api/analytics.service'
import type { Question } from '@/api/types'

interface QuestionHistoryProps {
  contentId: string
}

export function QuestionHistory({ contentId }: QuestionHistoryProps) {
  const [limit] = useState(50)

  const { data, isLoading, error } = useQuery({
    queryKey: ['content-questions', contentId, limit],
    queryFn: () => analyticsService.getContentQuestions(contentId, limit),
    enabled: !!contentId,
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const columns: Column<Question>[] = [
    {
      key: 'question_text',
      label: 'Question',
      sortable: true,
      render: (value) => (
        <div className="max-w-md truncate" title={String(value)}>
          {String(value)}
        </div>
      ),
    },
    {
      key: 'question_type',
      label: 'Type',
      sortable: true,
      render: (value) => (
        <span className="inline-flex items-center gap-1 rounded-full bg-primary-50 px-2.5 py-0.5 text-xs font-medium text-primary-700">
          <Tag className="h-3 w-3" />
          {String(value || 'general')}
        </span>
      ),
    },
    {
      key: 'timestamp',
      label: 'Date',
      sortable: true,
      render: (value) => (
        <span className="text-sm text-slate-600">{formatDate(String(value))}</span>
      ),
    },
    {
      key: 'response_time_ms',
      label: 'Response Time',
      sortable: true,
      render: (value) => (
        <span className="inline-flex items-center gap-1 text-sm text-slate-600">
          <Clock className="h-3 w-3" />
          {Number(value)}ms
        </span>
      ),
    },
    {
      key: 'cached',
      label: 'Cached',
      sortable: true,
      render: (value) => (
        <span
          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
            value ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-50 text-slate-700'
          }`}
        >
          {value ? 'Yes' : 'No'}
        </span>
      ),
    },
  ]

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error || !data || data.questions.length === 0) {
    return (
      <EmptyState
        icon={MessageSquare}
        title="No Questions Yet"
        description="Questions asked about this document will appear here."
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900">Question History</h2>
        <span className="text-sm text-slate-600">{data.total} total questions</span>
      </div>
      <DataTable<Question>
        data={data.questions}
        columns={columns}
        searchable
        searchPlaceholder="Search questions..."
      />
    </div>
  )
}

