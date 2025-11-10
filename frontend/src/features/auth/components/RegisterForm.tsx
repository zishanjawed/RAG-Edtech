/**
 * RegisterForm Component
 * Registration form with role selection
 */
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Mail, Lock, User, Eye, EyeOff } from 'lucide-react'
import { Button, Input } from '@/components/ui'
import { useRegister } from '../hooks/useRegister'
import type { RegisterRequest } from '@/api/types'

export function RegisterForm() {
  const [showPassword, setShowPassword] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterRequest>()

  const registerMutation = useRegister()

  const onSubmit = (data: RegisterRequest) => {
    registerMutation.mutate(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Input
        label="Full Name"
        type="text"
        placeholder="John Doe"
        leftIcon={<User className="h-5 w-5" />}
        error={errors.full_name?.message}
        {...register('full_name', {
          required: 'Name is required',
          minLength: {
            value: 2,
            message: 'Name must be at least 2 characters',
          },
        })}
      />

      <Input
        label="Email"
        type="email"
        placeholder="you@example.com"
        leftIcon={<Mail className="h-5 w-5" />}
        error={errors.email?.message}
        {...register('email', {
          required: 'Email is required',
          pattern: {
            value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
            message: 'Invalid email address',
          },
        })}
      />

      <Input
        label="Password"
        type={showPassword ? 'text' : 'password'}
        placeholder="At least 8 characters"
        leftIcon={<Lock className="h-5 w-5" />}
        rightIcon={
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="text-slate-400 hover:text-slate-600"
          >
            {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
          </button>
        }
        error={errors.password?.message}
        helperText="Must contain at least 8 characters"
        {...register('password', {
          required: 'Password is required',
          minLength: {
            value: 8,
            message: 'Password must be at least 8 characters',
          },
        })}
      />

      <div>
        <label className="mb-2 block text-sm font-medium text-slate-700">Role</label>
        <div className="grid grid-cols-2 gap-4">
          <label className="flex cursor-pointer items-center rounded-lg border-2 border-slate-200 p-4 transition-colors hover:border-primary-300">
            <input
              type="radio"
              value="student"
              {...register('role', { required: 'Please select a role' })}
              className="h-4 w-4 text-primary-600"
            />
            <span className="ml-2 text-sm font-medium">Student</span>
          </label>
          <label className="flex cursor-pointer items-center rounded-lg border-2 border-slate-200 p-4 transition-colors hover:border-primary-300">
            <input
              type="radio"
              value="teacher"
              {...register('role', { required: 'Please select a role' })}
              className="h-4 w-4 text-primary-600"
            />
            <span className="ml-2 text-sm font-medium">Teacher</span>
          </label>
        </div>
        {errors.role && <p className="mt-1.5 text-sm text-red-600">{errors.role.message}</p>}
      </div>

      <Button type="submit" className="w-full" size="lg" isLoading={registerMutation.isPending}>
        Create Account
      </Button>
    </form>
  )
}

