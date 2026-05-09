---
name: fintrack-dev
description: Full context for developing, debugging, and extending the FinTrack personal finance app. Use whenever working on the Django backend, React frontend, deployment pipeline, or security configuration of this project.
---

# Instructions

FinTrack is a full-stack personal finance tracker built with Django 5 + DRF on the backend and React 18 + Vite + Tailwind CSS on the frontend. Always read this file at the start of any FinTrack development session to restore full project context before touching any code.

## Project Layout

```
fintrack/
├── fintrack_backend/      # Django 5 + DRF API
│   ├── config/            # settings.py, urls.py, wsgi.py, exceptions.py
│   ├── users/             # Custom User model, JWT auth views, throttles
│   ├── transactions/      # Category + Transaction CRUD, utils.py (safe date parsing)
│   ├── analytics/         # Summary, by-category, over-time aggregation views
│   └── requirements.txt
└── fintrack_frontend/     # React 18 + Vite + Tailwind
    └── src/
        ├── api/           # axios.js (JWT interceptors) + index.js (all API calls)
        ├── context/       # AuthContext.jsx (login / logout / register)
        ├── components/    # Navbar, BalanceSummaryCards, charts
        ├── hooks/         # useTransactions, useSummary
        ├── pages/         # Dashboard, Transactions, Categories, Login, Register
        └── utils/         # currency + date formatters
```

## Key Guidelines

### Backend conventions
- All querysets **must** be scoped to `request.user` — IDOR protection is non-negotiable.
- Date params from query strings go through `transactions/utils.py → parse_date_param()`. Never use `datetime.fromisoformat()` directly in views.
- Category ownership is validated in the serializer, not the view.
- Rate limiting lives in `users/throttles.py` — `LoginRateThrottle` (5/min) and `RegisterRateThrottle` (10/hr).
- The custom exception handler in `config/exceptions.py` suppresses stack traces in production; don't bypass it.
- Password hashing order: Argon2 → PBKDF2 → PBKDF2SHA1 → BCrypt. Never change Argon2 out of first position.
- Token lifetime: access = 15 min, refresh = 7 days, rotation + blacklist both enabled.
- `conn_max_age=600` + `conn_health_checks=True` are already set in the `dj_database_url.config()` call — do not duplicate.

### Frontend conventions
- API calls go through `src/api/index.js` — never call `axios` directly from a page or hook.
- The Axios instance (`src/api/axios.js`) has JWT interceptors: auto-attaches `Authorization: Bearer`, auto-refreshes on 401.
- Auth state lives in `AuthContext` only — no other component stores tokens or user data.
- Tokens are in `localStorage` (access + refresh). The `logout()` flow blacklists the refresh token server-side before clearing storage.
- Tailwind palette: `navy-*` (900/800/700) for dark surfaces, `brand-*` (blue 50–900) for interactive elements, `aqua-*` for accents. Auth pages use `bg-auth-gradient`; app shell uses `bg-app-bg`.
- Shared CSS utilities live in `src/index.css`: `.input-base`, `.input-auth`, `.btn-primary`, `.btn-auth`, `.card`.
- In dev, `VITE_API_URL` is left **empty** — Vite proxies `/api` to `localhost:8000`. In production it's set to the Render URL.

### Deployment
- **Backend**: Render (free tier) — web service running `gunicorn config.wsgi`.
- **Frontend**: Vercel — auto-deploys from `fintrack_frontend/` on push to `main`.
- **Database**: Neon PostgreSQL (free tier, serverless) with PgBouncer connection pooling enabled.
- Neon free tier suspends compute after inactivity. `conn_health_checks=True` handles stale connections automatically. If a deploy fails with `connection is bad`, check the Neon console and resume the project if suspended.
- Render free tier sleeps after 15 min of inactivity — first request after sleep takes ~30 s.
- Environment variables **never** go in source code. Backend uses `python-decouple`; frontend uses Vite `import.meta.env`.

### Security rules (do not regress)
- `SECURE_SSL_REDIRECT`, HSTS (1 yr + subdomains + preload), `X-Frame-Options: DENY`, `CONTENT_TYPE_NOSNIFF` are all active when `DEBUG=False`.
- `CORS_ALLOWED_ORIGINS` must be the exact Vercel URL with **no trailing slash**.
- `ALLOWED_HOSTS` must include the Render hostname (`fintrack-l6gz.onrender.com`).
- Never add `CORS_ALLOW_ALL_ORIGINS = True`.

### Migration workflow
```bash
cd fintrack_backend
python manage.py makemigrations users transactions analytics
python manage.py migrate
```
Run `makemigrations` per-app (not bare) to avoid ghost migrations.

## Environment Variables

### Backend (`fintrack_backend/.env`)
| Variable | Example |
|---|---|
| `SECRET_KEY` | `django-insecure-...` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `fintrack-l6gz.onrender.com` |
| `DATABASE_URL` | `postgresql://user:pass@host/db` (Neon pooler URL) |
| `CORS_ALLOWED_ORIGINS` | `https://fintrack-six-jet.vercel.app` |

### Frontend (`fintrack_frontend/.env`)
| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://fintrack-l6gz.onrender.com` (empty in dev) |

## Live URLs
| | URL |
|---|---|
| Frontend | https://fintrack-six-jet.vercel.app |
| API | https://fintrack-l6gz.onrender.com/api/ |

## Examples

### Input
"Add a budget tracking feature with monthly limits per category"

### Output
1. Add a `Budget` model in `transactions/models.py` with `user`, `category` (FK), `month` (DateField, store as first of month), `limit` (DecimalField). Scope queryset to `request.user`.
2. Add serializer with category ownership validation (same pattern as `TransactionSerializer`).
3. Add CRUD view in `transactions/views.py` — filter by `user=request.user`.
4. Wire up URL in `transactions/urls.py`.
5. Add `budgetsAPI` entry in `src/api/index.js`.
6. Build `useBudgets` hook following the `useTransactions` pattern.
7. Add a `Budgets` page and link it in `Navbar.jsx`.

### Input
"The deploy is failing with `DisallowedHost`"

### Output
Go to Render → Environment → `ALLOWED_HOSTS` and add the Render hostname (e.g. `fintrack-l6gz.onrender.com`). No code change needed — `ALLOWED_HOSTS` is read from the env var via `python-decouple`.

### Input
"Add a new analytics endpoint"

### Output
Add a new function-based or class-based view in `analytics/views.py`. Filter all ORM queries with `user=request.user`. Parse any date params with `parse_date_param()`. Register the URL in `analytics/urls.py`. Add the corresponding method to `analyticsAPI` in `src/api/index.js`.
