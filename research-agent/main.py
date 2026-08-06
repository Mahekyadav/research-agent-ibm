"""
Main entry point — ResearchMind Agent
Run: python main.py  OR  uvicorn main:app --reload
"""
import logging
import uvicorn
from app.api import app
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )
