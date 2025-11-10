/**
 * DocumentChatPage Component
 * Document-specific chat with suggested prompts and sources
 */

import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChatMessage, SuggestedPrompt, Document } from '../../../api/types'
import { SuggestedPrompts } from '../components/SuggestedPrompts'
import { SourceCitations } from '../components/SourceCitations'
import { Card } from '../../../components/ui/Card'
import { Badge } from '../../../components/ui/Badge'
import { Button } from '../../../components/ui/Button'
import { ScrollArea } from '../../../components/ui/scroll-area'
import { Input } from '../../../components/ui/Input'
import {
  FileText,
  Bot,
  User as UserIcon,
  Send,
  ArrowLeft,
  Sparkles,
  Loader2,
} from 'lucide-react'
import { chatService } from '../../../api/chat.service'
import { documentsService } from '../../../api/documents.service'
import { useAuth } from '../../auth/hooks/useAuth'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '../../../lib/utils'

export function DocumentChatPage() {
  const { documentId } = useParams<{ documentId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [document, setDocument] = useState<Document | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [suggestedPrompts, setSuggestedPrompts] = useState<SuggestedPrompt[]>([])
  const [showSources, setShowSources] = useState(true)
  const [useSourcesMode, setUseSourcesMode] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const streamingMessageRef = useRef<string>('')

  // Load document and prompts
  useEffect(() => {
    if (documentId) {
      loadDocument(documentId)
      loadDocumentPrompts(documentId)
    }
  }, [documentId])

  const loadDocument = async (id: string) => {
    try {
      const doc = await documentsService.getDocument(id)
      setDocument(doc)
    } catch (error) {
      // Handle error silently
    }
  }

  const loadDocumentPrompts = async (id: string) => {
    try {
      const response = await documentsService.getDocumentPrompts(id)
      setSuggestedPrompts(response.prompts || [])
    } catch (error) {
      setSuggestedPrompts([
        { id: '1', text: 'Explain the key concepts', category: 'explanation' },
        { id: '2', text: 'What are the main definitions?', category: 'definition' },
        { id: '3', text: 'Give me practice problems', category: 'application' },
      ])
    }
  }

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Handle sending message
  const handleSend = async () => {
    const question = input.trim()
    if (!question || !documentId || !user) return

    // Add user message
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setSuggestedPrompts([]) // Hide prompts after first message

    if (useSourcesMode) {
      // Use complete mode with sources (real API)
      setIsStreaming(true)
      
      try {
        const response = await chatService.askQuestionComplete(documentId, {
          question,
          user_id: user.id,
        })

        const assistantMessage: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          role: 'assistant',
          content: response.answer,
          timestamp: new Date().toISOString(),
          sources: response.sources,
          metadata: {
            response_time_ms: response.metadata.response_time_ms,
            tokens_used: response.metadata.tokens_used?.total_tokens,
            model: response.metadata.model,
          },
        }
        setMessages((prev) => [...prev, assistantMessage])
      } catch (error) {
        const errorMessage: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date().toISOString(),
          error: true,
        }
        setMessages((prev) => [...prev, errorMessage])
      } finally {
        setIsStreaming(false)
      }
    } else {
      // Use streaming mode (fast) - real API
      setIsStreaming(true)
      streamingMessageRef.current = ''

      const assistantMessageId = `msg-${Date.now() + 1}`
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        streaming: true,
      }
      setMessages((prev) => [...prev, assistantMessage])

      try {
        // Use existing streaming service
        chatService.askQuestionStream(
          documentId,
          { question, user_id: user.id },
          (chunk) => {
            if (chunk.content) {
              streamingMessageRef.current += chunk.content
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: streamingMessageRef.current }
                    : msg
                )
              )
            }
          },
          () => {
            // Stream complete
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId ? { ...msg, streaming: false } : msg
              )
            )
            setIsStreaming(false)
            streamingMessageRef.current = ''
          },
          (error) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      content: 'Sorry, I encountered an error. Please try again.',
                      streaming: false,
                      error: true,
                    }
                  : msg
              )
            )
            setIsStreaming(false)
            streamingMessageRef.current = ''
          }
        )
      } catch (error) {
        setIsStreaming(false)
        streamingMessageRef.current = ''
      }
    }
  }

  // Handle prompt click
  const handlePromptClick = (promptText: string) => {
    setInput(promptText)
    // Auto-send after short delay for better UX
    setTimeout(() => {
      handleSend()
    }, 100)
  }

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!document) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col bg-gradient-to-b from-background to-muted/20">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="sm" onClick={() => navigate('/documents')}>
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div className="p-2 rounded-lg bg-primary/10">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h1 className="text-lg font-bold flex items-center gap-2">
                  {document.title}
                  {document.status === 'processing' && (
                    <Badge variant="warning" className="text-xs">
                      Processing
                    </Badge>
                  )}
                </h1>
                <p className="text-sm text-muted-foreground">
                  {document.subject} • {document.chunks_count || 0} chunks
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setUseSourcesMode(!useSourcesMode)}
                className="group flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted"
              >
                <div
                  className={cn(
                    'flex items-center justify-center w-10 h-5 rounded-full transition-colors',
                    useSourcesMode ? 'bg-primary' : 'bg-muted-foreground/30'
                  )}
                >
                  <div
                    className={cn(
                      'w-4 h-4 rounded-full bg-white transition-transform',
                      useSourcesMode ? 'translate-x-2.5' : '-translate-x-2.5'
                    )}
                  />
                </div>
                <Sparkles
                  className={cn(
                    'h-4 w-4 transition-colors',
                    useSourcesMode ? 'text-primary' : 'text-muted-foreground'
                  )}
                />
                <span>{useSourcesMode ? 'With Sources' : 'Fast Mode'}</span>
              </button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSources(!showSources)}
              >
                {showSources ? 'Hide' : 'Show'} Sources
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="container mx-auto px-4 py-8 max-w-4xl">
            {messages.length === 0 ? (
              /* Empty state with suggested prompts */
              <div className="flex flex-col items-center justify-center py-12">
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="text-center mb-8"
                >
                  <div className="inline-flex p-4 rounded-full bg-primary/10 mb-4">
                    <FileText className="h-12 w-12 text-primary" />
                  </div>
                  <h2 className="text-2xl font-bold mb-2">Ask about {document.title}</h2>
                  <p className="text-muted-foreground">
                    Get answers based on this {document.subject} document
                  </p>
                </motion.div>

                <SuggestedPrompts
                  prompts={suggestedPrompts}
                  onPromptClick={handlePromptClick}
                  className="w-full max-w-2xl"
                />
              </div>
            ) : (
              /* Messages */
              <div className="space-y-6">
                <AnimatePresence>
                  {messages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div
                        className={cn(
                          'flex gap-4',
                          message.role === 'user' ? 'justify-end' : 'justify-start'
                        )}
                      >
                        {message.role === 'assistant' && (
                          <div className="flex-shrink-0">
                            <div className="p-2 rounded-full bg-primary/10">
                              <Bot className="h-5 w-5 text-primary" />
                            </div>
                          </div>
                        )}

                        <div
                          className={cn(
                            'flex-1 max-w-3xl',
                            message.role === 'user' && 'max-w-2xl'
                          )}
                        >
                          <Card
                            className={cn(
                              'overflow-hidden',
                              message.role === 'user'
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-card',
                              message.error && 'border-red-500'
                            )}
                          >
                            <div className="p-4">
                              <div
                                className={cn(
                                  'prose prose-sm max-w-none',
                                  message.role === 'user' && 'prose-invert'
                                )}
                              >
                                {message.content}
                                {message.streaming && (
                                  <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
                                )}
                              </div>

                              {message.metadata && (
                                <div className="mt-3 pt-3 border-t flex items-center gap-4 text-xs text-muted-foreground">
                                  <span>{message.metadata.response_time_ms}ms</span>
                                  <span>{message.metadata.tokens_used} tokens</span>
                                  <span>{message.metadata.model}</span>
                                </div>
                              )}
                            </div>
                          </Card>

                          {/* Sources */}
                          {message.role === 'assistant' &&
                            !message.streaming &&
                            message.sources &&
                            message.sources.length > 0 &&
                            showSources && (
                              <div className="mt-4">
                                <SourceCitations sources={message.sources} />
                              </div>
                            )}
                        </div>

                        {message.role === 'user' && (
                          <div className="flex-shrink-0">
                            <div className="p-2 rounded-full bg-primary">
                              <UserIcon className="h-5 w-5 text-primary-foreground" />
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Input area */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4 max-w-4xl">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about this document..."
              disabled={isStreaming || document.status !== 'completed'}
              className="flex-1"
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming || document.status !== 'completed'}
              size="lg"
              className="px-6"
            >
              {isStreaming ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

