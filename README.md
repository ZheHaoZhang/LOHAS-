# LOHAS 樂活五線譜

一個使用 **Vue 3 + Vite** 製作的簡單網站，可輸入股票代號並顯示樂活五線譜；後端使用 **FastAPI + yfinance** 取得歷史資料，並以 **OLS 線性回歸趨勢線 + 殘差標準差** 計算五條平行直線。

## 功能

- 輸入 yfinance 股票代號，例如 `SPY`、`2330.TW`、`AAPL`
- 切換顯示區間：`1 年`、`3 年`、`3.5 年`、`5 年`、`10 年`、`全部`
- 顯示收盤價與五條樂活線：極度樂觀線、相對樂觀線、趨勢線、相對悲觀線、極度悲觀線
- 內建啟動腳本，可一鍵安裝依賴與啟動前後端

## 五線譜公式

- 趨勢線：使用 OLS 線性回歸 `Y = a + bX`
- 相對樂觀線：`TL + 1SD`
- 極度樂觀線：`TL + 2SD`
- 相對悲觀線：`TL - 1SD`
- 極度悲觀線：`TL - 2SD`

其中 `SD` 為價格相對於趨勢線殘差的標準差，因此圖上五條線會保持互相平行。

## 快速開始

```bash
./scripts/setup.sh
./scripts/dev.sh
```

## 啟動方式

### 1. 安裝依賴

```bash
./scripts/setup.sh
```

### 2. 一鍵啟動前後端

```bash
./scripts/dev.sh
```

### 3. 分開啟動後端與前端

```bash
./scripts/start-backend.sh
```

後端預設啟動在 `http://127.0.0.1:8000`。

```bash
./scripts/start-frontend.sh
```

前端預設啟動在 `http://127.0.0.1:5173`，已透過 Vite proxy 將 `/api` 轉送到本機後端。

如果預設埠號被佔用：

```bash
API_PORT=8100 FRONTEND_PORT=5175 ./scripts/dev.sh
```

`./scripts/dev.sh` 也會自動往上找可用埠號。

如果後端不是跑在預設位置，也可以在 `frontend` 目錄建立 `.env.local`：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## API

### `GET /api/lohas`

查詢參數：

- `symbol`: yfinance 股票代號
- `range`: `1y`、`3y`、`3.5y`、`5y`、`10y`、`max`

範例：

```bash
curl "http://127.0.0.1:8000/api/lohas?symbol=SPY&range=3.5y"
```
