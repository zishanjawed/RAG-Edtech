/**
 * App Component
 * Main application router with lazy loading
 */
import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './lib/react-query'
import { ToastContainer } from './components/ui'
import { ErrorBoundary } from './components/ErrorBoundary'
import { AnalyticsDashboardSkeleton } from './features/analytics/components/AnalyticsSkeleton'
import { ChatPageSkeleton } from './features/chat/components/ChatSkeleton'
import { TeacherDashboardSkeleton } from './features/teacher/components/TeacherSkeleton'

// Layouts
import { MainLayout } from './layouts/MainLayout'

// Auth (not lazy loaded - need immediate access)
import { LoginPage } from './features/auth/pages/LoginPage'
import { RegisterPage } from './features/auth/pages/RegisterPage'
import { ProtectedRoute } from './features/auth/components/ProtectedRoute'

// Lazy loaded pages
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })))
const UploadPage = lazy(() => import('./features/documents/pages/UploadPage').then(m => ({ default: m.UploadPage })))
const ChatPage = lazy(() => import('./features/chat/pages/ChatPage').then(m => ({ default: m.ChatPage })))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then(m => ({ default: m.NotFoundPage })))

// Import new pages directly (not lazy) to avoid import errors
import { DocumentsPage } from './features/documents/pages/DocumentsPage'
import { DocumentChatPage } from './features/chat/pages/DocumentChatPage'
import { GlobalChatPage } from './features/chat/pages/GlobalChatPage'

// Analytics
const StudentDashboard = lazy(() => import('./features/analytics/pages/StudentDashboard').then(m => ({ default: m.StudentDashboard })))
const DocumentDetailPage = lazy(() => import('./features/documents/pages/DocumentDetailPage').then(m => ({ default: m.DocumentDetailPage })))

// Teacher
const TeacherDashboard = lazy(() => import('./features/teacher/pages/TeacherDashboard').then(m => ({ default: m.TeacherDashboard })))
const StudentListPage = lazy(() => import('./features/teacher/pages/StudentListPage').then(m => ({ default: m.StudentListPage })))
const ContentEngagementPage = lazy(() => import('./features/teacher/pages/ContentEngagementPage').then(m => ({ default: m.ContentEngagementPage })))
const ProfilePage = lazy(() => import('./features/profile/pages/ProfilePage').then(m => ({ default: m.ProfilePage })))
const SettingsPage = lazy(() => import('./features/settings/pages/SettingsPage').then(m => ({ default: m.SettingsPage })))

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Suspense fallback={<AnalyticsDashboardSkeleton />}>
            <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected Routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<MainLayout />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                
                {/* Documents */}
                <Route path="/documents" element={<DocumentsPage />} />
                <Route path="/upload" element={<UploadPage />} />
                
                {/* Chat */}
                <Route path="/chat/global" element={<GlobalChatPage />} />
                <Route path="/chat/:documentId" element={<DocumentChatPage />} />
                
                {/* Student Analytics */}
                <Route path="/analytics" element={
                  <Suspense fallback={<AnalyticsDashboardSkeleton />}>
                    <StudentDashboard />
                  </Suspense>
                } />
                <Route path="/documents/:documentId/stats" element={<DocumentDetailPage />} />
                
                {/* Teacher Dashboard */}
                <Route path="/teacher/dashboard" element={
                  <Suspense fallback={<TeacherDashboardSkeleton />}>
                    <TeacherDashboard />
                  </Suspense>
                } />
                <Route path="/teacher/students" element={<StudentListPage />} />
                <Route path="/teacher/content/:contentId/engagement" element={<ContentEngagementPage />} />

                {/* Account */}
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>

            {/* 404 */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>

          {/* Toast Notifications */}
          <ToastContainer />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
