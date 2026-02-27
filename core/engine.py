"""
Execution Engine - Orchestrates the AI agent pipeline
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

from agents import PlannerAgent, CoderAgent, EvaluatorAgent
from agents.base import AgentResponse
from agents.planner import ProjectPlan
from agents.coder import GeneratedCode
from agents.evaluator import EvaluationResult, QualityLevel


@dataclass
class PipelineConfig:
    """Configuration for the execution pipeline"""
    max_evaluation_iterations: int = 3
    auto_fix_enabled: bool = True
    save_intermediate_results: bool = True
    verbose: bool = True


@dataclass
class PipelineResult:
    """Result of the execution pipeline"""
    success: bool
    project_plan: Optional[ProjectPlan] = None
    generated_code: Optional[GeneratedCode] = None
    evaluation: Optional[EvaluationResult] = None
    iterations: int = 0
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionEngine:
    """
    Execution Engine - Orchestrates the AI agent pipeline
    
    Manages the flow between:
    1. Planner Agent - Creates project plan
    2. Coder Agent - Generates code
    3. Evaluator Agent - Evaluates and provides feedback
    
    Implements the feedback loop for iterative improvement.
    """
    
    def __init__(
        self,
        planner: Optional[PlannerAgent] = None,
        coder: Optional[CoderAgent] = None,
        evaluator: Optional[EvaluatorAgent] = None,
        config: Optional[PipelineConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the execution engine
        
        Args:
            planner: Planner agent instance
            coder: Coder agent instance
            evaluator: Evaluator agent instance
            config: Pipeline configuration
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger("ExecutionEngine")
        self.config = config or PipelineConfig()
        
        # Initialize agents
        self.planner = planner or PlannerAgent()
        self.coder = coder or CoderAgent()
        self.evaluator = evaluator or EvaluatorAgent()
        
        # Initialize agents
        self.planner.initialize()
        self.coder.initialize()
        self.evaluator.initialize()
        
        self.logger.info("ExecutionEngine initialized")
    
    async def execute(
        self, 
        project_overview: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """
        Execute the full pipeline
        
        Args:
            project_overview: User's project description
            context: Additional context
            
        Returns:
            PipelineResult with execution results
        """
        result = PipelineResult(
            started_at=datetime.now(),
            success=False
        )
        
        self.logger.info(f"Starting pipeline execution for: {project_overview[:50]}...")
        
        try:
            # Step 1: Planning
            self.logger.info("Step 1/3: Running Planner Agent")
            plan_response = await self.planner.execute(project_overview, context)
            
            if not plan_response.success:
                result.error = f"Planner failed: {plan_response.error}"
                return result
            
            result.project_plan = plan_response.content
            
            # Step 2: Code Generation
            self.logger.info("Step 2/3: Running Coder Agent")
            code_response = await self.coder.execute(result.project_plan, context)
            
            if not code_response.success:
                result.error = f"Coder failed: {code_response.error}"
                return result
            
            result.generated_code = code_response.content
            
            # Step 3: Evaluation with feedback loop
            self.logger.info("Step 3/3: Running Evaluator Agent")
            evaluation = await self._evaluate_with_feedback(
                result.generated_code, 
                context
            )
            
            result.evaluation = evaluation
            result.iterations = evaluation.metadata.get('iterations', 1)
            result.success = evaluation.passed
            
            result.completed_at = datetime.now()
            
            self.logger.info(
                f"Pipeline completed: success={result.success}, "
                f"iterations={result.iterations}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            result.error = str(e)
            result.completed_at = datetime.now()
            return result
    
    async def _evaluate_with_feedback(
        self,
        generated_code: GeneratedCode,
        context: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate code with feedback loop
        
        Args:
            generated_code: Generated code to evaluate
            context: Additional context
            
        Returns:
            Final evaluation result
        """
        iteration = 0
        current_code = generated_code
        last_evaluation: Optional[EvaluationResult] = None
        
        while iteration < self.config.max_evaluation_iterations:
            iteration += 1
            self.logger.info(f"Evaluation iteration {iteration}/{self.config.max_evaluation_iterations}")
            
            # Evaluate current code
            eval_response = await self.evaluator.execute(current_code, context)
            
            if not eval_response.success:
                self.logger.error(f"Evaluation failed: {eval_response.error}")
                break
            
            last_evaluation = eval_response.content
            
            # Check if evaluation passed
            if last_evaluation.passed:
                self.logger.info("Evaluation passed!")
                break
            
            # If not passed and auto-fix is enabled, try to fix
            if self.config.auto_fix_enabled and iteration < self.config.max_evaluation_iterations:
                self.logger.info("Evaluation failed, attempting to fix...")
                
                # Get suggestions from evaluation
                suggestions = last_evaluation.suggestions
                
                # Request code modification from coder
                for suggestion in suggestions[:2]:  # Take top 2 suggestions
                    mod_response = await self.coder.modify_code(
                        file_path="",  # Would specify actual file
                        modifications=suggestion,
                        reason="Evaluation feedback"
                    )
                    
                    if mod_response.success:
                        self.logger.info(f"Applied fix: {suggestion[:50]}...")
            
            # Add iteration metadata
            last_evaluation.metadata['iterations'] = iteration
        
        if last_evaluation:
            last_evaluation.metadata['iterations'] = iteration
        
        return last_evaluation or EvaluationResult(
            passed=False,
            quality_level=QualityLevel.FAILED,
            metrics=None,
            summary="Evaluation failed"
        )
    
    async def run_planner_only(
        self, 
        project_overview: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Run only the planner agent"""
        return await self.planner.execute(project_overview, context)
    
    async def run_coder_only(
        self,
        project_plan: ProjectPlan,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Run only the coder agent"""
        return await self.coder.execute(project_plan, context)
    
    async def run_evaluator_only(
        self,
        generated_code: GeneratedCode,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Run only the evaluator agent"""
        return await self.evaluator.execute(generated_code, context)
    
    def get_agent_status(self) -> Dict[str, bool]:
        """Get status of all agents"""
        return {
            "planner": self.planner.is_initialized,
            "coder": self.coder.is_initialized,
            "evaluator": self.evaluator.is_initialized
        }
    
    def reset(self):
        """Reset all agents"""
        self.planner.clear_history()
        self.coder.clear_history()
        self.evaluator.clear_history()
        self.logger.info("All agents reset")