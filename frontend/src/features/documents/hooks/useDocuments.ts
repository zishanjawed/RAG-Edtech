/**
 * useDocuments Hook
 * React Query for fetching documents
 */
import { useQuery } from '@tanstack/react-query'
import { documentsService } from '@/api/documents.service'

export function useDocuments(userId: string) {
  return useQuery({
    queryKey: ['documents', userId],
    queryFn: () => documentsService.getDocuments(userId),
    enabled: !!userId,
  })
}

