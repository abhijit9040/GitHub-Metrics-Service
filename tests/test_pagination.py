import pytest
from unittest.mock import AsyncMock, patch
from app.services.github_client import GitHubClient
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_pagination_handles_multiple_pages():
    """Test that pagination correctly handles multiple pages of issues"""
    client = GitHubClient()
    
    # Mock responses for multiple pages
    mock_responses = [
        # Page 1: 100 issues (all are actual issues, no PRs)
        [{"id": i, "title": f"Issue {i}"} for i in range(100)],
        # Page 2: 50 issues (last page)
        [{"id": i + 100, "title": f"Issue {i + 100}"} for i in range(50)]
    ]
    
    with patch.object(client.client, "get") as mock_get:
        # Setup mock responses
        mock_get.side_effect = [
            type("Response", (), {
                "status_code": 200,
                "json": lambda: mock_responses[0],
                "headers": {},
                "raise_for_status": lambda: None
            })(),
            type("Response", (), {
                "status_code": 200,
                "json": lambda: mock_responses[1],
                "headers": {},
                "raise_for_status": lambda: None
            })()
        ]
        
        count = await client.get_open_issues_count("test", "repo")
        assert count == 150  # 100 + 50
    
    await client.close()


@pytest.mark.asyncio
async def test_pagination_filters_pull_requests():
    """Test that pagination correctly filters out pull requests"""
    client = GitHubClient()
    
    # Mock response with mix of issues and PRs
    mock_response = [
        {"id": 1, "title": "Issue 1"},  # Real issue
        {"id": 2, "title": "PR 1", "pull_request": {}},  # PR
        {"id": 3, "title": "Issue 2"},  # Real issue
        {"id": 4, "title": "PR 2", "pull_request": {}},  # PR
    ]
    
    with patch.object(client.client, "get") as mock_get:
        mock_get.return_value = type("Response", (), {
            "status_code": 200,
            "json": lambda: mock_response,
            "headers": {},
            "raise_for_status": lambda: None
        })()
        
        count = await client.get_open_issues_count("test", "repo")
        assert count == 2  # Only 2 real issues, PRs filtered out
    
    await client.close()


