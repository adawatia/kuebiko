# Comic Book Website FastAPI Project

## Features
- FastAPI backend for comic book management
- CRUD for comics (title, description, genre, PDF upload)
- PDF file upload and download
- Ready for future author/genre management

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python main.py
   ```

3. API docs available at: http://localhost:8000/docs

## Project Structure
- app.py: FastAPI app and endpoints
- main.py: Entrypoint to run the server
- requirements.txt: Python dependencies
- uploads/: Directory for uploaded comic PDFs

---

You can extend the models and endpoints to add author and genre management as needed.
