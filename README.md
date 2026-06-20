# Neighborhood Library App - Backend

This is the backend API for the Neighborhood Library Management System, built with Python FastAPI.

## Location

This backend code is located at:
```
/Users/sunitasahu/Documents/interview assignment/neigh-library-BE
```

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0.23
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Logging**: Structured JSON logging
- **Testing**: Pytest
- **Containerization**: Docker

## Quick Start

### Run with Docker Compose (Recommended)

From the backend directory or use the docker-compose in the main project:
```bash
cd "/Users/sunitasahu/Documents/interview assignment/senior arcitect role"
docker-compose up -d
```

### Run Standalone (Development)

```bash
cd "/Users/sunitasahu/Documents/interview assignment/neigh-library-BE"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://library_user:library_password@localhost:5432/library_db"
export SECRET_KEY="your-secret-key-change-in-production"

# Run the server
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
- ✅ Error handling with rollback
- ✅ Type hints throughout
- ✅ OpenAPI documentation

## Project Structure

```
neigh-library-BE/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── api/                    # API route handlers
│   │   ├── auth.py
│   │   ├── members.py
│   │   ├── books.py
│   │   └── borrowings.py
│   ├── controllers/            # Business logic layer
│   │   ├── base_controller.py
│   │   ├── member_controller.py
│   │   ├── book_controller.py
│   │   ├── borrowing_controller.py
│   │   └── auth_controller.py
│   ├── core/                   # Core utilities
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   ├── middleware.py
│   │   └── deps.py
│   ├── models/                 # SQLAlchemy models
│   │   └── models.py
│   ├── schemas/                # Pydantic schemas
│   │   └── schemas.py
│   └── db/
│       └── database.py
├── db/
│   └── schema.sql              # PostgreSQL schema
├── tests/                      # Unit tests
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_members.py
│   └── test_books.py
├── requirements.txt
├── requirements-test.txt
├── Dockerfile
└── README.md
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get JWT token |
| GET | `/auth/me` | Get current user info |

### Members
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/members/` | List all members |
| POST | `/members/` | Create new member |
| GET | `/members/{id}/` | Get member by ID |
| PUT | `/members/{id}/` | Update member |
| DELETE | `/members/{id}/` | Delete member (soft) |

### Books
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/books/` | List all books |
| POST | `/books/` | Create new book |
| GET | `/books/{id}/` | Get book by ID |
| PUT | `/books/{id}/` | Update book |
| DELETE | `/books/{id}/` | Delete book |

### Borrowings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/borrowings/` | List all borrowings |
| POST | `/borrowings/` | Borrow a book |
| GET | `/borrowings/{id}/` | Get borrowing by ID |
| POST | `/borrowings/{id}/return/` | Return a book |
| GET | `/borrowings/member/{id}/` | Get member's borrowings |
| GET | `/borrowings/book/{id}/` | Get book's borrowing history |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Required | PostgreSQL connection string |
| `SECRET_KEY` | Required | JWT secret key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiration time |

## Database Schema

- **users**: Authentication and user management
- **members**: Library members
- **books**: Book inventory
- **borrowings**: Borrowing records

Key features:
- Foreign key constraints
- CHECK constraints (e.g., available_copies <= total_copies)
- Automatic timestamps
- Database triggers for inventory management

## Testing

### Run Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_members.py

# Run specific test
pytest tests/test_members.py::TestMemberEndpoints::test_create_member_success
```

### Test Coverage

- ✅ Authentication (login, register, token validation)
- ✅ Member CRUD (all operations + edge cases)
- ✅ Book CRUD (all operations)
- ✅ Borrowing operations
- ✅ Error handling
- ✅ Input validation

## Error Handling & Logging

### Log Levels
- **INFO**: Normal operations (API requests, business events)
- **WARNING**: Unusual but handled situations
- **ERROR**: Expected errors (validation, duplicates, not found)
- **CRITICAL**: Unexpected errors requiring immediate attention

### Error Response Format
```json
{
  "detail": "User-friendly error message"
}
```

All errors include:
- Structured logging with context
- Database rollback on failures
- Request ID for tracing
- User ID for accountability

## Default Credentials

After running the database initialization:
- **Username**: `admin`
- **Password**: `admin123`

## API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development

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

### Import Errors
```bash
# Ensure you're in virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Documentation

Complete documentation available in the main project:
- `ARCHITECTURE.md` - System architecture
- `TESTING_GUIDE.md` - Testing documentation
- `ERROR_HANDLING_GUIDE.md` - Error handling patterns
- `CONTROLLER_ARCHITECTURE.md` - Controller pattern details

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
