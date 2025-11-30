import pytest
from unittest.mock import patch
from app.services.github_client import GitHubClient
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_github_client_handles_rate_limit():
    """Test that GitHub client properly handles rate limit errors"""
    client = GitHubClient()
    
    with patch.object(client.client, "get") as mock_get:
        mock_response = type("Response", (), {
            "status_code": 403,
            "headers": {"X-RateLimit-Remaining": "0"},
            "raise_for_status": lambda: None
        })()
        mock_get.return_value = mock_response
        
        with pytest.raises(HTTPException) as exc_info:
            await client.get_repository("test", "repo")
        
        assert exc_info.value.status_code == 403
        assert "rate limit" in exc_info.value.detail.lower()
    
    await client.close()


@pytest.mark.asyncio
async def test_github_client_handles_timeout():
    """Test that GitHub client handles timeout errors"""
    client = GitHubClient()
    
    import httpx
    with patch.object(client.client, "get", side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(HTTPException) as exc_info:
            await client.get_repository("test", "repo")
        
        assert exc_info.value.status_code == 504
        assert "timeout" in exc_info.value.detail.lower()
    
    await client.close()


