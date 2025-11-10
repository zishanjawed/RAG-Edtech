/**
 * Document Store
 * Global document state management
 */
import { create } from 'zustand'
import { documentsService } from '@/api/documents.service'
import type { Document } from '@/api/types'

type UploadStage = 'uploading' | 'extracting' | 'chunking' | 'embedding' | 'finalizing' | 'complete' | 'error'

interface DocumentState {
  documents: Document[]
  selectedDocument: Document | null
  uploadProgress: number
  uploadStage: UploadStage
  uploadError: string | null
  isLoading: boolean

  // Actions
  fetchDocuments: (userId: string) => Promise<void>
  selectDocument: (document: Document | null) => void
  setUploadProgress: (progress: number) => void
  setUploadStage: (stage: UploadStage) => void
  setUploadError: (error: string | null) => void
  clearSelection: () => void
  resetUpload: () => void
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  selectedDocument: null,
  uploadProgress: 0,
  uploadStage: 'uploading',
  uploadError: null,
  isLoading: false,

  fetchDocuments: async (userId: string) => {
    set({ isLoading: true })
    try {
      const documents = await documentsService.getDocuments(userId)
      set({ documents, isLoading: false })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },

  selectDocument: (document) => set({ selectedDocument: document }),

  setUploadProgress: (progress) => set({ uploadProgress: progress }),

  setUploadStage: (stage) => set({ uploadStage: stage }),

  setUploadError: (error) => set({ uploadError: error, uploadStage: 'error' }),

  clearSelection: () => set({ selectedDocument: null }),

  resetUpload: () => set({ 
    uploadProgress: 0, 
    uploadStage: 'uploading', 
    uploadError: null 
  }),
}))

