from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf

DisplayRange = Literal["1y", "3y", "3.5y", "5y", "10y", "max"]
AnalysisMode = Literal["five-lines", "channel"]

DISPLAY_RANGE_DAYS: dict[DisplayRange, int | None] = {
    "1y": 365,
    "3y": 365 * 3,
    "3.5y": int(365.25 * 3.5),
    "5y": 365 * 5,
    "10y": 365 * 10,
    "max": None,
}

DISPLAY_RANGE_LABELS: dict[DisplayRange, str] = {
    "1y": "1 年",
    "3y": "3 年",
    "3.5y": "3.5 年",
    "5y": "5 年",
    "10y": "10 年",
    "max": "全部歷史",
}

ANALYSIS_MODE_LABELS: dict[AnalysisMode, str] = {
    "five-lines": "樂活五線譜",
    "channel": "樂活通道",
}

MIN_REQUIRED_POINTS = 30
CHANNEL_WINDOW_WEEKS = 20
CHANNEL_STD_MULTIPLIER = 2


class LohasDataError(Exception):
    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


def get_lohas_data(symbol: str, display_range: DisplayRange) -> dict[str, object]:
    normalized_symbol = normalize_symbol(symbol)
    history = download_history(normalized_symbol, display_range)
    five_lines = build_five_lines_response(normalized_symbol, display_range, history)
    channel = build_channel_response(normalized_symbol, display_range, history)

    return {
        "symbol": normalized_symbol,
        "displayRange": display_range,
        "displayRangeLabel": DISPLAY_RANGE_LABELS[display_range],
        "analyses": {
            "five-lines": five_lines,
            "channel": channel,
        },
    }


def build_five_lines_response(
    symbol: str, display_range: DisplayRange, history: pd.DataFrame
) -> dict[str, object]:
    lohas_frame = build_five_lines_frame(history)

    if lohas_frame.empty:
        raise LohasDataError(
            "可用資料不足，無法顯示所選區間。請改用較長區間或更換股票代號。"
        )

    latest = lohas_frame.iloc[-1]

    points = [
        {
            "date": index.strftime("%Y-%m-%d"),
            "close": round(float(row["close"]), 2),
            "optimistic": round(float(row["optimistic"]), 2),
            "relativeOptimistic": round(float(row["relative_optimistic"]), 2),
            "trend": round(float(row["trend"]), 2),
            "relativePessimistic": round(float(row["relative_pessimistic"]), 2),
            "pessimistic": round(float(row["pessimistic"]), 2),
        }
        for index, row in lohas_frame.iterrows()
    ]

    latest_close = float(latest["close"])
    latest_trend = float(latest["trend"])
    latest_std = float(latest["std"])
    latest_z_score = 0.0 if latest_std == 0 else (latest_close - latest_trend) / latest_std

    return {
        "symbol": symbol,
        "displayRange": display_range,
        "displayRangeLabel": DISPLAY_RANGE_LABELS[display_range],
        "analysisMode": "five-lines",
        "analysisTitle": ANALYSIS_MODE_LABELS["five-lines"],
        "pointCount": len(points),
        "standardDeviation": round(latest_std, 2),
        "latestClose": round(latest_close, 2),
        "latestTrend": round(latest_trend, 2),
        "latestZScore": round(latest_z_score, 2),
        "latestPosition": classify_five_lines_position(latest),
        "points": points,
    }


def build_channel_response(
    symbol: str, display_range: DisplayRange, history: pd.DataFrame
) -> dict[str, object]:
    channel_frame = build_channel_frame(history)

    if channel_frame.empty:
        raise LohasDataError(
            "可用週資料不足，無法顯示樂活通道。請改用較長區間或更換股票代號。"
        )

    latest = channel_frame.iloc[-1]
    previous = channel_frame.iloc[-2] if len(channel_frame.index) > 1 else None

    points = [
        {
            "date": index.strftime("%Y-%m-%d"),
            "close": round(float(row["close"]), 2),
            "upperBound": round(float(row["upper_bound"]), 2),
            "middle": round(float(row["middle"]), 2),
            "lowerBound": round(float(row["lower_bound"]), 2),
        }
        for index, row in channel_frame.iterrows()
    ]

    latest_close = float(latest["close"])
    latest_middle = float(latest["middle"])
    latest_upper_bound = float(latest["upper_bound"])
    latest_lower_bound = float(latest["lower_bound"])
    channel_width = latest_upper_bound - latest_lower_bound
    latest_percent_b = (
        0.5 if channel_width == 0 else (latest_close - latest_lower_bound) / channel_width
    )
    latest_bandwidth = 0.0 if latest_middle == 0 else channel_width / latest_middle

    return {
        "symbol": symbol,
        "displayRange": display_range,
        "displayRangeLabel": DISPLAY_RANGE_LABELS[display_range],
        "analysisMode": "channel",
        "analysisTitle": ANALYSIS_MODE_LABELS["channel"],
        "pointCount": len(points),
        "latestClose": round(latest_close, 2),
        "latestMiddle": round(latest_middle, 2),
        "latestUpperBound": round(latest_upper_bound, 2),
        "latestLowerBound": round(latest_lower_bound, 2),
        "latestUpperDistance": round(latest_close - latest_upper_bound, 2),
        "latestLowerDistance": round(latest_close - latest_lower_bound, 2),
        "latestBandwidth": round(latest_bandwidth, 4),
        "latestPercentB": round(latest_percent_b, 4),
        "latestPosition": classify_channel_position(latest),
        "latestSignal": describe_channel_signal(previous, latest),
        "points": points,
    }


def normalize_symbol(symbol: str) -> str:
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError("請輸入股票代號，例如 2330.TW 或 AAPL。")
    return normalized_symbol


def download_history(symbol: str, display_range: DisplayRange) -> pd.DataFrame:
    download_kwargs = {
        "tickers": symbol,
        "interval": "1d",
        "progress": False,
        "auto_adjust": False,
        "actions": False,
        "group_by": "column",
    }

    if display_range == "max":
        history = yf.download(period="max", **download_kwargs)
    else:
        range_days = DISPLAY_RANGE_DAYS[display_range]
        assert range_days is not None
        start_date = (datetime.now(timezone.utc) - timedelta(days=range_days + 7)).date()
        history = yf.download(start=start_date.isoformat(), **download_kwargs)

    if history.empty:
        raise LohasDataError("找不到這個股票代號的歷史資料。", status_code=404)

    if isinstance(history.columns, pd.MultiIndex):
        history.columns = history.columns.get_level_values(0)

    required_columns = {"Close", "High", "Low"}
    if not required_columns.issubset(history.columns):
        raise LohasDataError("取得的歷史資料缺少必要的價格欄位。", status_code=502)

    if "Adj Close" in history.columns:
        adjustment_factor = history["Adj Close"] / history["Close"].replace(0, np.nan)
        price_frame = pd.DataFrame(index=history.index)
        price_frame["close"] = history["Adj Close"]
        price_frame["high"] = history["High"] * adjustment_factor
        price_frame["low"] = history["Low"] * adjustment_factor
        history = price_frame.dropna()
    else:
        history = history[["Close", "High", "Low"]].rename(
            columns={"Close": "close", "High": "high", "Low": "low"}
        )
        history = history.dropna()

    if history.empty:
        raise LohasDataError("這個股票代號缺少可用的收盤價資料。", status_code=404)

    if getattr(history.index, "tz", None) is not None:
        history.index = history.index.tz_localize(None)

    return history


def build_five_lines_frame(history: pd.DataFrame) -> pd.DataFrame:
    if len(history.index) < MIN_REQUIRED_POINTS:
        raise LohasDataError(
            f"歷史資料至少需要 {MIN_REQUIRED_POINTS} 筆日線，才能計算樂活五線譜。"
        )

    x = history.index.map(pd.Timestamp.toordinal).to_numpy(dtype=float)
    x = x - x[0]
    y = history["close"].to_numpy(dtype=float)

    slope, intercept = np.polyfit(x, y, 1)
    trend = intercept + slope * x
    residuals = y - trend
    standard_deviation = float(np.std(residuals, ddof=0))

    lohas_frame = pd.DataFrame(index=history.index)
    lohas_frame["close"] = y
    lohas_frame["trend"] = trend
    lohas_frame["std"] = standard_deviation
    lohas_frame["relative_optimistic"] = lohas_frame["trend"] + standard_deviation
    lohas_frame["optimistic"] = lohas_frame["trend"] + standard_deviation * 2
    lohas_frame["relative_pessimistic"] = lohas_frame["trend"] - standard_deviation
    lohas_frame["pessimistic"] = lohas_frame["trend"] - standard_deviation * 2

    return lohas_frame


def build_channel_frame(history: pd.DataFrame) -> pd.DataFrame:
    weekly_history = history.groupby(history.index.to_period("W-SUN")).last().copy()
    weekly_history.index = weekly_history.index.to_timestamp(how="end").normalize()
    latest_history_date = pd.Timestamp(history.index.max()).normalize()
    weekly_history = weekly_history[weekly_history.index <= latest_history_date]

    if len(weekly_history.index) < CHANNEL_WINDOW_WEEKS:
        raise LohasDataError(
            f"歷史資料至少需要 {CHANNEL_WINDOW_WEEKS} 週收盤資料，才能計算樂活通道。"
        )

    weekly_close = weekly_history["close"]

    channel_frame = pd.DataFrame(index=weekly_history.index)
    channel_frame["close"] = weekly_close
    channel_frame["middle"] = weekly_close.rolling(CHANNEL_WINDOW_WEEKS).mean()
    rolling_std = weekly_close.rolling(CHANNEL_WINDOW_WEEKS).std(ddof=0)
    channel_frame["upper_bound"] = (
        channel_frame["middle"] + rolling_std * CHANNEL_STD_MULTIPLIER
    )
    channel_frame["lower_bound"] = (
        channel_frame["middle"] - rolling_std * CHANNEL_STD_MULTIPLIER
    )

    return channel_frame.dropna()


def classify_five_lines_position(latest_row: pd.Series) -> str:
    close = float(latest_row["close"])
    optimistic = float(latest_row["optimistic"])
    relative_optimistic = float(latest_row["relative_optimistic"])
    trend = float(latest_row["trend"])
    relative_pessimistic = float(latest_row["relative_pessimistic"])
    pessimistic = float(latest_row["pessimistic"])

    if close >= optimistic:
        return "高於極度樂觀線"
    if close >= relative_optimistic:
        return "位於相對樂觀區"
    if close >= trend:
        return "位於趨勢線上方"
    if close >= relative_pessimistic:
        return "位於趨勢線下方"
    if close >= pessimistic:
        return "位於相對悲觀區"
    return "低於極度悲觀線"


def classify_channel_position(latest_row: pd.Series) -> str:
    close = float(latest_row["close"])
    upper_bound = float(latest_row["upper_bound"])
    middle = float(latest_row["middle"])
    lower_bound = float(latest_row["lower_bound"])

    if close > upper_bound:
        return "過熱區（高於上限）"
    if close >= middle:
        return "正常區間（偏強）"
    if close >= lower_bound:
        return "正常區間（偏弱）"
    return "超跌區（低於下限）"


def describe_channel_signal(
    previous_row: pd.Series | None, latest_row: pd.Series
) -> str:
    latest_close = float(latest_row["close"])
    latest_upper_bound = float(latest_row["upper_bound"])
    latest_lower_bound = float(latest_row["lower_bound"])

    if previous_row is not None:
        previous_close = float(previous_row["close"])
        previous_upper_bound = float(previous_row["upper_bound"])
        previous_lower_bound = float(previous_row["lower_bound"])

        if previous_close < previous_lower_bound and latest_close >= latest_lower_bound:
            return "由下往上重回通道，可開始留意布局"
        if previous_close > previous_upper_bound and latest_close <= latest_upper_bound:
            return "由上往下跌回通道，可開始留意賣點"

    if latest_close < latest_lower_bound:
        return "跌破下軌，屬於超跌區，暫不宜追價"
    if latest_close > latest_upper_bound:
        return "突破上軌，屬於過熱區，暫不宜追高"
    return "位於通道內，等待進一步方向確認"
