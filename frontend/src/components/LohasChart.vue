<script setup lang="ts">
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import type { EChartsCoreOption, EChartsType } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { useTheme } from '../composables/useTheme'
import type { ChannelPoint, FiveLinesPoint, LohasResponse } from '../types'

use([LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

type FiveLinesKey =
  | 'close'
  | 'optimistic'
  | 'relativeOptimistic'
  | 'trend'
  | 'relativePessimistic'
  | 'pessimistic'

type ChannelKey = 'close' | 'upperBound' | 'middle' | 'lowerBound'

interface SeriesValueItem {
  color: string
  label: string
  value: string
}

const props = defineProps<{
  data: LohasResponse
}>()

const { theme } = useTheme()

const chartElement = ref<HTMLDivElement | null>(null)
let chart: EChartsType | null = null

function buildFiveLinesSeriesData(key: FiveLinesKey): [string, number][] {
  if (props.data.analysisMode !== 'five-lines') {
    return []
  }

  return props.data.points.map((point: FiveLinesPoint) => [point.date, point[key]])
}

function buildChannelSeriesData(key: ChannelKey): [string, number][] {
  if (props.data.analysisMode !== 'channel') {
    return []
  }

  return props.data.points.map((point: ChannelPoint) => [point.date, point[key]])
}

function formatSeriesValue(value: number): string {
  return Number.isInteger(value) ? `${value}` : value.toFixed(2)
}

function buildLineSeries(
  name: string,
  data: [string, number][],
  color: string,
  width = 2,
) {
  return {
    name,
    type: 'line' as const,
    showSymbol: false,
    lineStyle: { width },
    color,
    data,
  }
}

const latestSeriesValues = computed<SeriesValueItem[]>(() => {
  if (props.data.analysisMode === 'channel') {
    const latest = props.data.points.at(-1)

    if (!latest) {
      return []
    }

    return [
      { label: `${props.data.symbol} 收盤價`, value: formatSeriesValue(latest.close), color: closeColorForTheme(theme.value) },
      { label: '通道上限 (+2σ)', value: formatSeriesValue(latest.upperBound), color: '#2563eb' },
      { label: '20 週均線', value: formatSeriesValue(latest.middle), color: '#f97316' },
      { label: '通道下限 (-2σ)', value: formatSeriesValue(latest.lowerBound), color: '#16a34a' },
    ]
  }

  const latest = props.data.points.at(-1)

  if (!latest) {
    return []
  }

  return [
    { label: `${props.data.symbol} 收盤價`, value: formatSeriesValue(latest.close), color: closeColorForTheme(theme.value) },
    { label: '極度樂觀線 (+2σ)', value: formatSeriesValue(latest.optimistic), color: '#16a34a' },
    { label: '相對樂觀線 (+1σ)', value: formatSeriesValue(latest.relativeOptimistic), color: '#2563eb' },
    { label: '趨勢線', value: formatSeriesValue(latest.trend), color: '#f97316' },
    { label: '相對悲觀線 (-1σ)', value: formatSeriesValue(latest.relativePessimistic), color: '#eab308' },
    { label: '極度悲觀線 (-2σ)', value: formatSeriesValue(latest.pessimistic), color: '#9ca3af' },
  ]
})

function closeColorForTheme(activeTheme: 'light' | 'dark'): string {
  return activeTheme === 'dark' ? '#e2e8f0' : '#1f2937'
}

const option = computed<EChartsCoreOption>(() => {
  const isDark = theme.value === 'dark'
  const axisColor = isDark ? '#64748b' : '#6b7280'
  const splitLineColor = isDark ? '#1e293b' : '#e5e7eb'
  const tooltipBg = isDark ? '#1e293b' : '#fff'
  const tooltipBorder = isDark ? '#334155' : '#e5e7eb'
  const tooltipText = isDark ? '#f1f5f9' : '#0f172a'
  const closeColor = isDark ? '#e2e8f0' : '#1f2937'

  const baseOption = {
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: { color: tooltipText },
      valueFormatter: (value: number | string | null | undefined) => {
        if (typeof value === 'number') return value.toFixed(2)
        return `${value ?? ''}`
      },
    },
    legend: {
      top: 0,
      itemGap: 16,
      textStyle: { color: axisColor },
    },
    grid: { left: 56, right: 24, top: 56, bottom: 36 },
    xAxis: {
      type: 'time',
      axisLabel: { color: axisColor },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        color: axisColor,
        formatter: (value: number) => value.toFixed(0),
      },
      splitLine: { lineStyle: { color: splitLineColor } },
    },
  } satisfies EChartsCoreOption

  if (props.data.analysisMode === 'channel') {
    return {
      ...baseOption,
      color: [closeColor, '#2563eb', '#f97316', '#16a34a'],
      series: [
        buildLineSeries(`${props.data.symbol} 收盤價`, buildChannelSeriesData('close'), closeColor, 2.5),
        buildLineSeries('通道上限 (+2σ)', buildChannelSeriesData('upperBound'), '#2563eb'),
        buildLineSeries('20 週均線', buildChannelSeriesData('middle'), '#f97316'),
        buildLineSeries('通道下限 (-2σ)', buildChannelSeriesData('lowerBound'), '#16a34a'),
      ],
    }
  }

  return {
    ...baseOption,
    color: [closeColor, '#16a34a', '#2563eb', '#f97316', '#eab308', '#9ca3af'],
    series: [
      buildLineSeries(`${props.data.symbol} 收盤價`, buildFiveLinesSeriesData('close'), closeColor),
      buildLineSeries('極度樂觀線 (+2σ)', buildFiveLinesSeriesData('optimistic'), '#16a34a'),
      buildLineSeries('相對樂觀線 (+1σ)', buildFiveLinesSeriesData('relativeOptimistic'), '#2563eb'),
      buildLineSeries('趨勢線', buildFiveLinesSeriesData('trend'), '#f97316'),
      buildLineSeries('相對悲觀線 (-1σ)', buildFiveLinesSeriesData('relativePessimistic'), '#eab308'),
      buildLineSeries('極度悲觀線 (-2σ)', buildFiveLinesSeriesData('pessimistic'), '#9ca3af'),
    ],
  }
})

function renderChart(): void {
  if (!chartElement.value) {
    return
  }

  if (!chart) {
    chart = init(chartElement.value)
  }

  chart.setOption(option.value, true)
  chart.resize()
}

function resizeChart(): void {
  chart?.resize()
}

watch(
  () => props.data,
  () => {
    renderChart()
  },
  { deep: true },
)

watch(
  () => theme.value,
  () => {
    renderChart()
  },
)

onMounted(() => {
  renderChart()
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="chart-shell">
    <div ref="chartElement" class="chart"></div>
    <aside class="value-rail" aria-label="最新線值">
      <div v-for="item in latestSeriesValues" :key="item.label" class="value-rail-item">
        <span class="value-rail-marker" :style="{ backgroundColor: item.color }"></span>
        <div class="value-rail-copy">
          <span class="value-rail-label">{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.chart-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 168px;
  gap: 16px;
  align-items: start;
}

.chart {
  width: 100%;
  height: 520px;
}

.value-rail {
  display: grid;
  gap: 10px;
  padding-top: 56px;
}

.value-rail-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.value-rail-marker {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  margin-top: 7px;
  flex: none;
}

.value-rail-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.value-rail-label {
  color: var(--color-text-muted);
  font-size: 0.8rem;
  line-height: 1.35;
}

.value-rail-copy strong {
  color: var(--color-text);
  font-size: 0.98rem;
  line-height: 1.2;
}

@media (max-width: 768px) {
  .chart-shell {
    grid-template-columns: 1fr;
  }

  .chart {
    height: 380px;
  }

  .value-rail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    padding-top: 0;
  }
}
</style>
