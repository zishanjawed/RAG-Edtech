/**
 * FileUploader Component
 * Drag-and-drop file uploader with validation and preview
 */
import { useCallback, useState } from 'react'
import { Upload, X, File, CheckCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import { formatFileSize } from '@/utils/formatters'

export interface FileWithPreview extends File {
  preview?: string
}

export interface FileUploaderProps {
  onFilesChange: (files: File[]) => void
  accept?: string
  maxSize?: number // in bytes
  maxFiles?: number
  multiple?: boolean
  disabled?: boolean
  className?: string
}

export function FileUploader({
  onFilesChange,
  accept = '.pdf,.txt,.md,.docx',
  maxSize = 50 * 1024 * 1024, // 50MB default
  maxFiles = 1,
  multiple = false,
  disabled = false,
  className,
}: FileUploaderProps) {
  const [files, setFiles] = useState<FileWithPreview[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [errors, setErrors] = useState<string[]>([])

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxSize) {
      return `File ${file.name} is too large. Maximum size is ${formatFileSize(maxSize)}.`
    }

    // Check file type
    if (accept) {
      const acceptedTypes = accept.split(',').map((t) => t.trim())
      const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
      if (!acceptedTypes.some((type) => type === fileExt || type === '*')) {
        return `File ${file.name} is not an accepted file type. Accepted: ${accept}`
      }
    }

    return null
  }

  const handleFiles = useCallback(
    (newFiles: FileList | null) => {
      if (!newFiles || disabled) return

      const fileArray = Array.from(newFiles)
      const validFiles: FileWithPreview[] = []
      const newErrors: string[] = []

      // Check max files limit
      if (files.length + fileArray.length > maxFiles) {
        newErrors.push(`Maximum ${maxFiles} file(s) allowed.`)
      } else {
        fileArray.forEach((file) => {
          const error = validateFile(file)
          if (error) {
            newErrors.push(error)
          } else {
            validFiles.push(file)
          }
        })
      }

      if (validFiles.length > 0) {
        const updatedFiles = multiple ? [...files, ...validFiles] : validFiles
        setFiles(updatedFiles)
        onFilesChange(updatedFiles)
      }

      setErrors(newErrors)
    },
    [files, maxFiles, multiple, disabled, onFilesChange, accept, maxSize, validateFile]
  )

  const removeFile = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index)
    setFiles(updatedFiles)
    onFilesChange(updatedFiles)
    setErrors([])
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) {
      setIsDragging(true)
    }
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (!disabled) {
      handleFiles(e.dataTransfer.files)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files)
    // Reset input to allow selecting the same file again
    e.target.value = ''
  }

  return (
    <div className={cn('w-full', className)}>
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          'relative rounded-lg border-2 border-dashed p-8 text-center transition-colors',
          isDragging && !disabled
            ? 'border-primary-500 bg-primary-50'
            : 'border-slate-300 bg-slate-50',
          disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer hover:border-primary-400'
        )}
      >
        <input
          type="file"
          onChange={handleInputChange}
          accept={accept}
          multiple={multiple}
          disabled={disabled}
          className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
          aria-label="File upload"
        />

        <div className="flex flex-col items-center gap-2">
          <Upload
            className={cn(
              'h-12 w-12',
              isDragging && !disabled ? 'text-primary-600' : 'text-slate-400'
            )}
          />
          <div>
            <p className="text-sm font-medium text-slate-700">
              {isDragging ? 'Drop files here' : 'Drag and drop files here, or click to browse'}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {accept} (max {formatFileSize(maxSize)})
            </p>
          </div>
        </div>
      </div>

      {/* Errors */}
      {errors.length > 0 && (
        <div className="mt-3 rounded-lg bg-red-50 p-3">
          {errors.map((error, index) => (
            <p key={index} className="text-sm text-red-600">
              {error}
            </p>
          ))}
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          <AnimatePresence>
            {files.map((file, index) => (
              <motion.div
                key={`${file.name}-${index}`}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -100 }}
                className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-3"
              >
                <File className="h-5 w-5 flex-shrink-0 text-primary-600" />
                <div className="flex-1 min-w-0">
                  <p className="truncate text-sm font-medium text-slate-700">{file.name}</p>
                  <p className="text-xs text-slate-500">{formatFileSize(file.size)}</p>
                </div>
                <CheckCircle className="h-5 w-5 flex-shrink-0 text-green-600" />
                <button
                  onClick={() => removeFile(index)}
                  disabled={disabled}
                  className="flex-shrink-0 rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label={`Remove ${file.name}`}
                >
                  <X className="h-4 w-4" />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}

