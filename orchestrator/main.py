"""
Orchestrator API.

FastAPI application that provides endpoints for managing Claude
computer-use agent sessions and running tasks.

Uses Claude Agent SDK (ClaudeSDKClient + ClaudeAgentOptions) for agent execution.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
import logging
import httpx
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.schemas import (
    CreateSessionRequest, CreateSessionResponse,
    RunTaskRequest, RunTaskResponse,
    SessionStatus, SessionInfo,
    HealthResponse, ContainerHealthResponse, ErrorResponse
)
from orchestrator.session_manager import SessionManager
from orchestrator.ecs_manager import ECSManager
from orchestrator.s3_storage import upload_task_screenshots, list_session_screenshots

# Import the SDK-based agent
from agent.computer_use_agent import ComputerUseAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize managers
session_manager = SessionManager()
ecs_manager = ECSManager()

# Store active agents
active_agents: dict = {}

# HTTP client for health checks
http_client = httpx.AsyncClient(timeout=10.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Computer-Use Orchestrator API (SDK Version)...")
    yield
    logger.info("Shutting down...")
    # Cleanup all active agents
    for session_id, agent_info in list(active_agents.items()):
        try:
            await agent_info["agent"].cleanup()
            if agent_info.get("task_arn"):
                await ecs_manager.stop_container(agent_info["task_arn"])
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
    # Close HTTP client
    await http_client.aclose()


# Create FastAPI app
app = FastAPI(
    title="Computer-Use Agent Orchestrator (SDK)",
    description="""
    API for managing Claude computer-use agent sessions.

    Uses Claude Agent SDK (ClaudeSDKClient + ClaudeAgentOptions) for execution.

    This API allows you to:
    - Create agent sessions with containerized compute environments
    - Run tasks using Claude's computer-use capabilities
    - Monitor session status and health
    """,
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================
# Health Endpoints
# ===================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the status of the orchestrator and number of active sessions.
    """
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        sessions_active=session_manager.get_active_count()
    )


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Computer-Use Agent Orchestrator",
        "version": "2.0.0",
        "agent_type": "Claude Agent SDK",
        "docs": "/docs",
        "health": "/health"
    }


# ===================
# Session Endpoints
# ===================

@app.post(
    "/sessions",
    response_model=CreateSessionResponse,
    tags=["Sessions"],
    responses={500: {"model": ErrorResponse}}
)
async def create_session(request: CreateSessionRequest):
    """
    Create a new agent session.

    This spawns a container (or uses local docker-compose container)
    for the agent to work in. The session can then be used to run tasks.
    """
    try:
        logger.info(f"Creating session: {request.name or 'unnamed'}")

        # Create session record
        session = session_manager.create_session(name=request.name)

        # Spawn container
        container_info = await ecs_manager.spawn_container(session.session_id)

        # Update session with container info
        session_manager.update_session(
            session.session_id,
            container_url=container_info["container_url"],
            task_arn=container_info.get("task_arn"),
            status=SessionStatus.RUNNING
        )

        # Create SDK-based agent for this session
        agent = ComputerUseAgent(container_url=container_info["container_url"])
        logger.info(f"Created ComputerUseAgent (SDK) for session {session.session_id}")

        active_agents[session.session_id] = {
            "agent": agent,
            "task_arn": container_info.get("task_arn"),
            "container_url": container_info["container_url"]
        }

        logger.info(f"Session created: {session.session_id}")

        return CreateSessionResponse(
            session_id=session.session_id,
            status=SessionStatus.RUNNING,
            container_url=container_info["container_url"],
            created_at=session.created_at
        )

    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/sessions",
    response_model=list[SessionInfo],
    tags=["Sessions"]
)
async def list_sessions(status: SessionStatus = None):
    """
    List all sessions.

    Optionally filter by status.
    """
    return session_manager.list_sessions(status=status)


@app.get(
    "/sessions/{session_id}",
    response_model=SessionInfo,
    tags=["Sessions"],
    responses={404: {"model": ErrorResponse}}
)
async def get_session(session_id: str):
    """
    Get details of a specific session.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete(
    "/sessions/{session_id}",
    tags=["Sessions"],
    responses={404: {"model": ErrorResponse}}
)
async def delete_session(session_id: str, background_tasks: BackgroundTasks):
    """
    Delete a session and clean up resources.

    This stops the container and removes the session.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Clean up agent
    if session_id in active_agents:
        agent_info = active_agents[session_id]

        try:
            await agent_info["agent"].cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up agent: {e}")

        # Stop container in background
        if agent_info.get("task_arn"):
            background_tasks.add_task(
                ecs_manager.stop_container,
                agent_info["task_arn"]
            )

        del active_agents[session_id]

    # Update and delete session
    session_manager.update_session(session_id, status=SessionStatus.TERMINATED)
    session_manager.delete_session(session_id)

    logger.info(f"Session deleted: {session_id}")

    return {"status": "deleted", "session_id": session_id}


# ===================
# Task Endpoints
# ===================

@app.post(
    "/sessions/{session_id}/run",
    response_model=RunTaskResponse,
    tags=["Tasks"],
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def run_task(session_id: str, request: RunTaskRequest):
    """
    Run a task in an existing session using Claude Agent SDK.

    The agent will execute the task using computer-use tools
    (bash, browser, file operations, screenshots).

    With SDK, the agentic loop is handled internally - no manual iteration management.
    """
    # Verify session exists
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail=f"Session is not running (status: {session.status})"
        )

    # Get agent
    if session_id not in active_agents:
        raise HTTPException(
            status_code=500,
            detail="Agent not found for session"
        )

    agent_info = active_agents[session_id]
    agent: ComputerUseAgent = agent_info["agent"]

    logger.info(f"Running task in session {session_id}: {request.task[:100]}...")

    try:
        # Run the task using SDK (handles agentic loop internally)
        result = await agent.run(request.task)

        # Update session stats
        session_manager.increment_task_count(session_id)

        # Upload screenshots to S3
        container_url = agent_info.get("container_url")
        screenshot_urls = []
        if container_url:
            try:
                screenshot_urls = await upload_task_screenshots(
                    container_url, session_id, http_client
                )
                logger.info(f"Uploaded {len(screenshot_urls)} screenshots to S3")
            except Exception as e:
                logger.error(f"Failed to upload screenshots: {e}")

        logger.info(f"Task completed in session {session_id}")

        return RunTaskResponse(
            session_id=session_id,
            task=request.task,
            result=result,
            tool_calls=len(agent.conversation_history) // 2,
            status="completed",
            screenshot_urls=screenshot_urls
        )

    except Exception as e:
        logger.error(f"Task failed: {e}")
        return RunTaskResponse(
            session_id=session_id,
            task=request.task,
            result="",
            tool_calls=0,
            status="error",
            error=str(e)
        )


@app.post(
    "/sessions/{session_id}/reset",
    tags=["Tasks"],
    responses={404: {"model": ErrorResponse}}
)
async def reset_session(session_id: str):
    """
    Reset the conversation history for a session.

    This clears the agent's memory while keeping the session active.
    """
    if session_id not in active_agents:
        raise HTTPException(status_code=404, detail="Session not found")

    agent_info = active_agents[session_id]
    agent: ComputerUseAgent = agent_info["agent"]
    agent.reset_conversation()

    logger.info(f"Session {session_id} conversation reset")

    return {"status": "reset", "session_id": session_id}


# ===================
# Container Health
# ===================

@app.get(
    "/sessions/{session_id}/container-health",
    response_model=ContainerHealthResponse,
    tags=["Health"],
    responses={404: {"model": ErrorResponse}}
)
async def check_container_health(session_id: str):
    """
    Check the health of a session's container.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_id not in active_agents:
        return ContainerHealthResponse(
            session_id=session_id,
            container_url=session.container_url or "",
            healthy=False,
            details={"error": "Agent not active"}
        )

    agent_info = active_agents[session_id]
    container_url = agent_info.get("container_url", session.container_url)

    # Direct health check to container (SDK agent doesn't have executor)
    try:
        response = await http_client.get(f"{container_url}/health")
        healthy = response.status_code == 200
    except Exception as e:
        logger.error(f"Container health check failed: {e}")
        healthy = False

    return ContainerHealthResponse(
        session_id=session_id,
        container_url=container_url or "",
        healthy=healthy,
        details={"container_url": container_url}
    )


# ===================
# Direct Task Endpoint (No Session)
# ===================

@app.post("/task", tags=["Tasks"])
async def run_direct_task(request: RunTaskRequest):
    """
    Run a task directly without creating a session.

    Uses the default local container (http://localhost:8080).
    Good for quick testing.
    """
    container_url = os.getenv("LOCAL_CONTAINER_URL", "http://localhost:8080")
    session_id = f"direct-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    logger.info(f"Running direct task: {request.task[:100]}...")

    try:
        # Create a temporary agent
        agent = ComputerUseAgent(container_url=container_url)

        # Run the task (SDK handles agentic loop internally)
        result = await agent.run(request.task)

        # Upload screenshots to S3
        screenshot_urls = []
        try:
            screenshot_urls = await upload_task_screenshots(
                container_url, session_id, http_client
            )
            logger.info(f"Uploaded {len(screenshot_urls)} screenshots to S3")
        except Exception as e:
            logger.error(f"Failed to upload screenshots: {e}")

        # Cleanup
        await agent.cleanup()

        return {
            "task": request.task,
            "result": result,
            "status": "completed",
            "screenshot_urls": screenshot_urls
        }

    except Exception as e:
        logger.error(f"Direct task failed: {e}")
        return {
            "task": request.task,
            "result": "",
            "status": "error",
            "error": str(e)
        }


# ===================
# Main Entry Point
# ===================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
