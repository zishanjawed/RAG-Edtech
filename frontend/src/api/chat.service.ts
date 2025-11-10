/**
 * Chat Service
 * API calls for chat/query functionality
 */
import { apiClient } from './client'
import type { AskQuestionRequest, Message, StreamChunk, QuestionResponse, GlobalChatRequest, GlobalChatResponse } from './types'

export const chatService = {
  /**
   * Ask a question with streaming response
   */
  askQuestionStream(
    contentId: string,
    request: AskQuestionRequest,
    onChunk: (chunk: StreamChunk) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): () => void {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const token = localStorage.getItem('access_token')
    
    // Fixed endpoint path
    const url = `${baseURL}/api/content/${contentId}/question`
    
    const abortController = new AbortController()
    
    // Use fetch with streaming instead of EventSource
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify({
        question: request.question,
      }),
      signal: abortController.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
            const reader = response.body?.getReader()
            const decoder = new TextDecoder()
            
            if (!reader) {
              throw new Error('No response body')
            }
            
            while (true) {
          const { done, value } = await reader.read()
          
          if (done) {
            onComplete()
            break
          }
          
          // Decode and accumulate chunks
          const text = decoder.decode(value, { stream: true })
          
          // Send each character as a chunk for smooth streaming
          for (const char of text) {
            onChunk({
              type: 'token',
              content: char,
            })
          }
        }
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          onError(error)
        }
      })

    return () => abortController.abort()
  },

  /**
   * Ask a question with complete response (non-streaming) and sources
   */
  async askQuestionComplete(
    contentId: string,
    request: AskQuestionRequest
  ): Promise<QuestionResponse> {
    const response = await apiClient.post<QuestionResponse>(
      `/api/query/${contentId}/complete`,
      request
    )
    
    return response.data
  },

  /**
   * Get question history for a document
   */
  async getHistory(contentId: string): Promise<Message[]> {
    const response = await apiClient.get<{ questions: Message[] }>(
      `/api/content/${contentId}/questions`
    )
    return response.data.questions || []
  },

  /**
   * Ask a global question across multiple documents (complete mode with sources)
   */
  async askGlobalQuestionComplete(
    request: GlobalChatRequest
  ): Promise<QuestionResponse> {
    const response = await apiClient.post<QuestionResponse>(
      '/api/query/global/complete',
      request
    )
    
    return response.data
  },

  /**
   * Ask a global question with streaming
   */
  askGlobalQuestionStream(
    request: GlobalChatRequest,
    onChunk: (chunk: StreamChunk) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): () => void {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const token = localStorage.getItem('access_token')
    
    const url = `${baseURL}/api/query/global/question`
    
    const abortController = new AbortController()
    
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify(request),
      signal: abortController.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const reader = response.body?.getReader()
        const decoder = new TextDecoder()
        
        if (!reader) {
          throw new Error('No response body')
        }
        
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) {
            onComplete()
            break
          }
          
          const text = decoder.decode(value, { stream: true })
          
          for (const char of text) {
            onChunk({
              type: 'token',
              content: char,
            })
          }
        }
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          onError(error)
        }
      })

    return () => abortController.abort()
  },
}

