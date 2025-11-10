/**
 * UploadDialog Component
 * Modal dialog for uploading new documents with metadata
 */

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../../components/ui/dialog'
import { Button } from '../../../components/ui/Button'
import { Input } from '../../../components/ui/Input'
import { Label } from '../../../components/ui/label'
import { FileUploader } from '../../../components/ui/FileUploader'
import { Badge } from '../../../components/ui/Badge'
import { Alert, AlertDescription } from '../../../components/ui/alert'
import { Progress } from '../../../components/ui/progress'
import { Info, Upload, CheckCircle, Loader2 } from 'lucide-react'
import { Document } from '../../../api/types'
import { useAuth } from '../../auth/hooks/useAuth'

interface UploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onUploadComplete?: (document: Document) => void
}

export function UploadDialog({ open, onOpenChange, onUploadComplete }: UploadDialogProps) {
  const { user } = useAuth()
  const [files, setFiles] = useState<File[]>([])
  const [title, setTitle] = useState('')
  const [subject, setSubject] = useState('')
  const [tags, setTags] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [uploadedDoc, setUploadedDoc] = useState<Document | null>(null)
  const [processingStatus, setProcessingStatus] = useState('')
  const [processingProgress, setProcessingProgress] = useState(0)

  const handleFilesChange = (newFiles: File[]) => {
    setFiles(newFiles)
    // Auto-fill title from filename if empty
    if (newFiles.length > 0 && !title) {
      const filename = newFiles[0].name.replace(/\.[^/.]+$/, '') // Remove extension
      setTitle(filename)
    }
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setIsUploading(true)
    setUploadSuccess(false)
    setProcessingStatus('Uploading...')
    setProcessingProgress(0)

    try {
      const file = files[0]
      
      // Upload document via real API
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      
      if (!user) {
        throw new Error('User not authenticated')
      }
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('user_id', user.id)
      formData.append('title', title || file.name)
      if (subject) formData.append('subject', subject)
      if (tags) formData.append('tags', tags)

      const response = await fetch(`${apiBaseUrl}/api/content/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const document = await response.json()
      setUploadedDoc(document)

      // Connect to WebSocket for real-time status
      if (!document.is_duplicate) {
        connectWebSocket(document.content_id)
      } else {
        setUploadSuccess(true)
        setProcessingStatus('Duplicate detected - linked to your account')
        setProcessingProgress(100)
      }

      if (onUploadComplete) {
        onUploadComplete(document)
      }

      // Reset form after status complete
      if (document.is_duplicate) {
        setTimeout(() => {
          handleClose()
        }, 2000)
      }
    } catch (error) {
      console.error('Upload failed:', error)
      setProcessingStatus('Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const connectWebSocket = (contentId: string) => {
    const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
    const ws = new WebSocket(`${wsBaseUrl}/ws/document/${contentId}/status`)

    ws.onopen = () => {
      console.log('WebSocket connected for', contentId)
      // Send heartbeat every 25 seconds
      const heartbeat = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        } else {
          clearInterval(heartbeat)
        }
      }, 25000)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket status:', data)

      if (data.type === 'heartbeat' || data.type === 'pong') {
        return
      }

      setProcessingStatus(data.message || `Status: ${data.status}`)
      setProcessingProgress(data.progress || 0)

      if (data.status === 'completed') {
        setUploadSuccess(true)
        ws.close()
        
        // Close dialog after 2 seconds
        setTimeout(() => {
          handleClose()
        }, 2000)
      } else if (data.status === 'failed') {
        setProcessingStatus('Processing failed')
        ws.close()
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setProcessingStatus('Connection error - status unknown')
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
    }
  }

  const handleClose = () => {
    if (!isUploading) {
      setFiles([])
      setTitle('')
      setSubject('')
      setTags('')
      setUploadSuccess(false)
      setUploadedDoc(null)
      setProcessingStatus('')
      setProcessingProgress(0)
      onOpenChange(false)
    }
  }

  const isFormValid = files.length > 0 && title.trim() !== ''

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
          <DialogDescription>
            Add a new document to your knowledge base. Supported formats: PDF, TXT, MD, DOCX
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* File uploader */}
          <FileUploader
            onFilesChange={handleFilesChange}
            accept=".pdf,.txt,.md,.docx"
            maxSize={50 * 1024 * 1024}
            maxFiles={1}
            multiple={false}
            disabled={isUploading || uploadSuccess}
          />

          {/* Processing status */}
          {isUploading && processingStatus && (
            <Alert className="border-blue-200 bg-blue-50">
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
              <AlertDescription className="text-blue-800">
                <div className="space-y-2">
                  <div>{processingStatus}</div>
                  {processingProgress > 0 && (
                    <Progress value={processingProgress} className="h-2" />
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Success message */}
          {uploadSuccess && uploadedDoc && (
            <Alert className="border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                {uploadedDoc.is_duplicate ? (
                  <>
                    Document already exists in knowledge base! Linked to your account.
                    <Badge variant="secondary" className="ml-2">
                      Duplicate Detected
                    </Badge>
                  </>
                ) : (
                  `Document processed successfully! ${processingProgress}% complete`
                )}
              </AlertDescription>
            </Alert>
          )}

          {/* Metadata form */}
          <div className="grid gap-4">
            <div className="space-y-2">
              <Label htmlFor="title">Title *</Label>
              <Input
                id="title"
                placeholder="Document title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={isUploading || uploadSuccess}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                placeholder="e.g., Chemistry, Physics, Biology, Mathematics"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                disabled={isUploading || uploadSuccess}
              />
              <p className="text-xs text-muted-foreground">
                Enter the subject area for this document
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">Tags (comma-separated)</Label>
              <Input
                id="tags"
                placeholder="e.g., stoichiometry, moles, calculations"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                disabled={isUploading || uploadSuccess}
              />
              <p className="text-xs text-muted-foreground">
                Add tags to help organize and find your documents
              </p>
            </div>
          </div>

          {/* Info message */}
          {!uploadSuccess && !isUploading && (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Your document will be processed automatically with real-time status updates. 
                You'll be able to chat with it once processing is complete (usually 1-2 minutes).
              </AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isUploading}>
            {uploadSuccess ? 'Close' : 'Cancel'}
          </Button>
          {!uploadSuccess && (
            <Button onClick={handleUpload} disabled={!isFormValid || isUploading}>
              {isUploading ? (
                <>
                  <Upload className="mr-2 h-4 w-4 animate-pulse" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

