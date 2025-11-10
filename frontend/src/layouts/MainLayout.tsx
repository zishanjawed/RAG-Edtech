/**
 * MainLayout - 2025 Edition
 * Clean sidebar layout inspired by Linear and Vercel
 */
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { 
  GraduationCap, 
  Upload, 
  LogOut, 
  BarChart3, 
  Users, 
  Home,
  Settings,
  User,
  ChevronUp,
  PanelLeft,
  FileText,
  MessageSquareMore
} from 'lucide-react'
import { Button, Avatar } from '@/components/ui'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useAuthStore } from '@/features/auth/stores/authStore'
import { authService } from '@/api/auth.service'
import { useQuery } from '@tanstack/react-query'
import { cn } from '@/lib/utils'
import { PageTransition } from '@/components/layout/PageTransition'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Header } from '@/components/layout/Header'
import { Breadcrumbs, Crumb } from '@/components/layout/Breadcrumbs'
import { useEffect, useState } from 'react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

// Student navigation
const studentNavigation = [
  { name: 'Dashboard', to: '/analytics', icon: Home },
  { name: 'Documents', to: '/documents', icon: FileText },
  { name: 'Chat', to: '/chat/global', icon: MessageSquareMore },
  { name: 'My Analytics', to: '/analytics', icon: BarChart3 },
]

// Teacher navigation
const teacherNavigation = [
  { name: 'Dashboard', to: '/teacher/dashboard', icon: Home },
  { name: 'Documents', to: '/documents', icon: FileText },
  { name: 'Chat', to: '/chat/global', icon: MessageSquareMore },
  { name: 'Students', to: '/teacher/students', icon: Users },
]

export function MainLayout() {
  const { user, logout, token } = useAuth()
  const setUser = useAuthStore((s) => s.setUser)
  const location = useLocation()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('sidebar-collapsed')
    if (saved) setCollapsed(saved === 'true')
  }, [])
  useEffect(() => {
    localStorage.setItem('sidebar-collapsed', String(collapsed))
  }, [collapsed])

  // Hydrate user info on app load if token exists but user is not set
  const { data: me } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => authService.getMe(),
    enabled: !!token && !user,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  })

  useEffect(() => {
    if (me) setUser(me)
  }, [me, setUser])

  // Select navigation based on user role
  const navigation = user?.role === 'teacher' ? teacherNavigation : studentNavigation

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar - Clean 2025 Design */}
      <aside className={cn('border-r border-border bg-card hidden md:flex flex-col transition-all duration-200', collapsed ? 'w-16' : 'w-64')}>
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className={cn('flex h-14 items-center border-b border-border', collapsed ? 'px-3' : 'px-6')}>
            <Link 
              to={user?.role === 'teacher' ? '/teacher/dashboard' : '/dashboard'} 
              className={cn('flex items-center', collapsed ? 'justify-center w-full' : 'gap-2')}
            >
              <GraduationCap className="h-6 w-6 text-primary" />
              {!collapsed && <span className="text-lg font-semibold text-foreground">RAG Edtech</span>}
            </Link>
          </div>

          {/* Navigation */}
          <nav className={cn('flex-1 space-y-1', collapsed ? 'p-2' : 'p-3')}>
            {navigation.map((item) => {
              const isActive = location.pathname.startsWith(item.to)
              const Icon = item.icon

              return (
                <Button
                  key={item.name}
                  variant={isActive ? 'secondary' : 'ghost'}
                  className={cn(
                    'w-full',
                    collapsed ? 'justify-center' : 'justify-start',
                    isActive && 'bg-secondary/40 font-medium relative'
                  )}
                >
                  {collapsed ? (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Link
                            to={item.to}
                            className={cn('inline-flex items-center gap-2 w-full justify-center')}
                          >
                            {isActive && <span className="absolute left-0 top-0 h-full w-1 rounded-r bg-primary" aria-hidden="true" />}
                            <Icon className="h-4 w-4" />
                          </Link>
                        </TooltipTrigger>
                        <TooltipContent side="right">{item.name}</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  ) : (
                    <Link
                      to={item.to}
                      className="inline-flex items-center gap-2 w-full text-left"
                    >
                      {isActive && <span className="absolute left-0 top-0 h-full w-1 rounded-r bg-primary" aria-hidden="true" />}
                      <Icon className="h-4 w-4" />
                      <span>{item.name}</span>
                    </Link>
                  )}
                </Button>
              )
            })}
          </nav>

          {/* User Profile (bottom) */}
          <div className={cn('border-t border-border', collapsed ? 'p-2' : 'p-3')}>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className={cn('w-full', collapsed ? 'justify-center' : 'justify-start')}>
                  <Avatar name={user?.full_name || 'User'} size="sm" className="h-9 w-9" />
                  {!collapsed && (
                    <div className="ml-3 text-left text-sm flex-1">
                      <p className="font-medium text-foreground truncate">{user?.full_name}</p>
                      <p className="text-xs text-muted-foreground capitalize">{user?.role}</p>
                    </div>
                  )}
                  <ChevronUp className="ml-auto h-4 w-4 text-muted-foreground" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onSelect={(e) => {
                    e.preventDefault()
                    navigate('/profile')
                  }}
                >
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem
                  onSelect={(e) => {
                    e.preventDefault()
                    navigate('/settings')
                  }}
                >
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </aside>

      {/* Mobile Drawer */}
      <Dialog open={mobileOpen} onOpenChange={setMobileOpen}>
        <DialogContent className="p-0 max-w-xs left-0 top-0 h-full translate-x-0 translate-y-0 data-[state=open]:slide-in-from-left-2">
          <nav className="space-y-1 p-3">
            {navigation.map((item) => {
              const isActive = location.pathname.startsWith(item.to)
              const Icon = item.icon
              return (
                <Button
                  key={item.name}
                  variant={isActive ? 'secondary' : 'ghost'}
                  className="w-full justify-start"
                  onClick={() => setMobileOpen(false)}
                >
                  <Link to={item.to} className="inline-flex items-center gap-2 w-full text-left">
                    <Icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </Link>
                </Button>
              )
            })}
          </nav>
        </DialogContent>
      </Dialog>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Header
          title={buildCrumbs(location.pathname, navigation).slice(-1)[0]?.label || ''}
          actions={
            <>
              <div className="hidden md:block">
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                  onClick={() => setCollapsed((c) => !c)}
                  leftIcon={<PanelLeft className="h-4 w-4" />}
                >
                  {collapsed ? 'Expand' : 'Collapse'}
                </Button>
              </div>
              <div className="md:hidden">
                <Button variant="ghost" size="sm" onClick={() => setMobileOpen(true)}>
                  Menu
                </Button>
              </div>
            </>
          }
        >
          <Breadcrumbs
            items={buildCrumbs(location.pathname, navigation)}
          />
        </Header>
        <div className="h-[calc(100%-56px)]">
          <PageTransition routeKey={location.pathname}>
            <Outlet />
          </PageTransition>
        </div>
      </main>
    </div>
  )
}

function buildCrumbs(pathname: string, nav: { name: string; to: string }[]): Crumb[] {
  const segments = pathname.split('/').filter(Boolean)
  const crumbs: Crumb[] = []
  let current = ''
  for (const seg of segments) {
    current += `/${seg}`
    const match = nav.find(n => current.startsWith(n.to))
    if (match) {
      crumbs.push({ label: match.name, to: match.to })
    } else {
      // Fallback: capitalize segment
      const label = seg.replace(/[-_]/g, ' ')
      crumbs.push({ label: label.charAt(0).toUpperCase() + label.slice(1) })
    }
  }
  if (crumbs.length === 0) crumbs.push({ label: 'Home', to: '/' })
  // Deduplicate subsequent identical labels
  return crumbs.filter((c, i, arr) => i === 0 || c.label !== arr[i - 1].label)
}

