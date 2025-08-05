"""
Session Management - Handles conversation persistence and memory
Provides both persistent (SQLite file) and temporary (in-memory) session strategies
"""

from typing import Dict, Optional, List, Any
from agents import SQLiteSession
import asyncio
import os
from pathlib import Path


class SessionManager:
    """
    Manages conversation sessions with different persistence strategies
    
    Supports:
    - Persistent sessions: SQLite file storage, survives app restart
    - Temporary sessions: In-memory storage, cleared when app closes
    - Automatic session lifecycle management
    """
    
    def __init__(self, db_directory: str = "sessions"):
        """
        Initialize session manager
        
        Args:
            db_directory: Directory to store persistent session files
        """
        self.db_directory = Path(db_directory)
        self.db_directory.mkdir(exist_ok=True)
        
        # Active session cache
        self._sessions: Dict[str, SQLiteSession] = {}
        
        print(f"📁 Session Manager initialized with directory: {self.db_directory}")
    
    def get_session(
        self, 
        user_id: str, 
        session_type: str = "persistent",
        conversation_id: Optional[str] = None
    ) -> SQLiteSession:
        """
        Get or create a session
        
        Args:
            user_id: Unique user identifier
            session_type: "persistent" (file) or "temporary" (memory)
            conversation_id: Optional conversation identifier for multiple conversations per user
            
        Returns:
            SQLiteSession: Configured session instance
        """
        # Create unique session key
        session_key = f"{user_id}_{session_type}"
        if conversation_id:
            session_key += f"_{conversation_id}"
        
        # Return existing session if available
        if session_key in self._sessions:
            return self._sessions[session_key]
        
        # Create new session
        if session_type == "persistent":
            db_file = self.db_directory / f"session_{session_key}.db"
            session = SQLiteSession(session_key, str(db_file))
            print(f"📁 Created persistent session: {db_file}")
        else:
            session = SQLiteSession(session_key)  # In-memory
            print(f"💾 Created temporary session: {session_key}")
        
        # Cache the session
        self._sessions[session_key] = session
        return session
    
    async def clear_session(
        self, 
        user_id: str, 
        session_type: str = "persistent",
        conversation_id: Optional[str] = None
    ) -> bool:
        """
        Clear a specific session
        
        Args:
            user_id: User identifier
            session_type: Session type to clear
            conversation_id: Optional conversation identifier
            
        Returns:
            bool: True if session was cleared, False if not found
        """
        session_key = f"{user_id}_{session_type}"
        if conversation_id:
            session_key += f"_{conversation_id}"
        
        if session_key in self._sessions:
            session = self._sessions[session_key]
            await session.clear_session()
            del self._sessions[session_key]
            print(f"🗑️ Cleared session: {session_key}")
            return True
        
        return False
    
    async def clear_all_user_sessions(self, user_id: str) -> int:
        """
        Clear all sessions for a specific user
        
        Args:
            user_id: User identifier
            
        Returns:
            int: Number of sessions cleared
        """
        cleared_count = 0
        sessions_to_clear = []
        
        # Find all sessions for this user
        for session_key in self._sessions.keys():
            if session_key.startswith(f"{user_id}_"):
                sessions_to_clear.append(session_key)
        
        # Clear each session
        for session_key in sessions_to_clear:
            session = self._sessions[session_key]
            await session.clear_session()
            del self._sessions[session_key]
            cleared_count += 1
        
        print(f"🗑️ Cleared {cleared_count} sessions for user {user_id}")
        return cleared_count
    
    async def get_session_summary(
        self, 
        user_id: str, 
        session_type: str = "persistent",
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get summary information about a session
        
        Args:
            user_id: User identifier
            session_type: Session type
            conversation_id: Optional conversation identifier
            
        Returns:
            Dict containing session summary
        """
        session = self.get_session(user_id, session_type, conversation_id)
        
        # Get all items in session
        items = await session.get_items()
        
        # Count different message types
        user_messages = len([item for item in items if item.get("role") == "user"])
        assistant_messages = len([item for item in items if item.get("role") == "assistant"])
        
        return {
            "session_key": f"{user_id}_{session_type}" + (f"_{conversation_id}" if conversation_id else ""),
            "total_items": len(items),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "session_type": session_type,
            "has_conversation_data": len(items) > 0
        }
    
    def list_active_sessions(self) -> List[str]:
        """
        List all active session keys
        
        Returns:
            List of active session keys
        """
        return list(self._sessions.keys())
    
    async def export_session(
        self, 
        user_id: str, 
        session_type: str = "persistent",
        conversation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Export all messages from a session
        
        Args:
            user_id: User identifier
            session_type: Session type
            conversation_id: Optional conversation identifier
            
        Returns:
            List of all messages in the session
        """
        session = self.get_session(user_id, session_type, conversation_id)
        return await session.get_items()
    
    def get_session_file_path(self, user_id: str, conversation_id: Optional[str] = None) -> Path:
        """
        Get the file path for a persistent session
        
        Args:
            user_id: User identifier
            conversation_id: Optional conversation identifier
            
        Returns:
            Path to the session database file
        """
        session_key = f"{user_id}_persistent"
        if conversation_id:
            session_key += f"_{conversation_id}"
        
        return self.db_directory / f"session_{session_key}.db"
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Clean up old persistent session files
        
        Args:
            days_old: Remove files older than this many days
            
        Returns:
            Number of files removed
        """
        import time
        
        removed_count = 0
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        for db_file in self.db_directory.glob("session_*.db"):
            if db_file.stat().st_mtime < cutoff_time:
                db_file.unlink()
                removed_count += 1
                print(f"🗑️ Removed old session file: {db_file}")
        
        return removed_count


# Global session manager instance
session_manager = SessionManager()


# Utility functions for easy session management
async def get_user_session(user_id: str, persistent: bool = True) -> SQLiteSession:
    """
    Quick utility to get a user session
    
    Args:
        user_id: User identifier
        persistent: True for persistent, False for temporary
        
    Returns:
        SQLiteSession instance
    """
    session_type = "persistent" if persistent else "temporary"
    return session_manager.get_session(user_id, session_type)


async def clear_user_session(user_id: str, persistent: bool = True) -> bool:
    """
    Quick utility to clear a user session
    
    Args:
        user_id: User identifier
        persistent: True for persistent, False for temporary
        
    Returns:
        bool: True if cleared successfully
    """
    session_type = "persistent" if persistent else "temporary"
    return await session_manager.clear_session(user_id, session_type)

# Export main components
__all__ = [
    'SessionManager',
    'session_manager',
    'get_user_session', 
    'clear_user_session'
]