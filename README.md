# Comic API

A modern RESTful API for managing comics and their PDF files, built with FastAPI and SQLAlchemy.

## Project Structure

```
comic/
├── backend/           # Backend API (FastAPI + PostgreSQL)
│   ├── app/          # Application code
│   ├── alembic/      # Database migrations
│   ├── main.py       # Entry point
│   └── README.md     # Backend setup guide
├── frontend/         # Frontend (Vue.js)
│   └── src/         # Frontend source code
└── docker-compose.yml # PostgreSQL setup
```

## Features

- ✅ **JSON-based API** - Clean REST endpoints with JSON request/response
- ✅ **PDF Management** - Upload, download, and manage comic PDF files
- ✅ **Genre Classification** - Categorize comics with multiple genres
- ✅ **PostgreSQL Database** - Robust and scalable database
- ✅ **Input Validation** - Robust validation using Pydantic schemas
- ✅ **Advanced Search** - Search by title or description
- ✅ **Rich Filtering** - Filter by multiple genres
- ✅ **Auto Documentation** - Interactive API docs with Swagger UI
- ✅ **CORS Support** - Ready for frontend integration
- ✅ **Error Handling** - Comprehensive error handling with proper status codes
- ✅ **Database Migrations** - Alembic for schema management

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Start PostgreSQL**
```bash
docker-compose up -d
```

2. **Install backend dependencies**
```bash
cd backend
pip install -r requirements.txt
```

3. **Set up environment**
```bash
cd backend
cp .env.example .env
# Edit .env if needed (default PostgreSQL settings work with docker-compose)
```

4. **Run migrations**
```bash
cd backend
alembic upgrade head
```

5. **Create admin user**
```bash
cd backend
python create_superuser.py
```

6. **Run the application**
```bash
cd backend
python main.py
```

### Option 2: Manual PostgreSQL Setup

See [backend/README.md](backend/README.md) for detailed instructions.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

## API Access

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc


## Authentication

The API uses JWT authentication. 

### User Types
1. **Admin (Superuser)**: Can manage comics (create, update, delete, upload PDF).
2. **User**: Can view and read comics.

### API Endpoints
- **Register**: `POST /auth/register` (Create regular user)
- **Login**: `POST /auth/jwt/login` (Get access token)
- **Logout**: `POST /auth/jwt/logout`
- **Comics**: `/comics` (See API docs for details)

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

## Technology Stack

- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Robust database
- **Pydantic** - Data validation
- **Alembic** - Database migrations
- **Vue.js** - Frontend framework

## Development

### Running Tests
```bash
cd backend
pytest app/tests/
```

### Database Migrations
```bash
cd backend
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing patterns
- All tests pass
- New features include tests
- Documentation is updated
