/**
 * MessageBubble Component
 * Enhanced message display with animations
 */
import { motion } from 'framer-motion'
import { Zap, BarChart3 } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { MarkdownRenderer } from '@/components/ui/MarkdownRenderer'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
  cached?: boolean
  metadata?: {
    question_frequency?: number
    response_time_ms?: number
    tokens_used?: number
    model?: string
  }
}

interface MessageBubbleProps {
  message: Message
  index: number
}

export function MessageBubble({ message, index }: MessageBubbleProps) {
  if (message.role === 'user') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{
          type: "spring",
          stiffness: 350,
          damping: 25,
          delay: index * 0.05
        }}
        className="flex justify-end"
      >
        <motion.div
          className="max-w-[80%] rounded-2xl bg-primary-600 px-4 py-3 text-white shadow-soft-sm"
          whileHover={{ scale: 1.02 }}
          transition={{ type: "spring", stiffness: 400 }}
        >
          {message.content}
        </motion.div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        type: "spring",
        stiffness: 350,
        damping: 25,
        delay: index * 0.05
      }}
      className="flex justify-start"
    >
      <Card 
        className="max-w-[85%] shadow-soft-sm" 
        animated
      >
        <Card.Body>
          <MarkdownRenderer content={message.content} />
          
          {/* Cache and Frequency Badges */}
          {!message.isStreaming && (message.cached || message.metadata?.question_frequency) && (
            <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-200">
              {message.cached && (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-medium">
                  <Zap className="h-3 w-3" />
                  Cached
                </span>
              )}
              {message.metadata?.question_frequency && message.metadata.question_frequency > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
                  <BarChart3 className="h-3 w-3" />
                  Asked {message.metadata.question_frequency}x
                </span>
              )}
            </div>
          )}
        </Card.Body>
      </Card>
    </motion.div>
  )
}

