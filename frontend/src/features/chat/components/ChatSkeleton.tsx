/**
 * ChatSkeleton Component
 * Loading skeletons for chat interface
 */
import { Skeleton } from '@/components/ui/skeleton'

export function ChatHeaderSkeleton() {
  return (
    <div className="border-b border-slate-200 bg-white px-6 py-4">
      <div className="flex items-center gap-3">
        <Skeleton className="h-10 w-10 rounded-lg" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
    </div>
  )
}

export function MessageListSkeleton() {
  return (
    <div className="flex-1 bg-slate-50 px-6 py-6">
      <div className="mx-auto max-w-4xl space-y-6">
        {/* User message skeleton */}
        <div className="flex justify-end">
          <Skeleton className="h-12 w-64 rounded-2xl" />
        </div>

        {/* Assistant message skeleton */}
        <div className="flex justify-start">
          <div className="max-w-[85%] space-y-3 bg-white rounded-xl p-4 shadow-soft-sm">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-4/6" />
          </div>
        </div>

        {/* User message skeleton */}
        <div className="flex justify-end">
          <Skeleton className="h-16 w-72 rounded-2xl" />
        </div>

        {/* Assistant message skeleton */}
        <div className="flex justify-start">
          <div className="max-w-[85%] space-y-3 bg-white rounded-xl p-4 shadow-soft-sm">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        </div>
      </div>
    </div>
  )
}

export function ChatPageSkeleton() {
  return (
    <div className="flex h-screen flex-col">
      <ChatHeaderSkeleton />
      <MessageListSkeleton />
      <div className="border-t border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-4xl flex gap-3">
          <Skeleton className="flex-1 h-12 rounded-lg" />
          <Skeleton className="h-12 w-24 rounded-lg" />
        </div>
      </div>
    </div>
  )
}

