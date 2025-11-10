import { Moon, Sun } from 'lucide-react'
import { Button } from './Button'
import { useTheme } from '@/hooks/useTheme'

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <Button
      variant="ghost"
      size="sm"
      aria-pressed={isDark}
      aria-label="Toggle theme"
      onClick={toggleTheme}
      leftIcon={isDark ? <Sun /> : <Moon />}
    >
      {isDark ? 'Light' : 'Dark'}
    </Button>
  )
}


