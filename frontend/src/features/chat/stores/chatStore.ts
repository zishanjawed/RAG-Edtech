/**
 * Chat Store
 * Global chat state management
 */
import { create } from 'zustand'
import type { Document, Source, SourceReference } from '@/api/types'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
  sources?: Source[] | SourceReference[]
  timestamp: Date
  content_id?: string
  question?: string
  answer?: string
  user_id?: string
  created_at?: string
  response_time?: number
  token_count?: number
}

interface ChatState {
  messages: ChatMessage[]
  currentDocument: Document | null
  isStreaming: boolean

  // Actions
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  updateLastMessage: (content: string) => void
  addStreamingChunk: (chunk: string) => void
  setStreaming: (isStreaming: boolean) => void
  clearMessages: () => void
  setDocument: (doc: Document | null) => void
  setMessages: (messages: ChatMessage[]) => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  currentDocument: null,
  isStreaming: false,

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: Math.random().toString(36).substring(7),
          timestamp: new Date(),
        },
      ],
    })),

  updateLastMessage: (content) =>
    set((state) => {
      const messages = [...state.messages]
      if (messages.length > 0) {
        messages[messages.length - 1].content = content
      }
      return { messages }
    }),

  addStreamingChunk: (chunk) =>
    set((state) => {
      const messages = [...state.messages]
      if (messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
        messages[messages.length - 1].content += chunk
      }
      return { messages }
    }),

  setStreaming: (isStreaming) => set({ isStreaming }),

  clearMessages: () => set({ messages: [] }),

  setDocument: (doc) => set({ currentDocument: doc }),

  setMessages: (messages) => set({ messages }),
}))

