/**
 * DocumentsPage Component
 * Main documents hub with filtering, search, and grid view
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Document, DocumentFiltersState } from '../../../api/types'
import { DocumentFilters } from '../components/DocumentFilters'
import { DocumentCard } from '../components/DocumentCard'
import { UploadDialog } from '../components/UploadDialog'
import { Button } from '../../../components/ui/Button'
import { EmptyState } from '../../../components/ui/EmptyState'
import { Skeleton } from '../../../components/ui/skeleton'
import { Upload, MessageSquareMore, FileText } from 'lucide-react'
import { documentsService } from '../../../api/documents.service'
import { useAuth } from '../../auth/hooks/useAuth'

export function DocumentsPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [filters, setFilters] = useState<DocumentFiltersState>({
    filter: 'all',
    search: '',
    subjects: [],
    tags: [],
  })

  // Load documents when filters change
  useEffect(() => {
    if (user) {
      loadDocuments()
    }
  }, [user, filters])

  const loadDocuments = async () => {
    if (!user) return
    
    setIsLoading(true)
    try {
      // Use real API with filters
      const docs = await documentsService.getDocuments(
        user.id,
        filters.filter,
        filters.search,
        filters.subjects,
        filters.tags
      )
      setDocuments(docs)
    } catch (error) {
      // Handle error silently
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (contentId: string) => {
    if (!user) return
    
    try {
      await documentsService.deleteDocument(contentId, user.id)
      loadDocuments()
    } catch (error) {
      // Handle error silently
    }
  }

  const handleUploadComplete = (document: Document) => {
    setDocuments((prev) => [document, ...prev])
    setUploadDialogOpen(false)
  }

  const handleGlobalChatClick = () => {
    navigate('/chat/global')
  }

  // Get all unique subjects and tags for filter options
  const availableSubjects = Array.from(new Set(documents.map((doc) => doc.subject || doc.metadata?.subject).filter(Boolean)))
  const availableTags = Array.from(
    new Set(documents.flatMap((doc) => doc.tags || []))
  ).slice(0, 20)

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
            <p className="text-muted-foreground mt-1">
              Manage and chat with your knowledge base
            </p>
          </div>
          <div className="flex gap-3">
            <Button onClick={handleGlobalChatClick} variant="outline" size="lg">
              <MessageSquareMore className="h-5 w-5 mr-2" />
              Chat
            </Button>
            <Button onClick={() => setUploadDialogOpen(true)} size="lg">
              <Upload className="h-5 w-5 mr-2" />
              Upload New
            </Button>
          </div>
        </div>

        {/* Filters */}
        <DocumentFilters
          filters={filters}
          onFiltersChange={setFilters}
          availableSubjects={availableSubjects}
          availableTags={availableTags}
        />
      </div>

      {/* Documents Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="space-y-3">
              <Skeleton className="h-[280px] w-full rounded-lg" />
            </div>
          ))}
        </div>
      ) : documents.length === 0 ? (
        <EmptyState
          icon={FileText}
          title={
            filters.search || filters.subjects.length > 0 || filters.tags.length > 0
              ? 'No documents found'
              : filters.filter === 'owned'
              ? 'No documents uploaded yet'
              : filters.filter === 'shared'
              ? 'No shared documents'
              : 'No documents available'
          }
          description={
            filters.search || filters.subjects.length > 0 || filters.tags.length > 0
              ? 'Try adjusting your filters or search terms'
              : filters.filter === 'owned'
              ? 'Upload your first document to get started'
              : filters.filter === 'shared'
              ? 'Documents shared with you will appear here'
              : 'Get started by uploading a document'
          }
          action={
            <Button onClick={() => setUploadDialogOpen(true)}>
              <Upload className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
          }
        />
      ) : (
        <>
          {/* Results count */}
          <div className="mb-4 text-sm text-muted-foreground">
            Showing {documents.length} document{documents.length !== 1 ? 's' : ''}
          </div>

          {/* Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {documents.map((document) => (
              <DocumentCard
                key={document.content_id}
                document={document}
                onDelete={handleDelete}
              />
            ))}
          </div>
        </>
      )}

      {/* Upload Dialog */}
      <UploadDialog
        open={uploadDialogOpen}
        onOpenChange={setUploadDialogOpen}
        onUploadComplete={handleUploadComplete}
      />
    </div>
  )
}

