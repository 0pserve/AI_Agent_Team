"""
Memory Module - Manages session state and code history
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging


@dataclass
class Session:
    """Session data structure"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    project_overview: str = ""
    project_plan: Optional[Dict[str, Any]] = None
    generated_code: Optional[Dict[str, Any]] = None
    evaluation_result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeHistoryEntry:
    """Code history entry"""
    timestamp: datetime
    file_path: str
    content: str
    action: str  # created, modified, evaluated
    metadata: Dict[str, Any] = field(default_factory=dict)


class Memory:
    """
    Memory - Manages session state and code history
    
    Responsibilities:
    - Store and retrieve session data
    - Maintain code history
    - Manage conversation context
    - Support session persistence
    """
    
    def __init__(
        self,
        session_ttl: int = 3600,
        history_size: int = 100,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize memory
        
        Args:
            session_ttl: Session time-to-live in seconds
            history_size: Maximum history size
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger("Memory")
        self.session_ttl = session_ttl
        self.history_size = history_size
        
        # In-memory storage (would use Redis/VectorDB in production)
        self._sessions: Dict[str, Session] = {}
        self._code_history: List[CodeHistoryEntry] = []
        self._current_session_id: Optional[str] = None
        
        self.logger.info("Memory initialized")
    
    def create_session(self, session_id: str, project_overview: str = "") -> Session:
        """
        Create a new session
        
        Args:
            session_id: Unique session identifier
            project_overview: Initial project description
            
        Returns:
            Created session
        """
        session = Session(
            session_id=session_id,
            project_overview=project_overview
        )
        self._sessions[session_id] = session
        self._current_session_id = session_id
        
        self.logger.info(f"Created session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session if found, None otherwise
        """
        return self._sessions.get(session_id)
    
    def get_current_session(self) -> Optional[Session]:
        """Get the current active session"""
        if self._current_session_id:
            return self._sessions.get(self._current_session_id)
        return None
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session identifier
            **kwargs: Fields to update
            
        Returns:
            True if updated, False if session not found
        """
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.updated_at = datetime.now()
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            if self._current_session_id == session_id:
                self._current_session_id = None
            self.logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    def list_sessions(self) -> List[str]:
        """List all session IDs"""
        return list(self._sessions.keys())
    
    def add_code_history(
        self,
        file_path: str,
        content: str,
        action: str = "created",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add entry to code history
        
        Args:
            file_path: Path to the file
            content: File content
            action: Action type (created, modified, evaluated)
            metadata: Additional metadata
        """
        entry = CodeHistoryEntry(
            timestamp=datetime.now(),
            file_path=file_path,
            content=content,
            action=action,
            metadata=metadata or {}
        )
        
        self._code_history.append(entry)
        
        # Trim history if needed
        if len(self._code_history) > self.history_size:
            self._code_history = self._code_history[-self.history_size:]
        
        self.logger.debug(f"Added code history: {file_path} ({action})")
    
    def get_code_history(
        self,
        file_path: Optional[str] = None,
        limit: int = 10
    ) -> List[CodeHistoryEntry]:
        """
        Get code history
        
        Args:
            file_path: Filter by file path (optional)
            limit: Maximum number of entries
            
        Returns:
            List of history entries
        """
        history = self._code_history
        
        if file_path:
            history = [e for e in history if e.file_path == file_path]
        
        return history[-limit:]
    
    def search_code(self, query: str) -> List[CodeHistoryEntry]:
        """
        Search code history
        
        Args:
            query: Search query
            
        Returns:
            Matching history entries
        """
        results = []
        query_lower = query.lower()
        
        for entry in self._code_history:
            if query_lower in entry.content.lower() or query_lower in entry.file_path.lower():
                results.append(entry)
        
        return results
    
    def save_session_to_file(self, session_id: str, filepath: str) -> bool:
        """
        Save session to file
        
        Args:
            session_id: Session identifier
            filepath: Output file path
            
        Returns:
            True if saved successfully
        """
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        try:
            # Convert session to dict
            session_dict = {
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "project_overview": session.project_overview,
                "project_plan": session.project_plan,
                "generated_code": session.generated_code,
                "evaluation_result": session.evaluation_result,
                "metadata": session.metadata
            }
            
            with open(filepath, 'w') as f:
                json.dump(session_dict, f, indent=2)
            
            self.logger.info(f"Saved session to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save session: {str(e)}")
            return False
    
    def load_session_from_file(self, filepath: str) -> Optional[Session]:
        """
        Load session from file
        
        Args:
            filepath: Input file path
            
        Returns:
            Loaded session or None
        """
        try:
            with open(filepath, 'r') as f:
                session_dict = json.load(f)
            
            session = Session(
                session_id=session_dict["session_id"],
                project_overview=session_dict.get("project_overview", ""),
                project_plan=session_dict.get("project_plan"),
                generated_code=session_dict.get("generated_code"),
                evaluation_result=session_dict.get("evaluation_result"),
                metadata=session_dict.get("metadata", {})
            )
            
            # Parse datetime
            session.created_at = datetime.fromisoformat(session_dict["created_at"])
            session.updated_at = datetime.fromisoformat(session_dict["updated_at"])
            
            self._sessions[session.session_id] = session
            self.logger.info(f"Loaded session from {filepath}")
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to load session: {str(e)}")
            return None
    
    def clear(self):
        """Clear all memory"""
        self._sessions.clear()
        self._code_history.clear()
        self._current_session_id = None
        self.logger.info("Memory cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "sessions_count": len(self._sessions),
            "code_history_count": len(self._code_history),
            "current_session": self._current_session_id,
            "session_ttl": self.session_ttl,
            "history_size": self.history_size
        }