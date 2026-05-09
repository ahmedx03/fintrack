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

## Screenshots

| Dashboard | Transactions | Add Transaction |
|---|---|---|
| ![Dashboard](https://via.placeholder.com/380x220/1e3a8a/ffffff?text=Dashboard) | ![Transactions](https://via.placeholder.com/380x220/1e3a8a/ffffff?text=Transactions) | ![Add Transaction](https://via.placeholder.com/380x220/1e3a8a/ffffff?text=Add+Transaction) |

| Login | Categories |  |
|---|---|---|
| ![Login](https://via.placeholder.com/380x220/0d1b2e/ffffff?text=Login) | ![Categories](https://via.placeholder.com/380x220/1e3a8a/ffffff?text=Categories) | |

---

## Features

### Core
- **User authentication** — register, login, logout with JWT (access + refresh tokens)
- **Token blacklisting** — logout invalidates the refresh token server-side
- **Transaction tracking** — add, edit, delete income and expense records
- **Category management** — create and organise custom income/expense categories
- **Filtering** — filter transactions by type, category, and date range

### Analytics Dashboard
- **Balance summary** — net balance, total income, and total expenses at a glance
- **Spending by category** — interactive donut chart (Recharts)
- **Balance over time** — monthly line chart showing income, expenses, and net balance
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
    │  ├─ /api/auth/        → JWT login, register, logout, refresh, me
    │  ├─ /api/transactions/ → CRUD (user-scoped)
    │  ├─ /api/categories/  → CRUD (user-scoped)
    │  └─ /api/analytics/   → summary, by-category, over-time
    │
    ▼
Neon PostgreSQL
    ├─ users_user
    ├─ transactions_category
    ├─ transactions_transaction
    └─ token_blacklist_*
```

**Auth flow:**
1. User logs in → Django returns `access` (15 min) + `refresh` (7 days) tokens
2. Axios attaches `Authorization: Bearer <access>` to every request
3. On 401, axios automatically calls `/auth/refresh/` and retries the original request
4. On logout, the refresh token is POSTed to `/auth/logout/` and blacklisted in the database

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
python manage.py makemigrations
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
| `SECRET_KEY` | Django secret key — generate at [djecrety.ir](https://djecrety.ir) | `django-insecure-...` |
| `DEBUG` | Enable debug mode (`True` in dev, `False` in prod) | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames | `localhost,127.0.0.1` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:5173` |

> **Never commit `.env` to version control.** It is listed in `.gitignore`.

### Frontend (`fintrack_frontend/.env`)

| Variable | Description | Example |
|---|---|---|
| `VITE_API_URL` | Backend API base URL (empty = use Vite proxy in dev) | `https://fintrack-api.onrender.com` |

---

## API Reference

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register/` | None | Register a new user |
| `POST` | `/api/auth/login/` | None | Obtain access + refresh tokens |
| `POST` | `/api/auth/refresh/` | None | Rotate refresh token |
| `POST` | `/api/auth/logout/` | Bearer | Blacklist refresh token |
| `GET` | `/api/auth/me/` | Bearer | Get current user info |

### Transactions
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/transactions/` | Bearer | List transactions (supports `?type`, `?category`, `?from`, `?to`) |
| `POST` | `/api/transactions/` | Bearer | Create a transaction |
| `PUT` | `/api/transactions/:id/` | Bearer | Update a transaction |
| `DELETE` | `/api/transactions/:id/` | Bearer | Delete a transaction |

### Categories
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/categories/` | Bearer | List categories |
| `POST` | `/api/categories/` | Bearer | Create a category |
| `DELETE` | `/api/categories/:id/` | Bearer | Delete a category |

### Analytics
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/analytics/summary/` | Bearer | Income, expenses, balance totals |
| `GET` | `/api/analytics/by-category/` | Bearer | Spending grouped by category |
| `GET` | `/api/analytics/over-time/` | Bearer | Monthly income/expense/balance trend |

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
│   │   ├── settings.py       # Environment-based configuration
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── exceptions.py     # Custom DRF exception handler
│   ├── users/
│   │   ├── models.py         # Custom User model
│   │   ├── serializers.py    # Register + User serializers
│   │   ├── views.py          # Register, Me, Logout views
│   │   ├── urls.py
│   │   └── throttles.py      # Login + Register rate limiters
│   ├── transactions/
│   │   ├── models.py         # Category + Transaction models
│   │   ├── serializers.py    # With category ownership validation
│   │   ├── views.py          # CRUD views (user-scoped)
│   │   └── utils.py          # Safe date param parsing
│   ├── analytics/
│   │   └── views.py          # Summary, by-category, over-time
│   ├── requirements.txt
│   ├── .env.example
│   └── render.yaml
│
└── fintrack_frontend/
    ├── src/
    │   ├── api/              # Axios instance + JWT interceptors
    │   ├── components/       # Navbar, charts, summary cards
    │   ├── context/          # AuthContext (login/logout/register)
    │   ├── hooks/            # useTransactions, useSummary
    │   ├── pages/            # Dashboard, Transactions, Categories, Auth
    │   └── utils/            # Currency + date formatters
    ├── public/
    │   └── favicon.svg
    ├── index.html
    └── tailwind.config.js
```

---

## Future Improvements

- [ ] **Budget tracking** — set monthly limits per category with progress indicators
- [ ] **Recurring transactions** — auto-log repeating income/expenses
- [ ] **CSV export** — download transaction history
- [ ] **Pagination** — cursor-based pagination for large transaction sets
- [ ] **Account settings** — change password and email
- [ ] **httpOnly cookie auth** — migrate from localStorage to server-set httpOnly cookies to eliminate XSS token theft risk
- [x] **Test suite** — 70 pytest tests covering auth, IDOR, CRUD, filters, and analytics
- [x] **CI/CD** — GitHub Actions runs the full suite on every push; auto-deploys to Render on green main
- [ ] **Error monitoring** — Sentry integration for production error tracking
- [ ] **Custom domain** — branded URL

---

## Author

Built by **Pookii**

---

## License

MIT — free to use, fork, and build on.
