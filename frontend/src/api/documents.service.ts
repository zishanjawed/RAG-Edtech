/**
 * Documents Service
 * API calls for document management
 */
import { apiClient, createFormData } from './client'
import type { Document, DocumentUploadRequest, DocumentUploadResponse, DocumentListResponse, DocumentFilter } from './types'

export const documentsService = {
  /**
   * Upload a document
   */
  async uploadDocument(request: DocumentUploadRequest): Promise<DocumentUploadResponse> {
    const formData = createFormData(request as unknown as Record<string, unknown>)

    const response = await apiClient.post<DocumentUploadResponse>(
      '/api/content/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    return response.data
  },

  /**
   * Get user's documents with filters
   */
  async getDocuments(
    userId: string,
    filter: DocumentFilter = 'all',
    search?: string,
    subjects?: string[],
    tags?: string[]
  ): Promise<Document[]> {
    const params = new URLSearchParams()
    params.append('filter', filter)
    if (search) params.append('search', search)
    if (subjects && subjects.length > 0) params.append('subjects', subjects.join(','))
    if (tags && tags.length > 0) params.append('tags', tags.join(','))

    const response = await apiClient.get<DocumentListResponse>(
      `/api/content/user/${userId}?${params.toString()}`
    )
    return response.data.documents || []
  },

  /**
   * Get single document
   */
  async getDocument(contentId: string): Promise<Document> {
    const response = await apiClient.get<Document>(`/api/content/${contentId}`)
    return response.data
  },

  /**
   * Delete document
   */
  async deleteDocument(contentId: string, userId: string): Promise<void> {
    await apiClient.delete(`/api/content/${contentId}?user_id=${userId}`)
  },

  /**
   * Get suggested prompts for a document
   */
  async getDocumentPrompts(contentId: string): Promise<any> {
    const response = await apiClient.get(`/api/prompts/document/${contentId}`)
    return response.data
  },

  /**
   * Get global chat prompts
   */
  async getGlobalPrompts(userId: string): Promise<any> {
    const response = await apiClient.get(`/api/prompts/global?user_id=${userId}`)
    return response.data
  },
}

