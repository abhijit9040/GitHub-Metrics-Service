from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Repository
from app.schemas import OwnerReposResponse, GitHubRepoInfo
from app.services.github_client import GitHubClient
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
github_client = GitHubClient()


@router.get("/{owner}/repos", response_model=OwnerReposResponse)
async def get_owner_repositories(
    owner: str,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of repositories to return"),
    store: bool = Query(True, description="Store repositories in database"),
    db: Session = Depends(get_db)
):
    """
    Fetch all repositories for a GitHub owner/user directly from GitHub API and optionally store in database
    
    This endpoint fetches repositories directly from GitHub API. If store=true (default),
    it will also save all repositories to the local database.
    
    - **owner**: GitHub username or organization name (e.g., "facebook", "microsoft")
    - **limit**: Optional limit on number of repositories to return (1-1000)
    - **store**: Whether to store repositories in database (default: true)
    
    Returns a list of all repositories owned by the specified user/organization.
    """
    # Validate input
    if not owner or not owner.strip():
        raise HTTPException(status_code=400, detail="Owner cannot be empty")
    
    owner_clean = owner.strip()
    owner_lower = owner_clean.lower()
    
    try:
        # Fetch repositories from GitHub
        repos_data = await github_client.get_owner_repositories(owner_clean, limit=limit)
        
        # Store repositories in database if requested
        stored_count = 0
        updated_count = 0
        
        if store:
            logger.info(f"Storing {len(repos_data)} repositories for owner {owner_clean} in database")
            
            for repo_info in repos_data:
                repo_name = repo_info.get("name", "")
                repo_lower = repo_name.lower()
                
                # Check if repository already exists
                existing_repo = db.query(Repository).filter(
                    Repository.owner == owner_lower,
                    Repository.repo == repo_lower
                ).first()
                
                if existing_repo:
                    # Update existing record
                    existing_repo.stars = repo_info.get("stars", 0)
                    existing_repo.issues = repo_info.get("open_issues", 0)
                    existing_repo.language = repo_info.get("language")
                    updated_count += 1
                else:
                    # Create new record
                    db_repo = Repository(
                        owner=owner_lower,
                        repo=repo_lower,
                        stars=repo_info.get("stars", 0),
                        issues=repo_info.get("open_issues", 0),
                        language=repo_info.get("language")
                    )
                    db.add(db_repo)
                    stored_count += 1
            
            # Commit all changes
            try:
                db.commit()
                logger.info(f"Successfully stored {stored_count} new and updated {updated_count} existing repositories")
            except Exception as e:
                db.rollback()
                logger.error(f"Error committing repositories to database: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error storing repositories in database: {str(e)}"
                )
        
        # Convert to response models
        repos = [GitHubRepoInfo(**repo) for repo in repos_data]
        
        response = OwnerReposResponse(
            owner=owner_clean,
            total=len(repos),
            repos=repos,
            stored=stored_count if store else None,
            updated=updated_count if store else None
        )
        
        # Log storage info
        if store:
            logger.info(f"Fetched and stored {len(repos)} repositories for {owner_clean} (new: {stored_count}, updated: {updated_count})")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (already properly formatted)
        raise
    except Exception as e:
        logger.error(f"Error fetching repositories for owner {owner_clean}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


