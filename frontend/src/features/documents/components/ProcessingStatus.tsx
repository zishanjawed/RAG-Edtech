/**
 * ProcessingStatus Component
 * Shows document processing status inline
 */
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'

interface ProcessingStatusProps {
  status: 'processing' | 'ready' | 'failed'
  totalChunks: number
  processedChunks: number
}

export function ProcessingStatus({ 
  status, 
  totalChunks, 
  processedChunks 
}: ProcessingStatusProps) {
  const progress = totalChunks > 0 ? (processedChunks / totalChunks) * 100 : 0

  if (status !== 'processing') return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="relative overflow-hidden rounded-lg border border-primary/20 bg-primary/5 p-4"
    >
      {/* Animated background gradient */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent"
        animate={{ x: [-1000, 1000] }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
      />

      <div className="relative z-10 flex items-center gap-4">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        >
          <Loader2 className="h-5 w-5 text-primary" />
        </motion.div>
        
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium">Processing Document</span>
            <span className="text-xs text-muted-foreground">
              {processedChunks}/{totalChunks} chunks
            </span>
          </div>
          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-primary"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

