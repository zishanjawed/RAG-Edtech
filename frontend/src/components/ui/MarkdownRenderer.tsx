/**
 * MarkdownRenderer Component
 * Renders markdown with syntax highlighting for code blocks
 */
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { cn } from '@/lib/utils'
import 'highlight.js/styles/github-dark.css'

export interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div
      className={cn(
        'prose prose-slate max-w-none',
        'prose-headings:font-semibold prose-headings:text-slate-900',
        'prose-p:text-slate-700 prose-p:leading-relaxed',
        'prose-a:text-primary-600 prose-a:no-underline hover:prose-a:underline',
        'prose-strong:text-slate-900 prose-strong:font-semibold',
        'prose-code:rounded prose-code:bg-slate-100 prose-code:px-1.5 prose-code:py-0.5',
        'prose-code:text-sm prose-code:text-slate-800 prose-code:before:content-none prose-code:after:content-none',
        'prose-pre:rounded-lg prose-pre:bg-slate-900 prose-pre:p-4',
        'prose-blockquote:border-l-4 prose-blockquote:border-primary-500 prose-blockquote:bg-primary-50',
        'prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-slate-700',
        'prose-ul:list-disc prose-ol:list-decimal',
        'prose-li:text-slate-700 prose-li:marker:text-primary-600',
        'prose-img:rounded-lg prose-img:shadow-md',
        'prose-hr:border-slate-200',
        'prose-table:border-collapse prose-table:border prose-table:border-slate-200',
        'prose-th:border prose-th:border-slate-200 prose-th:bg-slate-50 prose-th:p-2 prose-th:font-semibold',
        'prose-td:border prose-td:border-slate-200 prose-td:p-2',
        className
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Custom link handling (open external links in new tab)
          a: ({ ...props }) => {
            const isExternal = props.href?.startsWith('http')
            return (
              <a
                {...props}
                target={isExternal ? '_blank' : undefined}
                rel={isExternal ? 'noopener noreferrer' : undefined}
              />
            )
          },
          // Custom code block styling
          code: ({ className, children, ...props }: React.HTMLAttributes<HTMLElement>) => {
            return (
              <code className={className} {...props}>
                {children}
              </code>
            )
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

