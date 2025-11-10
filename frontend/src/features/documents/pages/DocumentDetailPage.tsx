/**
 * Document Detail Page
 * Shows document stats and question analytics
 */
import { useParams, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FileText, Users, MessageSquare, TrendingUp, Trash2, Calendar, AlertTriangle } from 'lucide-react'
import { Button, MetricCard, Spinner, EmptyState, Card } from '@/components/ui'
import { QuestionHistory } from '@/features/analytics/components/QuestionHistory'
import { QuestionTypeChart } from '@/features/analytics/components/QuestionTypeChart'
import { analyticsService } from '@/api/analytics.service'
import { documentsService } from '@/api/documents.service'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useToast } from '@/hooks/useToast'

export function DocumentDetailPage() {
  const { documentId } = useParams<{ documentId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const { data: document, isLoading: docLoading } = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => documentsService.getDocument(documentId!),
    enabled: !!documentId,
  })

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['content-stats', documentId],
    queryFn: () => analyticsService.getContentStats(documentId!),
    enabled: !!documentId,
  })

  const deleteMutation = useMutation({
    mutationFn: () => documentsService.deleteDocument(documentId!),
    onSuccess: () => {
      toast({
        type: 'success',
        title: 'Document deleted',
        description: 'The document has been removed from your library.',
      })
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      navigate('/analytics')
    },
    onError: (error: Error) => {
      toast({
        type: 'error',
        title: 'Deletion failed',
        description: error.message || 'Failed to delete document',
      })
    },
  })

  const canDelete = user && document && (
    user.role === 'teacher' ||
    document.user_id === user.id ||
    document.original_uploader_id === user.id ||
    document.upload_history?.some(entry => entry.user_id === user.id)
  )

  const handleDelete = () => {
    setShowDeleteConfirm(true)
  }

  const confirmDelete = () => {
    deleteMutation.mutate()
    setShowDeleteConfirm(false)
  }

  const isLoading = docLoading || statsLoading

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!document) {
    return (
      <EmptyState
        icon={FileText}
        title="Document Not Found"
        description="The document you're looking for doesn't exist."
        action={{
          label: 'Go Back',
          onClick: () => navigate(-1),
        }}
      />
    )
  }

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
            <h1 className="text-3xl font-bold text-slate-900">{document.title}</h1>
            <p className="mt-1 text-slate-600">
              {document.subject} - Grade {document.grade_level}
            </p>
          </div>
        </div>
        {canDelete && (
          <Button
            variant="outline"
            size="sm"
            leftIcon={<Trash2 className="h-4 w-4" />}
            onClick={handleDelete}
            className="text-red-600 hover:bg-red-50 border-red-300"
          >
            Delete Document
          </Button>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="max-w-md">
            <Card.Header>
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-6 w-6 text-red-600" />
                <h3 className="text-lg font-semibold">Delete Document?</h3>
              </div>
            </Card.Header>
            <Card.Body>
              <p className="text-sm text-slate-600 mb-4">
                This will permanently delete the document, all its vectors, and related questions. This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={deleteMutation.isPending}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  className="flex-1"
                  onClick={confirmDelete}
                  isLoading={deleteMutation.isPending}
                >
                  Delete
                </Button>
              </div>
            </Card.Body>
          </Card>
        </div>
      )}

      {stats && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Questions"
            value={stats.total_questions}
            icon={<MessageSquare className="h-6 w-6" />}
          />
          <MetricCard
            title="Unique Students"
            value={stats.unique_students}
            icon={<Users className="h-6 w-6" />}
          />
          <MetricCard
            title="Avg Response Time"
            value={`${Math.round(stats.avg_response_time_ms)}ms`}
            icon={<TrendingUp className="h-6 w-6" />}
          />
          <MetricCard
            title="Cache Hit Rate"
            value={`${Math.round(stats.cache_hit_rate * 100)}%`}
            subtitle={`${stats.total_cached_responses} cached`}
            icon={<FileText className="h-6 w-6" />}
          />
        </div>
      )}

      {/* Upload History */}
      {document.upload_history && document.upload_history.length > 0 && (
        <Card>
          <Card.Header>
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              <h3 className="text-lg font-semibold">Upload History</h3>
            </div>
            <p className="text-sm text-slate-600 mt-1">
              This document has been uploaded {document.upload_history.length} time(s) by {new Set(document.upload_history.map(h => h.user_name)).size} user(s)
            </p>
          </Card.Header>
          <Card.Body>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-slate-200 bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-slate-700">Uploader</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-700">Filename</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-700">Upload Date</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-700">Content Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {document.upload_history.map((entry, index) => (
                    <tr key={index} className="hover:bg-slate-50">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4 text-slate-400" />
                          <span className="font-medium">{entry.user_name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-slate-400" />
                          {entry.filename}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-slate-400" />
                          {new Date(entry.upload_date).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">
                        {entry.content_hash.substring(0, 16)}...
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card.Body>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <QuestionTypeChart contentId={documentId!} />
        </div>
        <div className="lg:col-span-2">
          <QuestionHistory contentId={documentId!} />
        </div>
      </div>
    </div>
  )
}

