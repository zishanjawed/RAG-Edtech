/**
 * SourceCitations
 * Display source citations from RAG responses
 */
import { ExternalLink, FileText, User, Calendar, Hash, TrendingUp } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import type { SourceReference } from '@/api/types'

interface SourceCitationsProps {
  sources: SourceReference[]
}

export function SourceCitations({ sources }: SourceCitationsProps) {
  if (!sources || sources.length === 0) {
    return null
  }

  return (
    <div className="mt-4 space-y-2">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
        <FileText className="h-4 w-4" />
        <span>Sources ({sources.length})</span>
      </div>
      <div className="grid gap-2">
        {sources.map((source) => (
          <Card 
            key={source.source_id}
            className="border-l-4 border-l-primary-500 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer group"
          >
            <Card.Body className="p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="secondary" className="text-xs">
                      Source {source.source_id}
                    </Badge>
                    <span className="font-medium text-sm text-slate-900 truncate">
                      {source.document_title}
                    </span>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-600">
                    <div className="flex items-center gap-1" title="Uploaded by">
                      <User className="h-3 w-3" />
                      <span>{source.uploader_name}</span>
                    </div>
                    
                    <div className="flex items-center gap-1" title="Upload date">
                      <Calendar className="h-3 w-3" />
                      <span>{source.upload_date}</span>
                    </div>
                    
                    <div className="flex items-center gap-1" title="Chunk index">
                      <Hash className="h-3 w-3" />
                      <span>Chunk {source.chunk_index}</span>
                    </div>
                    
                    <div className="flex items-center gap-1" title="Similarity score">
                      <TrendingUp className="h-3 w-3" />
                      <span>{(source.similarity_score * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
                
                <ExternalLink className="h-4 w-4 text-slate-400 group-hover:text-primary-600 transition-colors flex-shrink-0" />
              </div>
            </Card.Body>
          </Card>
        ))}
      </div>
    </div>
  )
}

