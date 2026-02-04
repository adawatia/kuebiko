"""
Main entry point for the Comic API application.
Run with: python backend/main.py or cd backend && uvicorn main:app --reload
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

