/**
 * SettingsPage
 * Account security settings (change password)
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { authService } from '@/api/auth.service'
import { Card, Button, Input } from '@/components/ui'
import { useToast } from '@/hooks/useToast'

export function SettingsPage() {
  const { success, error } = useToast()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')

  const { mutateAsync: changePassword, isPending } = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      authService.changePassword(data),
    onSuccess: (res) => {
      success('Password updated', res.message || 'Your password has been changed.')
      setCurrentPassword('')
      setNewPassword('')
    },
    onError: (err: Error) => {
      error('Update failed', err.message || 'Please try again.')
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await changePassword({
      current_password: currentPassword,
      new_password: newPassword,
    })
  }

  return (
    <div className="mx-auto max-w-2xl p-6">
      <Card>
        <Card.Header>
          <h3 className="text-lg font-semibold">Settings</h3>
          <p className="text-sm text-muted-foreground">Manage your account security</p>
        </Card.Header>
        <Card.Body>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Current password</label>
              <Input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">New password</label>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="At least 8 characters"
              />
            </div>
            <div className="flex justify-end">
              <Button type="submit" disabled={isPending || !currentPassword || !newPassword}>
                {isPending ? 'Saving...' : 'Change password'}
              </Button>
            </div>
          </form>
        </Card.Body>
      </Card>
    </div>
  )
}


