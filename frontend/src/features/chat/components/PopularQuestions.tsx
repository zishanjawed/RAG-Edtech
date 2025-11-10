/**
 * PopularQuestions Component
 * Displays frequently asked questions for a document
 */
import { motion } from 'framer-motion'
import { TrendingUp, Zap, MessageSquare } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import type { PopularQuestion } from '@/api/types'

interface PopularQuestionsProps {
  questions: PopularQuestion[]
  onQuestionClick: (question: string) => void
  isLoading?: boolean
}

export function PopularQuestions({ questions, onQuestionClick, isLoading = false }: PopularQuestionsProps) {
  if (isLoading) {
    return (
      <Card className="mb-4">
        <Card.Header>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary-600" />
            <h3 className="text-sm font-semibold text-slate-900">Frequently Asked Questions</h3>
          </div>
        </Card.Header>
        <Card.Body>
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-slate-100 rounded-lg animate-pulse" />
            ))}
          </div>
        </Card.Body>
      </Card>
    )
  }

  if (questions.length === 0) {
    return (
      <Card className="mb-4">
        <Card.Header>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary-600" />
            <h3 className="text-sm font-semibold text-slate-900">Frequently Asked Questions</h3>
          </div>
        </Card.Header>
        <Card.Body>
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <MessageSquare className="h-8 w-8 text-slate-300 mb-2" />
            <p className="text-sm text-slate-500">
              No popular questions yet
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Ask questions to see popular ones here
            </p>
          </div>
        </Card.Body>
      </Card>
    )
  }

  return (
    <Card className="mb-4">
      <Card.Header>
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary-600" />
          <h3 className="text-sm font-semibold text-slate-900">Frequently Asked Questions</h3>
        </div>
      </Card.Header>
      <Card.Body>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {questions.map((question, index) => (
            <motion.button
              key={`${question.question}-${index}`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => onQuestionClick(question.question)}
              className="w-full text-left p-3 rounded-lg border border-slate-200 hover:border-primary-300 hover:bg-primary-50 transition-all group"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-slate-700 group-hover:text-primary-700 line-clamp-2 flex-1">
                  {question.question}
                </p>
                <div className="flex items-center gap-1 flex-shrink-0">
                  {question.is_cached && (
                    <div className="flex items-center justify-center w-5 h-5 rounded-full bg-green-100">
                      <Zap className="h-3 w-3 text-green-600" />
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
                  Asked {question.frequency}x
                </span>
                {question.is_cached && (
                  <span className="text-xs text-green-600 font-medium">
                    Instant response
                  </span>
                )}
              </div>
            </motion.button>
          ))}
        </div>
      </Card.Body>
    </Card>
  )
}

