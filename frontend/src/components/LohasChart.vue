<script setup lang="ts">
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import type { EChartsCoreOption, EChartsType } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { useTheme } from '../composables/useTheme'
import type { LohasPoint } from '../types'

use([LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

type LineKey =
  | 'close'
  | 'optimistic'
  | 'relativeOptimistic'
  | 'trend'
  | 'relativePessimistic'
  | 'pessimistic'

const props = defineProps<{
  points: LohasPoint[]
  symbol: string
}>()

const { theme } = useTheme()

const chartElement = ref<HTMLDivElement | null>(null)
let chart: EChartsType | null = null

function buildSeriesData(key: LineKey): [string, number][] {
  return props.points.map((point) => [point.date, point[key]])
}

const option = computed<EChartsCoreOption>(() => {
  const isDark = theme.value === 'dark'
  const axisColor = isDark ? '#64748b' : '#6b7280'
  const splitLineColor = isDark ? '#1e293b' : '#e5e7eb'
  const tooltipBg = isDark ? '#1e293b' : '#fff'
  const tooltipBorder = isDark ? '#334155' : '#e5e7eb'
  const tooltipText = isDark ? '#f1f5f9' : '#0f172a'
  const closeColor = isDark ? '#e2e8f0' : '#1f2937'

  return {
    animation: false,
    color: [closeColor, '#16a34a', '#2563eb', '#f97316', '#eab308', '#9ca3af'],
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
    series: [
      {
        name: `${props.symbol} 收盤價`,
        type: 'line',
        showSymbol: false,
        lineStyle: { width: 2 },
        data: buildSeriesData('close'),
      },
      {
        name: '極度樂觀線 (+2σ)',
        type: 'line',
        showSymbol: false,
        lineStyle: { width: 2 },
        data: buildSeriesData('optimistic'),
      },
      {
        name: '相對樂觀線 (+1σ)',
        type: 'line',
        showSymbol: false,
        lineStyle: { width: 2 },
        data: buildSeriesData('relativeOptimistic'),
      },
      {
        name: '趨勢線',
        type: 'line',
        showSymbol: false,
        lineStyle: { width: 2 },
        data: buildSeriesData('trend'),
      },
      {
        name: '相對悲觀線 (-1σ)',
        type: 'line',
        showSymbol: false,
        lineStyle: { width: 2 },
        data: buildSeriesData('relativePessimistic'),
      },
      {
        name: '極度悲觀線 (-2σ)',
        type: 'line',
        showSymbol: false,
        lineStyle: { width: 2 },
        data: buildSeriesData('pessimistic'),
      },
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
  () => props.points,
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
  <div ref="chartElement" class="chart"></div>
</template>

<style scoped>
.chart {
  width: 100%;
  height: 520px;
}

@media (max-width: 768px) {
  .chart {
    height: 380px;
  }
}
</style>
