/**
 * ChatComposer Component
 * Input area with @-mention support for documents
 */

import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { Document } from '../../../api/types'
import { Button } from '../../../components/ui/Button'
import { Badge } from '../../../components/ui/Badge'
import { TypeaheadPopover } from './TypeaheadPopover'
import { Send, X } from 'lucide-react'
import { cn } from '../../../lib/utils'

interface ChatComposerProps {
  onSend: (message: string, selectedDocIds: string[]) => void
  availableDocuments?: Document[]
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function ChatComposer({
  onSend,
  availableDocuments = [],
  placeholder = 'Ask a question...',
  disabled = false,
  className,
}: ChatComposerProps) {
  const [input, setInput] = useState('')
  const [selectedDocs, setSelectedDocs] = useState<Document[]>([])
  const [showTypeahead, setShowTypeahead] = useState(false)
  const [typeaheadQuery, setTypeaheadQuery] = useState('')
  const [typeaheadPosition, setTypeaheadPosition] = useState({ top: 0, left: 0 })
  const [highlightedIndex, setHighlightedIndex] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const composerRef = useRef<HTMLDivElement>(null)

  // Filter documents based on typeahead query
  const filteredDocs = availableDocuments
    .filter((doc) => {
      if (!typeaheadQuery) return true
      const query = typeaheadQuery.toLowerCase()
      return (
        doc.title.toLowerCase().includes(query) ||
        doc.subject.toLowerCase().includes(query) ||
        doc.tags?.some((tag) => tag.toLowerCase().includes(query))
      )
    })
    .filter((doc) => !selectedDocs.some((selected) => selected.content_id === doc.content_id))
    .slice(0, 5)

  // Handle input change and detect @ mentions
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setInput(value)

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }

    // Detect @ mention
    const cursorPos = e.target.selectionStart
    const textBeforeCursor = value.slice(0, cursorPos)
    const lastAtSymbol = textBeforeCursor.lastIndexOf('@')

    if (lastAtSymbol !== -1 && availableDocuments.length > 0) {
      const queryAfterAt = textBeforeCursor.slice(lastAtSymbol + 1)
      // Show typeahead if @ is at start or after space, and no space after @
      if (
        (lastAtSymbol === 0 || textBeforeCursor[lastAtSymbol - 1] === ' ') &&
        !queryAfterAt.includes(' ')
      ) {
        setTypeaheadQuery(queryAfterAt)
        setShowTypeahead(true)
        setHighlightedIndex(0)

        // Calculate position
        if (textareaRef.current && composerRef.current) {
          const rect = textareaRef.current.getBoundingClientRect()
          const composerRect = composerRef.current.getBoundingClientRect()
          setTypeaheadPosition({
            top: rect.top - composerRect.top - 320, // Show above input
            left: rect.left - composerRect.left,
          })
        }
        return
      }
    }

    setShowTypeahead(false)
  }

  // Handle document selection from typeahead
  const handleDocSelect = (doc: Document) => {
    if (selectedDocs.some((d) => d.content_id === doc.content_id)) {
      // Already selected, remove it
      setSelectedDocs(selectedDocs.filter((d) => d.content_id !== doc.content_id))
    } else {
      // Add to selection
      setSelectedDocs([...selectedDocs, doc])
    }

    // Remove @mention from input
    const cursorPos = textareaRef.current?.selectionStart || 0
    const textBeforeCursor = input.slice(0, cursorPos)
    const lastAtSymbol = textBeforeCursor.lastIndexOf('@')
    const textAfterCursor = input.slice(cursorPos)

    const newInput = input.slice(0, lastAtSymbol) + textAfterCursor
    setInput(newInput)
    setShowTypeahead(false)

    // Focus back to textarea
    setTimeout(() => {
      textareaRef.current?.focus()
    }, 0)
  }

  // Remove selected document
  const handleRemoveDoc = (contentId: string) => {
    setSelectedDocs(selectedDocs.filter((doc) => doc.content_id !== contentId))
  }

  // Handle keyboard navigation in typeahead
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (showTypeahead && filteredDocs.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setHighlightedIndex((prev) => (prev + 1) % filteredDocs.length)
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setHighlightedIndex((prev) => (prev - 1 + filteredDocs.length) % filteredDocs.length)
      } else if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleDocSelect(filteredDocs[highlightedIndex])
      } else if (e.key === 'Escape') {
        e.preventDefault()
        setShowTypeahead(false)
      }
      return
    }

    // Send message on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Send message
  const handleSend = () => {
    const trimmedInput = input.trim()
    if (!trimmedInput || disabled) return

    onSend(
      trimmedInput,
      selectedDocs.map((doc) => doc.content_id)
    )

    // Clear input and selections
    setInput('')
    setSelectedDocs([])
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  // Close typeahead when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (composerRef.current && !composerRef.current.contains(e.target as Node)) {
        setShowTypeahead(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div ref={composerRef} className={cn('relative', className)}>
      {/* Typeahead popover */}
      {showTypeahead && (
        <TypeaheadPopover
          documents={filteredDocs}
          selectedIds={selectedDocs.map((d) => d.content_id)}
          query={typeaheadQuery}
          onSelect={handleDocSelect}
          position={typeaheadPosition}
          highlightedIndex={highlightedIndex}
        />
      )}

      {/* Selected documents */}
      {selectedDocs.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {selectedDocs.map((doc) => (
            <Badge key={doc.content_id} variant="secondary" className="gap-2 py-1">
              {doc.title}
              <button
                onClick={() => handleRemoveDoc(doc.content_id)}
                className="hover:bg-muted-foreground/20 rounded-full"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}

      {/* Input area */}
      <div className="flex gap-2 items-end">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className={cn(
              'w-full resize-none rounded-lg border border-input bg-background px-4 py-3 text-sm',
              'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
              'disabled:cursor-not-allowed disabled:opacity-50',
              'min-h-[48px] max-h-[200px]'
            )}
          />
          {availableDocuments.length > 0 && (
            <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
              Tip: Type @ to mention documents
            </div>
          )}
        </div>
        <Button
          onClick={handleSend}
          disabled={!input.trim() || disabled}
          size="lg"
          className="h-12 px-6"
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>
    </div>
  )
}

