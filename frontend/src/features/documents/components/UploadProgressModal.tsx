/**
 * UploadProgressModal Component
 * Animated upload progress with processing steps
 */
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, CheckCircle2, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui/Card'

interface UploadProgressModalProps {
  isOpen: boolean
  progress: number
  stage?: 'uploading' | 'extracting' | 'chunking' | 'embedding' | 'finalizing' | 'complete' | 'error'
  error?: string
}

const stages = [
  { id: 'uploading', label: 'Uploading file', threshold: 20 },
  { id: 'extracting', label: 'Extracting text', threshold: 40 },
  { id: 'chunking', label: 'Creating chunks', threshold: 60 },
  { id: 'embedding', label: 'Generating embeddings', threshold: 80 },
  { id: 'finalizing', label: 'Finalizing', threshold: 100 },
]

export function UploadProgressModal({ 
  isOpen, 
  progress, 
  stage = 'uploading',
  error 
}: UploadProgressModalProps) {
  if (!isOpen) return null

  const isComplete = progress === 100 && stage === 'complete'
  const hasError = stage === 'error' || !!error

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: "spring", damping: 25 }}
          >
            <Card className="w-full max-w-md p-8">
              <div className="text-center space-y-6">
                {/* Animated Icon */}
                <motion.div
                  className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center"
                  animate={!isComplete && !hasError ? { 
                    rotate: 360,
                    scale: [1, 1.1, 1]
                  } : {}}
                  transition={!isComplete && !hasError ? { 
                    rotate: { duration: 2, repeat: Infinity, ease: "linear" },
                    scale: { duration: 1, repeat: Infinity }
                  } : {}}
                >
                  {hasError ? (
                    <motion.div
                      initial={{ scale: 0, rotate: -180 }}
                      animate={{ scale: 1, rotate: 0 }}
                      transition={{ type: "spring", stiffness: 500 }}
                    >
                      <AlertCircle className="h-8 w-8 text-red-600" />
                    </motion.div>
                  ) : isComplete ? (
                    <motion.div
                      initial={{ scale: 0, rotate: -180 }}
                      animate={{ scale: 1, rotate: 0 }}
                      transition={{ type: "spring", stiffness: 500 }}
                    >
                      <CheckCircle2 className="h-8 w-8 text-green-600" />
                    </motion.div>
                  ) : (
                    <Upload className="h-8 w-8 text-primary" />
                  )}
                </motion.div>

                {/* Title */}
                <div>
                  <h3 className="text-xl font-semibold mb-2">
                    {hasError ? 'Upload Failed' : isComplete ? 'Upload Complete!' : 'Uploading Document'}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {hasError 
                      ? error || 'An error occurred during upload'
                      : isComplete 
                        ? 'Your document is ready to use'
                        : 'Processing your file...'}
                  </p>
                </div>

                {/* Progress Bar */}
                {!hasError && !isComplete && (
                  <div className="space-y-2">
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-primary via-primary-600 to-primary-700"
                        initial={{ width: "0%" }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.5, ease: "easeOut" }}
                      />
                    </div>
                    <p className="text-sm font-medium">{progress}%</p>
                  </div>
                )}

                {/* Processing Steps */}
                {!hasError && (
                  <div className="space-y-2 text-left">
                    {stages.map((s, i) => {
                      const isDone = progress >= s.threshold
                      const isCurrent = stage === s.id

                      return (
                        <motion.div
                          key={s.id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.1 }}
                          className="flex items-center gap-2 text-sm"
                        >
                          {isDone ? (
                            <motion.div
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              transition={{ type: "spring", stiffness: 500 }}
                            >
                              <CheckCircle2 className="h-4 w-4 text-green-600" />
                            </motion.div>
                          ) : isCurrent ? (
                            <motion.div
                              animate={{ rotate: 360 }}
                              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                              className="h-4 w-4"
                            >
                              <div className="h-full w-full rounded-full border-2 border-primary border-t-transparent" />
                            </motion.div>
                          ) : (
                            <div className="h-4 w-4 rounded-full border-2 border-muted" />
                          )}
                          <span className={isDone || isCurrent ? "text-foreground font-medium" : "text-muted-foreground"}>
                            {s.label}
                          </span>
                        </motion.div>
                      )
                    })}
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

