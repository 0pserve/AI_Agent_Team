"""
Tests for AI Agents
"""
import pytest
from agents.planner import PlannerAgent, ProjectPlan
from agents.coder import CoderAgent, GeneratedCode
from agents.evaluator import EvaluatorAgent, EvaluationResult


class TestPlannerAgent:
    """Test cases for PlannerAgent"""
    
    @pytest.fixture
    def planner(self):
        return PlannerAgent()
    
    @pytest.mark.asyncio
    async def test_planner_initialization(self, planner):
        """Test planner agent initialization"""
        assert planner.name == "PlannerAgent"
        assert not planner.is_initialized
        
        planner.initialize()
        assert planner.is_initialized
    
    @pytest.mark.asyncio
    async def test_execute_with_string_input(self, planner):
        """Test planner execution with string input"""
        planner.initialize()
        
        result = await planner.execute("Create a web API")
        
        assert result.success
        assert isinstance(result.content, ProjectPlan)
    
    @pytest.mark.asyncio
    async def test_plan_validation(self, planner):
        """Test project plan validation"""
        planner.initialize()
        
        # Valid plan
        valid_plan = ProjectPlan(
            project_name="test_project",
            tech_stack={"language": "Python"},
            implementation_steps=[{"step": 1, "description": "Test"}]
        )
        
        issues = planner.validate_plan(valid_plan)
        assert len(issues) == 0


class TestCoderAgent:
    """Test cases for CoderAgent"""
    
    @pytest.fixture
    def coder(self):
        return CoderAgent()
    
    @pytest.fixture
    def sample_plan(self):
        return ProjectPlan(
            project_name="test_project",
            description="Test project",
            tech_stack={"language": "Python", "framework": "FastAPI"},
            requirements=[],
            file_structure=["main.py"],
            implementation_steps=[]
        )
    
    @pytest.mark.asyncio
    async def test_coder_initialization(self, coder):
        """Test coder agent initialization"""
        assert coder.name == "CoderAgent"
        coder.initialize()
        assert coder.is_initialized
    
    @pytest.mark.asyncio
    async def test_execute_with_plan(self, coder, sample_plan):
        """Test coder execution with project plan"""
        coder.initialize()
        
        result = await coder.execute(sample_plan)
        
        assert result.success
        assert isinstance(result.content, GeneratedCode)
        assert len(result.content.files) > 0


class TestEvaluatorAgent:
    """Test cases for EvaluatorAgent"""
    
    @pytest.fixture
    def evaluator(self):
        return EvaluatorAgent()
    
    @pytest.fixture
    def sample_code(self):
        return GeneratedCode(
            project_name="test",
            files=[],
            metadata={}
        )
    
    @pytest.mark.asyncio
    async def test_evaluator_initialization(self, evaluator):
        """Test evaluator agent initialization"""
        assert evaluator.name == "EvaluatorAgent"
        evaluator.initialize()
        assert evaluator.is_initialized
    
    @pytest.mark.asyncio
    async def test_execute_with_code(self, evaluator, sample_code):
        """Test evaluator execution with generated code"""
        evaluator.initialize()
        
        result = await evaluator.execute(sample_code)
        
        assert result.success
        assert isinstance(result.content, EvaluationResult)