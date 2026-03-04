"""
SQLAlchemy ORM models for Jaguar Re-identification system.
Production-ready database layer with connection pooling and proper transaction handling.
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey, LargeBinary, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.pool import QueuePool
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class Jaguar(Base):
    """Main jaguar entity with embeddings."""
    __tablename__ = 'jaguars'
    
    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    embedding = Column(LargeBinary, nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    times_seen = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = relationship("Image", back_populates="jaguar", cascade="all, delete-orphan")
    sightings = relationship("Sighting", back_populates="jaguar", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="jaguar", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="jaguar", cascade="all, delete-orphan")


class Image(Base):
    """Images associated with jaguars."""
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    jaguar_id = Column(String(255), ForeignKey('jaguars.id', ondelete='CASCADE'), nullable=False)
    image_url = Column(Text)
    local_path = Column(Text)
    storage_type = Column(String(50), default='local')
    file_name = Column(String(255))
    file_size = Column(Integer)
    image_width = Column(Integer)
    image_height = Column(Integer)
    format = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jaguar = relationship("Jaguar", back_populates="images")
    image_metadata = relationship("ImageMetadata", back_populates="image", uselist=False, cascade="all, delete-orphan")


class ImageMetadata(Base):
    """Additional metadata for images (GPS, camera trap info, etc.)."""
    __tablename__ = 'image_metadata'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey('images.id', ondelete='CASCADE'), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    location_name = Column(Text)
    camera_trap_id = Column(String(255))
    photographer = Column(Text)
    notes = Column(Text)
    tags = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    image = relationship("Image", back_populates="image_metadata")


class Sighting(Base):
    """Jaguar sightings/matches."""
    __tablename__ = 'sightings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    jaguar_id = Column(String(255), ForeignKey('jaguars.id', ondelete='CASCADE'), nullable=False)
    similarity_score = Column(Float, nullable=False)
    matched_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jaguar = relationship("Jaguar", back_populates="sightings")


class Comment(Base):
    """Comments on jaguar images."""
    __tablename__ = 'jaguar_comments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    jaguar_id = Column(String(255), ForeignKey('jaguars.id', ondelete='CASCADE'), nullable=False)
    author = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jaguar = relationship("Jaguar", back_populates="comments")


class Like(Base):
    """Likes on jaguar images."""
    __tablename__ = 'jaguar_likes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    jaguar_id = Column(String(255), ForeignKey('jaguars.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jaguar = relationship("Jaguar", back_populates="likes")


# Database engine and session factory
def get_engine():
    """Create database engine with connection pooling."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set in environment")
    
    # Conservative pool settings for Azure PostgreSQL Free/Basic tier
    # Azure Free tier has very limited connections (typically 5-10)
    return create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=2,           # Keep only 2 connections in pool (reduced from 10)
        max_overflow=3,        # Allow max 3 additional connections (reduced from 20)
        pool_pre_ping=True,    # Verify connections before using
        pool_recycle=300,      # Recycle connections after 5 minutes (reduced from 1 hour)
        pool_timeout=30,       # Wait 30 seconds for available connection
        connect_args={
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'  # 30 second query timeout
        },
        echo=False  # Disable SQL logging
    )


# Lazy initialization - create engine and session on first use
_engine = None
_session_local = None


def get_or_create_engine():
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        _engine = get_engine()
    return _engine


def get_session_factory():
    """Get or create the session factory (lazy initialization)."""
    global _session_local
    if _session_local is None:
        engine = get_or_create_engine()
        _session_local = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    return _session_local


def init_db():
    """Initialize database tables."""
    engine = get_or_create_engine()
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Get a database session. Use with context manager."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
