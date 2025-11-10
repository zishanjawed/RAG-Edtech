/**
 * TypeaheadPopover Component
 * Lightweight popover for @-mentioning documents
 */

import { Document } from '../../../api/types'
import { Card } from '../../../components/ui/Card'
import { FileText, CheckCircle } from 'lucide-react'
import { cn } from '../../../lib/utils'

interface TypeaheadPopoverProps {
  documents: Document[]
  selectedIds: string[]
  query: string
  onSelect: (doc: Document) => void
  position: { top: number; left: number }
  highlightedIndex: number
}

export function TypeaheadPopover({
  documents,
  selectedIds,
  query,
  onSelect,
  position,
  highlightedIndex,
}: TypeaheadPopoverProps) {
  if (documents.length === 0) return null

  return (
    <Card
      className="absolute z-50 max-h-[300px] overflow-y-auto shadow-lg border-2"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
        minWidth: '320px',
      }}
    >
      <div className="p-2">
        <div className="text-xs text-muted-foreground px-2 py-1.5 border-b mb-1">
          Select documents to narrow search
        </div>
        {documents.map((doc, index) => {
          const isSelected = selectedIds.includes(doc.content_id)
          const isHighlighted = index === highlightedIndex

          return (
            <button
              key={doc.content_id}
              onClick={() => onSelect(doc)}
              className={cn(
                'w-full text-left px-3 py-2 rounded-md flex items-start gap-3 transition-colors',
                isHighlighted && 'bg-primary/10',
                !isHighlighted && 'hover:bg-muted'
              )}
            >
              <FileText className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm line-clamp-1">{doc.title}</span>
                  {isSelected && <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />}
                </div>
                <div className="text-xs text-muted-foreground">{doc.subject}</div>
              </div>
            </button>
          )
        })}
      </div>
    </Card>
  )
}

