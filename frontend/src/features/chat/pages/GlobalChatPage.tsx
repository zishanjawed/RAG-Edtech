/**
 * GlobalChatPage Component
 * Global chat interface with @-mention support and suggested prompts
 */

import { useState, useEffect, useRef } from 'react'
import { ChatMessage, SuggestedPrompt, Document } from '../../../api/types'
import { ChatComposer } from '../components/ChatComposer'
import { SuggestedPrompts } from '../components/SuggestedPrompts'
import { SourceCitations } from '../components/SourceCitations'
import { MarkdownRenderer } from '../../../components/ui/MarkdownRenderer'
import { Card } from '../../../components/ui/Card'
import { Badge } from '../../../components/ui/Badge'
import { Button } from '../../../components/ui/Button'
import { ScrollArea } from '../../../components/ui/scroll-area'
import { Spinner } from '../../../components/ui/Spinner'
import { MessageSquareMore, Bot, User as UserIcon, Sparkles } from 'lucide-react'
import { chatService } from '../../../api/chat.service'
import { documentsService } from '../../../api/documents.service'
import { useAuth } from '../../auth/hooks/useAuth'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '../../../lib/utils'

export function GlobalChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [documents, setDocuments] = useState<Document[]>([]) // All documents
  const [availableDocuments, setAvailableDocuments] = useState<Document[]>([]) // Only completed
  const [suggestedPrompts, setSuggestedPrompts] = useState<SuggestedPrompt[]>([])
  const [showSources, setShowSources] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const streamingMessageRef = useRef<string>('')

  // Load available documents and prompts
  useEffect(() => {
    if (user) {
      loadDocuments()
      loadGlobalPrompts()
    }
  }, [user])

  // Auto-refresh documents while processing
  useEffect(() => {
    if (!user) return

    // Check if any documents are still processing
    const hasProcessingDocs = documents.some(doc => doc.status === 'processing')
    
    if (hasProcessingDocs) {
      // Poll every 5 seconds while documents are processing
      const interval = setInterval(() => {
        loadDocuments()
      }, 5000)
      
      return () => clearInterval(interval)
    }
  }, [user, documents])

  const loadDocuments = async () => {
    if (!user) return
    
    try {
      const docs = await documentsService.getDocuments(user.id, 'all')
      // Store all documents for processing status tracking
      setDocuments(docs)
      // Only show completed ones for chat
      setAvailableDocuments(docs.filter((doc) => doc.status === 'completed'))
    } catch (error) {
      console.error('Failed to load documents:', error)
    }
  }

  const loadGlobalPrompts = async () => {
    if (!user) return
    
    try {
      const response = await documentsService.getGlobalPrompts(user.id)
      setSuggestedPrompts(response.prompts || [])
    } catch (error) {
      setSuggestedPrompts([
        { id: '1', text: 'Compare the main concepts across my documents', category: 'comparison' },
        { id: '2', text: 'What are the key formulas and definitions in my materials?', category: 'definition' },
        { id: '3', text: 'Explain the connections between different topics', category: 'explanation' },
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
  const handleSend = async (question: string, selectedDocIds: string[]) => {
    if (!user) return
    
    // Add user message
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])
    setSuggestedPrompts([]) // Hide prompts after first message

    // Start streaming response
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
      // Use complete mode to get sources (real API)
      const response = await chatService.askGlobalQuestionComplete({
        question,
        user_id: user.id,
        selected_doc_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
      })

      // Update message with complete response
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: response.answer,
                streaming: false,
                sources: response.sources,
                cached: response.cached,
                metadata: {
                  response_time_ms: response.metadata.response_time_ms,
                  tokens_used: response.metadata.tokens_used?.total_tokens,
                  model: response.metadata.model,
                  question_frequency: response.metadata.question_frequency,
                },
              }
            : msg
        )
      )
    } catch (error) {
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
    } finally {
      setIsStreaming(false)
      streamingMessageRef.current = ''
    }
  }

  // Handle prompt click
  const handlePromptClick = (promptText: string) => {
    handleSend(promptText, [])
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col bg-gradient-to-b from-background to-muted/20">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <MessageSquareMore className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold flex items-center gap-2">
                  Chat
                  <Badge variant="secondary" className="text-xs">
                    <Sparkles className="h-3 w-3 mr-1" />
                    All Documents
                  </Badge>
                </h1>
                <p className="text-sm text-muted-foreground">
                  Search across {availableDocuments.length} documents
                </p>
              </div>
            </div>
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

      {/* Processing status banner */}
      {documents.length > 0 && documents.filter(d => d.status === 'processing').length > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 p-4">
          <div className="container mx-auto px-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400 animate-spin" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700 dark:text-yellow-200">
                  <strong>{documents.filter(d => d.status === 'processing').length} document(s) still processing.</strong>
                  {' '}They'll become searchable when complete (usually 1-2 minutes). This page will update automatically.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

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
                    <MessageSquareMore className="h-12 w-12 text-primary" />
                  </div>
                  <h2 className="text-2xl font-bold mb-2">
                    {availableDocuments.length === 0 
                      ? "Upload documents to get started"
                      : `Ask anything across your ${availableDocuments.length} documents`
                    }
                  </h2>
                  <p className="text-muted-foreground">
                    {availableDocuments.length === 0
                      ? "Upload your first document to start chatting. Processing takes 1-2 minutes."
                      : `Get answers from all ${availableDocuments.length} documents at once. Use @ to narrow your search.`
                    }
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
                  {messages.map((message, index) => (
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
                        {message.role === 'assistant' && message.streaming && !message.content ? (
                          <>
                            <div className="flex-shrink-0">
                              <div className="p-2 rounded-full bg-primary/10">
                                <Bot className="h-5 w-5 text-primary" />
                              </div>
                            </div>
                            <div className="flex-1 max-w-3xl">
                              <Card className="bg-card">
                                <div className="p-4 space-y-3">
                                  <div className="h-3 bg-muted rounded animate-pulse w-full" />
                                  <div className="h-3 bg-muted rounded animate-pulse w-5/6" />
                                  <div className="h-3 bg-muted rounded animate-pulse w-4/6" />
                                </div>
                              </Card>
                            </div>
                          </>
                        ) : (
                          <>
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
                                  {message.role === 'user' && (
                                    <div className="flex items-center gap-2 mb-2 text-primary-foreground/80 text-sm">
                                      <UserIcon className="h-4 w-4" />
                                      <span>You</span>
                                    </div>
                                  )}
                                  
                                  <div
                                    className={cn(
                                      'prose prose-sm max-w-none',
                                      message.role === 'user' && 'prose-invert'
                                    )}
                                  >
                                    {message.role === 'user' ? (
                                      message.content
                                    ) : (
                                      <MarkdownRenderer content={message.content} />
                                    )}
                                    {message.streaming && message.content && (
                                      <span className="inline-flex items-center gap-1 ml-2">
                                        <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                      </span>
                                    )}
                                  </div>

                                  {/* Cache and Frequency Badges */}
                                  {message.role === 'assistant' && !message.streaming && (message.cached || message.metadata?.question_frequency) && (
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
                          </>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {/* Suggested prompts after first exchange */}
                {messages.length > 0 && messages.length % 4 === 0 && !isStreaming && (
                  <SuggestedPrompts
                    prompts={suggestedPrompts.slice(0, 3)}
                    onPromptClick={handlePromptClick}
                  />
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Input area */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4 max-w-4xl">
          <ChatComposer
            onSend={handleSend}
            availableDocuments={availableDocuments}
            placeholder="Ask a question across all documents... (Use @ to mention specific docs)"
            disabled={isStreaming}
          />
        </div>
      </div>
    </div>
  )
}

