/**
 * ChatPage
 * Chat interface with streaming responses and optional source attribution
 */
import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, BookOpen, Sparkles } from 'lucide-react'
import { Button, Card } from '@/components/ui'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useChat } from '../hooks/useChat'
import { useStreaming } from '../hooks/useStreaming'
import { chatService } from '@/api/chat.service'
import { documentsService } from '@/api/documents.service'
import { ChatPageSkeleton } from '../components/ChatSkeleton'
import { TypingIndicator } from '../components/TypingIndicator'
import { MessageBubble } from '../components/MessageBubble'
import { PopularQuestions } from '../components/PopularQuestions'
import { SourceCitations } from '../components/SourceCitations'
import { useToast } from '@/hooks/useToast'
import type { Document, SourceReference, PopularQuestion } from '@/api/types'

export function ChatPage() {
  const { documentId } = useParams<{ documentId: string }>()
  const [document, setDocument] = useState<Document | null>(null)
  const [input, setInput] = useState('')
  const [isLoadingDoc, setIsLoadingDoc] = useState(true)
  const [useSourcesMode, setUseSourcesMode] = useState(false)
  const [isLoadingComplete, setIsLoadingComplete] = useState(false)
  const [popularQuestions, setPopularQuestions] = useState<PopularQuestion[]>([])
  const [loadingPopular, setLoadingPopular] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { user } = useAuth()
  const { toast } = useToast()
  const { messages, addMessage, isStreaming } = useChat()
  const { askQuestion } = useStreaming(documentId || '')

  useEffect(() => {
    if (documentId) {
      documentsService
        .getDocument(documentId)
        .then((doc) => {
          setDocument(doc)
          setIsLoadingDoc(false)
        })
        .catch((err) => {
          setIsLoadingDoc(false)
        })
      
      // Load popular questions
      loadPopularQuestions(documentId)
    }
  }, [documentId])

  const loadPopularQuestions = async (id: string) => {
    try {
      setLoadingPopular(true)
      const questions = await chatService.getPopularQuestions(id, 10)
      setPopularQuestions(questions)
    } catch (error) {
      setPopularQuestions([])
    } finally {
      setLoadingPopular(false)
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !user || isStreaming || isLoadingComplete) return

    const question = input.trim()
    setInput('')

    if (useSourcesMode) {
      // Use complete (non-streaming) endpoint with sources
      setIsLoadingComplete(true)
      
      try {
        const response = await chatService.askQuestionComplete(documentId!, {
          question,
          user_id: user.id,
        })

        // Add question message
        addMessage({
          role: 'user',
          content: question,
          isStreaming: false,
          content_id: documentId!,
          question,
          user_id: user.id,
        })

        // Add answer message with sources
        addMessage({
          role: 'assistant',
          content: response.answer,
          isStreaming: false,
          sources: response.sources as SourceReference[],
          content_id: documentId!,
          question,
          answer: response.answer,
          user_id: user.id,
        })

        toast({
          type: 'success',
          title: 'Answer generated',
          description: `Generated with ${response.sources.length} sources`,
        })
      } catch (error) {
        toast({
          type: 'error',
          title: 'Error',
          description: 'Failed to get answer. Please try again.',
        })
      } finally {
        setIsLoadingComplete(false)
      }
    } else {
      // Use streaming mode (existing behavior)
      askQuestion({
        question,
        user_id: user.id,
      })
    }
  }

  if (isLoadingDoc) {
    return <ChatPageSkeleton />
  }

  if (!document) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Card className="max-w-md">
          <Card.Body>
            <p className="text-center text-slate-600">Document not found</p>
          </Card.Body>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <div className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary-100 p-2">
            <BookOpen className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-900">{document.title}</h1>
            <p className="text-sm text-slate-600">
              {document.subject} - {document.grade_level}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 bg-slate-50 px-6 py-6">
        <div className="mx-auto max-w-4xl space-y-6">
          {messages.length === 0 && (
            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center"
              >
                <div className="inline-flex rounded-full bg-primary-100 p-4 mb-4">
                  <BookOpen className="h-8 w-8 text-primary-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Ask Me Anything</h2>
                <p className="text-slate-600">
                  Start by asking a question about {document.title}
                </p>
              </motion.div>
              
              {/* Popular Questions */}
              {(popularQuestions.length > 0 || loadingPopular) && (
                <PopularQuestions
                  questions={popularQuestions}
                  onQuestionClick={(question) => setInput(question)}
                  isLoading={loadingPopular}
                />
              )}
            </div>
          )}

          <AnimatePresence mode="popLayout">
            {messages.map((message, index) => (
              <motion.div
                key={message.id}
                layout
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{
                  layout: { type: "spring", stiffness: 350, damping: 25 },
                  opacity: { duration: 0.2 },
                  scale: { duration: 0.2 }
                }}
              >
                {message.isStreaming && !message.content ? (
                  <div className="flex justify-start">
                    <TypingIndicator />
                  </div>
                ) : (
                  <div>
                    <MessageBubble message={message} index={index} />
                    {message.role === 'assistant' && message.sources && 'source_id' in message.sources[0] && (
                      <SourceCitations sources={message.sources as SourceReference[]} />
                    )}
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Bar */}
      <div className="border-t border-slate-200 bg-white px-6 py-4">
        <form onSubmit={handleSubmit} className="mx-auto max-w-4xl space-y-3">
          {/* Mode Toggle */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setUseSourcesMode(!useSourcesMode)}
              className="group flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors hover:bg-slate-100"
            >
              <div className={`flex items-center justify-center w-10 h-5 rounded-full transition-colors ${useSourcesMode ? 'bg-primary-600' : 'bg-slate-300'}`}>
                <div className={`w-4 h-4 rounded-full bg-white transition-transform ${useSourcesMode ? 'translate-x-2.5' : '-translate-x-2.5'}`} />
              </div>
              <Sparkles className={`h-4 w-4 transition-colors ${useSourcesMode ? 'text-primary-600' : 'text-slate-500'}`} />
              <span className={`transition-colors ${useSourcesMode ? 'text-primary-900' : 'text-slate-700'}`}>
                {useSourcesMode ? 'With Sources' : 'Fast Mode'}
              </span>
            </button>
            <span className="text-xs text-slate-500">
              {useSourcesMode ? 'Slower, includes citations' : 'Faster, streaming response'}
            </span>
          </div>

          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about this document..."
              disabled={isStreaming || isLoadingComplete}
              className="flex-1 rounded-lg border border-slate-300 px-4 py-3 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100 disabled:cursor-not-allowed"
            />
            <Button
              type="submit"
              size="md"
              disabled={!input.trim() || isStreaming || isLoadingComplete}
              isLoading={isStreaming || isLoadingComplete}
              leftIcon={!isStreaming && !isLoadingComplete ? <Send className="h-5 w-5" /> : undefined}
            >
              {isStreaming || isLoadingComplete ? 'Sending...' : 'Send'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

