from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Repository
from app.services.github_client import GitHubClient
from app.schemas import RepositoryResponse
from pydantic import BaseModel
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
github_client = GitHubClient()


class GitHubDetailsResponse(BaseModel):
    """Detailed GitHub repository information"""
    owner: str
    repo: str
    stars: int
    language: Optional[str] = None
    issues_open: int
    issues_closed: int
    prs_open: int
    prs_closed: int
    total_issues: int
    total_prs: int


@router.get("/{owner}/{repo}/details", response_model=GitHubDetailsResponse)
async def get_github_repository_details(
    owner: str,
    repo: str,
    store: bool = Query(False, description="Store the fetched data in database"),
    db: Session = Depends(get_db)
):
    """
    Get detailed GitHub repository information including opened/closed issues and PRs
    
    This endpoint fetches comprehensive information directly from GitHub API:
    - Open and closed issues count
    - Open and closed pull requests count
    - Stars, language, and other metrics
    
    - **owner**: GitHub repository owner (e.g., "facebook")
    - **repo**: Repository name (e.g., "react")
    - **store**: Whether to store the data in database (default: false)
    
    Returns detailed counts of issues and PRs in both open and closed states.
    """
    # Validate input
    if not owner or not owner.strip():
        raise HTTPException(status_code=400, detail="Owner cannot be empty")
    
    if not repo or not repo.strip():
        raise HTTPException(status_code=400, detail="Repo cannot be empty")
    
    owner_clean = owner.strip()
    repo_clean = repo.strip()
    
    try:
        # Fetch detailed metrics from GitHub
        metrics = await github_client.fetch_repository_metrics(owner_clean, repo_clean, include_detailed=True)
        
        # Extract detailed counts
        issues_open = metrics.get("issues_open", 0)
        issues_closed = metrics.get("issues_closed", 0)
        prs_open = metrics.get("prs_open", 0)
        prs_closed = metrics.get("prs_closed", 0)
        
        response = GitHubDetailsResponse(
            owner=owner_clean,
            repo=repo_clean,
            stars=metrics["stars"],
            language=metrics.get("language"),
            issues_open=issues_open,
            issues_closed=issues_closed,
            prs_open=prs_open,
            prs_closed=prs_closed,
            total_issues=issues_open + issues_closed,
            total_prs=prs_open + prs_closed
        )
        
        # Store in database if requested
        if store:
            owner_lower = owner_clean.lower()
            repo_lower = repo_clean.lower()
            
            try:
                existing_repo = db.query(Repository).filter(
                    Repository.owner == owner_lower,
                    Repository.repo == repo_lower
                ).first()
                
                if existing_repo:
                    existing_repo.stars = metrics["stars"]
                    existing_repo.issues = metrics["issues"]
                    existing_repo.language = metrics["language"]
                    existing_repo.issues_open = issues_open
                    existing_repo.issues_closed = issues_closed
                    existing_repo.prs_open = prs_open
                    existing_repo.prs_closed = prs_closed
                else:
                    db_repo = Repository(
                        owner=owner_lower,
                        repo=repo_lower,
                        stars=metrics["stars"],
                        issues=metrics["issues"],
                        language=metrics["language"],
                        issues_open=issues_open,
                        issues_closed=issues_closed,
                        prs_open=prs_open,
                        prs_closed=prs_closed
                    )
                    db.add(db_repo)
                
                db.commit()
                logger.info(f"Stored detailed metrics for {owner_clean}/{repo_clean} in database")
            except Exception as e:
                db.rollback()
                logger.error(f"Error storing repository in database: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error storing in database: {str(e)}"
                )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching GitHub details for {owner_clean}/{repo_clean}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

