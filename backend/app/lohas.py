from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf

DisplayRange = Literal["1y", "3y", "3.5y", "5y", "10y", "max"]

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

MIN_REQUIRED_POINTS = 30


class LohasDataError(Exception):
    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


def get_lohas_data(symbol: str, display_range: DisplayRange) -> dict[str, object]:
    normalized_symbol = normalize_symbol(symbol)
    history = download_history(normalized_symbol, display_range)
    lohas_frame = build_lohas_frame(history)

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
        "symbol": normalized_symbol,
        "displayRange": display_range,
        "analysisLabel": DISPLAY_RANGE_LABELS[display_range],
        "pointCount": len(points),
        "standardDeviation": round(latest_std, 2),
        "latestClose": round(latest_close, 2),
        "latestTrend": round(latest_trend, 2),
        "latestZScore": round(latest_z_score, 2),
        "latestPosition": classify_position(latest),
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

    price_column = "Adj Close" if "Adj Close" in history.columns else "Close"
    if price_column not in history.columns:
        raise LohasDataError("取得的歷史資料缺少收盤價欄位。", status_code=502)

    history = history[[price_column]].rename(columns={price_column: "close"}).dropna()

    if history.empty:
        raise LohasDataError("這個股票代號缺少可用的收盤價資料。", status_code=404)

    if getattr(history.index, "tz", None) is not None:
        history.index = history.index.tz_localize(None)

    return history


def build_lohas_frame(history: pd.DataFrame) -> pd.DataFrame:
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


def classify_position(latest_row: pd.Series) -> str:
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
