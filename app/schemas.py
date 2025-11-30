from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, List


class RepositoryBase(BaseModel):
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    stars: int = Field(..., ge=0, description="Number of stars")
    issues: int = Field(..., ge=0, description="Number of open issues")
    language: Optional[str] = Field(None, description="Primary programming language")
    issues_open: Optional[int] = Field(None, ge=0, description="Number of open issues")
    issues_closed: Optional[int] = Field(None, ge=0, description="Number of closed issues")
    prs_open: Optional[int] = Field(None, ge=0, description="Number of open pull requests")
    prs_closed: Optional[int] = Field(None, ge=0, description="Number of closed pull requests")


class RepositoryCreate(RepositoryBase):
    pass


class RepositoryResponse(RepositoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    timestamp: datetime


class FetchResponse(BaseModel):
    success: bool
    message: str
    data: Optional[RepositoryResponse] = None


class RepoListResponse(BaseModel):
    repos: List[RepositoryResponse]
    total: int


class AggregationResponse(BaseModel):
    total_stars: int
    total_issues: int
    repo_count: int
    by_language: Dict[str, int]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class GitHubRepoInfo(BaseModel):
    """Repository information from GitHub API (not from database)"""
    name: str
    full_name: str
    owner: str
    description: Optional[str] = None
    stars: int = Field(..., ge=0)
    forks: int = Field(..., ge=0)
    open_issues: int = Field(..., ge=0)
    language: Optional[str] = None
    is_private: bool = False
    is_fork: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pushed_at: Optional[str] = None
    url: Optional[str] = None
    api_url: Optional[str] = None


class OwnerReposResponse(BaseModel):
    """Response for owner repositories endpoint"""
    owner: str
    total: int
    repos: List[GitHubRepoInfo]
    stored: Optional[int] = Field(None, description="Number of repositories stored in database")
    updated: Optional[int] = Field(None, description="Number of repositories updated in database")

