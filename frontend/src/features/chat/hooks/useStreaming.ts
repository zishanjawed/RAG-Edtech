/**
 * useStreaming Hook
 * Handle streaming responses
 */
import { useRef, useCallback } from 'react'
import { chatService } from '@/api/chat.service'
import { useChatStore } from '../stores/chatStore'
import { useToast } from '@/hooks/useToast'
import type { AskQuestionRequest, StreamChunk } from '@/api/types'

export function useStreaming(contentId: string) {
  const cleanupRef = useRef<(() => void) | null>(null)
  const { addMessage, addStreamingChunk, setStreaming } = useChatStore()
  const { error: showError } = useToast()

  const askQuestion = useCallback(
    (request: AskQuestionRequest) => {
      // Add user message
      addMessage({
        role: 'user',
        content: request.question,
      })

      // Add empty assistant message for streaming
      addMessage({
        role: 'assistant',
        content: '',
        isStreaming: true,
      })

      setStreaming(true)

      // Start streaming
      cleanupRef.current = chatService.askQuestionStream(
        contentId,
        request,
        (chunk: StreamChunk) => {
          if (chunk.type === 'token' && chunk.content) {
            addStreamingChunk(chunk.content)
          } else if (chunk.type === 'sources' && chunk.sources) {
            // Update last message with sources
            // You could enhance this to update the message object with sources
          } else if (chunk.type === 'error' && chunk.error) {
            showError('Error', chunk.error)
          }
        },
        () => {
          setStreaming(false)
        },
        (err) => {
          setStreaming(false)
          showError('Connection Error', err.message)
        }
      )
    },
    [contentId, addMessage, addStreamingChunk, setStreaming, showError]
  )

  const stopStreaming = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current()
      cleanupRef.current = null
    }
    setStreaming(false)
  }, [setStreaming])

  return { askQuestion, stopStreaming }
}

