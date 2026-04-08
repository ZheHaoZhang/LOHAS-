<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import LohasChart from './components/LohasChart.vue'
import { fetchLohasData } from './lib/api'
import type { DisplayRange, LohasResponse } from './types'

interface RangeOption {
  label: string
  value: DisplayRange
}

const rangeOptions: RangeOption[] = [
  { label: '1 年', value: '1y' },
  { label: '3 年', value: '3y' },
  { label: '3.5 年', value: '3.5y' },
  { label: '5 年', value: '5y' },
  { label: '10 年', value: '10y' },
  { label: '全部', value: 'max' },
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
const chartData = ref<LohasResponse | null>(null)
const isLoading = ref(false)
const errorMessage = ref('')
let activeRequestId = 0

const latestPoint = computed(() => chartData.value?.points.at(-1) ?? null)
const activeRangeLabel = computed(
  () => rangeOptions.find((option) => option.value === selectedRange.value)?.label ?? '',
)
const divergencePercent = computed(() => {
  if (!latestPoint.value || latestPoint.value.trend === 0) {
    return null
  }

  return (latestPoint.value.close - latestPoint.value.trend) / latestPoint.value.trend
})

function formatNumber(value: number): string {
  return numberFormatter.format(value)
}

function formatPercent(value: number): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${percentFormatter.format(value * 100)}%`
}

function normalizeSymbol(symbol: string): string {
  return symbol.trim().toUpperCase()
}

async function loadData(symbol = symbolInput.value, range = selectedRange.value): Promise<void> {
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
  void loadData(symbolInput.value, selectedRange.value)
}

function switchRange(range: DisplayRange): void {
  if (range === selectedRange.value && chartData.value) {
    return
  }

  void loadData(symbolInput.value, range)
}

onMounted(() => {
  void loadData()
})
</script>

<template>
  <main class="page-shell">
    <section class="hero-card">
      <div class="hero-copy">
        <p class="eyebrow">Vue + yfinance 樂活五線譜</p>
        <h1>輸入股票代號，快速查看均值回歸區間</h1>
        <p class="hero-description">
          以時間和股價做 OLS 線性回歸，先算出趨勢線，再用殘差標準差畫出五條彼此平行的直線。
        </p>
      </div>

      <form class="search-panel" @submit.prevent="submitSearch">
        <label class="input-group" for="stock-symbol">
          <span>股票代號</span>
          <input
            id="stock-symbol"
            v-model="symbolInput"
            type="text"
            inputmode="text"
            placeholder="例如 SPY、2330.TW、AAPL"
          />
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
        yfinance 股票代號格式，例如美股 <strong>SPY</strong>、台股 <strong>2330.TW</strong>。
      </p>
    </section>

    <section v-if="chartData && latestPoint" class="summary-grid">
      <article class="summary-card">
        <span class="summary-label">標的</span>
        <strong>{{ chartData.symbol }}</strong>
        <small>顯示區間：{{ activeRangeLabel }}</small>
      </article>

      <article class="summary-card">
        <span class="summary-label">最新收盤價</span>
        <strong>{{ formatNumber(chartData.latestClose) }}</strong>
        <small>Z-Score：{{ formatNumber(chartData.latestZScore) }}</small>
      </article>

      <article class="summary-card">
        <span class="summary-label">趨勢線</span>
        <strong>{{ formatNumber(chartData.latestTrend) }}</strong>
        <small v-if="divergencePercent !== null">
          與趨勢線差距：{{ formatPercent(divergencePercent) }}
        </small>
      </article>

      <article class="summary-card">
        <span class="summary-label">目前區間</span>
        <strong>{{ chartData.latestPosition }}</strong>
        <small>分析區間：{{ chartData.analysisLabel }} / 標準差：{{ formatNumber(chartData.standardDeviation) }}</small>
      </article>
    </section>

    <section class="chart-card">
      <div class="chart-header">
        <div>
          <h2>樂活五線譜</h2>
          <p>黑線為收盤價，其餘五條平行直線依序代表 +2σ、+1σ、趨勢線、-1σ、-2σ。</p>
        </div>
        <span v-if="chartData" class="point-count">共 {{ chartData.pointCount }} 筆資料</span>
      </div>

      <p v-if="errorMessage" class="message error-message">{{ errorMessage }}</p>
      <p v-else-if="isLoading" class="message loading-message">正在抓取 yfinance 歷史資料...</p>

      <LohasChart
        v-if="chartData && latestPoint"
        :points="chartData.points"
        :symbol="chartData.symbol"
      />
      <div v-else-if="!isLoading" class="empty-state">
        查無可顯示的資料，請確認股票代號或改用較長的歷史區間。
      </div>
    </section>
  </main>
</template>
