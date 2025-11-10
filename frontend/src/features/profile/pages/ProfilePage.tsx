/**
 * ProfilePage
 * View and update user profile (name, email)
 */
import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { authService } from '@/api/auth.service'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useAuthStore } from '@/features/auth/stores/authStore'
import { Card, Button, Input } from '@/components/ui'
import { useToast } from '@/hooks/useToast'

export function ProfilePage() {
  const { user } = useAuth()
  const setUser = useAuthStore((s) => s.setUser)
  const { success, error } = useToast()

  const [fullName, setFullName] = useState(user?.full_name || '')

  useEffect(() => {
    setFullName(user?.full_name || '')
  }, [user])

  const { mutateAsync: updateProfile, isPending } = useMutation({
    mutationFn: (data: { full_name?: string }) => authService.updateProfile(data),
    onSuccess: (updated) => {
      setUser(updated)
      success('Profile updated', 'Your name has been saved.')
    },
    onError: (err: Error) => {
      error('Update failed', err.message || 'Please try again.')
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await updateProfile({
      full_name: fullName.trim() || undefined,
    })
  }

  return (
    <div className="mx-auto max-w-2xl p-6">
      <Card>
        <Card.Header>
          <h3 className="text-lg font-semibold">Profile</h3>
          <p className="text-sm text-muted-foreground">Manage your account information</p>
        </Card.Header>
        <Card.Body>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Email</label>
              <div className="text-sm text-muted-foreground">{user?.email}</div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Full name</label>
              <Input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your name"
              />
            </div>
            <div className="flex justify-end">
              <Button type="submit" disabled={isPending}>
                {isPending ? 'Saving...' : 'Save changes'}
              </Button>
            </div>
          </form>
        </Card.Body>
      </Card>
    </div>
  )
}


