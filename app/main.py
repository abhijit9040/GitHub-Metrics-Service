from fastapi import FastAPI
from dotenv import load_dotenv
import logging
from app.database import engine, Base
from app.routers import fetch, repos, aggregate, owner, github_details

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GitHub Metrics Service",
    description="A service to fetch, store, and aggregate GitHub repository metrics",
    version="1.0.0"
)

# Include routers
app.include_router(fetch.router, prefix="/fetch", tags=["fetch"])
app.include_router(repos.router, prefix="/repos", tags=["repos"])
app.include_router(aggregate.router, prefix="/aggregate", tags=["aggregate"])
app.include_router(owner.router, prefix="/owner", tags=["owner"])
app.include_router(github_details.router, prefix="/github", tags=["github-details"])


@app.get("/")
async def root():
    return {
        "message": "GitHub Metrics Service",
        "version": "1.0.0",
        "endpoints": {
            "fetch": "/fetch/{owner}/{repo}",
            "repos": "/repos",
            "aggregate": "/aggregate",
            "owner_repos": "/owner/{owner}/repos",
            "github_details": "/github/{owner}/{repo}/details"
        }
    }

