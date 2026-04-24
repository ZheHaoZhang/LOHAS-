export type DisplayRange = '1y' | '3y' | '3.5y' | '5y' | '10y' | 'max'
export type AnalysisMode = 'five-lines' | 'channel'

export interface FiveLinesPoint {
  date: string
  close: number
  optimistic: number
  relativeOptimistic: number
  trend: number
  relativePessimistic: number
  pessimistic: number
}

export interface ChannelPoint {
  date: string
  close: number
  upperBound: number
  middle: number
  lowerBound: number
}

interface BaseResponse {
  symbol: string
  displayRange: DisplayRange
  displayRangeLabel: string
  analysisMode: AnalysisMode
  analysisTitle: string
  pointCount: number
  latestClose: number
  latestPosition: string
}

export interface FiveLinesResponse extends BaseResponse {
  analysisMode: 'five-lines'
  standardDeviation: number
  latestTrend: number
  latestZScore: number
  points: FiveLinesPoint[]
}

export interface ChannelResponse extends BaseResponse {
  analysisMode: 'channel'
  latestMiddle: number
  latestUpperBound: number
  latestLowerBound: number
  latestUpperDistance: number
  latestLowerDistance: number
  latestBandwidth: number
  latestPercentB: number
  latestSignal: string
  points: ChannelPoint[]
}

export type LohasResponse = FiveLinesResponse | ChannelResponse

export interface LohasBundleResponse {
  symbol: string
  displayRange: DisplayRange
  displayRangeLabel: string
  analyses: {
    'five-lines': FiveLinesResponse
    channel: ChannelResponse
  }
}
