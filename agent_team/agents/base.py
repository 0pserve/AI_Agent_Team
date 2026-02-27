"""
Base Agent class for all AI agents in the system
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import logging


@dataclass
class AgentMessage:
    """Message structure for agent communication"""
    role: str  # 'user', 'assistant', 'system', 'agent'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Response structure from agent execution"""
    success: bool
    content: Any
    messages: List[AgentMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Provides common functionality for LLM interaction, message handling, and logging.
    """
    
    def __init__(
        self, 
        name: str,
        llm_config: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the base agent
        
        Args:
            name: Agent name
            llm_config: LLM configuration dictionary
            logger: Logger instance
        """
        self.name = name
        self.llm_config = llm_config or {}
        self.logger = logger or logging.getLogger(name)
        self.conversation_history: List[AgentMessage] = []
        self._initialized = False
    
    @abstractmethod
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Execute the agent's main task
        
        Args:
            input_data: Input data for the agent
            context: Additional context information
            
        Returns:
            AgentResponse containing the execution result
        """
        pass
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation history"""
        message = AgentMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.conversation_history.append(message)
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
    
    def get_history(self) -> List[AgentMessage]:
        """Get conversation history"""
        return self.conversation_history.copy()
    
    async def _call_llm(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Call the LLM with the given messages
        
        This is a placeholder implementation. In a real system, 
        this would integrate with OpenAI, Anthropic, or other LLM providers.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters for LLM call
            
        Returns:
            LLM response content
        """
        # Placeholder - would integrate with actual LLM API
        self.logger.info(f"[{self.name}] Calling LLM with {len(messages)} messages")
        
        # Default response for demonstration
        return "LLM response placeholder"
    
    def _format_messages(self, system_prompt: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Format messages for LLM call"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in self.conversation_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages
    
    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized"""
        return self._initialized
    
    def initialize(self):
        """Initialize the agent"""
        self._initialized = True
        self.logger.info(f"[{self.name}] Agent initialized")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
