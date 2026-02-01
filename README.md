# Comic API

A modern RESTful API for managing comics and their PDF files, built with FastAPI and SQLAlchemy.

## Features

- ✅ **JSON-based API** - Clean REST endpoints with JSON request/response
- ✅ **PDF Management** - Upload, download, and manage comic PDF files
- ✅ **Genre Classification** - Categorize comics with multiple genres
- ✅ **Input Validation** - Robust validation using Pydantic schemas
- ✅ **Advanced Search** - Search by title or description
- ✅ **Rich Filtering** - Filter by multiple genres
- ✅ **Auto Documentation** - Interactive API docs with Swagger UI
- ✅ **CORS Support** - Ready for frontend integration
- ✅ **Error Handling** - Comprehensive error handling with proper status codes
- ✅ **Database Migrations** - Alembic for schema management

## Authentication

The API uses JWT authentication. 

### User Types
1. **Admin (Superuser)**: Can manage comics (create, update, delete, upload PDF).
2. **User**: Can view and read comics.

### Setup
To create an admin user, run the helper script:
```bash
python create_superuser.py
```

### API Endpoints
- **Register**: `POST /auth/register` (Create regular user)
- **Login**: `POST /auth/jwt/login` (Get access token)
- **Logout**: `POST /auth/jwt/logout`
- **Comics**: `/comics` (See API docs for details)

### Swagger UI
Navigate to `http://localhost:8000/docs`.
- Click "Authorize" button.
- Login with your credentials.
- Test the endpoints.

## Quick Start

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd comic
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment**
```bash
# Create .env file
echo "DATABASE_URL=sqlite:///./comics.db" > .env
```

4. **Run the application**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

## API Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/` | API welcome message | Public |
| GET | `/health` | Health check | Public |
| POST | `/auth/register` | Register new user | Public |
| POST | `/auth/jwt/login` | Login (Get Token) | Public |
| GET | `/comics/` | List all comics | Authenticated |
| GET | `/comics/{id}` | Get comic details | Authenticated |
| GET | `/comics/{id}/pdf` | Download PDF file | Authenticated |
| POST | `/comics/` | Create a new comic | **Admin** |
| PUT | `/comics/{id}` | Update comic metadata | **Admin** |
| DELETE | `/comics/{id}` | Delete comic | **Admin** |
| POST | `/comics/{id}/pdf` | Upload or Update PDF file | **Admin** |

## Example Usage

### 1. Login & Get Token
```bash
# Returns access_token
curl -X POST "http://localhost:8000/auth/jwt/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin"
```

### 2. Create a Comic (Admin)
```bash
curl -X POST "http://localhost:8000/comics/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "title": "Spider-Man",
    "description": "Amazing adventures",
    "genres": ["Action", "Adventure"]
  }'
```

### 3. Upload PDF (Admin)
```bash
curl -X POST "http://localhost:8000/comics/1/pdf" \
  -H "Authorization: Bearer <your_access_token>" \
  -F "pdf=@comic.pdf"
```

### 4. Get All Comics (User/Admin)
```bash
curl "http://localhost:8000/comics/" \
  -H "Authorization: Bearer <your_access_token>"
```

## Available Genres

- Action
- Adventure
- Fantasy
- Horror
- Romance
- Sci-Fi
- Mystery
- Other

## Project Structure

The project follows a modular structure:
- `app/` - Core application logic
- `app/api/` - API endpoints
- `app/models.py` - Database models
- `app/schemas.py` - Pydantic models

## API Documentation

Interactive documentation is available at `/docs` (Swagger UI).

## Technology Stack

- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation
- **Alembic** - Database migrations
- **SQLite** - Database (easily swappable)

## Development

### Running Tests
```bash
pytest app/tests/
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Code Quality
- Type hints throughout
- Comprehensive error handling
- Input validation
- Clean code principles

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing patterns
- All tests pass
- New features include tests
- Documentation is updated
