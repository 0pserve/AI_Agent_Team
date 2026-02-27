"""
Planner Agent - Analyzes project requirements and creates detailed plans
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import re

from .base import BaseAgent, AgentResponse


@dataclass
class ProjectRequirement:
    """Project requirement structure"""
    name: str
    description: str
    priority: str = "medium"  # high, medium, low
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ProjectPlan:
    """Project plan structure"""
    project_name: str
    description: str
    tech_stack: Dict[str, str] = field(default_factory=dict)
    requirements: List[ProjectRequirement] = field(default_factory=list)
    file_structure: List[str] = field(default_factory=list)
    implementation_steps: List[Dict[str, Any]] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class PlannerAgent(BaseAgent):
    """
    Planner Agent -负责分析项目需求并创建详细计划
    
    Responsibilities:
    - Analyze user project overview
    - Extract requirements
    - Select appropriate tech stack
    - Create detailed project plan
    - Identify risks
    """
    
    SYSTEM_PROMPT = """You are a Senior Software Architect AI assistant.
Your role is to analyze project requirements and create comprehensive, actionable project plans.

When given a project overview, you should:
1. Analyze the requirements thoroughly
2. Identify necessary technologies, frameworks, and libraries
3. Break down the project into manageable components
4. Define the file structure
5. List implementation steps in order
6. Identify potential risks and mitigation strategies

Respond in JSON format with the following structure:
{
    "project_name": "string",
    "description": "string",
    "tech_stack": {"language": "string", "framework": "string", "libraries": []},
    "requirements": [{"name": "string", "description": "string", "priority": "string"}],
    "file_structure": ["path/to/file1.py", "path/to/file2.py", ...],
    "implementation_steps": [{"step": number, "description": "string", "files": []}],
    "risks": ["risk1", "risk2", ...]
}

Be practical and choose technologies that are well-suited for the project scope."""
    
    def __init__(
        self,
        llm_config: Optional[Dict[str, Any]] = None,
        logger: Optional[Any] = None
    ):
        super().__init__("PlannerAgent", llm_config, logger)
        self.current_plan: Optional[ProjectPlan] = None
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Execute the planner agent to analyze requirements and create a plan
        
        Args:
            input_data: Project overview from user (str or dict)
            context: Additional context (optional)
            
        Returns:
            AgentResponse with ProjectPlan
        """
        self.logger.info(f"[PlannerAgent] Starting project planning")
        
        try:
            # Parse input
            if isinstance(input_data, str):
                project_overview = input_data
            elif isinstance(input_data, dict):
                project_overview = input_data.get('overview', '')
            else:
                project_overview = str(input_data)
            
            # Add user message to history
            self.add_message('user', f"Create a project plan for: {project_overview}")
            
            # Call LLM to generate plan
            messages = self._format_messages(self.SYSTEM_PROMPT)
            messages.append({
                "role": "user", 
                "content": f"Project Overview: {project_overview}\n\nPlease create a detailed project plan."
            })
            
            # For demonstration, we'll create a structured response
            # In production, this would call the actual LLM
            response_content = await self._call_llm(messages)
            
            # Parse the response (in real implementation, this would parse actual LLM output)
            plan = await self._parse_llm_response(response_content, project_overview)
            
            self.current_plan = plan
            
            # Add assistant message
            self.add_message('assistant', f"Project plan created: {plan.project_name}")
            
            self.logger.info(f"[PlannerAgent] Project plan created successfully")
            
            return AgentResponse(
                success=True,
                content=plan,
                metadata={
                    "plan_name": plan.project_name,
                    "requirements_count": len(plan.requirements),
                    "steps_count": len(plan.implementation_steps)
                }
            )
            
        except Exception as e:
            self.logger.error(f"[PlannerAgent] Error: {str(e)}")
            return AgentResponse(
                success=False,
                content=None,
                error=str(e)
            )
    
    async def _parse_llm_response(self, response: str, project_overview: str) -> ProjectPlan:
        """
        Parse LLM response into ProjectPlan
        
        In a real implementation, this would parse actual JSON from LLM.
        For demonstration, we create a sample plan.
        """
        # This would parse actual LLM JSON output in production
        # For now, create a structured plan based on the overview
        
        project_name = self._extract_project_name(project_overview)
        
        # Create sample tech stack based on project type
        tech_stack = self._determine_tech_stack(project_overview)
        
        # Create sample requirements
        requirements = self._generate_requirements(project_overview)
        
        # Create file structure
        file_structure = self._generate_file_structure(project_name, tech_stack)
        
        # Create implementation steps
        steps = self._generate_implementation_steps(requirements, file_structure)
        
        # Identify risks
        risks = self._identify_risks(tech_stack, requirements)
        
        return ProjectPlan(
            project_name=project_name,
            description=project_overview[:200],
            tech_stack=tech_stack,
            requirements=requirements,
            file_structure=file_structure,
            implementation_steps=steps,
            risks=risks
        )
    
    def _extract_project_name(self, overview: str) -> str:
        """Extract project name from overview"""
        # Simple extraction - take first few words
        words = overview.split()[:3]
        name = '_'.join(words).lower()
        # Remove special characters
        name = re.sub(r'[^a-z0-9_]', '', name)
        return name or "project"
    
    def _determine_tech_stack(self, overview: str) -> Dict[str, str]:
        """Determine appropriate tech stack based on project overview"""
        overview_lower = overview.lower()
        
        tech_stack = {
            "language": "Python",
            "framework": "",
            "libraries": [],
            "database": ""
        }
        
        # Simple heuristics for tech stack selection
        if "web" in overview_lower or "api" in overview_lower:
            tech_stack["framework"] = "FastAPI"
            tech_stack["libraries"] = ["pydantic", "uvicorn"]
        elif "webapp" in overview_lower or "frontend" in overview_lower:
            tech_stack["framework"] = "React"
            tech_stack["language"] = "TypeScript"
        elif "data" in overview_lower or "analysis" in overview_lower:
            tech_stack["framework"] = "Pandas"
            tech_stack["libraries"] = ["numpy", "matplotlib"]
        
        if "database" in overview_lower or "db" in overview_lower:
            tech_stack["database"] = "PostgreSQL"
        
        return tech_stack
    
    def _generate_requirements(self, overview: str) -> List[ProjectRequirement]:
        """Generate requirements from overview"""
        # Generate sample requirements based on common patterns
        requirements = [
            ProjectRequirement(
                name="project_setup",
                description="Initialize project with proper structure and dependencies",
                priority="high"
            ),
            ProjectRequirement(
                name="core_functionality",
                description="Implement core business logic",
                priority="high"
            ),
            ProjectRequirement(
                name="api_endpoints",
                description="Create API endpoints if needed",
                priority="medium"
            ),
            ProjectRequirement(
                name="testing",
                description="Write unit and integration tests",
                priority="high"
            ),
            ProjectRequirement(
                name="documentation",
                description="Add documentation and README",
                priority="low"
            )
        ]
        return requirements
    
    def _generate_file_structure(self, project_name: str, tech_stack: Dict[str, str]) -> List[str]:
        """Generate file structure based on tech stack"""
        files = [
            f"{project_name}/__init__.py",
            f"{project_name}/main.py",
            f"{project_name}/config.py",
            f"{project_name}/models.py",
            f"{project_name}/routes.py" if tech_stack.get("framework") else "",
            f"{project_name}/services.py",
            f"tests/__init__.py",
            f"tests/test_main.py",
            f"requirements.txt",
            f".gitignore",
            f"README.md"
        ]
        return [f for f in files if f]
    
    def _generate_implementation_steps(
        self, 
        requirements: List[ProjectRequirement],
        file_structure: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate implementation steps"""
        steps = []
        for i, req in enumerate(requirements, 1):
            step = {
                "step": i,
                "description": req.description,
                "requirement": req.name,
                "priority": req.priority,
                "estimated_time": "1-2 hours"
            }
            steps.append(step)
        return steps
    
    def _identify_risks(
        self, 
        tech_stack: Dict[str, str], 
        requirements: List[ProjectRequirement]
    ) -> List[str]:
        """Identify potential risks"""
        risks = []
        
        if tech_stack.get("database"):
            risks.append(f"Database migration and schema management")
        
        if len(requirements) > 5:
            risks.append("Scope creep - too many requirements")
        
        risks.append("Dependency compatibility issues")
        risks.append("Integration testing challenges")
        
        return risks
    
    def get_current_plan(self) -> Optional[ProjectPlan]:
        """Get the current project plan"""
        return self.current_plan
    
    def validate_plan(self, plan: ProjectPlan) -> List[str]:
        """Validate a project plan and return issues"""
        issues = []
        
        if not plan.project_name:
            issues.append("Project name is required")
        
        if not plan.tech_stack.get("language"):
            issues.append("Technology stack must be specified")
        
        if not plan.implementation_steps:
            issues.append("Implementation steps are required")
        
        return issues
