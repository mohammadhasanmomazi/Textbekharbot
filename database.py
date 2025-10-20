import sqlite3
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from config import DATABASE_PATH, UserRole, ContentCategory, ContentType

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations with proper connection handling"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table with role-based system
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    phone TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    province TEXT,
                    city TEXT,
                    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'super_admin')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Content categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Contents table with proper foreign key relationships
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    type TEXT NOT NULL CHECK (type IN ('text', 'music', 'audio', 'document')),
                    content TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    file_id TEXT,
                    file_size INTEGER,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (category_id) REFERENCES content_categories (id),
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            
            # User sessions for temporary data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Insert default content categories
            self._insert_default_categories(cursor)
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def _insert_default_categories(self, cursor):
        """Insert default content categories"""
        categories = [
            ('top_tracks', 'پر بازدید ترین ترک ها 🔥', 'Most popular tracks'),
            ('economic_package', 'پکیج اقتصادی 💰', 'Economic package'),
            ('vip_package', 'پکیج مگاهیت VIP 👑', 'VIP package')
        ]
        
        for category in categories:
            cursor.execute('''
                INSERT OR IGNORE INTO content_categories (name, display_name, description)
                VALUES (?, ?, ?)
            ''', category)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    # User operations
    def create_user(self, user_id: int, phone: str, first_name: str, 
                   last_name: str, province: str, city: str, role: str = UserRole.USER) -> bool:
        """Create a new user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, phone, first_name, last_name, province, city, role, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, phone, first_name, last_name, province, city, role))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by user_id"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ? AND is_active = 1', (user_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def update_user_role(self, user_id: int, role: str) -> bool:
        """Update user role"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ? AND is_active = 1
                ''', (role, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            return False
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin or super_admin"""
        user = self.get_user(user_id)
        return user and user['role'] in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    
    # Content operations
    def add_content(self, category_name: str, content_type: str, content: str, 
                   title: str = None, description: str = None, file_id: str = None,
                   file_size: int = None, created_by: int = None) -> bool:
        """Add new content"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get category ID
                cursor.execute('SELECT id FROM content_categories WHERE name = ?', (category_name,))
                category_row = cursor.fetchone()
                if not category_row:
                    logger.error(f"Category {category_name} not found")
                    return False
                
                category_id = category_row['id']
                
                cursor.execute('''
                    INSERT INTO contents 
                    (category_id, type, content, title, description, file_id, file_size, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (category_id, content_type, content, title, description, file_id, file_size, created_by))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding content: {e}")
            return False
    
    def get_content_by_category(self, category_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all content for a specific category"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.*, cc.display_name as category_display_name
                    FROM contents c
                    JOIN content_categories cc ON c.category_id = cc.id
                    WHERE cc.name = ? AND c.is_active = 1
                    ORDER BY c.created_at DESC
                ''', (category_name,))
                
                contents = [dict(row) for row in cursor.fetchall()]
                
                # Group by type
                result = {'text': [], 'music': [], 'audio': [], 'document': []}
                for content in contents:
                    content_type = content['type']
                    if content_type in result:
                        result[content_type].append(content)
                
                return result
        except Exception as e:
            logger.error(f"Error getting content by category: {e}")
            return {'text': [], 'music': [], 'audio': [], 'document': []}
    
    def get_category_display_name(self, category_name: str) -> Optional[str]:
        """Get display name for category"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT display_name FROM content_categories WHERE name = ?', (category_name,))
                row = cursor.fetchone()
                return row['display_name'] if row else None
        except Exception as e:
            logger.error(f"Error getting category display name: {e}")
            return None
    
    # Session operations
    def save_session(self, user_id: int, session_data: Dict[str, Any], expires_in_hours: int = 24) -> bool:
        """Save user session data"""
        try:
            import json
            from datetime import datetime, timedelta
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear existing sessions for user
                cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
                
                # Insert new session
                expires_at = datetime.now() + timedelta(hours=expires_in_hours)
                cursor.execute('''
                    INSERT INTO user_sessions (user_id, session_data, expires_at)
                    VALUES (?, ?, ?)
                ''', (user_id, json.dumps(session_data), expires_at))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False
    
    def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        try:
            import json
            from datetime import datetime
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT session_data FROM user_sessions 
                    WHERE user_id = ? AND expires_at > ?
                ''', (user_id, datetime.now()))
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row['session_data'])
                return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    def clear_session(self, user_id: int) -> bool:
        """Clear user session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return False
    
    def ban_user(self, user_id: int) -> bool:
        """Ban a user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ? AND role != 'super_admin'
                ''', (user_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            return False
    
    def unban_user(self, user_id: int) -> bool:
        """Unban a user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET is_active = 1, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            return False
    
    def get_users_paginated(self, page: int = 1, per_page: int = 10, search: str = None) -> Dict[str, Any]:
        """Get paginated users with optional search"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build search condition
                search_condition = ""
                search_params = []
                if search:
                    search_condition = "AND (first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR province LIKE ?)"
                    search_term = f"%{search}%"
                    search_params = [search_term, search_term, search_term, search_term]
                
                # Get total count
                cursor.execute(f'''
                    SELECT COUNT(*) as total FROM users 
                    WHERE is_active = 1 {search_condition}
                ''', search_params)
                total = cursor.fetchone()['total']
                
                # Get paginated results
                offset = (page - 1) * per_page
                cursor.execute(f'''
                    SELECT * FROM users 
                    WHERE is_active = 1 {search_condition}
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                ''', search_params + [per_page, offset])
                
                users = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'users': users,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page
                }
        except Exception as e:
            logger.error(f"Error getting paginated users: {e}")
            return {'users': [], 'total': 0, 'page': 1, 'per_page': 10, 'total_pages': 0}