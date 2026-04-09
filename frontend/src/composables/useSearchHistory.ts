import { computed, ref } from 'vue'

const STORAGE_KEY = 'lohas-search-history'
const MAX_ITEMS = 10

function loadHistory(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as string[]) : []
  } catch {
    return []
  }
}

const history = ref<string[]>(loadHistory())

function saveHistory(): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history.value))
}

export function useSearchHistory() {
  function addToHistory(symbol: string): void {
    const s = symbol.trim().toUpperCase()
    if (!s) return
    history.value = [s, ...history.value.filter((h) => h !== s)].slice(0, MAX_ITEMS)
    saveHistory()
  }

  function removeFromHistory(symbol: string): void {
    history.value = history.value.filter((h) => h !== symbol)
    saveHistory()
  }

  function getSuggestions(query: string): string[] {
    const q = query.trim().toUpperCase()
    if (!q) return history.value
    return history.value.filter((h) => h.includes(q))
  }

  const hasHistory = computed(() => history.value.length > 0)

  return { history, hasHistory, addToHistory, removeFromHistory, getSuggestions }
}
