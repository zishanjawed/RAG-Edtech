/**
 * SuggestedPrompts Component
 * Displays clickable prompt suggestions for users
 */

import { SuggestedPrompt } from '../../../api/types'
import { Button } from '../../../components/ui/Button'
import { 
  Lightbulb, 
  BookOpen, 
  Scale, 
  ListOrdered, 
  Zap, 
  Target 
} from 'lucide-react'
import { motion } from 'framer-motion'

interface SuggestedPromptsProps {
  prompts: SuggestedPrompt[]
  onPromptClick: (prompt: string) => void
  className?: string
}

const categoryIcons = {
  definition: BookOpen,
  explanation: Lightbulb,
  comparison: Scale,
  procedure: ListOrdered,
  application: Zap,
  evaluation: Target,
}

export function SuggestedPrompts({ prompts, onPromptClick, className }: SuggestedPromptsProps) {
  if (prompts.length === 0) return null

  return (
    <div className={className}>
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-medium text-muted-foreground">Suggested Questions</h3>
      </div>
      
      <div className="flex flex-wrap gap-2">
        {prompts.map((prompt, index) => {
          const Icon = prompt.category ? categoryIcons[prompt.category] : Lightbulb
          
          return (
            <motion.div
              key={prompt.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPromptClick(prompt.text)}
                className="h-auto py-2 px-3 text-left whitespace-normal justify-start hover:bg-primary/10 hover:border-primary transition-colors"
              >
                <Icon className="h-3.5 w-3.5 mr-2 flex-shrink-0 mt-0.5" />
                <span className="text-sm">{prompt.text}</span>
              </Button>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

