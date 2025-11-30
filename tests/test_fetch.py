import pytest
from unittest.mock import AsyncMock, patch
from app.routers.fetch import fetch_repository
from app.models import Repository
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_fetch_repository_success(client, db_session):
    """Test successful repository fetch and storage"""
    with patch("app.routers.fetch.github_client.fetch_repository_metrics") as mock_fetch:
        mock_fetch.return_value = {
            "owner": "facebook",
            "repo": "react",
            "stars": 200000,
            "issues": 500,
            "language": "JavaScript"
        }
        
        response = client.post("/fetch/facebook/react")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["owner"] == "facebook"
        assert data["data"]["repo"] == "react"
        assert data["data"]["stars"] == 200000
        assert data["data"]["issues"] == 500
        assert data["data"]["language"] == "JavaScript"
        
        # Verify stored in database
        repo = db_session.query(Repository).filter(
            Repository.owner == "facebook",
            Repository.repo == "react"
        ).first()
        assert repo is not None
        assert repo.stars == 200000


@pytest.mark.asyncio
async def test_fetch_repository_not_found(client):
    """Test handling of repository not found error"""
    with patch("app.routers.fetch.github_client.fetch_repository_metrics") as mock_fetch:
        from fastapi import HTTPException
        mock_fetch.side_effect = HTTPException(
            status_code=404,
            detail="Repository 'invalid/notfound' not found on GitHub"
        )
        
        response = client.post("/fetch/invalid/notfound")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_fetch_repository_invalid_input(client):
    """Test validation of invalid input parameters"""
    # Empty owner
    response = client.post("/fetch/ /test")
    assert response.status_code == 400
    
    # Empty repo
    response = client.post("/fetch/test/ ")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_fetch_repository_update_existing(client, db_session):
    """Test updating existing repository with new data"""
    # Create existing repo
    existing_repo = Repository(
        owner="facebook",
        repo="react",
        stars=100000,
        issues=300,
        language="JavaScript"
    )
    db_session.add(existing_repo)
    db_session.commit()
    
    with patch("app.routers.fetch.github_client.fetch_repository_metrics") as mock_fetch:
        mock_fetch.return_value = {
            "owner": "facebook",
            "repo": "react",
            "stars": 200000,
            "issues": 500,
            "language": "TypeScript"
        }
        
        response = client.post("/fetch/facebook/react")
        
        assert response.status_code == 200
        data = response.json()
        assert "updated" in data["message"].lower()
        assert data["data"]["stars"] == 200000
        assert data["data"]["language"] == "TypeScript"
        
        # Verify only one record exists
        repos = db_session.query(Repository).filter(
            Repository.owner == "facebook",
            Repository.repo == "react"
        ).all()
        assert len(repos) == 1


