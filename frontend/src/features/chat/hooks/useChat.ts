/**
 * useChat Hook
 * Chat state and actions
 */
import { useChatStore } from '../stores/chatStore'

export function useChat() {
  return useChatStore()
}

