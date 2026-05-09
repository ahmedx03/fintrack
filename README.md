# FinTrack

![Tests](https://github.com/ahmedx03/fintrack/actions/workflows/test.yml/badge.svg)

> A full-stack personal finance tracker — built for clarity, secured for production.

![Django](https://img.shields.io/badge/Django-5.0-092E20?style=flat&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.15-red?style=flat&logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat&logo=vite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-38BDF8?style=flat&logo=tailwindcss&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=flat&logo=postgresql&logoColor=white)
![Deployed on Render](https://img.shields.io/badge/API-Render-46E3B7?style=flat&logo=render&logoColor=white)
![Deployed on Vercel](https://img.shields.io/badge/Frontend-Vercel-000?style=flat&logo=vercel&logoColor=white)

---

## Live Demo

| | URL |
|---|---|
| **Frontend** | https://fintrack-six-jet.vercel.app |
| **API** | https://fintrack-l6gz.onrender.com/api/ |

> Note: The API is hosted on Render's free tier. The first request after a period of inactivity may take ~30 seconds to wake up.

---

## Features

### Core
- **User authentication** — register, login, logout with JWT (access + refresh tokens)
- **Token blacklisting** — logout invalidates the refresh token server-side
- **Transaction tracking** — add, edit, delete income and expense records
- **Category management** — create and organise custom income/expense categories
- **Filtering** — filter transactions by type, category, and date range
- **Cursor-based pagination** — stable, tamper-proof pagination for large transaction sets
- **CSV export** — download filtered transaction history as a CSV file
- **Account settings** — update email and change password from within the app

### Budget Tracking
- Set monthly spending limits per expense category
- Live progress bars showing spent vs. limit (colour-coded green / amber / red)
- Over-budget detection with remaining amount display

### Recurring Transactions
- Schedule repeating income or expense entries (weekly or monthly)
- Pause and resume schedules without deleting them
- Lazy processing — due schedules are automatically fired when the user opens their transactions, no cron job required

### Analytics Dashboard
- **Balance summary** — net balance, total income, and total expenses at a glance
- **Spending by category** — interactive donut chart (Recharts)
- **Balance over time** — monthly line chart showing income, expenses, and net balance
- **Budget status** — current month spent, remaining, and percentage used per budget
- **Recent transactions** — live feed of the last 8 transactions

### Security
- JWT authentication with 15-minute access tokens and 7-day rotating refresh tokens
- Token blacklist on logout — stolen refresh tokens are invalidated immediately
- Rate limiting on login (5/min) and register (10/hr) to prevent brute force
- Full IDOR protection — every query is scoped to the authenticated user
- Argon2 password hashing (current industry standard)
- CORS restricted to the exact frontend origin — no wildcards
- HSTS, `X-Frame-Options: DENY`, `Content-Type-Options: nosniff` in production
- Environment-based configuration — no secrets in source code

---

## Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 18 | UI framework |
| Vite 5 | Build tool & dev server |
| React Router v6 | Client-side routing |
| Tailwind CSS 3 | Utility-first styling |
| Recharts | Chart components |
| Axios | HTTP client with JWT interceptors |

### Backend
| Technology | Purpose |
|---|---|
| Django 5 | Web framework |
| Django REST Framework | API layer |
| SimpleJWT | JWT authentication + token blacklist |
| django-cors-headers | CORS policy enforcement |
| python-decouple | Environment variable management |
| Argon2 (argon2-cffi) | Password hashing |
| Gunicorn | Production WSGI server |
| WhiteNoise | Static file serving |

### Database & Infrastructure
| Technology | Purpose |
|---|---|
| PostgreSQL (Neon) | Primary database — serverless, free tier |
| Render | Backend hosting |
| Vercel | Frontend hosting |
| dj-database-url | Parse `DATABASE_URL` connection string |

---

## Architecture

```
Browser (Vercel)
    │
    │  HTTPS  ──  React SPA
    │              │  axios + JWT interceptors
    │              │
    ▼              ▼
Render (Gunicorn)
    │
    │  Django + DRF
    │  ├─ /api/auth/         → register, login, logout, refresh, me (GET/PATCH)
    │  ├─ /api/transactions/ → CRUD, cursor pagination, CSV export
    │  ├─ /api/categories/   → CRUD
    │  ├─ /api/budgets/      → CRUD (one per category)
    │  ├─ /api/recurring/    → CRUD, pause/resume
    │  └─ /api/analytics/    → summary, by-category, over-time, budget-status
    │
    ▼
Neon PostgreSQL
    ├─ users_user
    ├─ transactions_category
    ├─ transactions_transaction
    ├─ transactions_budget
    ├─ transactions_recurringtransaction
    └─ token_blacklist_*
```

**Auth flow:**
1. User logs in → Django returns `access` (15 min) + `refresh` (7 days) tokens
2. Axios attaches `Authorization: Bearer <access>` to every request
3. On 401, axios automatically calls `/auth/refresh/` and retries the original request
4. On logout, the refresh token is POSTed to `/auth/logout/` and blacklisted in the database

**Recurring transaction flow:**
1. User creates a schedule with an interval and first occurrence date
2. On every `GET /api/transactions/` call, due schedules are lazily fired — real transactions are created and the next occurrence date advances
3. No cron job or external scheduler required

---

## Local Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- A PostgreSQL database (local or [Neon](https://neon.tech) free tier)

---

### Backend

```bash
# 1. Clone the repo
git clone https://github.com/ahmedx03/fintrack.git
cd fintrack/fintrack_backend

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
copy .env.example .env
# Edit .env with your values (see Environment Variables section below)

# 5. Run migrations
python manage.py migrate

# 6. Start the development server
python manage.py runserver
# API available at http://localhost:8000
```

---

### Frontend

```bash
cd fintrack/fintrack_frontend

# 1. Install dependencies
npm install

# 2. Create your .env file
echo "VITE_API_URL=" > .env
# Leave VITE_API_URL empty — Vite proxies /api to localhost:8000 in dev

# 3. Start the dev server
npm run dev
# App available at http://localhost:5173
```

---

## Environment Variables

### Backend (`fintrack_backend/.env`)

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Enable debug mode | `True` in dev, `False` in prod |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames | `localhost,127.0.0.1` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:5173` |

> **Never commit `.env` to version control.** It is listed in `.gitignore`.

### Frontend (`fintrack_frontend/.env`)

| Variable | Description | Example |
|---|---|---|
| `VITE_API_URL` | Backend API base URL (empty = use Vite proxy in dev) | `https://fintrack-l6gz.onrender.com` |

---

## API Reference

All endpoints except auth require an `Authorization: Bearer <access_token>` header.

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register/` | Register a new user |
| `POST` | `/api/auth/login/` | Obtain access + refresh tokens |
| `POST` | `/api/auth/refresh/` | Rotate refresh token |
| `POST` | `/api/auth/logout/` | Blacklist refresh token |
| `GET` | `/api/auth/me/` | Get current user profile |
| `PATCH` | `/api/auth/me/` | Update email or change password |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/transactions/` | List transactions — cursor paginated. Filters: `type`, `category`, `from`, `to` |
| `POST` | `/api/transactions/` | Create a transaction |
| `GET` | `/api/transactions/:id/` | Retrieve a single transaction |
| `PATCH` | `/api/transactions/:id/` | Update a transaction |
| `DELETE` | `/api/transactions/:id/` | Delete a transaction |
| `GET` | `/api/transactions/export/` | Download transactions as CSV (accepts same filters as list) |

### Categories
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/categories/` | List categories |
| `POST` | `/api/categories/` | Create a category |
| `DELETE` | `/api/categories/:id/` | Delete a category |

### Budgets
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/budgets/` | List budgets |
| `POST` | `/api/budgets/` | Create a budget (one per category) |
| `PATCH` | `/api/budgets/:id/` | Update monthly limit |
| `DELETE` | `/api/budgets/:id/` | Delete a budget |

### Recurring Transactions
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/recurring/` | List recurring schedules |
| `POST` | `/api/recurring/` | Create a schedule |
| `PATCH` | `/api/recurring/:id/` | Update a schedule (e.g. pause with `is_active: false`) |
| `DELETE` | `/api/recurring/:id/` | Delete a schedule |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/summary/` | Income, expenses, balance totals. Filters: `from`, `to` |
| `GET` | `/api/analytics/by-category/` | Spending grouped by category. Filters: `type`, `from`, `to` |
| `GET` | `/api/analytics/over-time/` | Monthly income/expense/balance trend. Filters: `period`, `from`, `to` |
| `GET` | `/api/analytics/budget-status/` | Current month spent, remaining, and % used per budget |

---

## Testing

```bash
cd fintrack_backend
python -m pytest
```

107 tests across users, transactions, analytics, budgets, and recurring transactions. Uses `--reuse-db` to avoid recreating the Neon test database on every run.

---

## Security Highlights

| Area | Implementation |
|---|---|
| Password hashing | Argon2 (PHC winner, stronger than bcrypt/PBKDF2) |
| Token lifetime | Access: 15 min · Refresh: 7 days, rotated on use |
| Token invalidation | Refresh tokens blacklisted in DB on logout |
| Brute force | Login: 5 req/min · Register: 10 req/hr per IP |
| IDOR | All queries filtered by `user=request.user` |
| Category ownership | Serializer validates category belongs to the requesting user |
| CORS | Restricted to exact frontend origin — no wildcards |
| HTTPS | Enforced in production via `SECURE_SSL_REDIRECT` |
| HSTS | 1-year policy with `includeSubdomains` + preload |
| Clickjacking | `X-Frame-Options: DENY` |
| Error responses | Custom exception handler — no stack traces in production |
| Secrets | All via environment variables — never in source code |

---

## Project Structure

```
fintrack/
├── fintrack_backend/
│   ├── config/
│   │   ├── settings.py           # Environment-based configuration
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── exceptions.py         # Custom DRF exception handler
│   ├── users/
│   │   ├── models.py             # Custom User model
│   │   ├── serializers.py        # Register, User, UpdateMe serializers
│   │   ├── views.py              # Register, Me (GET/PATCH), Logout views
│   │   ├── urls.py
│   │   └── throttles.py          # Login + Register rate limiters
│   ├── transactions/
│   │   ├── models.py             # Category, Transaction, Budget, RecurringTransaction
│   │   ├── serializers.py        # With ownership + duplicate-budget validation
│   │   ├── views.py              # CRUD views + lazy recurring processing
│   │   ├── urls.py
│   │   ├── utils.py              # parse_date_param, process_recurring_for_user
│   │   └── management/
│   │       └── commands/
│   │           └── process_recurring.py  # Manual backfill command
│   ├── analytics/
│   │   ├── views.py              # Summary, by-category, over-time, budget-status
│   │   └── urls.py
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── .env.example
│   ├── Procfile
│   └── render.yaml
│
└── fintrack_frontend/
    ├── src/
    │   ├── api/
    │   │   ├── axios.js           # Axios instance + JWT interceptors
    │   │   └── index.js           # All API call definitions
    │   ├── context/
    │   │   └── AuthContext.jsx    # Login, logout, register state
    │   ├── components/
    │   │   ├── Navbar.jsx
    │   │   ├── BalanceSummaryCards.jsx
    │   │   ├── SpendingPieChart.jsx
    │   │   └── BalanceLineChart.jsx
    │   ├── hooks/
    │   │   ├── useTransactions.js # Cursor pagination + loadMore
    │   │   └── useSummary.js
    │   ├── pages/
    │   │   ├── Dashboard.jsx
    │   │   ├── Transactions.jsx   # Filters, CSV export, load more
    │   │   ├── AddTransaction.jsx # Create + edit
    │   │   ├── Categories.jsx
    │   │   ├── Budgets.jsx        # Progress bars, CRUD
    │   │   ├── Recurring.jsx      # Schedules, pause/resume
    │   │   ├── Settings.jsx       # Email + password change
    │   │   ├── Login.jsx
    │   │   └── Register.jsx
    │   └── utils/
    │       └── format.js          # formatCurrency, formatDate
    ├── vercel.json
    └── vite.config.js
```

---

## Future Improvements

- [ ] **httpOnly cookie auth** — migrate from localStorage to server-set httpOnly cookies to eliminate XSS token theft risk
- [ ] **Error monitoring** — Sentry integration for production error tracking
- [ ] **Custom domain** — branded URL
- [ ] **Dark mode** — system-preference-aware theme toggle
- [ ] **Budget alerts** — email notification when a budget hits 80% or 100%

---

## Author

Built by **Pookii**

---

## License

MIT — free to use, fork, and build on.
