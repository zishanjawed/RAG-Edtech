/**
 * Student List Page - 2025 Edition
 * Clean professional table with search, filters, and mobile cards
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Users, Search, UserPlus, MoreHorizontal, Clock } from 'lucide-react'
import { Button, Badge, Avatar } from '@/components/ui'
import { Card, CardBody } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { teacherService } from '@/api/teacher.service'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { PageShell } from '@/components/layout/PageShell'
import { PageHeader } from '@/components/layout/PageHeader'

interface StudentRow {
  student_id: string
  student_name?: string
  student_email?: string
  total_questions: number
  unique_content: number
  avg_response_time: number
  last_activity: string
  days_active: number
  status: 'active' | 'inactive'
}

export function StudentListPage() {
  const { user } = useAuth()
  const [teacherId] = useState(user?.id || '')
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')

  const { data, isLoading, error } = useQuery({
    queryKey: ['teacher-students', teacherId],
    queryFn: () => teacherService.getAllStudents(teacherId),
    enabled: !!teacherId,
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const getInitials = (id: string) => {
    return id.slice(0, 2).toUpperCase()
  }

  // Transform and filter data
  const students: StudentRow[] = data?.students
    .map((s) => ({
      student_id: s.student_id || '',
      student_name: s.student_name,
      student_email: s.student_email,
      total_questions: s.total_questions || 0,
      unique_content: s.unique_content || 0,
      avg_response_time: s.avg_response_time || 0,
      last_activity: s.last_activity || new Date().toISOString(),
      days_active: s.days_active || 0,
      status: (s.status as 'active' | 'inactive') || 'inactive',
    }))
    .filter((s) => {
      const searchLower = searchQuery.toLowerCase()
      const matchesSearch = 
        s.student_id.toLowerCase().includes(searchLower) ||
        s.student_name?.toLowerCase().includes(searchLower) ||
        s.student_email?.toLowerCase().includes(searchLower)
      const matchesStatus = statusFilter === 'all' || s.status === statusFilter
      return matchesSearch && matchesStatus
    }) || []

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-20 w-full" />
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <Card className="flex flex-col items-center justify-center p-12 shadow-soft-md">
          <Users className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-semibold">No students yet</h3>
          <p className="text-sm text-muted-foreground mt-2 text-center max-w-sm">
            Student activity will appear here once they start asking questions
          </p>
          <Button className="mt-6 gap-2" disabled>
            <UserPlus className="h-4 w-4" />
            Add First Student
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <PageShell className="py-6 space-y-6">
      <PageHeader
        title="Students"
        description={`Manage and monitor student activity (${data.total_count} total)`}
        actions={
          <Button className="gap-2" disabled>
            <UserPlus className="h-4 w-4" />
            Add Student
          </Button>
        }
      />

      {/* Search & Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search students..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={statusFilter === 'all' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setStatusFilter('all')}
          >
            All
          </Button>
          <Button
            variant={statusFilter === 'active' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setStatusFilter('active')}
          >
            Active
          </Button>
          <Button
            variant={statusFilter === 'inactive' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setStatusFilter('inactive')}
          >
            Inactive
          </Button>
        </div>
      </div>

      {/* Desktop Table */}
      <Card className="shadow-soft-md hidden md:block">
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-card">
            <TableRow className="hover:bg-transparent">
              <TableHead>Student</TableHead>
              <TableHead className="text-right">Questions</TableHead>
              <TableHead className="text-right">Content</TableHead>
              <TableHead className="text-right">Avg Response</TableHead>
              <TableHead>Last Activity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-[70px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {students.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-12">
                  <div className="flex flex-col items-center text-muted-foreground">
                    <Users className="h-8 w-8 mb-2" />
                    <p>No students found</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              students.map((student) => (
                <TableRow
                  key={student.student_id}
                  className="hover:bg-muted/50 transition-colors cursor-pointer h-14"
                >
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <Avatar
                        name={student.student_name || getInitials(student.student_id)}
                        size="sm"
                        className="bg-primary/10 text-primary"
                      />
                      <div>
                        <div className="font-medium">
                          {student.student_name || `student:${student.student_id.slice(0, 8)}`}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {student.student_email || `ID: ${student.student_id.slice(0, 12)}...`}
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="font-medium text-right tabular-nums">{student.total_questions}</TableCell>
                  <TableCell className="text-right tabular-nums">{student.unique_content}</TableCell>
                  <TableCell className="text-muted-foreground text-right">
                    <div className="inline-flex items-center justify-end gap-1">
                      <Clock className="h-3 w-3" />
                      <span className="tabular-nums">{Math.round(student.avg_response_time)}ms</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDate(student.last_activity)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={student.status === 'active' ? 'success' : 'default'}>
                      {student.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>View Details</DropdownMenuItem>
                        <DropdownMenuItem>Send Message</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-destructive">
                          Remove
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-3">
        {students.length === 0 ? (
          <Card className="shadow-soft-sm p-12 flex flex-col items-center text-center">
            <Users className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-muted-foreground">No students found</p>
          </Card>
        ) : (
          students.map((student) => (
            <Card key={student.student_id} variant="default" hover>
              <CardBody className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Avatar
                      name={student.student_name || getInitials(student.student_id)}
                      size="md"
                      className="bg-primary/10 text-primary"
                    />
                    <div>
                      <div className="font-medium">
                        {student.student_name || `student:${student.student_id.slice(0, 8)}`}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {student.student_email || `ID: ${student.student_id.slice(0, 16)}...`}
                      </div>
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>View Details</DropdownMenuItem>
                      <DropdownMenuItem>Send Message</DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-destructive">
                        Remove
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                <Separator className="my-3" />
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground text-xs">Questions</div>
                    <div className="font-semibold mt-1">{student.total_questions}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground text-xs">Content</div>
                    <div className="font-semibold mt-1">{student.unique_content}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground text-xs">Last Activity</div>
                    <div className="font-semibold mt-1 text-xs">{formatDate(student.last_activity)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground text-xs">Status</div>
                    <Badge variant={student.status === 'active' ? 'success' : 'default'} className="mt-1">
                      {student.status}
                    </Badge>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))
        )}
      </div>
    </PageShell>
  )
}
