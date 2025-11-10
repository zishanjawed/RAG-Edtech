/**
 * useDocumentUpload Hook
 * React Query mutation for document upload
 */
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { documentsService } from '@/api/documents.service'
import { useToast } from '@/hooks/useToast'
import { useDocumentStore } from '../stores/documentStore'
import type { DocumentUploadRequest } from '@/api/types'

export function useDocumentUpload() {
  const { success, error } = useToast()
  const navigate = useNavigate()
  const setUploadProgress = useDocumentStore((state) => state.setUploadProgress)

  return useMutation({
    mutationFn: (request: DocumentUploadRequest) => documentsService.uploadDocument(request),
    onSuccess: (data) => {
      setUploadProgress(100)
      success('Upload successful', 'Your document is being processed')
      
      // Navigate to chat page after a brief delay
      setTimeout(() => {
        navigate(`/chat/${data.content_id}`)
      }, 1500)
    },
    onError: (err: Error) => {
      setUploadProgress(0)
      error('Upload failed', err.message || 'Please try again')
    },
  })
}

