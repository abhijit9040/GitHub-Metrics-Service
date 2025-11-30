import httpx
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class GitHubClient:
    """Async client for GitHub API with pagination support"""

    BASE_URL = "https://api.github.com"
    TIMEOUT = 30.0

    def __init__(self):
        import os
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Metrics-Service"
        }
        
        # Add GitHub token if available (increases rate limits)
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self.TIMEOUT,
            headers=headers
        )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetch repository metadata from GitHub API
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary containing repository data
            
        Raises:
            HTTPException: If repository not found or API error
        """
        try:
            response = await self.client.get(f"/repos/{owner}/{repo}")
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Repository '{owner}/{repo}' not found on GitHub"
                )
            
            if response.status_code == 403:
                # Rate limit or forbidden
                rate_limit_info = response.headers.get("X-RateLimit-Remaining", "unknown")
                raise HTTPException(
                    status_code=403,
                    detail=f"GitHub API rate limit exceeded or access forbidden. Remaining: {rate_limit_info}"
                )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            logger.error(f"Timeout while fetching {owner}/{repo}")
            raise HTTPException(
                status_code=504,
                detail="Request to GitHub API timed out"
            )
        except httpx.RequestError as e:
            logger.error(f"Network error while fetching {owner}/{repo}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to GitHub API: {str(e)}"
            )

    async def get_open_issues_count(self, owner: str, repo: str) -> int:
        """
        Count open issues by paginating through all pages
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Total count of open issues (excluding pull requests)
        """
        total_issues = 0
        page = 1
        per_page = 100  # GitHub API max per page
        max_pages = 100  # Safety limit to prevent infinite loops
        
        try:
            while page <= max_pages:
                response = await self.client.get(
                    f"/repos/{owner}/{repo}/issues",
                    params={
                        "state": "open",
                        "page": page,
                        "per_page": per_page
                    }
                )
                
                if response.status_code == 404:
                    # Repo not found, return 0 issues
                    logger.warning(f"Repository {owner}/{repo} not found when fetching issues")
                    return 0
                
                if response.status_code == 403:
                    rate_limit_info = response.headers.get("X-RateLimit-Remaining", "unknown")
                    logger.error(f"Rate limit exceeded for {owner}/{repo}. Remaining: {rate_limit_info}")
                    raise HTTPException(
                        status_code=403,
                        detail=f"GitHub API rate limit exceeded. Remaining: {rate_limit_info}"
                    )
                
                response.raise_for_status()
                issues = response.json()
                
                # If no issues returned, we've reached the end
                if not issues:
                    logger.debug(f"Reached end of issues for {owner}/{repo} at page {page}")
                    break
                
                # Filter out pull requests (GitHub API returns PRs in issues endpoint)
                # PRs have a "pull_request" key in the response
                open_issues_only = [issue for issue in issues if "pull_request" not in issue]
                total_issues += len(open_issues_only)
                
                logger.debug(f"Page {page}: Found {len(open_issues_only)} issues (filtered from {len(issues)} total items)")
                
                # If we got fewer than per_page items, we're on the last page
                if len(issues) < per_page:
                    logger.debug(f"Last page reached for {owner}/{repo} at page {page}")
                    break
                
                page += 1
            
            logger.info(f"Total open issues for {owner}/{repo}: {total_issues}")
            return total_issues
                
        except httpx.TimeoutException:
            logger.error(f"Timeout while fetching issues for {owner}/{repo}")
            raise HTTPException(
                status_code=504,
                detail="Request to GitHub API timed out while fetching issues"
            )
        except httpx.RequestError as e:
            logger.error(f"Network error while fetching issues for {owner}/{repo}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to GitHub API: {str(e)}"
            )
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching issues for {owner}/{repo}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error counting issues: {str(e)}"
            )

    async def fetch_repository_metrics(self, owner: str, repo: str, include_detailed: bool = True) -> Dict[str, Any]:
        """
        Fetch complete repository metrics including stars, issues, and language
        
        Args:
            owner: Repository owner
            repo: Repository name
            include_detailed: Whether to fetch detailed issue/PR counts (opened/closed)
            
        Returns:
            Dictionary with metrics: stars, issues, language, and optionally detailed counts
        """
        logger.info(f"Fetching metrics for {owner}/{repo}")
        
        # Fetch repository metadata
        repo_data = await self.get_repository(owner, repo)
        
        # Extract basic info
        stars = repo_data.get("stargazers_count", 0)
        language = repo_data.get("language")
        
        logger.info(f"Repository {owner}/{repo}: {stars} stars, language: {language}")
        
        # Fetch open issues count (with pagination)
        try:
            issues_count = await self.get_open_issues_count(owner, repo)
        except Exception as e:
            logger.error(f"Error fetching issues count for {owner}/{repo}: {str(e)}")
            # Fallback to repository's open_issues_count if pagination fails
            issues_count = repo_data.get("open_issues_count", 0)
            logger.warning(f"Using repository's open_issues_count as fallback: {issues_count}")
        
        result = {
            "owner": owner,
            "repo": repo,
            "stars": stars,
            "issues": issues_count,
            "language": language
        }
        
        # Fetch detailed issue and PR counts if requested
        if include_detailed:
            try:
                detailed_counts = await self.get_issues_and_prs_counts(owner, repo)
                result.update(detailed_counts)
            except Exception as e:
                logger.warning(f"Error fetching detailed counts for {owner}/{repo}: {str(e)}")
                # Set defaults if detailed fetch fails
                result.update({
                    "issues_open": issues_count,
                    "issues_closed": 0,
                    "prs_open": 0,
                    "prs_closed": 0
                })
        
        logger.info(f"Successfully fetched metrics for {owner}/{repo}: {result}")
        return result

    async def get_owner_repositories(self, owner: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch all repositories for a GitHub owner/user
        
        Args:
            owner: GitHub username or organization name
            limit: Optional limit on number of repositories to return
            
        Returns:
            List of repository dictionaries with basic info
        """
        all_repos = []
        page = 1
        per_page = 100  # GitHub API max per page
        max_pages = 100  # Safety limit
        
        logger.info(f"Fetching repositories for owner: {owner}")
        
        try:
            while page <= max_pages:
                response = await self.client.get(
                    f"/users/{owner}/repos",
                    params={
                        "page": page,
                        "per_page": per_page,
                        "sort": "updated",
                        "direction": "desc"
                    }
                )
                
                if response.status_code == 404:
                    logger.warning(f"Owner '{owner}' not found on GitHub")
                    raise HTTPException(
                        status_code=404,
                        detail=f"Owner '{owner}' not found on GitHub"
                    )
                
                if response.status_code == 403:
                    rate_limit_info = response.headers.get("X-RateLimit-Remaining", "unknown")
                    logger.error(f"Rate limit exceeded for owner {owner}. Remaining: {rate_limit_info}")
                    raise HTTPException(
                        status_code=403,
                        detail=f"GitHub API rate limit exceeded. Remaining: {rate_limit_info}"
                    )
                
                response.raise_for_status()
                repos = response.json()
                
                # If no repos returned, we've reached the end
                if not repos:
                    logger.debug(f"Reached end of repositories for {owner} at page {page}")
                    break
                
                # Extract relevant information from each repo
                for repo in repos:
                    repo_info = {
                        "name": repo.get("name"),
                        "full_name": repo.get("full_name"),
                        "owner": repo.get("owner", {}).get("login"),
                        "description": repo.get("description"),
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "open_issues": repo.get("open_issues_count", 0),
                        "language": repo.get("language"),
                        "is_private": repo.get("private", False),
                        "is_fork": repo.get("fork", False),
                        "created_at": repo.get("created_at"),
                        "updated_at": repo.get("updated_at"),
                        "pushed_at": repo.get("pushed_at"),
                        "url": repo.get("html_url"),
                        "api_url": repo.get("url")
                    }
                    all_repos.append(repo_info)
                    
                    # Check if we've reached the limit
                    if limit and len(all_repos) >= limit:
                        logger.info(f"Reached limit of {limit} repositories for {owner}")
                        return all_repos[:limit]
                
                # If we got fewer than per_page items, we're on the last page
                if len(repos) < per_page:
                    logger.debug(f"Last page reached for {owner} at page {page}")
                    break
                
                page += 1
            
            logger.info(f"Fetched {len(all_repos)} repositories for {owner}")
            return all_repos
                
        except httpx.TimeoutException:
            logger.error(f"Timeout while fetching repositories for {owner}")
            raise HTTPException(
                status_code=504,
                detail="Request to GitHub API timed out while fetching repositories"
            )
        except httpx.RequestError as e:
            logger.error(f"Network error while fetching repositories for {owner}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to GitHub API: {str(e)}"
            )
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching repositories for {owner}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching repositories: {str(e)}"
            )

    async def get_issues_and_prs_counts(self, owner: str, repo: str) -> Dict[str, int]:
        """
        Get detailed counts of issues and PRs (opened and closed)
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with counts: issues_open, issues_closed, prs_open, prs_closed
        """
        counts = {
            "issues_open": 0,
            "issues_closed": 0,
            "prs_open": 0,
            "prs_closed": 0
        }
        
        logger.info(f"Fetching detailed issues and PRs counts for {owner}/{repo}")
        
        # Fetch open issues (excluding PRs)
        try:
            counts["issues_open"] = await self._count_items(f"/repos/{owner}/{repo}/issues", "open", is_pr=False)
        except Exception as e:
            logger.warning(f"Error counting open issues for {owner}/{repo}: {str(e)}")
        
        # Fetch closed issues (excluding PRs)
        try:
            counts["issues_closed"] = await self._count_items(f"/repos/{owner}/{repo}/issues", "closed", is_pr=False)
        except Exception as e:
            logger.warning(f"Error counting closed issues for {owner}/{repo}: {str(e)}")
        
        # Fetch open PRs
        try:
            counts["prs_open"] = await self._count_items(f"/repos/{owner}/{repo}/pulls", "open", is_pr=True)
        except Exception as e:
            logger.warning(f"Error counting open PRs for {owner}/{repo}: {str(e)}")
        
        # Fetch closed PRs
        try:
            counts["prs_closed"] = await self._count_items(f"/repos/{owner}/{repo}/pulls", "closed", is_pr=True)
        except Exception as e:
            logger.warning(f"Error counting closed PRs for {owner}/{repo}: {str(e)}")
        
        logger.info(f"Counts for {owner}/{repo}: {counts}")
        return counts

    async def _count_items(self, endpoint: str, state: str, is_pr: bool = False) -> int:
        """
        Helper method to count items (issues or PRs) with pagination
        
        Args:
            endpoint: API endpoint path
            state: "open" or "closed"
            is_pr: True if counting PRs, False if counting issues
            
        Returns:
            Total count of items
        """
        total_count = 0
        page = 1
        per_page = 100
        max_pages = 100
        
        try:
            while page <= max_pages:
                response = await self.client.get(
                    endpoint,
                    params={
                        "state": state,
                        "page": page,
                        "per_page": per_page
                    }
                )
                
                if response.status_code == 404:
                    return 0
                
                if response.status_code == 403:
                    rate_limit_info = response.headers.get("X-RateLimit-Remaining", "unknown")
                    raise HTTPException(
                        status_code=403,
                        detail=f"GitHub API rate limit exceeded. Remaining: {rate_limit_info}"
                    )
                
                response.raise_for_status()
                items = response.json()
                
                if not items:
                    break
                
                # For issues endpoint, filter out PRs if needed
                if not is_pr:
                    items = [item for item in items if "pull_request" not in item]
                
                total_count += len(items)
                
                if len(items) < per_page:
                    break
                
                page += 1
            
            return total_count
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error counting items from {endpoint}: {str(e)}")
            raise

