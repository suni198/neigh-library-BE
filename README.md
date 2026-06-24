# Neighborhood Library App — Backend

REST API for the Neighborhood Library Management System, built with Python FastAPI.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.104.1 |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2.0.23 |
| Migrations | Alembic |
| Auth | JWT (python-jose + bcrypt) |
| Logging | Structured JSON (python-json-logger) |
| Testing | Pytest 7 + TestClient (SQLite in-memory) |
| Container | Docker |

---

## Bug Fixes Implemented

This assignment required identifying and fixing **4 bugs** in the original codebase:

### Bug 1 — No Confirmation Before Delete
**Problem:** Members and books were deleted immediately on clicking the delete icon with no confirmation dialog.  
**Fix:** Implemented a custom `ConfirmationModal` React component (frontend). Backend correctly returns `204 No Content` on success.

### Bug 2 — Members/Books With Active Borrowings Could Be Deleted
**Problem:** The API allowed deleting a member or book even when they had active (status=`BORROWED`) borrowings, breaking referential integrity.  
**Fix:** Added pre-delete checks in `member_controller.py` and `book_controller.py`:
```python
active_borrowings = db.query(Borrowing).filter(
    Borrowing.member_id == member_id,
    Borrowing.status == 'BORROWED'
).count()
if active_borrowings > 0:
    raise HTTPException(400, detail=f"Cannot delete member. Member has {active_borrowings} active borrowing(s)...")
```

### Bug 3 — Borrow Modal Member List Was Empty
**Problem:** The borrow book modal in the frontend always showed an empty member list because the API call was not being awaited.  
**Fix:** Corrected the async/await usage in the frontend API service call that fetches members for the dropdown.

### Bug 4 — Data Not Refreshed After Operations
**Problem:** After creating, updating, or deleting a record the UI did not refresh — stale data remained visible.  
**Fix:** Added explicit data refresh calls after every mutating operation in the frontend.

---

## Quick Start

### Option 1 — Docker Compose (Recommended)

Clone all three repositories into the same parent directory, then run from the parent:

```bash
git clone https://github.com/suni198/neigh-library-BE.git
git clone https://github.com/suni198/neigh-library-FE.git
git clone https://github.com/suni198/neigh-library-deployment.git

# Copy docker-compose to parent and start
cp neigh-library-deployment/docker-compose.yml .
docker-compose up -d
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3001 |
| Backend API | http://localhost:8001/docs |
| Backend ReDoc | http://localhost:8001/redoc |

Default credentials: `admin` / `admin123`

### Option 2 — Standalone Development

```bash
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

export DATABASE_URL="postgresql://library_user:library_password@localhost:5432/library_db"
export SECRET_KEY="your-secret-key-change-in-production"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access API: http://localhost:8000/docs

## Features

### Core Functionality
- ✅ RESTful API with full CRUD operations
- ✅ JWT-based authentication
- ✅ Member management
- ✅ Book inventory management
- ✅ Borrowing/return workflow
- ✅ Automatic inventory tracking (database triggers)

### Architecture
- ✅ Controller pattern for business logic
- ✅ Pydantic schemas for validation
- ✅ SQLAlchemy models for database
- ✅ Dependency injection
- ✅ Middleware for logging and auth

### Observability
- ✅ Structured JSON logging
- ✅ Request ID tracking
- ✅ User ID context propagation
- ✅ ERROR and CRITICAL log levels
- ✅ Exception tracking with stack traces

### Quality
- ✅ 25+ unit tests (pytest)
- ✅ Input validation
- ✅ Type hints throughout
- ✅ OpenAPI documentation

## Project Structure

```
neigh-library-BE/
├── app/
│   ├── main.py                     # FastAPI app, middleware, router registration
│   ├── api/                        # Route handlers (thin — delegate to controllers)
│   │   ├── auth.py
│   │   ├── members.py
│   │   ├── books.py
│   │   └── borrowings.py
│   ├── controllers/                # Business logic layer
│   │   ├── base_controller.py      # Shared CRUD helpers
│   │   ├── member_controller.py    # Member + active-borrowing guard
│   │   ├── book_controller.py      # Book + active-borrowing guard
│   │   ├── borrowing_controller.py # Borrow / return workflow
│   │   └── auth_controller.py      # JWT generation & verification
│   ├── core/
│   │   ├── config.py               # Settings via pydantic-settings
│   │   ├── security.py             # Password hashing, JWT helpers
│   │   ├── logging.py              # Structured JSON log configuration
│   │   ├── middleware.py           # Request logging, error handling
│   │   └── deps.py                 # FastAPI dependency injection
│   ├── models/
│   │   └── models.py               # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── schemas.py              # Pydantic request/response schemas
│   └── db/
│       └── database.py             # Engine, session factory, Base
├── db/
│   └── schema.sql                  # PostgreSQL DDL with triggers & constraints
├── tests/
│   ├── conftest.py                 # Fixtures: SQLite in-memory engine, TestClient
│   ├── test_auth.py                # Auth endpoint tests
│   ├── test_members.py             # Member CRUD + deletion guard tests
│   └── test_books.py               # Book CRUD + borrowing workflow tests
├── requirements.txt
├── requirements-test.txt
├── Dockerfile
└── README.md
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login — returns JWT |
| GET | `/auth/me` | Current user info |

### Members
| Method | Endpoint | Description |
|---|---|---|
| GET | `/members/` | List all members |
| POST | `/members/` | Create member |
| GET | `/members/{id}/` | Get by ID |
| PUT | `/members/{id}/` | Update |
| DELETE | `/members/{id}/` | Soft-delete (blocked if active borrowings) |

### Books
| Method | Endpoint | Description |
|---|---|---|
| GET | `/books/` | List all books |
| POST | `/books/` | Create book |
| GET | `/books/{id}/` | Get by ID |
| PUT | `/books/{id}/` | Update |
| DELETE | `/books/{id}/` | Delete (blocked if active borrowings) |

### Borrowings
| Method | Endpoint | Description |
|---|---|---|
| GET | `/borrowings/` | List all borrowings |
| POST | `/borrowings/` | Borrow a book |
| GET | `/borrowings/{id}/` | Get by ID |
| POST | `/borrowings/{id}/return/` | Return a book |
| GET | `/borrowings/member/{id}/` | Member borrowing history |
| GET | `/borrowings/book/{id}/` | Book borrowing history |

---

## Database Schema

Four tables in PostgreSQL:

```
users           — system authentication (username, hashed_password, is_superuser)
members         — library patrons (email unique, is_active soft-delete)
books           — inventory (isbn unique, total_copies, available_copies)
borrowings      — transaction ledger (member_id FK, book_id FK, status, fine_amount)
```

Key constraints:
- `books.available_copies <= books.total_copies` (CHECK)
- `borrowings.return_date >= borrowings.borrowed_date` (CHECK)
- `ON DELETE RESTRICT` on all FKs — history is preserved
- DB triggers automatically update `updated_at` on every row change

See `db/schema.sql` for full DDL.

---

## Testing

Tests use SQLite in-memory so they run offline with no Postgres dependency.

```bash
pip install -r requirements-test.txt

# Run all 37 tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Coverage: 37 tests, 0 failures

| File | Tests |
|---|---|
| `test_auth.py` | Login success/failure, register, token validation |
| `test_members.py` | Full CRUD, duplicate email, deletion guard (active borrowings), unauthorized access |
| `test_books.py` | Full CRUD, duplicate ISBN, deletion guard, borrow/return workflow, availability tracking |

**Note on test isolation:** Tests run against SQLite in-memory; production uses PostgreSQL. Fixtures import all ORM models before calling `Base.metadata.create_all()` to ensure every table exists regardless of test execution order.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing key |
| `ALGORITHM` | No (default `HS256`) | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No (default `30`) | Token TTL |

---

## Error Handling & Logging

All errors return:
```json
{ "detail": "Human-readable message" }
```

Logging is structured JSON with fields: `timestamp`, `level`, `request_id`, `user_id`, `method`, `path`, `duration_ms`. Every request and business event is logged.

---

## Production Checklist

- [ ] Rotate `SECRET_KEY` from the default
- [ ] Set `DATABASE_URL` from environment / secrets manager
- [ ] Enable HTTPS/TLS termination at load balancer
- [ ] Configure CORS for frontend domain only
- [ ] Set up log aggregation (ELK / CloudWatch)
- [ ] Configure connection pooling (PgBouncer)
- [ ] Enable rate limiting

---

## Repository

### Adding New Features

1. Create model in `app/models/models.py`
2. Create schemas in `app/schemas/schemas.py`
3. Create controller in `app/controllers/`
4. Create API routes in `app/api/`
5. Add tests in `tests/`
6. Update documentation

### Database Migration

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Docker

### Build Image

```bash
docker build -t library-backend .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e SECRET_KEY="your-secret" \
  library-backend
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U library_user -d library_db
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

## Production Deployment

Recommendations:
1. Use environment variables for secrets (never commit)
2. Enable CORS for frontend domain
3. Set up log aggregation (ELK/CloudWatch)
4. Configure database connection pooling
5. Enable rate limiting
6. Set up monitoring and alerts
7. Use HTTPS/TLS
8. Regular security updates

## Support

Repository: https://github.com/suni198/neigh-library-BE

For the complete full-stack application, see the docker-compose setup at:
```
/Users/sunitasahu/Documents/interview assignment/senior arcitect role/
```
