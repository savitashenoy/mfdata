# Mutual Fund Analysis Dashboard - Flask/Vercel Ready

This version routes all mutual-fund API calls through Flask. The browser no longer depends on CORS proxy services.

## What changed

- `api.mfapi.in` calls are routed through Flask:
  - `/api/mf/search?q=<fund>`
  - `/api/mf/<scheme_code>`
  - `/api/mf/<scheme_code>/latest`
- `mfdata.in` holdings calls are routed through Flask:
  - `/api/mfdata/<path>`
- Removed browser-side proxy fallback logic for CORS services.
- Added backend timeout, cache headers, error handling, and route guard for `mfdata` paths.
- Kept the existing dashboard UI and fund dataset intact.

## Local run

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Health check:

```text
http://127.0.0.1:5000/healthz
```

## Vercel deployment

From this folder:

```bash
vercel
```

or push this folder to GitHub and import it into Vercel.

Required files are already included:

```text
app.py
requirements.txt
vercel.json
templates/index.html
runtime.txt
Procfile
```

## Backend routes

```text
/                         Dashboard UI
/healthz                  Health check
/api/mf/search?q=query    Search mutual funds through Flask
/api/mf/<code>            Full NAV history through Flask
/api/mf/<code>/latest     Latest NAV through Flask
/api/mfdata/<path>        Holdings/portfolio API through Flask
```
