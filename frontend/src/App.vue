<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import LohasArticlePage from './components/LohasArticlePage.vue'
import LohasChart from './components/LohasChart.vue'
import { useIosHomeScreenPrompt } from './composables/useIosHomeScreenPrompt'
import { useSearchHistory } from './composables/useSearchHistory'
import { useTheme } from './composables/useTheme'
import { fetchLohasData } from './lib/api'
import type { AnalysisMode, DisplayRange, LohasBundleResponse } from './types'

const { theme, toggleTheme } = useTheme()
const { shouldShowPrompt: showIosHomeScreenPrompt, dismissPrompt: dismissIosHomeScreenPrompt } =
  useIosHomeScreenPrompt()
const { addToHistory, removeFromHistory, getSuggestions } = useSearchHistory()

interface RangeOption {
  label: string
  value: DisplayRange
}

interface ModeOption {
  label: string
  value: AnalysisMode
}

const rangeOptions: RangeOption[] = [
  { label: '1 年', value: '1y' },
  { label: '3 年', value: '3y' },
  { label: '3.5 年', value: '3.5y' },
  { label: '5 年', value: '5y' },
  { label: '10 年', value: '10y' },
  { label: '全部', value: 'max' },
]

const modeOptions: ModeOption[] = [
  { label: '樂活五線譜', value: 'five-lines' },
  { label: '樂活通道', value: 'channel' },
]

const numberFormatter = new Intl.NumberFormat('zh-TW', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const percentFormatter = new Intl.NumberFormat('zh-TW', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const symbolInput = ref('SPY')
const selectedRange = ref<DisplayRange>('3.5y')
const selectedMode = ref<AnalysisMode>('five-lines')
const chartData = ref<LohasBundleResponse | null>(null)
const isLoading = ref(false)
const errorMessage = ref('')
const showSuggestions = ref(false)
const currentHash = ref('')
let activeRequestId = 0

const isArticlePage = computed(() => currentHash.value === '#/article')
const suggestions = computed(() => getSuggestions(symbolInput.value))
const activeAnalysis = computed(() => chartData.value?.analyses[selectedMode.value] ?? null)
const activeRangeLabel = computed(
  () =>
    chartData.value?.displayRangeLabel ??
    rangeOptions.find((option) => option.value === selectedRange.value)?.label ??
    '',
)
const chartTitle = computed(
  () => {
    const baseTitle =
      activeAnalysis.value?.analysisTitle ??
      modeOptions.find((option) => option.value === selectedMode.value)?.label ??
      '樂活五線譜'

    return selectedMode.value === 'channel'
      ? `${baseTitle} (Preview)`
      : baseTitle
  },
)
const chartDescription = computed(() => {
  if (selectedMode.value === 'channel') {
    return '黑線為每週收盤價，週線時間點以每週日標記；另外三條線依序為通道上限、20 週均線與通道下限。通道以最近 20 週收盤價的移動平均與上下 2 倍標準差計算，跌破下限先停看，回到通道內再留意下一步。'
  }

  return '黑線為收盤價，其餘五條平行直線依序代表 +2σ、+1σ、趨勢線、-1σ、-2σ，用來觀察均值回歸區間。'
})
const pointCountLabel = computed(() => {
  if (!activeAnalysis.value) {
    return ''
  }

  return activeAnalysis.value.analysisMode === 'channel'
    ? `共 ${activeAnalysis.value.pointCount} 週資料`
    : `共 ${activeAnalysis.value.pointCount} 筆資料`
})
const guideSections = computed(() => [
  {
    key: 'sentiment',
    label: '市場情緒',
    title: '價格不只反映價值，也反映投資人的樂觀與悲觀',
    body: '基本面決定長線方向，情緒則讓價格在趨勢附近上下擺盪。看這個頁面時，重點不是預測每天漲跌，而是辨認市場是否已經過熱、過冷，避免追高殺低。',
    active: false,
  },
  {
    key: 'five-lines',
    label: '樂活五線譜',
    title: '用均值回歸觀察長期趨勢，判斷目前價格偏離了多少',
    body: '五線譜適合用在長期趨勢穩定的指數 ETF、產業龍頭或景氣循環明確的標的。當價格靠近上方線，代表市場情緒偏熱；靠近下方線，代表市場情緒偏冷，可作為分批布局或分批調節的參考。',
    active: selectedMode.value === 'five-lines',
  },
  {
    key: 'channel',
    label: '樂活通道',
    title: '用 20 週通道過濾短中期動能，避免太早抄底或太晚降溫',
    body: '樂活通道以 20 週均線與上下 2 倍標準差觀察市場是否失衡。跌破下軌代表空方動能過強，先不要急著接；等價格由下往上回到通道內，再和五線譜的低估區交叉確認。反過來，衝上上軌後若跌回通道內，才是較有紀律的減碼提示。',
    active: selectedMode.value === 'channel',
  },
])
const summaryCards = computed(() => {
  if (!activeAnalysis.value) {
    return []
  }

  if (activeAnalysis.value.analysisMode === 'five-lines') {
    const divergencePercent =
      activeAnalysis.value.latestTrend === 0
        ? null
        : (activeAnalysis.value.latestClose - activeAnalysis.value.latestTrend) / activeAnalysis.value.latestTrend

    return [
      {
        label: '標的',
        value: activeAnalysis.value.symbol,
        meta: `顯示區間：${activeRangeLabel.value}`,
      },
      {
        label: '最新收盤價',
        value: formatNumber(activeAnalysis.value.latestClose),
        meta: `Z-Score：${formatNumber(activeAnalysis.value.latestZScore)}`,
      },
      {
        label: '趨勢線',
        value: formatNumber(activeAnalysis.value.latestTrend),
        meta:
          divergencePercent === null
            ? '與趨勢線差距：--'
            : `與趨勢線差距：${formatPercent(divergencePercent)}`,
      },
      {
        label: '目前區間',
        value: activeAnalysis.value.latestPosition,
        meta: `標準差：${formatNumber(activeAnalysis.value.standardDeviation)}`,
      },
    ]
  }

  return [
    {
      label: '標的',
      value: activeAnalysis.value.symbol,
      meta: `顯示區間：${activeRangeLabel.value}`,
    },
    {
      label: '最新收盤價',
      value: formatNumber(activeAnalysis.value.latestClose),
      meta: `20 週均線：${formatNumber(activeAnalysis.value.latestMiddle)}`,
    },
    {
      label: '通道寬度',
      value: formatPercent(activeAnalysis.value.latestBandwidth),
      meta: `%b：${formatNumber(activeAnalysis.value.latestPercentB)} / 區間：${formatNumber(activeAnalysis.value.latestLowerBound)} - ${formatNumber(activeAnalysis.value.latestUpperBound)}`,
    },
    {
      label: '通道狀態',
      value: activeAnalysis.value.latestSignal,
      meta: `${activeAnalysis.value.latestPosition} / 距上限：${formatSignedNumber(activeAnalysis.value.latestUpperDistance)} / 距下限：${formatSignedNumber(activeAnalysis.value.latestLowerDistance)}`,
    },
  ]
})

function formatNumber(value: number): string {
  return numberFormatter.format(value)
}

function formatSignedNumber(value: number): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${numberFormatter.format(value)}`
}

function formatPercent(value: number): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${percentFormatter.format(value * 100)}%`
}

function normalizeSymbol(symbol: string): string {
  return symbol.trim().toUpperCase()
}

async function loadData(
  symbol = symbolInput.value,
  range = selectedRange.value,
): Promise<void> {
  const normalizedSymbol = normalizeSymbol(symbol)

  if (!normalizedSymbol) {
    chartData.value = null
    errorMessage.value = '請輸入股票代號，例如 2330.TW 或 AAPL。'
    return
  }

  symbolInput.value = normalizedSymbol
  selectedRange.value = range
  errorMessage.value = ''
  isLoading.value = true
  const requestId = ++activeRequestId

  try {
    const data = await fetchLohasData(normalizedSymbol, range)

    if (requestId !== activeRequestId) {
      return
    }

    chartData.value = data
    addToHistory(normalizedSymbol)
  } catch (error) {
    if (requestId !== activeRequestId) {
      return
    }

    chartData.value = null
    errorMessage.value =
      error instanceof Error ? error.message : '讀取資料失敗，請稍後再試。'
  } finally {
    if (requestId === activeRequestId) {
      isLoading.value = false
    }
  }
}

function submitSearch(): void {
  showSuggestions.value = false
  void loadData(symbolInput.value, selectedRange.value)
}

function switchRange(range: DisplayRange): void {
  if (range === selectedRange.value && chartData.value) {
    return
  }

  void loadData(symbolInput.value, range)
}

function switchMode(mode: AnalysisMode): void {
  if (mode === selectedMode.value) {
    return
  }

  selectedMode.value = mode
}

function onInputFocus(): void {
  showSuggestions.value = true
}

function onInputBlur(): void {
  setTimeout(() => {
    showSuggestions.value = false
  }, 150)
}

function selectSuggestion(symbol: string): void {
  symbolInput.value = symbol
  showSuggestions.value = false
  void loadData(symbol, selectedRange.value)
}

function syncHashRoute(): void {
  currentHash.value = window.location.hash
}

watch(isArticlePage, (articlePage) => {
  if (!articlePage && !chartData.value && !isLoading.value) {
    void loadData()
  }
})

onMounted(() => {
  syncHashRoute()
  window.addEventListener('hashchange', syncHashRoute)

  if (!isArticlePage.value) {
    void loadData()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('hashchange', syncHashRoute)
})
</script>

<template>
  <LohasArticlePage
    v-if="isArticlePage"
    :theme="theme"
    :on-toggle-theme="toggleTheme"
  />

  <main v-else class="page-shell">
    <section class="hero-card">
      <button class="theme-toggle" type="button" :aria-label="theme === 'dark' ? '切換為日間模式' : '切換為夜間模式'" @click="toggleTheme">
        <svg v-if="theme === 'dark'" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      </button>
      <div class="hero-copy">
        <p class="eyebrow">Vue + yfinance 樂活五線譜 / 樂活通道</p>
        <h1>輸入股票代號，切換查看均值回歸區間與趨勢通道</h1>
        <p class="hero-description">
          先用樂活五線譜找出股價偏熱或偏冷的位置，再用 20 週樂活通道確認短中期動能是否仍在統計常態範圍內。
        </p>
        <div class="hero-actions">
          <a class="secondary-button" href="#/article">閱讀研究原文</a>
        </div>
      </div>

      <aside v-if="showIosHomeScreenPrompt" class="ios-install-banner" aria-live="polite">
        <div class="ios-install-copy">
          <strong>可加入主畫面快速開啟</strong>
          <p>若想用接近 App 的全螢幕體驗，請改用 Safari 的分享選單，點選「加入主畫面」。</p>
        </div>
        <button class="ios-install-dismiss" type="button" @click="dismissIosHomeScreenPrompt">
          知道了
        </button>
      </aside>

      <form class="search-panel" @submit.prevent="submitSearch">
        <label class="input-group" for="stock-symbol">
          <span>股票代號</span>
          <div class="input-wrapper">
            <input
              id="stock-symbol"
              v-model="symbolInput"
              type="text"
              inputmode="text"
              placeholder="例如 SPY、2330.TW、AAPL"
              autocomplete="off"
              @focus="onInputFocus"
              @blur="onInputBlur"
            />
            <ul v-if="showSuggestions && suggestions.length" class="suggestions-dropdown" role="listbox" aria-label="近期查詢">
              <li
                v-for="symbol in suggestions"
                :key="symbol"
                class="suggestion-item"
                role="option"
                @mousedown.prevent="selectSuggestion(symbol)"
              >
                <span>{{ symbol }}</span>
                <button
                  type="button"
                  class="suggestion-remove"
                  :aria-label="`移除 ${symbol}`"
                  @mousedown.prevent.stop="removeFromHistory(symbol)"
                >×</button>
              </li>
            </ul>
          </div>
        </label>

        <button class="primary-button" type="submit" :disabled="isLoading">
          {{ isLoading ? '載入中...' : '更新圖表' }}
        </button>
      </form>

      <div class="range-switcher" role="group" aria-label="切換顯示區間">
        <button
          v-for="option in rangeOptions"
          :key="option.value"
          type="button"
          class="range-button"
          :class="{ active: option.value === selectedRange }"
          :disabled="isLoading"
          @click="switchRange(option.value)"
        >
          {{ option.label }}
        </button>
      </div>

      <p class="helper-text">
        yfinance 股票代號格式，例如美股 <strong>SPY</strong>、台股 <strong>2330.TW</strong>；切換模式後會沿用同一檔標的與期間重新分析。
      </p>
    </section>

    <section v-if="activeAnalysis" class="summary-grid">
      <article v-for="card in summaryCards" :key="card.label" class="summary-card">
        <span class="summary-label">{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.meta }}</small>
      </article>
    </section>

    <section class="chart-card">
      <div class="chart-header">
        <div>
          <h2>{{ chartTitle }}</h2>
          <p>{{ chartDescription }}</p>
        </div>
        <div class="chart-actions">
          <div class="mode-switcher chart-mode-switcher" role="tablist" aria-label="切換分析模式">
            <button
              v-for="option in modeOptions"
              :key="option.value"
              type="button"
              class="mode-button"
              :class="{ active: option.value === selectedMode }"
              :disabled="isLoading"
              :aria-pressed="option.value === selectedMode"
              @click="switchMode(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
          <span v-if="activeAnalysis" class="point-count">{{ pointCountLabel }}</span>
        </div>
      </div>

      <p v-if="errorMessage" class="message error-message">{{ errorMessage }}</p>
      <p v-else-if="isLoading" class="message loading-message">正在抓取 yfinance 歷史資料...</p>

      <LohasChart v-if="activeAnalysis" :data="activeAnalysis" />
      <div v-else-if="!isLoading" class="empty-state">
        查無可顯示的資料，請確認股票代號或改用較長的歷史區間。
      </div>
    </section>

    <section class="guide-card">
      <div class="guide-header">
        <div>
          <h2>怎麼把這兩個工具一起看</h2>
          <p>先用樂活五線譜判斷價格目前位在長期趨勢的哪個區間，再用樂活通道確認 20 週動能是否失衡：跌破下軌先停手，重新站回通道再布局；突破上軌後若跌回通道內，再搭配五線譜找較有紀律的減碼點。</p>
        </div>
      </div>
      <div class="guide-grid">
        <article
          v-for="section in guideSections"
          :key="section.key"
          class="guide-item"
          :class="{ active: section.active }"
        >
          <span class="summary-label">{{ section.label }}</span>
          <strong>{{ section.title }}</strong>
          <p>{{ section.body }}</p>
        </article>
      </div>
    </section>
  </main>
</template>
