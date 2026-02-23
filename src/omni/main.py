"""Main entry point for OMNI application."""

import uvicorn

from omni.api.app import app
from omni.db.engine import init_db
import asyncio


async def init_database():
    """Initialize the database on startup."""
    try:
        await init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")


def main():
    """Run the OMNI API server."""
    # Initialize database on startup
    asyncio.run(init_database())

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
