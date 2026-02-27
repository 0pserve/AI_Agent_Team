"""
Settings and configuration for the AI Software Development Automation System
"""
import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class LLMSettings:
    """LLM (Large Language Model) configuration"""
    provider: str = "openai"
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4000
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@dataclass
class EvaluationSettings:
    """Evaluation and debugging settings"""
    max_iterations: int = 3
    min_test_coverage: float = 0.70
    max_complexity: int = 10
    max_duplicate_rate: float = 0.05
    min_documentation_rate: float = 0.30
    allow_security_vulnerabilities: bool = False


@dataclass
class ExecutionSettings:
    """Execution engine settings"""
    docker_enabled: bool = False
    shell_timeout: int = 300
    temp_dir: str = "/tmp/agent_team"
    test_framework: str = "pytest"


@dataclass
class MemorySettings:
    """Memory and storage settings"""
    vector_db_enabled: bool = False
    redis_enabled: bool = False
    session_ttl: int = 3600
    history_size: int = 100


@dataclass
class Settings:
    """Main settings class"""
    # LLM configurations for each agent
    planner_llm: LLMSettings = field(default_factory=LLMSettings)
    coder_llm: LLMSettings = field(default_factory=LLMSettings)
    evaluator_llm: LLMSettings = field(default_factory=LLMSettings)
    
    # Evaluation settings
    evaluation: EvaluationSettings = field(default_factory=EvaluationSettings)
    
    # Execution settings
    execution: ExecutionSettings = field(default_factory=ExecutionSettings)
    
    # Memory settings
    memory: MemorySettings = field(default_factory=MemorySettings)
    
    # Debug mode
    debug: bool = False
    verbose: bool = True
    
    @classmethod
    def from_env(cls) -> 'Settings':
        """Create settings from environment variables"""
        settings = cls()
        
        # Load API keys from environment
        settings.planner_llm.api_key = os.getenv("OPENAI_API_KEY")
        settings.coder_llm.api_key = os.getenv("OPENAI_API_KEY")
        settings.evaluator_llm.api_key = os.getenv("OPENAI_API_KEY")
        
        # Override with environment variables if set
        if model := os.getenv("LLM_MODEL"):
            settings.planner_llm.model = model
            settings.coder_llm.model = model
            settings.evaluator_llm.model = model
        
        settings.debug = os.getenv("DEBUG", "false").lower() == "true"
        settings.verbose = os.getenv("VERBOSE", "true").lower() == "true"
        
        return settings


# Default settings instance
default_settings = Settings.from_env()
