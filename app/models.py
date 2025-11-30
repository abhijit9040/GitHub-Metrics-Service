from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, index=True, nullable=False)
    repo = Column(String, index=True, nullable=False)
    stars = Column(Integer, default=0)
    issues = Column(Integer, default=0)  # Open issues (for backward compatibility)
    language = Column(String, nullable=True)
    # Detailed issue and PR counts
    issues_open = Column(Integer, default=0)
    issues_closed = Column(Integer, default=0)
    prs_open = Column(Integer, default=0)
    prs_closed = Column(Integer, default=0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


