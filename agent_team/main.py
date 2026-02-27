"""
AI Software Development Automation System
Main entry point

This system implements a 3-stage AI model pipeline:
1. Planner Agent - Analyzes requirements and creates project plans
2. Coder Agent - Generates code based on plans
3. Evaluator Agent - Evaluates code quality and provides feedback
"""
import asyncio
import argparse
import logging
import sys
from typing import Optional

from config import Settings
from core import ExecutionEngine, Memory
from agents import PlannerAgent, CoderAgent, EvaluatorAgent


def setup_logging(verbose: bool = True):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


async def run_interactive():
    """Run in interactive mode"""
    print("=" * 60)
    print("AI Software Development Automation System")
    print("=" * 60)
    print()
    print("This system uses a 3-stage AI pipeline:")
    print("  1. Planner - Analyzes requirements and creates plans")
    print("  2. Coder - Generates code based on plans")
    print("  3. Evaluator - Evaluates code quality")
    print()
    
    # Get project overview from user
    project_overview = input("Enter your project description: ").strip()
    
    if not project_overview:
        print("Error: Project description cannot be empty")
        return
    
    print("\nInitializing agents...")
    
    # Initialize engine
    engine = ExecutionEngine()
    
    print("Running pipeline...\n")
    
    # Execute pipeline
    result = await engine.execute(project_overview)
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if result.success:
        print("✅ Pipeline completed successfully!")
    else:
        print("❌ Pipeline failed")
        if result.error:
            print(f"Error: {result.error}")
    
    if result.project_plan:
        print(f"\nProject: {result.project_plan.project_name}")
        print(f"Tech Stack: {result.project_plan.tech_stack}")
        print(f"Requirements: {len(result.project_plan.requirements)}")
    
    if result.generated_code:
        print(f"\nGenerated Files: {len(result.generated_code.files)}")
        for f in result.generated_code.files:
            print(f"  - {f.path} ({f.language})")
    
    if result.evaluation:
        print(f"\nEvaluation:")
        print(f"  Quality Level: {result.evaluation.quality_level.value}")
        print(f"  Issues Found: {len(result.evaluation.issues)}")
        print(f"  Summary: {result.evaluation.summary}")
        
        if result.evaluation.suggestions:
            print("\nSuggestions:")
            for s in result.evaluation.suggestions:
                print(f"  - {s}")
    
    print(f"\nIterations: {result.iterations}")
    print("=" * 60)


async def run_demo():
    """Run a demo with sample project"""
    print("Running demo with sample project...")
    
    # Sample project overview
    project_overview = "Create a REST API for a todo list application with FastAPI"
    
    # Initialize engine
    engine = ExecutionEngine()
    
    # Execute
    result = await engine.execute(project_overview)
    
    # Display results
    print("\n" + "=" * 60)
    print("DEMO RESULTS")
    print("=" * 60)
    
    print(f"Success: {result.success}")
    print(f"Iterations: {result.iterations}")
    
    if result.project_plan:
        print(f"\nProject: {result.project_plan.project_name}")
        print(f"Tech Stack: {result.project_plan.tech_stack}")
    
    if result.generated_code:
        print(f"\nGenerated {len(result.generated_code.files)} files")
    
    if result.evaluation:
        print(f"\nEvaluation: {result.evaluation.quality_level.value}")
        print(f"Issues: {len(result.evaluation.issues)}")
    
    print("=" * 60)


async def run_planner_only(overview: str):
    """Run only the planner agent"""
    print(f"Running planner for: {overview}")
    
    planner = PlannerAgent()
    planner.initialize()
    
    result = await planner.execute(overview)
    
    if result.success:
        plan = result.content
        print(f"\nProject: {plan.project_name}")
        print(f"Tech Stack: {plan.tech_stack}")
        print(f"Requirements: {len(plan.requirements)}")
        print(f"Implementation Steps: {len(plan.implementation_steps)}")
    else:
        print(f"Error: {result.error}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI Software Development Automation System"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Run demo with sample project"
    )
    
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Run only the planner agent"
    )
    
    parser.add_argument(
        "--overview",
        type=str,
        help="Project overview (for plan-only mode)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Run appropriate mode
    if args.demo:
        asyncio.run(run_demo())
    elif args.plan_only:
        if not args.overview:
            print("Error: --overview required for plan-only mode")
            sys.exit(1)
        asyncio.run(run_planner_only(args.overview))
    elif args.interactive:
        asyncio.run(run_interactive())
    else:
        # Default to demo
        asyncio.run(run_demo())


if __name__ == "__main__":
    main()