from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .lohas import DisplayRange, LohasDataError, get_lohas_data

app = FastAPI(
    title="LOHAS Five-Line API",
    version="0.1.0",
    summary="使用 yfinance 計算樂活五線譜的簡單 API。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/lohas")
def get_lohas(
    symbol: str = Query(..., min_length=1, description="yfinance 股票代號"),
    range: DisplayRange = Query(
        "3.5y",
        alias="range",
        description="顯示區間，可選 1y、3y、3.5y、5y、10y、max",
    ),
) -> dict[str, object]:
    try:
        return get_lohas_data(symbol=symbol, display_range=range)
    except LohasDataError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="目前無法從 yfinance 取得資料，請稍後再試。",
        ) from exc
