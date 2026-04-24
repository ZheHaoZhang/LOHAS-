# Copilot Instructions for LOHAS

## Build, run, and validation commands

### Setup
```bash
./scripts/setup.sh
```

### Run the full app locally
```bash
./scripts/dev.sh
```

### Run backend only
```bash
./scripts/start-backend.sh
```

### Run frontend only
```bash
./scripts/start-frontend.sh
```

### Frontend build
```bash
cd frontend && npm run build
```

### Backend smoke check
```bash
curl "http://127.0.0.1:8000/api/lohas?symbol=SPY&range=3.5y"
```

### Single-target validation
There is no dedicated test runner or linter configured in this repository right now. For focused validation, use one of these:

```bash
# Check one API path end-to-end
curl "http://127.0.0.1:8000/api/lohas?symbol=SPY&range=3.5y"

# Check one backend calculation directly
. .venv/bin/activate && python - <<'PY'
from backend.app.lohas import get_lohas_data
print(get_lohas_data('SPY', '3.5y')['analyses']['channel']['latestUpperBound'])
PY
```

## High-level architecture

- The backend is a small FastAPI service in `backend/app/main.py`. Its main responsibility is exposing `/api/lohas`, validating query params, and translating domain errors from `backend/app/lohas.py` into HTTP responses.
- `backend/app/lohas.py` is the analytics core. Each request downloads daily price history from yfinance once, normalizes it into a single DataFrame, then prepares **both** analysis modes in one response under `analyses["five-lines"]` and `analyses["channel"]`.
- The frontend is a single Vue 3 SPA rooted in `frontend/src/App.vue`. The page fetches the bundled API payload once per `symbol + range`, stores it in memory, and switches between analysis modes locally without another API call.
- `frontend/src/components/LohasChart.vue` is a shared chart renderer for both modes. It accepts the currently selected analysis object and branches on `analysisMode` to build the appropriate ECharts series.
- Frontend app-level state is intentionally lightweight and lives in composables instead of a store:
  - `useTheme.ts` drives `data-theme` on `<html>` and updates the `theme-color` meta tag.
  - `useSearchHistory.ts` keeps recent symbols in localStorage.
  - `useIosHomeScreenPrompt.ts` controls the Safari home-screen prompt banner.
- Local development assumes the backend is on `127.0.0.1:8000`. `frontend/vite.config.ts` proxies `/api` there, and `scripts/start-frontend.sh` can override it through `VITE_API_BASE_URL`.

## Key repository conventions

- Keep the two analysis modes keyed exactly as `'five-lines'` and `'channel'`. The backend bundles both into one response, and the frontend selects the active dataset from that bundle. Do **not** add mode-specific fetches when only the tab selection changes.
- The current 樂活通道 implementation is intentionally aligned with the `五線譜+通道V0.2(VBA版本).xlsm` workbook, not the older weekly-channel experiments:
  - input series: daily close
  - middle line: rolling 100-trading-day average
  - bands: `middle ± 2 * STDEVP(100-day closes)`
  - UI copy should keep this mode labeled as **Preview**
- The 樂活五線譜 calculation uses OLS regression over the full selected date range and residual standard deviation to derive the five parallel lines. If you change the backend math, keep the frontend summary cards and chart legend aligned with the returned field names.
- `download_history()` uses adjusted close when available and rescales high/low with the same adjustment factor. Reuse that normalization path instead of mixing adjusted and raw prices later in the pipeline.
- Symbol input is always normalized to uppercase before requests and before saving search history.
- Theme, search history, and iOS prompt dismissal each use fixed localStorage keys:
  - `lohas-theme`
  - `lohas-search-history`
  - `lohas-ios-home-screen-prompt-dismissed`
- Styling is centralized in `frontend/src/style.css` with CSS custom properties for light/dark tokens. Prefer extending those tokens over adding ad hoc inline styles or component-local color values.
- `frontend/vite.config.ts` already splits `echarts` and `zrender` into separate chunks. Preserve that pattern if bundle-related changes touch chart dependencies.
