/**
 * MessageBubble Component
 * Enhanced message display with animations
 */
import { motion } from 'framer-motion'
import { Card } from '@/components/ui/Card'
import { MarkdownRenderer } from '@/components/ui/MarkdownRenderer'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
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
        </Card.Body>
      </Card>
    </motion.div>
  )
}

