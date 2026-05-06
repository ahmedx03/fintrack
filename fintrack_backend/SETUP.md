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

## 4. Create the PostgreSQL database

```bash
psql -U postgres
CREATE DATABASE fintrack_db;
\q
```

## 5. Run migrations

```bash
python manage.py makemigrations users transactions analytics
python manage.py migrate
```

## 6. (Optional) Create a superuser for the admin panel

```bash
python manage.py createsuperuser
```

## 7. Start the dev server

```bash
python manage.py runserver
```

API is now live at http://localhost:8000

---

## API Reference

### Auth  (no token required)
| Method | URL | Body |
|--------|-----|------|
| POST | /api/auth/register/ | `username`, `email`, `password`, `password2` |
| POST | /api/auth/login/ | `username`, `password` → returns `access` + `refresh` |
| POST | /api/auth/refresh/ | `refresh` → returns new `access` |
| GET  | /api/auth/me/ | — (requires Bearer token) |

### Categories  (Bearer token required)
| Method | URL |
|--------|-----|
| GET | /api/categories/ |
| POST | /api/categories/ — body: `name`, `type` (income/expense) |
| DELETE | /api/categories/{id}/ |

### Transactions  (Bearer token required)
| Method | URL |
|--------|-----|
| GET | /api/transactions/?type=&category=&from=&to= |
| POST | /api/transactions/ — body: `type`, `amount`, `date`, `category`, `note` |
| PUT | /api/transactions/{id}/ |
| DELETE | /api/transactions/{id}/ |

### Analytics  (stub — Week 2)
| GET | /api/analytics/summary/ |
| GET | /api/analytics/by-category/ |
| GET | /api/analytics/over-time/ |
