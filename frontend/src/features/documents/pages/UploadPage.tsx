/**
 * UploadPage
 * Document upload page with stepper
 */
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, AlertCircle, Info, CheckCircle2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button, Input, Card, FileUploader } from '@/components/ui'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useDocumentUpload } from '../hooks/useDocumentUpload'
import { useDocumentStore } from '../stores/documentStore'
import { UploadProgressModal } from '../components/UploadProgressModal'
import type { DocumentUploadRequest } from '@/api/types'
import { PageShell } from '@/components/layout/PageShell'
import { PageHeader } from '@/components/layout/PageHeader'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface UploadFormData {
  title: string
  subject: string
  grade_level: string
}

export function UploadPage() {
  const [step, setStep] = useState(1)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const { user } = useAuth()
  const { uploadProgress, uploadStage, uploadError } = useDocumentStore()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UploadFormData>()

  const uploadMutation = useDocumentUpload()

  const handleFileSelect = (files: File[]) => {
    if (files.length > 0) {
      setSelectedFile(files[0])
      setStep(2)
    }
  }

  const onSubmit = (data: UploadFormData) => {
    if (!selectedFile || !user) return

    const request: DocumentUploadRequest = {
      file: selectedFile,
      ...data,
      user_id: user.id,
      instructor_id: user.id,
    }

    uploadMutation.mutate(request)
  }

  // Show duplicate banner after successful upload if it's a duplicate
  const uploadResponse = uploadMutation.data
  const isDuplicate = uploadResponse?.is_duplicate

  return (
    <PageShell className="py-12 space-y-6">
      {/* Upload Progress Modal */}
      <UploadProgressModal
        isOpen={uploadMutation.isPending}
        progress={uploadProgress}
        stage={uploadStage}
        error={uploadError || undefined}
      />

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <PageHeader
          title="Upload Document"
          description="Upload your study materials to start asking questions"
          className="text-center"
        />
      </motion.div>

      {/* Duplicate Document Banner */}
      {uploadMutation.isSuccess && isDuplicate && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mx-auto max-w-2xl"
        >
          <Card className="border-blue-200 bg-blue-50">
            <Card.Body>
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-600 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-blue-900 mb-1">
                    Document Already Exists
                  </h4>
                  <p className="text-sm text-blue-800 mb-3">
                    This document already exists in the knowledge base and has been linked to your library.
                    You can start asking questions right away!
                  </p>
                  <Link to={`/chat/${uploadResponse.content_id}`}>
                    <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      Ask Questions
                    </Button>
                  </Link>
                </div>
              </div>
            </Card.Body>
          </Card>
        </motion.div>
      )}

      {/* Tabs Stepper */}
      <Tabs value={String(step)} className="mb-8">
        <TabsList className="mx-auto flex">
          <TabsTrigger value="1" onClick={() => setStep(1)}>Select File</TabsTrigger>
          <TabsTrigger value="2" disabled={!selectedFile} onClick={() => selectedFile && setStep(2)}>Add Details</TabsTrigger>
          <TabsTrigger value="3" disabled={!uploadMutation.isSuccess}>Upload</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Step 1: File Selection */}
      {step === 1 && (
        <motion.div
          key="step1"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
        >
          <Card>
            <Card.Body>
              <div className="mb-4 text-sm text-muted-foreground">
                Drag and drop a file below, or click to browse. Accepted: PDF, TXT, MD, DOCX. Max 50MB.
              </div>
              <FileUploader
                onFilesChange={handleFileSelect}
                accept=".pdf,.txt,.md,.docx"
                maxFiles={1}
              />
            </Card.Body>
          </Card>
        </motion.div>
      )}

      {/* Step 2: Metadata Form */}
      {step === 2 && (
        <motion.div
          key="step2"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
        >
          <Card>
            <Card.Body>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div className="flex items-center gap-3 p-4 bg-primary-50 rounded-lg">
                  <FileText className="h-6 w-6 text-primary-600" />
                  <div>
                    <p className="font-medium text-slate-900">{selectedFile?.name}</p>
                    <p className="text-sm text-slate-600">
                      {selectedFile && (selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>

                <motion.div
                  animate={errors.title ? { x: [0, -10, 10, -10, 10, 0] } : {}}
                  transition={{ duration: 0.4 }}
                >
                  <Input
                    label="Document Title"
                    placeholder="e.g., IB Chemistry Notes - Chapter 5"
                    error={errors.title?.message}
                    {...register('title', { required: 'Title is required' })}
                  />
                  <AnimatePresence>
                    {errors.title && (
                      <motion.p
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="mt-1 text-sm text-red-600 flex items-center gap-1"
                      >
                        <AlertCircle className="h-3 w-3" />
                        {errors.title.message}
                      </motion.p>
                    )}
                  </AnimatePresence>
                </motion.div>

                <motion.div
                  animate={errors.subject ? { x: [0, -10, 10, -10, 10, 0] } : {}}
                  transition={{ duration: 0.4 }}
                >
                  <Input
                    label="Subject"
                    placeholder="e.g., Chemistry"
                    error={errors.subject?.message}
                    {...register('subject', { required: 'Subject is required' })}
                  />
                </motion.div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">
                    Grade Level
                  </label>
                  <select
                    className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    {...register('grade_level', { required: 'Grade level is required' })}
                  >
                    <option value="">Select grade level</option>
                    <option value="grade_9">Grade 9</option>
                    <option value="grade_10">Grade 10</option>
                    <option value="grade_11">Grade 11</option>
                    <option value="grade_12">Grade 12</option>
                    <option value="ib">IB</option>
                  </select>
                  {errors.grade_level && (
                    <p className="mt-1.5 text-sm text-red-600">{errors.grade_level.message}</p>
                  )}
                </div>

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1"
                    onClick={() => {
                      setStep(1)
                      setSelectedFile(null)
                    }}
                  >
                    Back
                  </Button>
                  <Button
                    type="submit"
                    className="flex-1"
                    leftIcon={<Upload className="h-5 w-5" />}
                    isLoading={uploadMutation.isPending}
                  >
                    Upload Document
                  </Button>
                </div>
              </form>
            </Card.Body>
          </Card>
        </motion.div>
      )}
    </PageShell>
  )
}

