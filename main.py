"""
Main entry point for the Comic API application.
Run with: python main.py or uvicorn main:app --reload
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

