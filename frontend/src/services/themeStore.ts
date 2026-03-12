/**
 * Theme Store
 * Zustand store for managing light/dark mode theme
 */

import { create } from 'zustand'

type Theme = 'light' | 'dark' | 'auto'

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
  isDark: boolean
  toggleTheme: () => void
  initializeTheme: () => void
}

export const useTheme = create<ThemeState>((set, get) => ({
  theme: 'auto',
  isDark: false,

  setTheme: (theme: Theme) => {
    const root = document.documentElement
    
    let isDark = false
    if (theme === 'dark') {
      root.classList.add('dark')
      isDark = true
    } else if (theme === 'light') {
      root.classList.remove('dark')
      isDark = false
    } else {
      // Auto: check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      if (prefersDark) {
        root.classList.add('dark')
        isDark = true
      } else {
        root.classList.remove('dark')
        isDark = false
      }
    }

    // Save to localStorage
    localStorage.setItem('theme', theme)

    set({ theme, isDark })
  },

  toggleTheme: () => {
    const state = get()
    const newTheme = state.theme === 'dark' ? 'light' : 'dark'
    state.setTheme(newTheme)
  },

  initializeTheme: () => {
    const savedTheme = localStorage.getItem('theme') as Theme | null
    const theme = savedTheme || 'auto'
    const state = get()
    state.setTheme(theme)

    // Watch for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      if (get().theme === 'auto') {
        state.setTheme('auto')
      }
    }
    mediaQuery.addEventListener('change', handleChange)
  },
}))
