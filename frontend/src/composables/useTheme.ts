import { ref, watchEffect } from 'vue'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'lohas-theme'
const THEME_COLORS: Record<Theme, string> = {
  light: '#f8fbff',
  dark: '#0a1020',
}

function getInitialTheme(): Theme {
  const stored = localStorage.getItem(STORAGE_KEY) as Theme | null
  if (stored === 'light' || stored === 'dark') return stored
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

const theme = ref<Theme>(getInitialTheme())

function applyTheme(nextTheme: Theme): void {
  const themeColor = THEME_COLORS[nextTheme]
  const root = document.documentElement

  root.setAttribute('data-theme', nextTheme)
  root.style.colorScheme = nextTheme
  root.style.backgroundColor = themeColor

  const themeColorMeta = document.querySelector('meta[name="theme-color"]')
  if (themeColorMeta) {
    themeColorMeta.setAttribute('content', themeColor)
  }

  localStorage.setItem(STORAGE_KEY, nextTheme)
}

watchEffect(() => {
  applyTheme(theme.value)
})

export function useTheme() {
  function toggleTheme(): void {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  return { theme, toggleTheme }
}
