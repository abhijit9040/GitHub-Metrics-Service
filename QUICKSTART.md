# Quick Start Guide

## Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Run the Server

```bash
# Option 1: Using uvicorn directly
uvicorn app.main:app --reload

# Option 2: Using the run script
python run.py
```

Server will be available at: http://localhost:8000

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Quick Test

```bash
# Fetch a repository
curl -X POST "http://localhost:8000/fetch/facebook/react"

# List all repositories
curl "http://localhost:8000/repos"

# Get aggregated metrics
curl "http://localhost:8000/aggregate"
```

## Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_fetch.py
```

## Project Structure

```
github-service-2/
├── app/              # Main application code
│   ├── main.py      # FastAPI app entry point
│   ├── models.py    # Database models
│   ├── schemas.py   # Pydantic schemas
│   ├── database.py  # Database configuration
│   ├── routers/     # API endpoints
│   └── services/    # Business logic (GitHub client)
├── tests/           # Test suite
├── requirements.txt # Python dependencies
└── README.md        # Full documentation
```


