import type { DisplayRange, LohasResponse } from '../types'

const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').trim().replace(/\/$/, '')

function buildApiUrl(path: string): string {
  return configuredBaseUrl ? `${configuredBaseUrl}${path}` : path
}

export async function fetchLohasData(
  symbol: string,
  range: DisplayRange,
): Promise<LohasResponse> {
  const params = new URLSearchParams({
    symbol,
    range,
  })

  const response = await fetch(buildApiUrl(`/api/lohas?${params.toString()}`))

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null
    const message =
      typeof payload?.detail === 'string' ? payload.detail : '讀取資料失敗，請稍後再試。'

    throw new Error(message)
  }

  return (await response.json()) as LohasResponse
}
