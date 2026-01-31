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

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API welcome message |
| GET | `/health` | Health check |
| POST | `/comics/` | Create a new comic |
| GET | `/comics/` | List all comics |
| GET | `/comics/{id}` | Get comic details |
| PUT | `/comics/{id}` | Update comic metadata |
| DELETE | `/comics/{id}` | Delete comic |
| POST | `/comics/{id}/pdf` | Upload PDF file |
| GET | `/comics/{id}/pdf` | Download PDF file |

## Example Usage

### Create a Comic
```bash
curl -X POST "http://localhost:8000/comics/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Spider-Man",
    "description": "Amazing adventures",
    "genres": ["Action", "Adventure"]
  }'
```

### Upload PDF
```bash
curl -X POST "http://localhost:8000/comics/1/pdf" \
  -F "pdf=@comic.pdf"
```

### Get All Comics
```bash
curl "http://localhost:8000/comics/"
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
