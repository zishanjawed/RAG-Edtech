/**
 * Mock Documents Data and Services
 * Simulates document management with filtering, search, and upload
 */

import { Document, DocumentFilter, SuggestedPrompt, SourceReference } from '../../../api/types'

// Mock current user ID (replace with actual auth context)
export const MOCK_CURRENT_USER_ID = 'user-001'

// Mock documents data
export const mockDocuments: Document[] = [
  {
    content_id: 'doc-001',
    title: 'IB Chemistry: Stoichiometry',
    file_path: '/uploads/chemistry-stoichiometry.pdf',
    file_type: 'pdf',
    file_size: 2457600,
    user_id: 'user-001',
    instructor_id: 'teacher-001',
    grade_level: 'IB Diploma',
    subject: 'Chemistry',
    status: 'completed',
    chunks_count: 45,
    upload_date: '2025-11-05T10:30:00Z',
    processed_date: '2025-11-05T10:35:00Z',
    content_hash: 'hash-001',
    is_duplicate: false,
    original_uploader_id: 'user-001',
    original_upload_date: '2025-11-05T10:30:00Z',
    upload_history: [
      {
        user_id: 'user-001',
        user_name: 'Tony Stark',
        upload_date: '2025-11-05T10:30:00Z',
        filename: 'chemistry-stoichiometry.pdf',
        content_hash: 'hash-001',
      },
    ],
    version_number: 1,
    tags: ['stoichiometry', 'moles', 'calculations'],
    last_activity: '2025-11-09T14:20:00Z',
    uploader_name: 'Tony Stark',
    is_owned: true,
    is_shared: false,
  },
  {
    content_id: 'doc-002',
    title: 'Organic Chemistry: Functional Groups',
    file_path: '/uploads/organic-functional-groups.pdf',
    file_type: 'pdf',
    file_size: 3145728,
    user_id: 'user-001',
    instructor_id: 'teacher-001',
    grade_level: 'IB Diploma',
    subject: 'Chemistry',
    status: 'completed',
    chunks_count: 67,
    upload_date: '2025-11-01T09:15:00Z',
    processed_date: '2025-11-01T09:22:00Z',
    content_hash: 'hash-002',
    is_duplicate: false,
    original_uploader_id: 'user-001',
    original_upload_date: '2025-11-01T09:15:00Z',
    tags: ['organic chemistry', 'functional groups', 'nomenclature'],
    last_activity: '2025-11-08T16:45:00Z',
    uploader_name: 'Tony Stark',
    is_owned: true,
    is_shared: false,
  },
  {
    content_id: 'doc-003',
    title: 'Thermodynamics and Kinetics',
    file_path: '/uploads/thermodynamics-kinetics.pdf',
    file_type: 'pdf',
    file_size: 4194304,
    user_id: 'user-002',
    instructor_id: 'teacher-001',
    grade_level: 'IB Diploma',
    subject: 'Chemistry',
    status: 'completed',
    chunks_count: 89,
    upload_date: '2025-10-28T14:00:00Z',
    processed_date: '2025-10-28T14:10:00Z',
    content_hash: 'hash-003',
    is_duplicate: false,
    original_uploader_id: 'user-002',
    original_upload_date: '2025-10-28T14:00:00Z',
    upload_history: [
      {
        user_id: 'user-002',
        user_name: 'Peter Parker',
        upload_date: '2025-10-28T14:00:00Z',
        filename: 'thermodynamics-kinetics.pdf',
        content_hash: 'hash-003',
      },
      {
        user_id: 'user-001',
        user_name: 'Tony Stark',
        upload_date: '2025-11-02T11:00:00Z',
        filename: 'thermo-kinetics-notes.pdf',
        content_hash: 'hash-003',
      },
    ],
    tags: ['thermodynamics', 'kinetics', 'energy', 'reaction rates'],
    last_activity: '2025-11-09T10:30:00Z',
    uploader_name: 'Peter Parker',
    is_owned: false,
    is_shared: true,
  },
  {
    content_id: 'doc-004',
    title: 'Electrochemistry Essentials',
    file_path: '/uploads/electrochemistry.pdf',
    file_type: 'pdf',
    file_size: 2621440,
    user_id: 'user-003',
    instructor_id: 'teacher-001',
    grade_level: 'IB Diploma',
    subject: 'Chemistry',
    status: 'completed',
    chunks_count: 53,
    upload_date: '2025-10-25T08:45:00Z',
    processed_date: '2025-10-25T08:52:00Z',
    content_hash: 'hash-004',
    is_duplicate: false,
    original_uploader_id: 'user-003',
    original_upload_date: '2025-10-25T08:45:00Z',
    upload_history: [
      {
        user_id: 'user-003',
        user_name: 'Diana Prince',
        upload_date: '2025-10-25T08:45:00Z',
        filename: 'electrochemistry.pdf',
        content_hash: 'hash-004',
      },
    ],
    tags: ['electrochemistry', 'redox', 'galvanic cells'],
    last_activity: '2025-11-07T13:15:00Z',
    uploader_name: 'Diana Prince',
    is_owned: false,
    is_shared: true,
  },
  {
    content_id: 'doc-005',
    title: 'Atomic Structure and Periodicity',
    file_path: '/uploads/atomic-structure.pdf',
    file_type: 'pdf',
    file_size: 1835008,
    user_id: 'user-001',
    instructor_id: 'teacher-001',
    grade_level: 'IB Diploma',
    subject: 'Chemistry',
    status: 'completed',
    chunks_count: 38,
    upload_date: '2025-10-20T11:30:00Z',
    processed_date: '2025-10-20T11:36:00Z',
    content_hash: 'hash-005',
    is_duplicate: false,
    original_uploader_id: 'user-001',
    original_upload_date: '2025-10-20T11:30:00Z',
    tags: ['atomic structure', 'periodic table', 'electron configuration'],
    last_activity: '2025-11-06T09:20:00Z',
    uploader_name: 'Tony Stark',
    is_owned: true,
    is_shared: false,
  },
  {
    content_id: 'doc-006',
    title: 'Acids and Bases',
    file_path: '/uploads/acids-bases.pdf',
    file_type: 'pdf',
    file_size: 2097152,
    user_id: 'user-001',
    instructor_id: 'teacher-001',
    grade_level: 'IB Diploma',
    subject: 'Chemistry',
    status: 'processing',
    chunks_count: 0,
    upload_date: '2025-11-10T08:00:00Z',
    content_hash: 'hash-006',
    is_duplicate: false,
    original_uploader_id: 'user-001',
    original_upload_date: '2025-11-10T08:00:00Z',
    tags: ['acids', 'bases', 'pH', 'buffers'],
    uploader_name: 'Tony Stark',
    is_owned: true,
    is_shared: false,
  },
]

// Mock sources for answers
export const mockSources: SourceReference[] = [
  {
    source_id: 1,
    document_title: 'IB Chemistry: Stoichiometry',
    uploader_name: 'Tony Stark',
    uploader_id: 'user-001',
    upload_date: '2025-11-05',
    chunk_index: 12,
    similarity_score: 0.94,
  },
  {
    source_id: 2,
    document_title: 'IB Chemistry: Stoichiometry',
    uploader_name: 'Tony Stark',
    uploader_id: 'user-001',
    upload_date: '2025-11-05',
    chunk_index: 15,
    similarity_score: 0.89,
  },
  {
    source_id: 3,
    document_title: 'Organic Chemistry: Functional Groups',
    uploader_name: 'Tony Stark',
    uploader_id: 'user-001',
    upload_date: '2025-11-01',
    chunk_index: 23,
    similarity_score: 0.82,
  },
]

// Suggested prompts templates
export const documentPromptTemplates = {
  chemistry: [
    'Explain the key concepts in this chapter',
    'What are the main definitions I need to know?',
    'Give me practice problems based on this content',
    'How does this topic connect to other chemistry concepts?',
    'What are common mistakes students make with this topic?',
  ],
  math: [
    'Walk me through the problem-solving steps',
    'What formulas should I memorize?',
    'Explain the theory behind these calculations',
    'Show me examples of this concept',
  ],
  default: [
    'Summarize the main points',
    'What should I focus on for the exam?',
    'Explain this in simpler terms',
    'Give me a study guide from this document',
  ],
}

export const globalPromptTemplates = [
  'Compare stoichiometry concepts across my documents',
  'What are the connections between organic and inorganic chemistry?',
  'Create a study plan based on my knowledge base',
  'What topics am I missing in my chemistry notes?',
  'Explain how thermodynamics relates to other concepts',
]

// Service functions
export class MockDocumentService {
  private documents: Document[] = [...mockDocuments]

  async getDocuments(filter: DocumentFilter = 'all', search = ''): Promise<Document[]> {
    // Simulate API delay
    await this.delay(300)

    let filtered = this.documents

    // Apply filter
    if (filter === 'owned') {
      filtered = filtered.filter((doc) => doc.is_owned)
    } else if (filter === 'shared') {
      filtered = filtered.filter((doc) => doc.is_shared)
    }

    // Apply search
    if (search) {
      const searchLower = search.toLowerCase()
      filtered = filtered.filter(
        (doc) =>
          doc.title.toLowerCase().includes(searchLower) ||
          doc.subject.toLowerCase().includes(searchLower) ||
          doc.tags?.some((tag) => tag.toLowerCase().includes(searchLower))
      )
    }

    return filtered
  }

  async getDocumentById(contentId: string): Promise<Document | null> {
    await this.delay(200)
    return this.documents.find((doc) => doc.content_id === contentId) || null
  }

  async uploadDocument(file: File, metadata: Partial<Document>): Promise<Document> {
    await this.delay(1000)

    // Simulate duplicate detection (20% chance)
    const isDuplicate = Math.random() < 0.2

    const newDoc: Document = {
      content_id: `doc-${Date.now()}`,
      title: metadata.title || file.name,
      file_path: `/uploads/${file.name}`,
      file_type: file.type,
      file_size: file.size,
      user_id: MOCK_CURRENT_USER_ID,
      instructor_id: metadata.instructor_id || 'teacher-001',
      grade_level: metadata.grade_level || 'IB Diploma',
      subject: metadata.subject || 'Chemistry',
      status: 'processing',
      chunks_count: 0,
      upload_date: new Date().toISOString(),
      content_hash: `hash-${Date.now()}`,
      is_duplicate: isDuplicate,
      original_uploader_id: MOCK_CURRENT_USER_ID,
      original_upload_date: new Date().toISOString(),
      upload_history: [
        {
          user_id: MOCK_CURRENT_USER_ID,
          user_name: 'Tony Stark',
          upload_date: new Date().toISOString(),
          filename: file.name,
          content_hash: `hash-${Date.now()}`,
        },
      ],
      tags: metadata.tags || [],
      uploader_name: 'Tony Stark',
      is_owned: true,
      is_shared: false,
    }

    this.documents.unshift(newDoc)

    // Simulate processing completion after 3 seconds
    setTimeout(() => {
      const doc = this.documents.find((d) => d.content_id === newDoc.content_id)
      if (doc) {
        doc.status = 'completed'
        doc.chunks_count = Math.floor(Math.random() * 50) + 20
        doc.processed_date = new Date().toISOString()
      }
    }, 3000)

    return newDoc
  }

  async deleteDocument(contentId: string): Promise<void> {
    await this.delay(500)
    this.documents = this.documents.filter((doc) => doc.content_id !== contentId)
  }

  getSuggestedPrompts(document: Document): SuggestedPrompt[] {
    const subjectKey = document.subject.toLowerCase()
    const templates =
      documentPromptTemplates[subjectKey as keyof typeof documentPromptTemplates] ||
      documentPromptTemplates.default

    return templates.map((text, idx) => ({
      id: `prompt-${document.content_id}-${idx}`,
      text,
      category: this.categorizePrompt(text),
    }))
  }

  getGlobalSuggestedPrompts(documents: Document[]): SuggestedPrompt[] {
    const subjects = [...new Set(documents.map((d) => d.subject))]

    return globalPromptTemplates.map((text, idx) => ({
      id: `global-prompt-${idx}`,
      text,
      category: this.categorizePrompt(text),
    }))
  }

  private categorizePrompt(
    text: string
  ): 'definition' | 'explanation' | 'comparison' | 'procedure' | 'application' | 'evaluation' {
    if (text.toLowerCase().includes('what') || text.toLowerCase().includes('define')) {
      return 'definition'
    }
    if (text.toLowerCase().includes('explain') || text.toLowerCase().includes('why')) {
      return 'explanation'
    }
    if (text.toLowerCase().includes('compare') || text.toLowerCase().includes('difference')) {
      return 'comparison'
    }
    if (text.toLowerCase().includes('how') || text.toLowerCase().includes('steps')) {
      return 'procedure'
    }
    if (text.toLowerCase().includes('apply') || text.toLowerCase().includes('solve')) {
      return 'application'
    }
    if (text.toLowerCase().includes('analyze') || text.toLowerCase().includes('evaluate')) {
      return 'evaluation'
    }
    return 'explanation'
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }
}

// Export singleton instance
export const mockDocumentService = new MockDocumentService()

