from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Repository
from app.schemas import FetchResponse, RepositoryResponse, ErrorResponse
from app.services.github_client import GitHubClient
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
github_client = GitHubClient()


@router.post("/{owner}/{repo}", response_model=FetchResponse)
async def fetch_repository(
    owner: str,
    repo: str,
    db: Session = Depends(get_db)
):
    """
    Fetch repository metrics from GitHub and store in database
    
    - **owner**: GitHub repository owner (e.g., "facebook")
    - **repo**: Repository name (e.g., "react")
    
    Returns repository metrics including stars, open issues, and language.
    """
    # Validate input
    if not owner or not owner.strip():
        raise HTTPException(status_code=400, detail="Owner cannot be empty")
    
    if not repo or not repo.strip():
        raise HTTPException(status_code=400, detail="Repo cannot be empty")
    
    # Clean inputs (strip whitespace, but preserve case for GitHub API)
    owner_clean = owner.strip()
    repo_clean = repo.strip()
    
    # Use lowercase for database storage/comparison (case-insensitive lookup)
    owner_lower = owner_clean.lower()
    repo_lower = repo_clean.lower()
    
    try:
        # Fetch metrics from GitHub (use original case - GitHub is case-sensitive)
        # Include detailed issue/PR counts
        metrics = await github_client.fetch_repository_metrics(owner_clean, repo_clean, include_detailed=True)
        
        # Check if repository already exists in database (case-insensitive lookup)
        existing_repo = db.query(Repository).filter(
            Repository.owner == owner_lower,
            Repository.repo == repo_lower
        ).first()
        
        if existing_repo:
            # Update existing record
            existing_repo.stars = metrics["stars"]
            existing_repo.issues = metrics["issues"]
            existing_repo.language = metrics["language"]
            # Update detailed counts if available
            if "issues_open" in metrics:
                existing_repo.issues_open = metrics.get("issues_open", 0)
                existing_repo.issues_closed = metrics.get("issues_closed", 0)
                existing_repo.prs_open = metrics.get("prs_open", 0)
                existing_repo.prs_closed = metrics.get("prs_closed", 0)
            db.commit()
            db.refresh(existing_repo)
            
            return FetchResponse(
                success=True,
                message=f"Repository '{owner_clean}/{repo_clean}' updated successfully",
                data=RepositoryResponse.model_validate(existing_repo)
            )
        else:
            # Create new record (store lowercase for case-insensitive queries)
            db_repo = Repository(
                owner=owner_lower,
                repo=repo_lower,
                stars=metrics["stars"],
                issues=metrics["issues"],
                language=metrics["language"],
                issues_open=metrics.get("issues_open", metrics["issues"]),
                issues_closed=metrics.get("issues_closed", 0),
                prs_open=metrics.get("prs_open", 0),
                prs_closed=metrics.get("prs_closed", 0)
            )
            db.add(db_repo)
            db.commit()
            db.refresh(db_repo)
            
            return FetchResponse(
                success=True,
                message=f"Repository '{owner_clean}/{repo_clean}' fetched and stored successfully",
                data=RepositoryResponse.model_validate(db_repo)
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions (already properly formatted)
        raise
    except Exception as e:
        logger.error(f"Error fetching repository {owner_clean}/{repo_clean}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

