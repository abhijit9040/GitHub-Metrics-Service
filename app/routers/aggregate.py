from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from collections import defaultdict
from app.database import get_db
from app.models import Repository
from app.schemas import AggregationResponse

router = APIRouter()


@router.get("", response_model=AggregationResponse)
async def aggregate_metrics(
    owner: Optional[str] = Query(None, description="Filter by owner"),
    language: Optional[str] = Query(None, description="Filter by programming language"),
    db: Session = Depends(get_db)
):
    """
    Aggregate metrics across all stored repositories
    
    Returns:
    - Total stars
    - Total open issues
    - Repository count
    - Breakdown by programming language
    
    - **owner**: Filter repositories by owner before aggregation
    - **language**: Filter repositories by programming language before aggregation
    """
    query = db.query(Repository)
    
    # Apply filters
    if owner:
        query = query.filter(Repository.owner == owner.lower().strip())
    
    if language:
        query = query.filter(Repository.language == language.strip())
    
    repos = query.all()
    
    # Calculate aggregations
    total_stars = sum(repo.stars for repo in repos)
    total_issues = sum(repo.issues for repo in repos)
    repo_count = len(repos)
    
    # Group by language
    by_language = defaultdict(int)
    for repo in repos:
        lang = repo.language or "Unknown"
        by_language[lang] += 1
    
    return AggregationResponse(
        total_stars=total_stars,
        total_issues=total_issues,
        repo_count=repo_count,
        by_language=dict(by_language)
    )

