import { computed, onMounted, ref } from 'vue'

const DISMISS_STORAGE_KEY = 'lohas-ios-home-screen-prompt-dismissed'

type NavigatorWithStandalone = Navigator & {
  standalone?: boolean
}

function isIosDevice(): boolean {
  const { userAgent, platform, maxTouchPoints } = window.navigator

  return /iPad|iPhone|iPod/.test(userAgent) || (platform === 'MacIntel' && maxTouchPoints > 1)
}

function isStandaloneMode(): boolean {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.matchMedia('(display-mode: fullscreen)').matches ||
    Boolean((window.navigator as NavigatorWithStandalone).standalone)
  )
}

function getInitialDismissedState(): boolean {
  return localStorage.getItem(DISMISS_STORAGE_KEY) === '1'
}

export function useIosHomeScreenPrompt() {
  const isIos = ref(false)
  const isStandalone = ref(false)
  const dismissed = ref(getInitialDismissedState())

  onMounted(() => {
    isIos.value = isIosDevice()
    isStandalone.value = isStandaloneMode()
  })

  function dismissPrompt(): void {
    dismissed.value = true
    localStorage.setItem(DISMISS_STORAGE_KEY, '1')
  }

  const shouldShowPrompt = computed(() => isIos.value && !isStandalone.value && !dismissed.value)

  return { shouldShowPrompt, dismissPrompt }
}
