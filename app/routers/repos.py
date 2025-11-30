from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Repository
from app.schemas import RepoListResponse, RepositoryResponse

router = APIRouter()


@router.get("", response_model=RepoListResponse)
async def list_repositories(
    owner: Optional[str] = Query(None, description="Filter by owner"),
    language: Optional[str] = Query(None, description="Filter by programming language"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    db: Session = Depends(get_db)
):
    """
    List all stored repositories with optional filters
    
    - **owner**: Filter repositories by owner
    - **language**: Filter repositories by programming language
    - **limit**: Maximum number of results to return (1-1000)
    """
    query = db.query(Repository)
    
    # Apply filters
    if owner:
        query = query.filter(Repository.owner == owner.lower().strip())
    
    if language:
        query = query.filter(Repository.language == language.strip())
    
    # Apply limit
    if limit:
        query = query.limit(limit)
    
    repos = query.all()
    
    return RepoListResponse(
        repos=[RepositoryResponse.model_validate(repo) for repo in repos],
        total=len(repos)
    )

