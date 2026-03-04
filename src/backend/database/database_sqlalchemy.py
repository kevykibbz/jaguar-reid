"""
SQLAlchemy-based database manager for Jaguar Re-identification.
Clean ORM implementation with proper session management.
"""
import torch
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import json

from .database_models import (
    get_session_factory, init_db, Jaguar, Image, ImageMetadata, Sighting, Comment, Like
)

logger = logging.getLogger(__name__)


class JaguarDatabaseORM:
    """SQLAlchemy ORM-based database manager."""
    
    def __init__(self):
        """Initialize database manager."""
        self._initialized = False
        logger.info("SQLAlchemy ORM manager created (lazy initialization)")
    
    def _ensure_initialized(self):
        """Ensure database is initialized (lazy)."""
        if not self._initialized:
            init_db()
            self._initialized = True
            logger.info("Database tables initialized")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        self._ensure_initialized()
        SessionLocal = get_session_factory()
        return SessionLocal()
    
    def register_jaguar(
        self, 
        jaguar_id: str, 
        name: str, 
        embedding: List[float],
        image_url: Optional[str] = None,
        local_path: Optional[str] = None,
        storage_type: str = 'local',
        file_info: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Register a new jaguar with embedding and first image."""
        session = self.get_session()
        try:
            # Convert list to tensor if needed, then to bytes
            if isinstance(embedding, list):
                embedding = torch.tensor(embedding, dtype=torch.float32)
            embedding_bytes = embedding.cpu().numpy().tobytes()
            
            # Create jaguar
            jaguar = Jaguar(
                id=jaguar_id,
                name=name,
                embedding=embedding_bytes,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                times_seen=1
            )
            session.add(jaguar)
            
            # Create image
            image = Image(
                jaguar_id=jaguar_id,
                image_url=image_url,
                local_path=local_path,
                storage_type=storage_type,
                file_name=file_info.get('file_name') if file_info else None,
                file_size=file_info.get('file_size') if file_info else None,
                image_width=file_info.get('width') if file_info else None,
                image_height=file_info.get('height') if file_info else None,
                format=file_info.get('format') if file_info else None
            )
            session.add(image)
            session.flush()  # Get image.id
            
            # Create metadata if provided
            if metadata:
                img_metadata = ImageMetadata(
                    image_id=image.id,
                    latitude=metadata.get('gps', {}).get('latitude'),
                    longitude=metadata.get('gps', {}).get('longitude'),
                    location_name=metadata.get('location_name'),
                    camera_trap_id=metadata.get('camera_trap_id'),
                    photographer=metadata.get('photographer'),
                    notes=metadata.get('notes'),
                    tags=json.dumps(metadata.get('tags', []))
                )
                session.add(img_metadata)
            
            session.commit()
            logger.info(f"Registered new jaguar: {name} ({jaguar_id})")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to register jaguar: {e}")
            return False
        finally:
            session.close()
    
    def find_matching_jaguar(
        self, 
        query_embedding: List[float], 
        threshold: float = 0.75
    ) -> tuple:
        """Find the most similar jaguar in the database.
        
        Returns:
            tuple: (match_found: bool, jaguar_data: Optional[Dict], similarity: float)
        """
        session = self.get_session()
        try:
            jaguars = session.query(Jaguar).all()
            
            best_match = None
            best_similarity = 0.0
            
            # Convert list to tensor if needed
            if isinstance(query_embedding, list):
                query_embedding = torch.tensor(query_embedding, dtype=torch.float32)
            
            query_embedding = query_embedding.cpu()
            
            for jaguar in jaguars:
                # Convert bytes back to tensor
                stored_embedding = torch.frombuffer(jaguar.embedding, dtype=torch.float32)
                
                # Compute cosine similarity
                similarity = torch.nn.functional.cosine_similarity(
                    query_embedding.unsqueeze(0),
                    stored_embedding.unsqueeze(0)
                ).item()
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = jaguar
            
            if best_similarity >= threshold and best_match:
                # Record sighting
                sighting = Sighting(
                    jaguar_id=best_match.id,
                    similarity_score=best_similarity
                )
                session.add(sighting)
                
                # Update jaguar
                best_match.last_seen = datetime.utcnow()
                best_match.times_seen += 1
                
                session.commit()
                
                jaguar_data = {
                    'id': best_match.id,
                    'name': best_match.name,
                    'first_seen': best_match.first_seen,
                    'last_seen': best_match.last_seen,
                    'times_seen': best_match.times_seen
                }
                
                return (True, jaguar_data, best_similarity)
            
            # No match found
            return (False, None, best_similarity)
            
        except Exception as e:
            logger.error(f"Error finding match: {e}")
            # Return tuple even on error
            return (False, None, 0.0)
        finally:
            session.close()
    
    def list_jaguars(self) -> List[Dict]:
        """List all jaguars with their first image."""
        session = self.get_session()
        try:
            # Optimized query with LEFT JOIN LATERAL equivalent
            jaguars = session.query(Jaguar).all()
            
            result = []
            for jaguar in jaguars:
                # Get first image
                first_image = session.query(Image).filter(
                    Image.jaguar_id == jaguar.id
                ).order_by(desc(Image.created_at)).first()
                
                # Get all images
                all_images = session.query(Image).filter(
                    Image.jaguar_id == jaguar.id
                ).order_by(desc(Image.created_at)).all()
                
                result.append({
                    'id': jaguar.id,
                    'name': jaguar.name,
                    'first_seen': jaguar.first_seen.isoformat() + 'Z' if jaguar.first_seen else None,
                    'last_seen': jaguar.last_seen.isoformat() + 'Z' if jaguar.last_seen else None,
                    'times_seen': jaguar.times_seen,
                    'image_url': first_image.image_url if first_image else None,
                    'file_name': first_image.file_name if first_image else None,
                    'images': [{
                        'url': img.image_url,
                        'path': img.local_path,
                        'storage': img.storage_type
                    } for img in all_images]
                })
            
            return result
            
        finally:
            session.close()
    
    def get_jaguar_detail(self, jaguar_id: str) -> Optional[Dict]:
        """Get detailed information about a specific jaguar including images."""
        session = self.get_session()
        try:
            jaguar = session.query(Jaguar).filter(Jaguar.id == jaguar_id).first()
            
            if not jaguar:
                return None
            
            # Get all images
            images = session.query(Image).filter(
                Image.jaguar_id == jaguar_id
            ).order_by(desc(Image.created_at)).all()
            
            return {
                'id': jaguar.id,
                'name': jaguar.name,
                'first_seen': jaguar.first_seen.isoformat() + 'Z' if jaguar.first_seen else None,
                'last_seen': jaguar.last_seen.isoformat() + 'Z' if jaguar.last_seen else None,
                'times_seen': jaguar.times_seen,
                'created_at': jaguar.created_at.isoformat() + 'Z' if jaguar.created_at else None,
                'images': [{
                    'url': img.image_url,
                    'path': img.local_path,
                    'storage': img.storage_type
                } for img in images]
            }
        finally:
            session.close()
    
    def get_comments(self, jaguar_id: str) -> List[Dict]:
        """Get all comments for a jaguar."""
        session = self.get_session()
        try:
            comments = session.query(Comment).filter(
                Comment.jaguar_id == jaguar_id
            ).order_by(desc(Comment.created_at)).all()
            
            return [{
                'id': comment.id,
                'author': comment.author,
                'content': comment.content,
                'created_at': comment.created_at.isoformat() + 'Z'  # Add Z to indicate UTC
            } for comment in comments]
        finally:
            session.close()
    
    def add_comment(self, jaguar_id: str, author: str, content: str) -> Dict:
        """Add a comment to a jaguar."""
        session = self.get_session()
        try:
            comment = Comment(
                jaguar_id=jaguar_id,
                author=author,
                content=content
            )
            session.add(comment)
            session.commit()
            session.refresh(comment)
            
            return {
                'id': comment.id,
                'author': comment.author,
                'content': comment.content,
                'created_at': comment.created_at.isoformat() + 'Z'  # Add Z to indicate UTC
            }
        finally:
            session.close()
    
    def get_like_count(self, jaguar_id: str) -> int:
        """Get total likes for a jaguar."""
        session = self.get_session()
        try:
            count = session.query(func.count(Like.id)).filter(
                Like.jaguar_id == jaguar_id
            ).scalar()
            return count or 0
        finally:
            session.close()
    
    def toggle_like(self, jaguar_id: str, user_id: str = 'anonymous') -> Dict:
        """Toggle like for a jaguar. Returns current state."""
        session = self.get_session()
        try:
            # Check if already liked
            existing = session.query(Like).filter(
                Like.jaguar_id == jaguar_id,
                Like.user_id == user_id
            ).first()
            
            if existing:
                # Unlike
                session.delete(existing)
                liked = False
            else:
                # Like
                like = Like(jaguar_id=jaguar_id, user_id=user_id)
                session.add(like)
                liked = True
            
            session.commit()
            
            # Get updated count
            count = session.query(func.count(Like.id)).filter(
                Like.jaguar_id == jaguar_id
            ).scalar()
            
            return {'liked': liked, 'count': count or 0}
        finally:
            session.close()
    
    def get_statistics(self) -> Dict:
        """Get database statistics in a single optimized query."""
        session = self.get_session()
        try:
            logger.info("Fetching statistics...")
            stats = session.query(
                func.count(func.distinct(Jaguar.id)).label('total_jaguars'),
                func.count(func.distinct(Image.id)).label('total_images'),
                func.sum(Jaguar.times_seen).label('total_sightings')
            ).outerjoin(Image).first()
            
            logger.info(f"Statistics fetched: jaguars={stats.total_jaguars}, images={stats.total_images}")
            
            return {
                'total_jaguars': stats.total_jaguars or 0,
                'total_images': stats.total_images or 0,
                'total_sightings': int(stats.total_sightings or 0)
            }
        except Exception as e:
            logger.error(f"Error fetching statistics: {e}")
            raise
        finally:
            session.close()
    
    def get_recent_activity(self, limit: int = 20) -> List[Dict]:
        """Get recent jaguar registrations and matches."""
        session = self.get_session()
        try:
            # Get recent sightings
            sightings = session.query(Sighting, Jaguar).join(
                Jaguar, Sighting.jaguar_id == Jaguar.id
            ).order_by(desc(Sighting.matched_at)).limit(limit).all()
            
            activity = []
            for sighting, jaguar in sightings:
                activity.append({
                    'type': 'match',
                    'jaguar_name': jaguar.name,
                    'similarity': round(sighting.similarity_score, 2),
                    'timestamp': sighting.matched_at.isoformat()
                })
            
            return activity
            
        finally:
            session.close()
    
    def close(self):
        """Close database connections."""
        SessionLocal.remove()
        logger.info("Database connections closed")
