"""
Coder Agent - Generates code based on project plans
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import os
import re

from .base import BaseAgent, AgentResponse
from .planner import ProjectPlan, ProjectRequirement


@dataclass
class CodeFile:
    """Generated code file structure"""
    path: str
    content: str
    language: str
    file_type: str  # source, test, config, documentation
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GeneratedCode:
    """Container for generated code files"""
    project_name: str
    files: List[CodeFile] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CoderAgent(BaseAgent):
    """
    Coder Agent - Generates code based on project plans
    
    Responsibilities:
    - Generate source code based on project plan
    - Create test files
    - Generate configuration files
    - Create documentation
    - Modify existing code based on feedback
    """
    
    SYSTEM_PROMPT = """You are an Expert Coder AI assistant.
Your role is to generate high-quality, production-ready code based on project plans.

When given a project plan, you should:
1. Generate all necessary source files
2. Create comprehensive test files
3. Generate configuration files
4. Add proper documentation and comments
5. Follow best practices for the specific language/framework

Always ensure:
- Code is well-structured and maintainable
- Tests provide good coverage
- Configuration is properly separated
- Documentation is clear and concise"""

    def __init__(
        self,
        llm_config: Optional[Dict[str, Any]] = None,
        logger: Optional[Any] = None
    ):
        super().__init__("CoderAgent", llm_config, logger)
        self.generated_code: Optional[GeneratedCode] = None
        self._output_dir: Optional[str] = None
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Execute the coder agent to generate code
        
        Args:
            input_data: ProjectPlan or dict with plan information
            context: Additional context (optional)
            
        Returns:
            AgentResponse with GeneratedCode
        """
        self.logger.info(f"[CoderAgent] Starting code generation")
        
        try:
            # Parse input - should be a ProjectPlan
            if isinstance(input_data, ProjectPlan):
                plan = input_data
            elif isinstance(input_data, dict):
                # Try to reconstruct plan from dict
                plan = self._dict_to_plan(input_data)
            else:
                raise ValueError("Input must be a ProjectPlan or dict")
            
            # Add user message to history
            self.add_message('user', f"Generate code for project: {plan.project_name}")
            
            # Generate code files
            generated = await self._generate_code(plan, context)
            
            self.generated_code = generated
            
            # Add assistant message
            self.add_message('assistant', f"Generated {len(generated.files)} files")
            
            self.logger.info(f"[CoderAgent] Code generation completed: {len(generated.files)} files")
            
            return AgentResponse(
                success=True,
                content=generated,
                metadata={
                    "project_name": plan.project_name,
                    "files_count": len(generated.files),
                    "languages": list(set(f.language for f in generated.files))
                }
            )
            
        except Exception as e:
            self.logger.error(f"[CoderAgent] Error: {str(e)}")
            return AgentResponse(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _dict_to_plan(self, data: Dict[str, Any]) -> ProjectPlan:
        """Convert dict to ProjectPlan"""
        requirements = []
        for req_data in data.get('requirements', []):
            if isinstance(req_data, dict):
                requirements.append(ProjectRequirement(
                    name=req_data.get('name', ''),
                    description=req_data.get('description', ''),
                    priority=req_data.get('priority', 'medium')
                ))
        
        return ProjectPlan(
            project_name=data.get('project_name', 'project'),
            description=data.get('description', ''),
            tech_stack=data.get('tech_stack', {}),
            requirements=requirements,
            file_structure=data.get('file_structure', []),
            implementation_steps=data.get('implementation_steps', []),
            risks=data.get('risks', [])
        )
    
    async def _generate_code(
        self, 
        plan: ProjectPlan, 
        context: Optional[Dict[str, Any]]
    ) -> GeneratedCode:
        """Generate code files based on plan"""
        files = []
        
        # Set output directory
        self._output_dir = context.get('output_dir') if context else None
        
        # Generate source files
        files.extend(await self._generate_source_files(plan))
        
        # Generate test files
        files.extend(await self._generate_test_files(plan))
        
        # Generate config files
        files.extend(await self._generate_config_files(plan))
        
        # Generate documentation
        files.extend(await self._generate_documentation(plan))
        
        return GeneratedCode(
            project_name=plan.project_name,
            files=files,
            metadata={
                "plan_description": plan.description,
                "tech_stack": plan.tech_stack
            }
        )
    
    async def _generate_source_files(self, plan: ProjectPlan) -> List[CodeFile]:
        """Generate source code files"""
        files = []
        project_name = plan.project_name
        tech_stack = plan.tech_stack
        
        # Main application file
        if tech_stack.get("framework") == "FastAPI":
            files.append(CodeFile(
                path=f"{project_name}/main.py",
                content=self._generate_fastapi_main(plan),
                language="python",
                file_type="source"
            ))
            files.append(CodeFile(
                path=f"{project_name}/config.py",
                content=self._generate_config(),
                language="python",
                file_type="source"
            ))
        elif tech_stack.get("framework") == "React":
            files.append(CodeFile(
                path=f"{project_name}/src/App.tsx",
                content=self._generate_react_app(),
                language="typescript",
                file_type="source"
            ))
        else:
            # Default Python main file
            files.append(CodeFile(
                path=f"{project_name}/main.py",
                content=self._generate_default_main(plan),
                language="python",
                file_type="source"
            ))
        
        # Models
        files.append(CodeFile(
            path=f"{project_name}/models.py",
            content=self._generate_models(plan),
            language="python",
            file_type="source"
        ))
        
        # Services
        files.append(CodeFile(
            path=f"{project_name}/services.py",
            content=self._generate_services(plan),
            language="python",
            file_type="source"
        ))
        
        # Routes (if applicable)
        if tech_stack.get("framework") in ["FastAPI", "Flask"]:
            files.append(CodeFile(
                path=f"{project_name}/routes.py",
                content=self._generate_routes(plan),
                language="python",
                file_type="source"
            ))
        
        return files
    
    async def _generate_test_files(self, plan: ProjectPlan) -> List[CodeFile]:
        """Generate test files"""
        files = []
        project_name = plan.project_name
        
        # Main test file
        files.append(CodeFile(
            path=f"tests/test_{project_name}.py",
            content=self._generate_test_main(plan),
            language="python",
            file_type="test"
        ))
        
        # Test __init__
        files.append(CodeFile(
            path="tests/__init__.py",
            content="",
            language="python",
            file_type="test"
        ))
        
        return files
    
    async def _generate_config_files(self, plan: ProjectPlan) -> List[CodeFile]:
        """Generate configuration files"""
        files = []
        project_name = plan.project_name
        tech_stack = plan.tech_stack
        
        # requirements.txt
        files.append(CodeFile(
            path="requirements.txt",
            content=self._generate_requirements_txt(tech_stack),
            language="text",
            file_type="config"
        ))
        
        # .gitignore
        files.append(CodeFile(
            path=".gitignore",
            content=self._generate_gitignore(),
            language="text",
            file_type="config"
        ))
        
        # pytest.ini or setup.cfg
        if tech_stack.get("language") == "Python":
            files.append(CodeFile(
                path="pytest.ini",
                content=self._generate_pytest_ini(),
                language="text",
                file_type="config"
            ))
        
        return files
    
    async def _generate_documentation(self, plan: ProjectPlan) -> List[CodeFile]:
        """Generate documentation files"""
        files = []
        
        # README.md
        files.append(CodeFile(
            path="README.md",
            content=self._generate_readme(plan),
            language="markdown",
            file_type="documentation"
        ))
        
        return files
    
    # Code generation templates
    
    def _generate_fastapi_main(self, plan: ProjectPlan) -> str:
        """Generate FastAPI main.py"""
        return f'''"""
{plan.project_name} - Main application entry point
Generated by AI Software Development Automation System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import logging

from .models import *
from .config import settings
from .routes import router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="{plan.project_name}",
    description="{plan.description}",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {{
        "message": "Welcome to {plan.project_name}",
        "version": "1.0.0"
    }}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {{"status": "healthy"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _generate_default_main(self, plan: ProjectPlan) -> str:
        """Generate default main.py"""
        return f'''"""
{plan.project_name} - Main application entry point
Generated by AI Software Development Automation System
"""

import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Application:
    """Main application class"""
    
    def __init__(self, name: str = "{plan.project_name}"):
        self.name = name
        logger.info(f"Initializing {{self.name}}")
    
    def run(self):
        """Run the application"""
        logger.info(f"Running {{self.name}}")
        # Add your application logic here
        pass


def main():
    """Main entry point"""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
'''
    
    def _generate_react_app(self) -> str:
        """Generate React App.tsx"""
        return '''import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Welcome</h1>
        <p>Edit src/App.tsx to get started</p>
      </header>
    </div>
  );
}

export default App;
'''
    
    def _generate_config(self) -> str:
        """Generate config.py"""
        return '''"""
Application configuration
Generated by AI Software Development Automation System
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Application"
    debug: bool = False
    
    # API
    api_version: str = "v1"
    
    # Database
    database_url: Optional[str] = None
    
    # Security
    secret_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
'''
    
    def _generate_models(self, plan: ProjectPlan) -> str:
        """Generate models.py"""
        return f'''"""
Data models for {plan.project_name}
Generated by AI Software Development Automation System
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Status(str, Enum):
    """Status enum"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseModel(BaseModel):
    """Base model with common fields"""
    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Item(BaseModel):
    """Example item model"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    status: Status = Status.PENDING
    
    class Config:
        use_enum_values = True
'''
    
    def _generate_services(self, plan: ProjectPlan) -> str:
        """Generate services.py"""
        return f'''"""
Business logic services for {plan.project_name}
Generated by AI Software Development Automation System
"""

from typing import List, Optional
from .models import Item, Status
import logging

logger = logging.getLogger(__name__)


class ItemService:
    """Service for managing items"""
    
    def __init__(self):
        self._items: List[Item] = []
    
    def create_item(self, name: str, description: Optional[str] = None) -> Item:
        """Create a new item"""
        item = Item(
            name=name,
            description=description,
            status=Status.PENDING
        )
        self._items.append(item)
        logger.info(f"Created item: {{item.name}}")
        return item
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """Get item by ID"""
        for item in self._items:
            if item.id == item_id:
                return item
        return None
    
    def list_items(self) -> List[Item]:
        """List all items"""
        return self._items
    
    def update_item_status(self, item_id: str, status: Status) -> Optional[Item]:
        """Update item status"""
        item = self.get_item(item_id)
        if item:
            item.status = status
            logger.info(f"Updated item {{item.name}} status to {{status}}")
        return item
    
    def delete_item(self, item_id: str) -> bool:
        """Delete an item"""
        for i, item in enumerate(self._items):
            if item.id == item_id:
                del self._items[i]
                logger.info(f"Deleted item: {{item.name}}")
                return True
        return False


# Singleton instance
item_service = ItemService()
'''
    
    def _generate_routes(self, plan: ProjectPlan) -> str:
        """Generate routes.py"""
        return f'''"""
API routes for {plan.project_name}
Generated by AI Software Development Automation System
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from .models import Item, Status
from .services import item_service

router = APIRouter(prefix="/api/v1", tags=["items"])


@router.get("/items", response_model=List[Item])
async def list_items():
    """List all items"""
    return item_service.list_items()


@router.post("/items", response_model=Item)
async def create_item(item: Item):
    """Create a new item"""
    return item_service.create_item(item.name, item.description)


@router.get("/items/{{item_id}}", response_model=Item)
async def get_item(item_id: str):
    """Get item by ID"""
    item = item_service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/items/{{item_id}}/status", response_model=Item)
async def update_item_status(item_id: str, status: Status):
    """Update item status"""
    item = item_service.update_item_status(item_id, status)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/items/{{item_id}}")
async def delete_item(item_id: str):
    """Delete an item"""
    if not item_service.delete_item(item_id):
        raise HTTPException(status_code=404, detail="Item not found")
    return {{"message": "Item deleted"}}
'''
    
    def _generate_test_main(self, plan: ProjectPlan) -> str:
        """Generate test file"""
        return f'''"""
Tests for {plan.project_name}
Generated by AI Software Development Automation System
"""

import pytest
from {plan.project_name}.models import Item, Status
from {plan.project_name}.services import item_service


class TestItem:
    """Test cases for Item model"""
    
    def test_item_creation(self):
        """Test creating an item"""
        item = Item(name="Test Item", description="Test description")
        assert item.name == "Test Item"
        assert item.description == "Test description"
        assert item.status == Status.PENDING
    
    def test_item_validation(self):
        """Test item field validation"""
        with pytest.raises(Exception):
            Item(name="")  # Empty name should fail


class TestItemService:
    """Test cases for ItemService"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.service = item_service
    
    def test_create_item(self):
        """Test creating an item via service"""
        item = self.service.create_item("Test", "Description")
        assert item.name == "Test"
        assert item.description == "Description"
    
    def test_list_items(self):
        """Test listing items"""
        items = self.service.list_items()
        assert isinstance(items, list)
    
    def test_get_item(self):
        """Test getting an item by ID"""
        item = self.service.create_item("Test Item")
        found = self.service.get_item(item.id)
        assert found is not None
        assert found.name == "Test Item"
'''
    
    def _generate_requirements_txt(self, tech_stack: Dict[str, str]) -> str:
        """Generate requirements.txt"""
        deps = ["pytest>=7.0.0", "pydantic>=2.0.0"]
        
        if tech_stack.get("framework") == "FastAPI":
            deps.extend(["fastapi>=0.100.0", "uvicorn>=0.23.0", "pydantic-settings>=2.0.0"])
        elif tech_stack.get("framework") == "Flask":
            deps.extend(["flask>=2.0.0", "flask-cors>=4.0.0"])
        
        if tech_stack.get("database"):
            deps.append("sqlalchemy>=2.0.0")
        
        return "\n".join(deps) + "\n"
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore"""
        return '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db
'''
    
    def _generate_pytest_ini(self) -> str:
        """Generate pytest.ini"""
        return '''[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
'''
    
    def _generate_readme(self, plan: ProjectPlan) -> str:
        """Generate README.md"""
        tech_stack_str = ", ".join([f"{k}: {v}" for k, v in plan.tech_stack.items() if v])
        
        return f'''# {plan.project_name}

{plan.description}

## Tech Stack

{tech_stack_str}

## Getting Started

### Prerequisites

- Python 3.8+
{'- PostgreSQL (if using database)' if plan.tech_stack.get('database') else ''}

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Run the application
python -m {plan.project_name}.main
```

### Testing

```bash
# Run tests
pytest
```

## Project Structure

```
{plan.project_name}/
{chr(10).join(f"  - {f}" for f in plan.file_structure[:5])}
```

## API Endpoints

{'- Add your API endpoints here' if plan.tech_stack.get('framework') in ['FastAPI', 'Flask'] else '- Not applicable for this project type'}

## License

MIT
'''
    
    def get_generated_code(self) -> Optional[GeneratedCode]:
        """Get the generated code"""
        return self.generated_code
    
    async def modify_code(
        self, 
        file_path: str, 
        modifications: str, 
        reason: str
    ) -> AgentResponse:
        """
        Modify existing code based on feedback
        
        Args:
            file_path: Path to file to modify
            modifications: Description of modifications needed
            reason: Reason for modification
            
        Returns:
            AgentResponse with modified content
        """
        self.logger.info(f"[CoderAgent] Modifying code: {file_path}")
        
        # Add to history
        self.add_message('user', f"Modify {file_path}: {modifications}")
        
        # In production, this would parse the existing file and apply modifications
        # For now, return a placeholder
        
        return AgentResponse(
            success=True,
            content={"file": file_path, "modified": True, "reason": reason},
            metadata={"modifications": modifications}
        )
