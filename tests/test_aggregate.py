import pytest
from app.models import Repository


def test_aggregate_metrics_basic(client, db_session):
    """Test basic aggregation across multiple repositories"""
    # Add test repositories
    repos = [
        Repository(owner="facebook", repo="react", stars=200000, issues=500, language="JavaScript"),
        Repository(owner="facebook", repo="react-native", stars=110000, issues=300, language="JavaScript"),
        Repository(owner="microsoft", repo="vscode", stars=150000, issues=200, language="TypeScript"),
    ]
    
    for repo in repos:
        db_session.add(repo)
    db_session.commit()
    
    response = client.get("/aggregate")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_stars"] == 460000  # 200000 + 110000 + 150000
    assert data["total_issues"] == 1000  # 500 + 300 + 200
    assert data["repo_count"] == 3
    assert data["by_language"]["JavaScript"] == 2
    assert data["by_language"]["TypeScript"] == 1


def test_aggregate_with_owner_filter(client, db_session):
    """Test aggregation with owner filter"""
    repos = [
        Repository(owner="facebook", repo="react", stars=200000, issues=500, language="JavaScript"),
        Repository(owner="facebook", repo="react-native", stars=110000, issues=300, language="JavaScript"),
        Repository(owner="microsoft", repo="vscode", stars=150000, issues=200, language="TypeScript"),
    ]
    
    for repo in repos:
        db_session.add(repo)
    db_session.commit()
    
    response = client.get("/aggregate?owner=facebook")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_stars"] == 310000  # Only Facebook repos
    assert data["total_issues"] == 800
    assert data["repo_count"] == 2


def test_aggregate_with_language_filter(client, db_session):
    """Test aggregation with language filter"""
    repos = [
        Repository(owner="facebook", repo="react", stars=200000, issues=500, language="JavaScript"),
        Repository(owner="facebook", repo="react-native", stars=110000, issues=300, language="JavaScript"),
        Repository(owner="microsoft", repo="vscode", stars=150000, issues=200, language="TypeScript"),
    ]
    
    for repo in repos:
        db_session.add(repo)
    db_session.commit()
    
    response = client.get("/aggregate?language=JavaScript")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_stars"] == 310000  # Only JavaScript repos
    assert data["total_issues"] == 800
    assert data["repo_count"] == 2
    assert "TypeScript" not in data["by_language"]


def test_aggregate_empty_database(client):
    """Test aggregation with empty database"""
    response = client.get("/aggregate")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_stars"] == 0
    assert data["total_issues"] == 0
    assert data["repo_count"] == 0
    assert data["by_language"] == {}


