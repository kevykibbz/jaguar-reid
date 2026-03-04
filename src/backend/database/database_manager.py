"""
Database module for storing jaguar information with metadata.
Supports SQLite by default, can be extended for PostgreSQL.
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


class JaguarDatabase:
    """Database manager for jaguar identification system."""
    
    def __init__(self, db_path: str = "./database/jaguars.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Connect to SQLite database."""
        try:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Main jaguars table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jaguars (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                embedding BLOB NOT NULL,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                times_seen INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Images table (multiple images per jaguar)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jaguar_id TEXT NOT NULL,
                image_url TEXT,
                local_path TEXT,
                storage_type TEXT DEFAULT 'local',
                file_name TEXT,
                file_size INTEGER,
                image_width INTEGER,
                image_height INTEGER,
                format TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (jaguar_id) REFERENCES jaguars(id) ON DELETE CASCADE
            )
        """)
        
        # Metadata table for additional information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                latitude REAL,
                longitude REAL,
                location_name TEXT,
                camera_trap_id TEXT,
                photographer TEXT,
                notes TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
            )
        """)
        
        # Sightings/matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sightings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jaguar_id TEXT NOT NULL,
                similarity_score REAL NOT NULL,
                matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (jaguar_id) REFERENCES jaguars(id) ON DELETE CASCADE
            )
        """)
        
        # Comments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jaguar_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jaguar_id TEXT NOT NULL,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (jaguar_id) REFERENCES jaguars(id) ON DELETE CASCADE
            )
        """)
        
        # Likes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jaguar_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jaguar_id TEXT NOT NULL,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (jaguar_id) REFERENCES jaguars(id) ON DELETE CASCADE
            )
        """)
        
        # Comments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jaguar_id TEXT NOT NULL,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (jaguar_id) REFERENCES jaguars(id) ON DELETE CASCADE
            )
        """)
        
        # Likes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jaguar_id TEXT NOT NULL,
                user_id TEXT NOT NULL DEFAULT 'anonymous',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (jaguar_id) REFERENCES jaguars(id) ON DELETE CASCADE,
                UNIQUE(jaguar_id, user_id)
            )
        """)
        
        self.conn.commit()
        logger.info("Database tables created/verified")
    
    def register_jaguar(
        self,
        jaguar_id: str,
        name: str,
        embedding: List[float],
        image_url: Optional[str] = None,
        local_path: Optional[str] = None,
        image_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register a new jaguar in the database.
        
        Args:
            jaguar_id: Unique jaguar identifier
            name: Jaguar name
            embedding: Feature embedding vector
            image_url: Azure Blob Storage URL
            local_path: Local file path (fallback)
            image_metadata: Dictionary with image metadata
        
        Returns:
            True if successful
        """
        try:
            cursor = self.conn.cursor()
            
            # Insert jaguar
            embedding_blob = json.dumps(embedding).encode('utf-8')
            cursor.execute("""
                INSERT INTO jaguars (id, name, embedding, first_seen, last_seen, times_seen)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (jaguar_id, name, embedding_blob, datetime.now(), datetime.now()))
            
            # Insert image
            metadata = image_metadata or {}
            storage_type = 'azure' if image_url else 'local'
            
            cursor.execute("""
                INSERT INTO images (
                    jaguar_id, image_url, local_path, storage_type,
                    file_name, file_size, image_width, image_height, format
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                jaguar_id,
                image_url,
                local_path,
                storage_type,
                metadata.get('file_name'),
                metadata.get('file_size'),
                metadata.get('width'),
                metadata.get('height'),
                metadata.get('format')
            ))
            
            image_id = cursor.lastrowid
            
            # Insert additional metadata if provided
            if metadata.get('latitude') or metadata.get('location_name'):
                cursor.execute("""
                    INSERT INTO image_metadata (
                        image_id, latitude, longitude, location_name,
                        camera_trap_id, photographer, notes, tags
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    image_id,
                    metadata.get('latitude'),
                    metadata.get('longitude'),
                    metadata.get('location_name'),
                    metadata.get('camera_trap_id'),
                    metadata.get('photographer'),
                    metadata.get('notes'),
                    metadata.get('tags')
                ))
            
            self.conn.commit()
            logger.info(f"Registered jaguar: {name} ({jaguar_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register jaguar: {e}")
            self.conn.rollback()
            return False
    
    def find_matching_jaguar(self, embedding: List[float], threshold: float = 0.80) -> tuple:
        """
        Find the closest matching jaguar by comparing embeddings.
        
        Args:
            embedding: Feature embedding to match
            threshold: Similarity threshold
        
        Returns:
            (match_found, jaguar_data, similarity)
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, name, embedding FROM jaguars")
            
            from torch.nn.functional import cosine_similarity
            import torch
            
            best_match = None
            best_similarity = 0.0
            query_embedding = torch.tensor(embedding)
            
            for row in cursor.fetchall():
                stored_embedding = json.loads(row['embedding'].decode('utf-8'))
                stored_tensor = torch.tensor(stored_embedding)
                
                similarity = cosine_similarity(
                    query_embedding.unsqueeze(0),
                    stored_tensor.unsqueeze(0)
                ).item()
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = dict(row)
            
            if best_similarity >= threshold and best_match:
                # Update sighting
                cursor.execute("""
                    INSERT INTO sightings (jaguar_id, similarity_score)
                    VALUES (?, ?)
                """, (best_match['id'], best_similarity))
                
                # Update last seen
                cursor.execute("""
                    UPDATE jaguars 
                    SET last_seen = ?, times_seen = times_seen + 1
                    WHERE id = ?
                """, (datetime.now(), best_match['id']))
                
                self.conn.commit()
                return True, best_match, best_similarity
            
            return False, None, best_similarity
            
        except Exception as e:
            logger.error(f"Error finding match: {e}")
            return False, None, 0.0
    
    def get_jaguar(self, jaguar_id: str) -> Optional[Dict]:
        """Get jaguar details by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, first_seen, last_seen, times_seen
            FROM jaguars WHERE id = ?
        """, (jaguar_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_jaguar_detail(self, jaguar_id: str) -> Optional[Dict]:
        """Get detailed information about a specific jaguar including images."""
        cursor = self.conn.cursor()
        
        # Get jaguar info
        cursor.execute("""
            SELECT id, name, first_seen, last_seen, times_seen, created_at
            FROM jaguars WHERE id = ?
        """, (jaguar_id,))
        jaguar = cursor.fetchone()
        
        if not jaguar:
            return None
        
        # Get all images
        cursor.execute("""
            SELECT 
                i.id, i.image_url, i.local_path, i.storage_type,
                i.file_name, i.file_size, i.image_width, i.image_height,
                i.format, i.created_at
            FROM images i
            WHERE i.jaguar_id = ?
            ORDER BY i.created_at DESC
        """, (jaguar_id,))
        images = [dict(row) for row in cursor.fetchall()]
        
        return {
            'id': jaguar['id'],
            'name': jaguar['name'],
            'first_seen': jaguar['first_seen'],
            'last_seen': jaguar['last_seen'],
            'times_seen': jaguar['times_seen'],
            'created_at': jaguar['created_at'],
            'images': [{'url': img['image_url'], 'path': img['local_path'], 'storage': img['storage_type']} for img in images]
        }
    
    def list_jaguars(self) -> List[Dict]:
        """List all registered jaguars with their images."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                j.id, j.name, j.first_seen, j.last_seen, j.times_seen,
                i.image_url, i.local_path, i.storage_type, i.file_name
            FROM jaguars j
            LEFT JOIN images i ON j.id = i.jaguar_id
            ORDER BY j.created_at DESC
        """)
        
        jaguars = {}
        for row in cursor.fetchall():
            jag_id = row['id']
            if jag_id not in jaguars:
                jaguars[jag_id] = {
                    'id': row['id'],
                    'name': row['name'],
                    'first_seen': row['first_seen'],
                    'last_seen': row['last_seen'],
                    'times_seen': row['times_seen'],
                    'image_url': None,  # Will be set to first image URL
                    'file_name': None,  # Will be set to first file name
                    'images': []
                }
            
            if row['image_url'] or row['local_path']:
                # Add to images array
                jaguars[jag_id]['images'].append({
                    'url': row['image_url'],
                    'path': row['local_path'],
                    'storage': row['storage_type']
                })
                
                # Set top-level fields from first image (for backward compatibility)
                if jaguars[jag_id]['image_url'] is None and row['image_url']:
                    jaguars[jag_id]['image_url'] = row['image_url']
                if jaguars[jag_id]['file_name'] is None and row['file_name']:
                    jaguars[jag_id]['file_name'] = row['file_name']
        
        return list(jaguars.values())
    
    def get_comments(self, jaguar_id: str) -> List[Dict]:
        """Get all comments for a jaguar."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, author, content, created_at
            FROM jaguar_comments
            WHERE jaguar_id = ?
            ORDER BY created_at DESC
        """, (jaguar_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def add_comment(self, jaguar_id: str, author: str, content: str) -> Dict:
        """Add a comment to a jaguar."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO jaguar_comments (jaguar_id, author, content)
            VALUES (?, ?, ?)
        """, (jaguar_id, author, content))
        self.conn.commit()
        
        comment_id = cursor.lastrowid
        cursor.execute("""
            SELECT id, author, content, created_at
            FROM jaguar_comments WHERE id = ?
        """, (comment_id,))
        
        return dict(cursor.fetchone())
    
    def get_like_count(self, jaguar_id: str) -> int:
        """Get total likes for a jaguar."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM jaguar_likes WHERE jaguar_id = ?
        """, (jaguar_id,))
        
        return cursor.fetchone()['count']
    
    def toggle_like(self, jaguar_id: str, user_id: str = 'anonymous') -> Dict:
        """Toggle like for a jaguar. Returns current state."""
        cursor = self.conn.cursor()
        
        # Check if already liked
        cursor.execute("""
            SELECT id FROM jaguar_likes WHERE jaguar_id = ? AND user_id = ?
        """, (jaguar_id, user_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # Unlike
            cursor.execute("""
                DELETE FROM jaguar_likes WHERE jaguar_id = ? AND user_id = ?
            """, (jaguar_id, user_id))
            liked = False
        else:
            # Like
            cursor.execute("""
                INSERT INTO jaguar_likes (jaguar_id, user_id)
                VALUES (?, ?)
            """, (jaguar_id, user_id))
            liked = True
        
        self.conn.commit()
        
        # Get updated count
        count = self.get_like_count(jaguar_id)
        
        return {'liked': liked, 'count': count}
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM jaguars")
        jaguar_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM images")
        image_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM sightings")
        sighting_count = cursor.fetchone()['count']
        
        return {
            'total_jaguars': jaguar_count,
            'total_images': image_count,
            'total_sightings': sighting_count
        }
    
    def get_recent_activity(self, limit: int = 20) -> List[Dict]:
        """Get recent activity feed (registrations and sightings)."""
        cursor = self.conn.cursor()
        
        # Get recent jaguar registrations
        cursor.execute("""
            SELECT 
                'registration' as type,
                j.id as jaguar_id,
                j.name as jaguar_name,
                j.created_at as timestamp,
                NULL as similarity
            FROM jaguars j
            ORDER BY j.created_at DESC
            LIMIT ?
        """, (limit,))
        
        activity = [dict(row) for row in cursor.fetchall()]
        return sorted(activity, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Global instance
_db_instance = None


def get_database():
    """Get or create global database instance using SQLAlchemy ORM."""
    global _db_instance
    if _db_instance is None:
        db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()
        
        if db_type == 'postgresql':
            try:
                from .database_sqlalchemy import JaguarDatabaseORM
                _db_instance = JaguarDatabaseORM()
                logger.info("✓ Using PostgreSQL with SQLAlchemy ORM")
            except Exception as e:
                logger.error(f"PostgreSQL/SQLAlchemy failed: {e}. Falling back to SQLite")
                _db_instance = JaguarDatabase()
        else:
            logger.info("✓ Using SQLite database")
            _db_instance = JaguarDatabase()
    
    return _db_instance
