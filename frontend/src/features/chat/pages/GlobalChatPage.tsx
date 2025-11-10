/**
 * GlobalChatPage Component
 * Global chat interface with @-mention support and suggested prompts
 */

import { useState, useEffect, useRef } from 'react'
import { ChatMessage, SuggestedPrompt, Document } from '../../../api/types'
import { ChatComposer } from '../components/ChatComposer'
import { SuggestedPrompts } from '../components/SuggestedPrompts'
import { SourceCitations } from '../components/SourceCitations'
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
  const [availableDocuments, setAvailableDocuments] = useState<Document[]>([])
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

  const loadDocuments = async () => {
    if (!user) return
    
    try {
      const docs = await documentsService.getDocuments(user.id, 'all')
      setAvailableDocuments(docs.filter((doc) => doc.status === 'completed'))
    } catch (error) {
      // Handle error silently
    }
  }

  const loadGlobalPrompts = async () => {
    if (!user) return
    
    try {
      const response = await documentsService.getGlobalPrompts(user.id)
      setSuggestedPrompts(response.prompts || [])
    } catch (error) {
      setSuggestedPrompts([
        { id: '1', text: 'Compare key concepts across my documents', category: 'comparison' },
        { id: '2', text: 'Create a study plan based on my knowledge base', category: 'evaluation' },
        { id: '3', text: 'What topics should I review?', category: 'evaluation' },
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
                metadata: {
                  response_time_ms: response.metadata.response_time_ms,
                  tokens_used: response.metadata.tokens_used?.total_tokens,
                  model: response.metadata.model,
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
                  <h2 className="text-2xl font-bold mb-2">Ask anything across your knowledge base</h2>
                  <p className="text-muted-foreground">
                    Get answers from all {availableDocuments.length} documents at once. Use @ to narrow your search.
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

