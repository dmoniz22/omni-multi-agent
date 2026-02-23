"""Main entry point for OMNI application."""

import uvicorn

from omni.api.app import app


def main():
    """Run the OMNI API server."""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
