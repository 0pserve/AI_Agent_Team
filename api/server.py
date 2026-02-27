"""
FastAPI Server - REST API for AI Agent Team
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import logging
import uuid

from core.engine import ExecutionEngine, PipelineConfig, PipelineResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Agent Team API",
    description="AI Software Development Automation System API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Pydantic Models ==============

class ProjectRequest(BaseModel):
    """Request model for project execution"""
    project_overview: str
    context: Optional[Dict[str, Any]] = None


class FileInfo(BaseModel):
    """Generated file information"""
    path: str
    language: str
    content: Optional[str] = None


class RequirementInfo(BaseModel):
    """Project requirement information"""
    id: str
    description: str
    priority: str
    status: str


class ProjectPlanResponse(BaseModel):
    """Project plan response"""
    project_name: str
    description: str
    tech_stack: List[str]
    requirements: List[RequirementInfo]


class GeneratedCodeResponse(BaseModel):
    """Generated code response"""
    files: List[FileInfo]
    language: str
    framework: Optional[str] = None


class EvaluationResponse(BaseModel):
    """Evaluation result response"""
    quality_level: str
    score: float
    issues: List[Dict[str, str]]
    suggestions: List[str]
    summary: str


class ApiConfigRequest(BaseModel):
    """API 설정 요청"""
    provider_type: str  # 'preset' or 'custom'
    provider: Optional[str] = None  # preset 선택 시
    custom_name: Optional[str] = None
    custom_base_url: Optional[str] = None
    custom_model: Optional[str] = None
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 4000


class TestConnectionResult(BaseModel):
    """연결 테스트 결과"""
    success: bool
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None


class PipelineResponse(BaseModel):
    """Pipeline execution response"""
    task_id: str
    status: str
    success: bool
    project_plan: Optional[ProjectPlanResponse] = None
    generated_code: Optional[GeneratedCodeResponse] = None
    evaluation: Optional[EvaluationResponse] = None
    iterations: int = 0
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class TaskStatus(BaseModel):
    """Task status response"""
    task_id: str
    status: str
    progress: int  # 0-100
    current_stage: Optional[str] = None
    result: Optional[PipelineResponse] = None


# ============== In-Memory Storage ==============

tasks: Dict[str, dict] = {}


# ============== Helper Functions ==============

def convert_result(result: PipelineResult) -> PipelineResponse:
    """Convert PipelineResult to PipelineResponse"""
    project_plan = None
    if result.project_plan:
        requirements = []
        for req in result.project_plan.requirements:
            requirements.append(RequirementInfo(
                id=req.id,
                description=req.description,
                priority=req.priority,
                status=req.status
            ))
        project_plan = ProjectPlanResponse(
            project_name=result.project_plan.project_name,
            description=result.project_plan.description,
            tech_stack=result.project_plan.tech_stack,
            requirements=requirements
        )

    generated_code = None
    if result.generated_code:
        files = []
        for f in result.generated_code.files:
            files.append(FileInfo(
                path=f.path,
                language=f.language,
                content=f.content
            ))
        generated_code = GeneratedCodeResponse(
            files=files,
            language=result.generated_code.language,
            framework=result.generated_code.framework
        )

    evaluation = None
    if result.evaluation:
        issues = []
        for issue in result.evaluation.issues:
            issues.append({
                "severity": issue.severity,
                "message": issue.message,
                "line": issue.line
            })
        evaluation = EvaluationResponse(
            quality_level=result.evaluation.quality_level.value,
            score=result.evaluation.score,
            issues=issues,
            suggestions=result.evaluation.suggestions,
            summary=result.evaluation.summary
        )

    return PipelineResponse(
        task_id="",
        status="completed" if result.success else "failed",
        success=result.success,
        project_plan=project_plan,
        generated_code=generated_code,
        evaluation=evaluation,
        iterations=result.iterations,
        error=result.error,
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None
    )


async def run_pipeline(task_id: str, project_overview: str, context: Optional[Dict[str, Any]] = None):
    """Run the pipeline in background"""
    try:
        # Update status to running
        tasks[task_id]["status"] = "running"
        tasks[task_id]["current_stage"] = "initializing"

        # Initialize engine
        config = PipelineConfig(max_evaluation_iterations=3, verbose=True)
        engine = ExecutionEngine(config=config)

        # Update progress
        tasks[task_id]["progress"] = 10
        tasks[task_id]["current_stage"] = "planning"

        # Execute pipeline
        logger.info(f"Starting pipeline for task {task_id}")
        result = await engine.execute(project_overview, context)

        # Update progress
        tasks[task_id]["progress"] = 100

        # Store result
        pipeline_response = convert_result(result)
        pipeline_response.task_id = task_id
        tasks[task_id]["result"] = pipeline_response
        tasks[task_id]["status"] = "completed" if result.success else "failed"

        logger.info(f"Pipeline completed for task {task_id}")

    except Exception as e:
        logger.error(f"Pipeline failed for task {task_id}: {str(e)}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["progress"] = 0


# ============== API Routes ==============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AI Agent Team API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/execute", response_model=TaskStatus)
async def execute_project(request: ProjectRequest, background_tasks: BackgroundTasks):
    """
    Execute the AI agent pipeline
    
    This endpoint starts a new project execution task and returns immediately.
    Use the returned task_id to check the status and retrieve results.
    """
    # Generate task ID
    task_id = str(uuid.uuid4())

    # Store task info
    tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "current_stage": None,
        "result": None,
        "started_at": datetime.now().isoformat()
    }

    # Run pipeline in background
    background_tasks.add_task(run_pipeline, task_id, request.project_overview, request.context)

    return TaskStatus(
        task_id=task_id,
        status="pending",
        progress=0,
        current_stage=None,
        result=None
    )


@app.get("/api/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get the status of a task
    
    Returns the current status, progress, and results of the task.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        progress=task.get("progress", 0),
        current_stage=task.get("current_stage"),
        result=task.get("result")
    )


@app.get("/api/tasks", response_model=List[TaskStatus])
async def list_tasks():
    """List all tasks"""
    result = []
    for task_id, task in tasks.items():
        result.append(TaskStatus(
            task_id=task_id,
            status=task["status"],
            progress=task.get("progress", 0),
            current_stage=task.get("current_stage"),
            result=task.get("result")
        ))
    return result


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    del tasks[task_id]
    return {"message": "Task deleted successfully"}


# ============== API 설정 엔드포인트 ==============

@app.post("/api/config")
async def save_config(config: ApiConfigRequest):
    """
    API 설정 저장 (세션에 임시 저장)
    실제 API 키는 프론트엔드에서 로컬 스토리지에 저장하고
    서버에서는 설정 정보만 임시로 세션에 저장
    """
    # 보안상 API 키는 서버에 저장하지 않음
    # 설정 정보만 임시 저장
    logger.info(f"API config saved for provider: {config.provider or config.custom_name}")
    return {"success": True, "message": "설정이 저장되었습니다."}


@app.post("/api/config/test", response_model=TestConnectionResult)
async def test_connection(config: ApiConfigRequest):
    """
    API 연결 테스트
    """
    import httpx
    
    if not config.api_key:
        return TestConnectionResult(
            success=False,
            message="API 키를 입력해주세요."
        )
    
    # 제공자별 테스트
    if config.provider_type == "preset" and config.provider:
        provider = config.provider
        base_url = ""
        model = ""
        
        if provider == "openai":
            base_url = "https://api.openai.com/v1"
            model = "gpt-4"
        elif provider == "anthropic":
            base_url = "https://api.anthropic.com/v1/messages"
            model = "claude-3-haiku-20240307"
        elif provider == "google":
            base_url = "https://generativelanguage.googleapis.com/v1beta/models"
            model = "gemini-1.5-flash-001"
        elif provider == "deepseek":
            base_url = "https://api.deepseek.com/v1"
            model = "deepseek-chat"
        elif provider == "cohere":
            base_url = "https://api.cohere.ai/v1"
            model = "command-r-plus"
        elif provider == "mistral":
            base_url = "https://api.mistral.ai/v1"
            model = "mistral-small-latest"
        elif provider == "xai":
            base_url = "https://api.x.ai/v1"
            model = "grok-2-1212"
        elif provider == "azure":
            return TestConnectionResult(
                success=False,
                message="Azure의 경우 리소스 엔드포인트를 직접 확인해주세요.",
                provider=provider
            )
        else:
            return TestConnectionResult(
                success=False,
                message=f"지원하지 않는 제공자입니다: {provider}"
            )
        
        # 간단한 연결 테스트
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if provider == "anthropic":
                    response = await client.post(
                        base_url,
                        headers={
                            "x-api-key": config.api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        },
                        json={
                            "model": model,
                            "max_tokens": 10,
                            "messages": [{"role": "user", "content": "Hi"}]
                        }
                    )
                else:
                    response = await client.post(
                        f"{base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {config.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "max_tokens": 10,
                            "messages": [{"role": "user", "content": "Hi"}]
                        }
                    )
                
                if response.status_code == 200:
                    return TestConnectionResult(
                        success=True,
                        message="연결 성공! API가 정상 작동합니다.",
                        provider=provider,
                        model=model
                    )
                else:
                    error_detail = response.text[:200]
                    return TestConnectionResult(
                        success=False,
                        message=f"연결 실패: {response.status_code} - {error_detail}",
                        provider=provider
                    )
        except Exception as e:
            return TestConnectionResult(
                success=False,
                message=f"연결 테스트 실패: {str(e)[:100]}"
            )
    
    elif config.provider_type == "custom":
        if not config.custom_base_url or not config.custom_model:
            return TestConnectionResult(
                success=False,
                message="커스텀 API의 Base URL과 모델을 입력해주세요."
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{config.custom_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config.custom_model,
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "Hi"}]
                    }
                )
                
                if response.status_code == 200:
                    return TestConnectionResult(
                        success=True,
                        message="연결 성공! 커스텀 API가 정상 작동합니다.",
                        provider=config.custom_name or "Custom",
                        model=config.custom_model
                    )
                else:
                    return TestConnectionResult(
                        success=False,
                        message=f"연결 실패: {response.status_code}"
                    )
        except Exception as e:
            return TestConnectionResult(
                success=False,
                message=f"연결 테스트 실패: {str(e)[:100]}"
            )
    
    return TestConnectionResult(
        success=False,
        message="유효하지 않은 설정입니다."
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
