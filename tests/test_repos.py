import pytest
from app.models import Repository


def test_list_repositories_basic(client, db_session):
    """Test listing all repositories"""
    repos = [
        Repository(owner="facebook", repo="react", stars=200000, issues=500, language="JavaScript"),
        Repository(owner="microsoft", repo="vscode", stars=150000, issues=200, language="TypeScript"),
    ]
    
    for repo in repos:
        db_session.add(repo)
    db_session.commit()
    
    response = client.get("/repos")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["repos"]) == 2


def test_list_repositories_with_owner_filter(client, db_session):
    """Test listing repositories filtered by owner"""
    repos = [
        Repository(owner="facebook", repo="react", stars=200000, issues=500, language="JavaScript"),
        Repository(owner="facebook", repo="react-native", stars=110000, issues=300, language="JavaScript"),
        Repository(owner="microsoft", repo="vscode", stars=150000, issues=200, language="TypeScript"),
    ]
    
    for repo in repos:
        db_session.add(repo)
    db_session.commit()
    
    response = client.get("/repos?owner=facebook")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(repo["owner"] == "facebook" for repo in data["repos"])


def test_list_repositories_with_language_filter(client, db_session):
    """Test listing repositories filtered by language"""
    repos = [
        Repository(owner="facebook", repo="react", stars=200000, issues=500, language="JavaScript"),
        Repository(owner="microsoft", repo="vscode", stars=150000, issues=200, language="TypeScript"),
    ]
    
    for repo in repos:
        db_session.add(repo)
    db_session.commit()
    
    response = client.get("/repos?language=JavaScript")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["repos"][0]["language"] == "JavaScript"


def test_list_repositories_with_limit(client, db_session):
    """Test listing repositories with limit parameter"""
    repos = [
        Repository(owner="facebook", repo=f"repo{i}", stars=1000, issues=10, language="JavaScript")
        for i in range(5)
    ]
    
    for repo in repos:
        db_session.add(repo)
    db_session.commit()
    
    response = client.get("/repos?limit=3")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["repos"]) == 3


