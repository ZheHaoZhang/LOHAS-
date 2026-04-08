export type DisplayRange = '1y' | '3y' | '3.5y' | '5y' | '10y' | 'max'

export interface LohasPoint {
  date: string
  close: number
  optimistic: number
  relativeOptimistic: number
  trend: number
  relativePessimistic: number
  pessimistic: number
}

export interface LohasResponse {
  symbol: string
  displayRange: DisplayRange
  analysisLabel: string
  pointCount: number
  standardDeviation: number
  latestClose: number
  latestTrend: number
  latestZScore: number
  latestPosition: string
  points: LohasPoint[]
}
