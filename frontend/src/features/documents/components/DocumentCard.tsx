/**
 * DocumentCard Component
 * Displays document information with quick actions (Chat, Open, Delete)
 */

import { Document } from '../../../api/types'
import { Card } from '../../../components/ui/Card'
import { Badge } from '../../../components/ui/Badge'
import { Button } from '../../../components/ui/Button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../../components/ui/dropdown-menu'
import { useNavigate } from 'react-router-dom'
import {
  MessageSquare,
  FileText,
  MoreVertical,
  Trash2,
  Clock,
  User,
  CheckCircle,
  Loader2,
  AlertCircle,
  Sparkles,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../../../components/ui/tooltip'

interface DocumentCardProps {
  document: Document
  onDelete?: (contentId: string) => void
  onOpen?: (contentId: string) => void
}

export function DocumentCard({ document, onDelete, onOpen }: DocumentCardProps) {
  const navigate = useNavigate()

  const handleChatClick = () => {
    navigate(`/chat/${document.content_id}`)
  }

  const handleOpenClick = () => {
    if (onOpen) {
      onOpen(document.content_id)
    }
  }

  const handleDeleteClick = () => {
    if (onDelete && window.confirm(`Delete "${document.title}"?`)) {
      onDelete(document.content_id)
    }
  }

  const getStatusIcon = () => {
    switch (document.status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'processing':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      default:
        return null
    }
  }

  const getStatusBadge = () => {
    switch (document.status) {
      case 'completed':
        return <Badge variant="success">Ready</Badge>
      case 'processing':
        return <Badge variant="warning">Processing</Badge>
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>
      default:
        return null
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getLastActivityText = () => {
    if (!document.last_activity) return null
    try {
      return formatDistanceToNow(new Date(document.last_activity), { addSuffix: true })
    } catch {
      return null
    }
  }

  return (
    <Card className="group hover:shadow-lg transition-all duration-200 hover:border-primary/50 flex flex-col h-full">
      <div className="p-6 flex flex-col flex-1">
        {/* Header with status */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start gap-2 flex-1">
            <FileText className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg leading-tight line-clamp-2 mb-1">
                {document.title || document.metadata?.title || document.filename}
              </h3>
            </div>
          </div>
          <div className="flex items-center gap-2 ml-2">
            {getStatusIcon()}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <DropdownMenuItem disabled className="opacity-50">
                        <FileText className="h-4 w-4 mr-2" />
                        Open Details
                        <Badge variant="outline" className="ml-auto text-xs">
                          v2
                        </Badge>
                      </DropdownMenuItem>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Coming in next version</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <DropdownMenuItem onClick={handleChatClick} disabled={document.status !== 'completed'}>
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Start Chat
                </DropdownMenuItem>
                {onDelete && (
                  <DropdownMenuItem onClick={handleDeleteClick} className="text-red-600">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Tags and subject */}
        <div className="flex flex-wrap gap-2 mb-3">
          <Badge variant="secondary">{document.subject || document.metadata?.subject || 'General'}</Badge>
          {document.is_owned && <Badge variant="default">Owned</Badge>}
          {document.is_shared && <Badge variant="outline">Shared</Badge>}
          {document.tags?.slice(0, 2).map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
          {document.tags && document.tags.length > 2 && (
            <Badge variant="outline" className="text-xs">
              +{document.tags.length - 2}
            </Badge>
          )}
        </div>

        {/* Metadata */}
        <div className="space-y-2 text-sm text-muted-foreground mb-4 flex-1">
          <div className="flex items-center gap-2">
            <User className="h-3.5 w-3.5" />
            <span className="truncate">{document.uploader_name || 'Unknown'}</span>
          </div>
          {getLastActivityText() && (
            <div className="flex items-center gap-2">
              <Clock className="h-3.5 w-3.5" />
              <span>Active {getLastActivityText()}</span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-xs">
              {document.chunks_count || 0} chunks • {formatFileSize(document.file_size)}
            </span>
            {getStatusBadge()}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-4 border-t">
          <Button
            variant="default"
            size="sm"
            className="flex-1"
            onClick={handleChatClick}
            disabled={document.status !== 'completed'}
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            Chat
          </Button>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" className="flex-1 relative" disabled>
                  <FileText className="h-4 w-4 mr-2" />
                  Open
                  <Sparkles className="h-3 w-3 ml-1 text-primary" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Document viewer coming in v2.0</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>
    </Card>
  )
}

