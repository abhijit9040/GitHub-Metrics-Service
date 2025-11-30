# GitHub Metrics Service

A FastAPI-based service that fetches, stores, and aggregates GitHub repository metrics including stars, open issues, and programming languages. This service demonstrates modern backend development practices with async operations, pagination handling, database storage, and comprehensive error handling.

## Features

- **Async Repository Fetching**: Fetch repository metrics from GitHub API asynchronously
- **Pagination Handling**: Automatically handles pagination for GitHub Issues API to get accurate issue counts
- **Database Storage**: Stores repository metrics in SQLite database
- **Aggregation API**: Compute totals and breakdowns across multiple repositories
- **Filtering**: Filter repositories by owner, language, and limit results
- **Input Validation**: Comprehensive validation with Pydantic models
- **Error Handling**: Graceful handling of rate limits, timeouts, and API errors
- **API Documentation**: Auto-generated Swagger UI documentation

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **httpx**: Async HTTP client for GitHub API calls
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation using Python type annotations
- **SQLite**: Lightweight database for local storage
- **PyTest**: Testing framework with async support

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd github-service-2
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Service

### Start the Server

```bash
uvicorn app.main:app --reload
```

The server will start on `http://localhost:8000`

### Access API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Fetch Repository Metrics

Fetch repository data from GitHub and store it in the database.

**Endpoint**: `POST /fetch/{owner}/{repo}`

**Parameters**:
- `owner` (path): GitHub repository owner (e.g., "facebook")
- `repo` (path): Repository name (e.g., "react")

**Example Request**:
```bash
curl -X POST "http://localhost:8000/fetch/facebook/react"
```

**Example Response**:
```json
{
  "success": true,
  "message": "Repository 'facebook/react' fetched and stored successfully",
  "data": {
    "id": 1,
    "owner": "facebook",
    "repo": "react",
    "stars": 200000,
    "issues": 500,
    "language": "JavaScript",
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

### 2. List Repositories

Retrieve all stored repositories with optional filters.

**Endpoint**: `GET /repos`

**Query Parameters**:
- `owner` (optional): Filter by owner
- `language` (optional): Filter by programming language
- `limit` (optional): Maximum number of results (1-1000)

**Example Request**:
```bash
curl "http://localhost:8000/repos?owner=facebook&limit=10"
```

**Example Response**:
```json
{
  "repos": [
    {
      "id": 1,
      "owner": "facebook",
      "repo": "react",
      "stars": 200000,
      "issues": 500,
      "language": "JavaScript",
      "timestamp": "2024-01-15T10:30:00"
    }
  ],
  "total": 1
}
```

### 3. Aggregate Metrics

Get aggregated statistics across all stored repositories.

**Endpoint**: `GET /aggregate`

**Query Parameters**:
- `owner` (optional): Filter by owner before aggregation
- `language` (optional): Filter by language before aggregation

**Example Request**:
```bash
curl "http://localhost:8000/aggregate"
```

**Example Response**:
```json
{
  "total_stars": 460000,
  "total_issues": 1000,
  "repo_count": 3,
  "by_language": {
    "JavaScript": 2,
    "TypeScript": 1
  }
}
```

### 4. Get Owner Repositories

Fetch all repositories for a GitHub owner/user directly from GitHub API.

**Endpoint**: `GET /owner/{owner}/repos`

**Query Parameters**:
- `owner` (path): GitHub username or organization name
- `limit` (optional): Limit number of repositories (1-1000)
- `store` (optional): Store repositories in database (default: true)

**Example Request**:
```bash
curl "http://localhost:8000/owner/facebook/repos?limit=10"
```

### 5. Get Detailed GitHub Repository Information

Get comprehensive repository details including opened/closed issues and PRs.

**Endpoint**: `GET /github/{owner}/{repo}/details`

**Query Parameters**:
- `owner` (path): GitHub repository owner
- `repo` (path): Repository name
- `store` (optional): Store the data in database (default: false)

**Example Request**:
```bash
curl "http://localhost:8000/github/facebook/react/details"
```

**Example Response**:
```json
{
  "owner": "facebook",
  "repo": "react",
  "stars": 200000,
  "language": "JavaScript",
  "issues_open": 450,
  "issues_closed": 8500,
  "prs_open": 25,
  "prs_closed": 1200,
  "total_issues": 8950,
  "total_prs": 1225
}
```

## Testing

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_fetch.py
```

### Test Categories

The test suite includes:

1. **Fetch Tests** (`tests/test_fetch.py`):
   - Successful repository fetch
   - Repository not found handling
   - Invalid input validation
   - Updating existing repositories

2. **Pagination Tests** (`tests/test_pagination.py`):
   - Multiple page handling
   - Pull request filtering

3. **Aggregation Tests** (`tests/test_aggregate.py`):
   - Basic aggregation
   - Filtered aggregation (owner, language)
   - Empty database handling

4. **Repository List Tests** (`tests/test_repos.py`):
   - Basic listing
   - Filtering by owner and language
   - Limit parameter

5. **Error Handling Tests** (`tests/test_error_handling.py`):
   - Rate limit handling
   - Timeout handling

## Project Structure

```
github-service-2/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas for validation
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── fetch.py         # Fetch endpoint
│   │   ├── repos.py         # List repositories endpoint
│   │   └── aggregate.py     # Aggregation endpoint
│   └── services/
│       ├── __init__.py
│       └── github_client.py # GitHub API client
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration
│   ├── test_fetch.py
│   ├── test_pagination.py
│   ├── test_aggregate.py
│   ├── test_repos.py
│   └── test_error_handling.py
├── requirements.txt
└── README.md
```

## Database

The service uses SQLite by default. The database file (`github_metrics.db`) is created automatically in the project root when you first run the application.

### Database Schema

**repositories** table:
- `id`: Primary key
- `owner`: Repository owner (indexed)
- `repo`: Repository name (indexed)
- `stars`: Number of stars
- `issues`: Number of open issues
- `language`: Primary programming language
- `timestamp`: Last update timestamp

## Error Handling

The service handles various error scenarios:

- **400 Bad Request**: Invalid input parameters
- **404 Not Found**: Repository not found on GitHub
- **403 Forbidden**: GitHub API rate limit exceeded
- **503 Service Unavailable**: Network errors or GitHub API unavailable
- **504 Gateway Timeout**: Request timeout

All errors return structured JSON responses with descriptive messages.

## Rate Limiting

GitHub API has rate limits:
- **Unauthenticated**: 60 requests per hour
- **Authenticated**: 5,000 requests per hour

To increase rate limits, you can add a GitHub personal access token to the `GitHubClient` headers:

```python
headers={
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token YOUR_GITHUB_TOKEN"
}
```

## Development

### Code Style

The project follows PEP 8 style guidelines. Consider using:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

### Adding New Features

1. Add new models in `app/models.py`
2. Add Pydantic schemas in `app/schemas.py`
3. Create service classes in `app/services/`
4. Add routes in `app/routers/`
5. Write tests in `tests/`

## License

This project is for educational purposes.

## Author

Built as a learning project to demonstrate modern backend development practices with FastAPI, async programming, and comprehensive testing.


