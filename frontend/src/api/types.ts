/**
 * API Types
 * TypeScript interfaces for all API requests and responses
 */

// Common types
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

// User types
export interface User {
  id: string
  email: string
  full_name: string
  role: 'student' | 'teacher'
  createdAt: string
  updatedAt: string
}

// Auth types
export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
  role: 'student' | 'teacher'
}

export interface RegisterResponse {
  user: User
  message: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface RefreshTokenResponse {
  access_token: string
  token_type: string
}

// Document types
export interface UploadHistoryEntry {
  user_id: string
  user_name: string
  upload_date: string
  filename: string
  content_hash: string
}

export interface Document {
  content_id: string
  title: string
  file_path: string
  file_type: string
  file_size: number
  user_id: string
  instructor_id: string
  grade_level: string
  subject: string
  status: 'processing' | 'completed' | 'failed'
  chunks_count?: number
  upload_date: string
  processed_date?: string
  // Deduplication fields
  content_hash?: string
  is_duplicate?: boolean
  // Traceability fields
  original_uploader_id?: string
  original_upload_date?: string
  upload_history?: UploadHistoryEntry[]
  version_number?: number
  parent_content_id?: string
  // UI helper fields
  tags?: string[]
  last_activity?: string
  uploader_name?: string
  is_owned?: boolean
  is_shared?: boolean
}

export interface DocumentUploadRequest {
  file: File
  title: string
  user_id: string
  instructor_id: string
  grade_level: string
  subject: string
}

export interface DocumentUploadResponse {
  content_id: string
  filename: string
  file_type: string
  status: string
  total_chunks: number
  message: string
  is_duplicate?: boolean
  duplicate_of?: string
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
}

// Chat/Query types
export interface Message {
  id: string
  content_id: string
  question: string
  answer: string
  user_id: string
  sources?: Source[]
  created_at: string
  response_time?: number
  token_count?: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  sources?: SourceReference[]
  streaming?: boolean
  error?: boolean
  metadata?: {
    response_time_ms?: number
    tokens_used?: number
    model?: string
    question_frequency?: number
  }
  cached?: boolean
}

export interface Source {
  chunk_id: string
  text: string
  score: number
  metadata?: Record<string, unknown>
}

export interface SourceReference {
  source_id: number
  document_title: string
  uploader_name: string
  uploader_id: string
  upload_date: string
  chunk_index: number
  similarity_score: number
}

export interface AskQuestionRequest {
  question: string
  user_id: string
}

export interface AskQuestionResponse {
  question_id: string
  answer: string
  sources: Source[]
  response_time: number
}

export interface QuestionResponse {
  question_id: string
  content_id: string
  question: string
  answer: string
  sources: SourceReference[]
  metadata: {
    chunks_used: number
    response_time_ms: number
    llm_time_ms: number
    tokens_used: {
      prompt_tokens: number
      completion_tokens: number
      total_tokens: number
    }
    model: string
    question_frequency?: number
  }
  cached: boolean
}

// Streaming response type
export interface StreamChunk {
  type: 'token' | 'sources' | 'complete' | 'error'
  content?: string
  sources?: Source[]
  error?: string
}

// Suggested Prompts
export interface SuggestedPrompt {
  id: string
  text: string
  category?: 'definition' | 'explanation' | 'comparison' | 'procedure' | 'application' | 'evaluation'
  icon?: string
}

// Popular Questions
export interface PopularQuestion {
  question: string
  frequency: number
  is_cached: boolean
}

// Global Chat types
export interface GlobalChatRequest {
  question: string
  user_id: string
  selected_doc_ids?: string[]
}

export interface GlobalChatResponse {
  question_id: string
  question: string
  answer: string
  sources: SourceReference[]
  metadata: {
    chunks_used: number
    documents_searched: number
    response_time_ms: number
    llm_time_ms: number
    tokens_used: {
      prompt_tokens: number
      completion_tokens: number
      total_tokens: number
    }
    model: string
  }
  cached: boolean
}

// Document filter types
export type DocumentFilter = 'all' | 'owned' | 'shared'

export interface DocumentFiltersState {
  filter: DocumentFilter
  search: string
  subjects: string[]
  tags: string[]
}

// Analytics types
export interface AnalyticsOverview {
  total_questions: number
  total_documents: number
  total_students: number
  avg_response_time: number
  total_tokens_used: number
}

export interface QuestionVolumeData {
  date: string
  count: number
}

export interface StudentEngagement {
  student_id: string
  total_questions: number
  unique_content_accessed: number
  avg_response_time_ms: number
  first_activity?: string
  last_activity: string
  recent_questions?: Array<{
    question_id: string
    content_id: string
    timestamp: string
  }>
}

export interface ContentUsage {
  content_id: string
  title: string
  subject: string
  question_count: number
  unique_users: number
  last_accessed: string
}

// Question types
export interface Question extends Record<string, unknown> {
  question_id: string
  content_id: string
  session_id: string
  student_id: string
  question_text: string
  answer_text: string
  timestamp: string
  response_time_ms: number
  cached: boolean
  question_type?: string
  classification_confidence?: number
  metadata?: {
    subject?: string
    grade_level?: string
  }
}

// Content Statistics
export interface ContentStats {
  content_id: string
  total_questions: number
  unique_students: number
  avg_response_time_ms: number
  total_cached_responses: number
  cache_hit_rate: number
}

// Question Type Distribution
export interface QuestionType {
  type: string
  count: number
  percentage: number
  avg_response_time_ms: number
}

export interface QuestionTypeDistribution {
  content_id: string
  total_questions: number
  question_types: QuestionType[]
}

// Teacher Dashboard types
export interface TeacherOverview {
  teacher_id: string
  overview: {
    total_students: number
    total_questions: number
    avg_questions_per_student: number
  }
  top_contents: Array<{
    content_id: string
    question_count: number
    student_count: number
  }>
  recent_students: Array<{
    _id: string
    total_questions: number
    last_activity: string
  }>
}

export interface StudentActivity {
  student_id: string
  student_name?: string
  student_email?: string
  total_questions: number
  unique_content: number
  avg_response_time: number
  last_activity: string
  days_active: number
  status: 'active' | 'inactive'
}

export interface ContentEngagement {
  content_id: string
  total_questions: number
  unique_students: number
  engagement_level: 'high' | 'medium' | 'low'
  question_trends: Array<{
    date: string
    count: number
  }>
  question_types: QuestionType[]
  top_students: Array<{
    student_id: string
    question_count: number
    avg_response_time: number
  }>
}

// Error types
export interface ApiError {
  message: string
  status?: number
  code?: string
  details?: unknown
}

