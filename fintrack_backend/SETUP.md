# FinTrack Backend — Quick Start

## 1. Create & activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure environment variables

```bash
cp .env.example .env
# Then edit .env with your PostgreSQL credentials and a real SECRET_KEY
```

Generate a secret key quickly:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 4. Run migrations

```bash
python manage.py migrate
```

## 5. (Optional) Create a superuser for the admin panel

```bash
python manage.py createsuperuser
```

## 6. Start the dev server

```bash
python manage.py runserver
```

API is now live at http://localhost:8000

---

## Running tests

```bash
python -m pytest
```

Tests use a separate Neon test database and `--reuse-db` to avoid recreating it on every run. 107 tests across users, transactions, analytics, budgets, and recurring transactions.

---

## Recurring transactions

Recurring schedules are processed lazily — when a user calls `GET /api/transactions/`, any due schedules are automatically fired and real transactions are created. No cron job required.

To manually process all due schedules for all users (e.g. for backfills):
```bash
python manage.py process_recurring
python manage.py process_recurring --dry-run   # preview only
```

---

## API Reference

All endpoints except auth require a `Bearer <access_token>` header.

### Auth
| Method | URL | Notes |
|--------|-----|-------|
| POST | `/api/auth/register/` | Body: `username`, `email`, `password`, `password2` |
| POST | `/api/auth/login/` | Body: `username`, `password` → returns `access` + `refresh` |
| POST | `/api/auth/refresh/` | Body: `refresh` → returns new `access` |
| GET | `/api/auth/me/` | Returns current user profile |
| PATCH | `/api/auth/me/` | Update `email` or change password (`current_password`, `new_password`) |
| POST | `/api/auth/logout/` | Body: `refresh` — blacklists the token |

### Categories
| Method | URL | Notes |
|--------|-----|-------|
| GET | `/api/categories/` | Lists the authenticated user's categories |
| POST | `/api/categories/` | Body: `name`, `type` (`income` or `expense`) |
| DELETE | `/api/categories/{id}/` | |

### Transactions
| Method | URL | Notes |
|--------|-----|-------|
| GET | `/api/transactions/` | Cursor-paginated. Filters: `type`, `category`, `from`, `to` |
| POST | `/api/transactions/` | Body: `type`, `amount`, `date`, `category` (id, optional), `note` |
| GET | `/api/transactions/{id}/` | |
| PATCH | `/api/transactions/{id}/` | |
| DELETE | `/api/transactions/{id}/` | |
| GET | `/api/transactions/export/` | Streams a CSV file. Accepts the same filters as the list endpoint |

### Budgets
| Method | URL | Notes |
|--------|-----|-------|
| GET | `/api/budgets/` | Lists the user's monthly budgets |
| POST | `/api/budgets/` | Body: `category` (id), `monthly_limit`. One budget per category |
| PATCH | `/api/budgets/{id}/` | Update `monthly_limit` |
| DELETE | `/api/budgets/{id}/` | |

### Recurring Transactions
| Method | URL | Notes |
|--------|-----|-------|
| GET | `/api/recurring/` | Lists the user's recurring schedules |
| POST | `/api/recurring/` | Body: `type`, `amount`, `interval` (`weekly`/`monthly`), `next_occurrence`, `category`, `note` |
| PATCH | `/api/recurring/{id}/` | e.g. pause with `is_active: false` |
| DELETE | `/api/recurring/{id}/` | |

### Analytics
| Method | URL | Notes |
|--------|-----|-------|
| GET | `/api/analytics/summary/` | Total income, expenses, balance. Filters: `from`, `to` |
| GET | `/api/analytics/by-category/` | Totals grouped by category. Filters: `type`, `from`, `to` |
| GET | `/api/analytics/over-time/` | Income/expenses per period. Filters: `period` (`day`/`month`), `from`, `to` |
| GET | `/api/analytics/budget-status/` | Current month spent/remaining for each budget |
