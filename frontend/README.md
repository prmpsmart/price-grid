# PriceGrid Web

Dashboard for the PriceGrid API. Same stack and look as `prmpsmart.github.io`:
React 18 + TypeScript + Vite + Tailwind, a tiny pushState router, forest theme.
No chart or router library; charts are inline SVG.

## Run

```bash
# API on :8000 (from the repo root)
docker-compose up --build

cd frontend
npm install
npm run dev        # http://localhost:5173
```

In dev, `/api` is proxied to `VITE_API_TARGET` (default `http://localhost:8000`),
because the API has no CORS middleware.

## Pages

| Route      | Uses                                   | Who             |
| ---------- | -------------------------------------- | --------------- |
| `/`        | `/prices/current`, `/alerts`           | everyone        |
| `/compare` | `/prices/compare`                      | everyone        |
| `/trends`  | `/prices/trends?window=7d\|30d\|90d`   | everyone        |
| `/history` | `/prices/history/{good_id}`            | everyone        |
| `/alerts`  | `/alerts`, `/alerts/thresholds`        | admin           |
| `/submit`  | `POST /prices`, `POST /vendors`        | vendor, admin   |
| `/catalog` | goods / markets / vendors, create forms| admin to create |

Role checks in the UI only hide controls; the API stays the authority.

## Production

`npm run build` emits `dist/`. Serve it behind the same origin as the API
(reverse proxy `/api` to FastAPI and fall back to `index.html` for unknown
paths), or set `VITE_API_BASE` to the API origin and add CORS to the API.
