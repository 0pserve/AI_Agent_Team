"""
Tests for Core modules
"""
import pytest
from core.engine import ExecutionEngine, PipelineConfig
from core.memory import Memory, Session


class TestExecutionEngine:
    """Test cases for ExecutionEngine"""
    
    @pytest.fixture
    def engine(self):
        return ExecutionEngine()
    
    def test_engine_initialization(self, engine):
        """Test engine initialization"""
        assert engine.planner is not None
        assert engine.coder is not None
        assert engine.evaluator is not None
    
    def test_get_agent_status(self, engine):
        """Test getting agent status"""
        status = engine.get_agent_status()
        
        assert "planner" in status
        assert "coder" in status
        assert "evaluator" in status
    
    def test_reset(self, engine):
        """Test resetting agents"""
        engine.reset()
        
        # Check that agents are reset (history cleared)
        assert engine.planner.conversation_history == []
        assert engine.coder.conversation_history == []


class TestMemory:
    """Test cases for Memory"""
    
    @pytest.fixture
    def memory(self):
        return Memory()
    
    def test_memory_initialization(self, memory):
        """Test memory initialization"""
        assert memory.session_ttl == 3600
        assert memory.history_size == 100
    
    def test_create_session(self, memory):
        """Test creating a session"""
        session = memory.create_session("test_session", "Test project")
        
        assert session.session_id == "test_session"
        assert session.project_overview == "Test project"
    
    def test_get_session(self, memory):
        """Test getting a session"""
        memory.create_session("test_session", "Test project")
        
        session = memory.get_session("test_session")
        assert session is not None
        assert session.session_id == "test_session"
    
    def test_update_session(self, memory):
        """Test updating a session"""
        memory.create_session("test_session")
        
        success = memory.update_session("test_session", project_overview="Updated")
        assert success
        
        session = memory.get_session("test_session")
        assert session.project_overview == "Updated"
    
    def test_delete_session(self, memory):
        """Test deleting a session"""
        memory.create_session("test_session")
        
        success = memory.delete_session("test_session")
        assert success
        
        session = memory.get_session("test_session")
        assert session is None
    
    def test_code_history(self, memory):
        """Test code history"""
        memory.add_code_history("test.py", "print('hello')", "created")
        
        history = memory.get_code_history()
        assert len(history) == 1
        assert history[0].file_path == "test.py"
    
    def test_get_stats(self, memory):
        """Test getting memory stats"""
        memory.create_session("test_session")
        
        stats = memory.get_stats()
        
        assert "sessions_count" in stats
        assert "code_history_count" in stats
        assert stats["sessions_count"] == 1