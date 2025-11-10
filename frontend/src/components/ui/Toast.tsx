/**
 * Toast Component
 * Notification system with animations
 */
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import { useToastStore, Toast as ToastType } from '@/hooks/useToast'
import { cn } from '@/lib/utils'

const toastIcons = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const toastStyles = {
  success: 'bg-accent-50 border-accent-200 text-accent-900',
  error: 'bg-red-50 border-red-200 text-red-900',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-900',
  info: 'bg-blue-50 border-blue-200 text-blue-900',
}

const iconStyles = {
  success: 'text-accent-600',
  error: 'text-red-600',
  warning: 'text-yellow-600',
  info: 'text-blue-600',
}

function ToastItem({ toast }: { toast: ToastType }) {
  const Icon = toastIcons[toast.type]
  const { removeToast } = useToastStore()

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -50, scale: 0.3 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: 300, scale: 0.5 }}
      transition={{
        type: "spring",
        stiffness: 500,
        damping: 30
      }}
      className={cn(
        'pointer-events-auto w-full max-w-sm overflow-hidden rounded-lg border shadow-lg',
        toastStyles[toast.type]
      )}
    >
      <div className="p-4">
        <div className="flex items-start">
          <motion.div 
            className="flex-shrink-0"
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ 
              type: "spring",
              stiffness: 500,
              damping: 25,
              delay: 0.1 
            }}
          >
            <Icon className={cn('h-6 w-6', iconStyles[toast.type])} aria-hidden="true" />
          </motion.div>

          <div className="ml-3 flex-1 pt-0.5">
            <p className="text-sm font-medium">{toast.title}</p>
            {toast.description && (
              <p className="mt-1 text-sm opacity-90">{toast.description}</p>
            )}
          </div>

          <div className="ml-4 flex flex-shrink-0">
            <motion.button
              type="button"
              className="inline-flex rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2"
              onClick={() => removeToast(toast.id)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <span className="sr-only">Close</span>
              <X className="h-5 w-5 opacity-50 hover:opacity-100" aria-hidden="true" />
            </motion.button>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export function ToastContainer() {
  const { toasts } = useToastStore()

  return (
    <div
      aria-live="assertive"
      className="pointer-events-none fixed inset-0 z-[1080] flex flex-col items-end gap-4 px-4 py-6 sm:p-6"
    >
      <AnimatePresence>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} />
        ))}
      </AnimatePresence>
    </div>
  )
}

