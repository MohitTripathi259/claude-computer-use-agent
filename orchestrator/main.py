"""
Orchestrator API.

FastAPI application that provides endpoints for managing Claude
computer-use agent sessions and running tasks.

The agent uses Anthropic's built-in computer-use tool types
(computer, bash, text_editor) executed against containerized
environments (local Docker or AWS ECS Fargate).
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

from agent.computer_use_agent import ComputerUseAgent

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("\n" + "=" * 70)
print("  ORCHESTRATOR — LOADING MODULES")
print("=" * 70)

# Initialize managers
print("  [init] Creating SessionManager...")
session_manager = SessionManager()
print("  [init] SessionManager created")

print("  [init] Creating ECSManager...")
ecs_manager = ECSManager()
print(f"  [init] ECSManager created (local_mode={ecs_manager.is_local_mode()})")

# Store active agents
active_agents: dict = {}
print("  [init] Active agents store initialized")

# HTTP client for health checks
http_client = httpx.AsyncClient(timeout=10.0)
print("  [init] HTTP client for health checks created (timeout=10s)")
print("=" * 70 + "\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("\n" + "=" * 70)
    print("  ORCHESTRATOR API — STARTING UP")
    print("=" * 70)
    print(f"  Time: {datetime.now().isoformat()}")
    print(f"  Local mode: {ecs_manager.is_local_mode()}")
    print(f"  Docs available at: http://localhost:8000/docs")
    print("=" * 70 + "\n")
    logger.info("Starting Computer-Use Orchestrator API...")
    yield
    print("\n" + "=" * 70)
    print("  ORCHESTRATOR API — SHUTTING DOWN")
    print("=" * 70)
    logger.info("Shutting down...")
    # Cleanup all active agents
    for session_id, agent_info in list(active_agents.items()):
        try:
            print(f"  [shutdown] Cleaning up session {session_id}...")
            await agent_info["agent"].cleanup()
            if agent_info.get("task_arn"):
                print(f"  [shutdown] Stopping ECS task {agent_info['task_arn']}...")
                await ecs_manager.stop_container(agent_info["task_arn"])
        except Exception as e:
            print(f"  [shutdown] ERROR cleaning session {session_id}: {e}")
            logger.error(f"Error cleaning up session {session_id}: {e}")
    # Close HTTP client
    await http_client.aclose()
    print("  [shutdown] HTTP client closed")
    print("=" * 70 + "\n")


# Create FastAPI app
app = FastAPI(
    title="Computer-Use Agent Orchestrator",
    description="""
    API for managing Claude computer-use agent sessions.

    Uses Anthropic's built-in computer-use tool types (computer, bash, text_editor)
    executed against containerized environments.

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
print("  [init] CORS middleware added (allow_origins=*)")


# ===================
# Health Endpoints
# ===================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the status of the orchestrator and number of active sessions.
    """
    active_count = session_manager.get_active_count()
    print(f"  [GET /health] Active sessions: {active_count}")
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        sessions_active=active_count
    )


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    print(f"  [GET /] Root endpoint hit")
    return {
        "name": "Computer-Use Agent Orchestrator",
        "version": "2.0.0",
        "agent_type": "Anthropic Computer-Use API",
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
        print(f"\n{'=' * 60}")
        print(f"  POST /sessions  — Creating new session")
        print(f"{'=' * 60}")
        print(f"  Session name: {request.name or '(unnamed)'}")
        print(f"  Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Creating session: {request.name or 'unnamed'}")

        # Create session record
        print(f"  [step 1/4] Creating session record in SessionManager...")
        session = session_manager.create_session(name=request.name)
        print(f"  [step 1/4] Session ID: {session.session_id}")

        # Spawn container
        print(f"  [step 2/4] Spawning container via ECSManager...")
        container_info = await ecs_manager.spawn_container(session.session_id)
        print(f"  [step 2/4] Container URL: {container_info['container_url']}")
        print(f"  [step 2/4] Task ARN: {container_info.get('task_arn', 'None (local mode)')}")

        # Update session with container info
        print(f"  [step 3/4] Updating session with container info...")
        session_manager.update_session(
            session.session_id,
            container_url=container_info["container_url"],
            task_arn=container_info.get("task_arn"),
            status=SessionStatus.RUNNING
        )
        print(f"  [step 3/4] Session status → RUNNING")

        # Create agent for this session
        print(f"  [step 4/4] Creating ComputerUseAgent for this session...")
        agent = ComputerUseAgent(container_url=container_info["container_url"])
        print(f"  [step 4/4] Agent created successfully")

        active_agents[session.session_id] = {
            "agent": agent,
            "task_arn": container_info.get("task_arn"),
            "container_url": container_info["container_url"]
        }

        print(f"\n  SESSION CREATED SUCCESSFULLY")
        print(f"  Session ID:     {session.session_id}")
        print(f"  Container URL:  {container_info['container_url']}")
        print(f"  Status:         RUNNING")
        print(f"  Active agents:  {len(active_agents)}")
        print(f"{'=' * 60}\n")

        logger.info(f"Session created: {session.session_id}")

        return CreateSessionResponse(
            session_id=session.session_id,
            status=SessionStatus.RUNNING,
            container_url=container_info["container_url"],
            created_at=session.created_at
        )

    except Exception as e:
        print(f"  [ERROR] Failed to create session: {e}")
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
    sessions = session_manager.list_sessions(status=status)
    print(f"  [GET /sessions] Returning {len(sessions)} sessions (filter={status})")
    return sessions


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
    print(f"  [GET /sessions/{session_id}] Looking up session...")
    session = session_manager.get_session(session_id)
    if not session:
        print(f"  [GET /sessions/{session_id}] NOT FOUND")
        raise HTTPException(status_code=404, detail="Session not found")
    print(f"  [GET /sessions/{session_id}] Found: status={session.status}, "
          f"tasks={session.task_count}")
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
    print(f"\n  [DELETE /sessions/{session_id}] Deleting session...")
    session = session_manager.get_session(session_id)
    if not session:
        print(f"  [DELETE] Session not found")
        raise HTTPException(status_code=404, detail="Session not found")

    # Clean up agent
    if session_id in active_agents:
        agent_info = active_agents[session_id]

        try:
            print(f"  [DELETE] Cleaning up agent...")
            await agent_info["agent"].cleanup()
            print(f"  [DELETE] Agent cleaned up")
        except Exception as e:
            print(f"  [DELETE] Error cleaning up agent: {e}")
            logger.error(f"Error cleaning up agent: {e}")

        # Stop container in background
        if agent_info.get("task_arn"):
            print(f"  [DELETE] Scheduling ECS task stop in background...")
            background_tasks.add_task(
                ecs_manager.stop_container,
                agent_info["task_arn"]
            )

        del active_agents[session_id]
        print(f"  [DELETE] Agent removed from active_agents")

    # Update and delete session
    session_manager.update_session(session_id, status=SessionStatus.TERMINATED)
    session_manager.delete_session(session_id)

    print(f"  [DELETE] Session {session_id} deleted successfully")
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
    Run a task in an existing session.

    The agent will execute the task using Anthropic's built-in
    computer-use tools (computer, bash, text_editor).
    """
    print(f"\n{'#' * 60}")
    print(f"  POST /sessions/{session_id}/run")
    print(f"{'#' * 60}")
    print(f"  Task: {request.task[:200]}")
    print(f"  Timestamp: {datetime.now().isoformat()}")

    # Verify session exists
    session = session_manager.get_session(session_id)
    if not session:
        print(f"  [ERROR] Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")
    print(f"  [OK] Session found: status={session.status}")

    if session.status != SessionStatus.RUNNING:
        print(f"  [ERROR] Session not running (status={session.status})")
        raise HTTPException(
            status_code=400,
            detail=f"Session is not running (status: {session.status})"
        )

    # Get agent
    if session_id not in active_agents:
        print(f"  [ERROR] No active agent for session {session_id}")
        raise HTTPException(
            status_code=500,
            detail="Agent not found for session"
        )

    agent_info = active_agents[session_id]
    agent: ComputerUseAgent = agent_info["agent"]
    print(f"  [OK] Agent found for session")
    print(f"  [OK] Container URL: {agent_info.get('container_url')}")

    logger.info(f"Running task in session {session_id}: {request.task[:100]}...")
    print(f"\n  >>> HANDING OFF TO AGENT (this may take a while)... <<<\n")

    try:
        task_start = datetime.now()
        result = await agent.run(request.task)
        task_elapsed = (datetime.now() - task_start).total_seconds()

        print(f"\n  >>> AGENT RETURNED <<<")
        print(f"  Task execution time: {task_elapsed:.1f}s")
        print(f"  Result length: {len(result)} chars")
        print(f"  Result preview: {result[:300]}")

        # Update session stats
        session_manager.increment_task_count(session_id)
        print(f"  [OK] Session task count incremented")

        # Upload screenshots to S3
        container_url = agent_info.get("container_url")
        screenshot_urls = []
        if container_url:
            try:
                print(f"  [S3] Uploading screenshots...")
                screenshot_urls = await upload_task_screenshots(
                    container_url, session_id, http_client
                )
                print(f"  [S3] Uploaded {len(screenshot_urls)} screenshots")
                logger.info(f"Uploaded {len(screenshot_urls)} screenshots to S3")
            except Exception as e:
                print(f"  [S3] Failed to upload screenshots: {e}")
                logger.error(f"Failed to upload screenshots: {e}")

        print(f"\n  TASK COMPLETED SUCCESSFULLY")
        print(f"  Session: {session_id}")
        print(f"  Tool calls: ~{agent.last_tool_count}")
        print(f"  Status: completed")
        print(f"{'#' * 60}\n")

        logger.info(f"Task completed in session {session_id}")

        return RunTaskResponse(
            session_id=session_id,
            task=request.task,
            result=result,
            tool_calls=agent.last_tool_count,
            status="completed",
            screenshot_urls=screenshot_urls
        )

    except Exception as e:
        print(f"\n  TASK FAILED")
        print(f"  Error: {e}")
        print(f"{'#' * 60}\n")
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
    print(f"  [POST /sessions/{session_id}/reset] Resetting conversation...")
    if session_id not in active_agents:
        print(f"  [reset] Session not found in active agents")
        raise HTTPException(status_code=404, detail="Session not found")

    agent_info = active_agents[session_id]
    agent: ComputerUseAgent = agent_info["agent"]
    agent.reset_conversation()

    print(f"  [reset] Conversation reset for session {session_id}")
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
    print(f"  [GET /sessions/{session_id}/container-health] Checking...")
    session = session_manager.get_session(session_id)
    if not session:
        print(f"  [container-health] Session not found")
        raise HTTPException(status_code=404, detail="Session not found")

    if session_id not in active_agents:
        print(f"  [container-health] Agent not active")
        return ContainerHealthResponse(
            session_id=session_id,
            container_url=session.container_url or "",
            healthy=False,
            details={"error": "Agent not active"}
        )

    agent_info = active_agents[session_id]
    container_url = agent_info.get("container_url", session.container_url)

    # Direct health check to container
    try:
        print(f"  [container-health] GET {container_url}/health")
        response = await http_client.get(f"{container_url}/health")
        healthy = response.status_code == 200
        print(f"  [container-health] Response: {response.status_code} → healthy={healthy}")
    except Exception as e:
        print(f"  [container-health] FAILED: {e}")
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

    print(f"\n{'#' * 60}")
    print(f"  POST /task  — Direct task (no session)")
    print(f"{'#' * 60}")
    print(f"  Task: {request.task[:200]}")
    print(f"  Container URL: {container_url}")
    print(f"  Temp session ID: {session_id}")
    print(f"  Timestamp: {datetime.now().isoformat()}")

    logger.info(f"Running direct task: {request.task[:100]}...")

    try:
        # Create a temporary agent
        print(f"\n  [step 1] Creating temporary agent...")
        agent = ComputerUseAgent(container_url=container_url)
        print(f"  [step 1] Agent created")

        print(f"\n  >>> HANDING OFF TO AGENT (this may take a while)... <<<\n")
        task_start = datetime.now()
        result = await agent.run(request.task)
        task_elapsed = (datetime.now() - task_start).total_seconds()

        print(f"\n  >>> AGENT RETURNED <<<")
        print(f"  Task execution time: {task_elapsed:.1f}s")
        print(f"  Result length: {len(result)} chars")
        print(f"  Result preview: {result[:300]}")

        # Upload screenshots to S3
        screenshot_urls = []
        try:
            print(f"  [S3] Uploading screenshots...")
            screenshot_urls = await upload_task_screenshots(
                container_url, session_id, http_client
            )
            print(f"  [S3] Uploaded {len(screenshot_urls)} screenshots")
            logger.info(f"Uploaded {len(screenshot_urls)} screenshots to S3")
        except Exception as e:
            print(f"  [S3] Failed to upload screenshots (non-fatal): {e}")
            logger.error(f"Failed to upload screenshots: {e}")

        # Cleanup
        print(f"  [cleanup] Cleaning up temporary agent...")
        await agent.cleanup()
        print(f"  [cleanup] Done")

        print(f"\n  DIRECT TASK COMPLETED")
        print(f"  Status: completed")
        print(f"  Screenshots: {len(screenshot_urls)}")
        print(f"{'#' * 60}\n")

        return {
            "task": request.task,
            "result": result,
            "status": "completed",
            "screenshot_urls": screenshot_urls
        }

    except Exception as e:
        print(f"\n  DIRECT TASK FAILED")
        print(f"  Error: {e}")
        print(f"{'#' * 60}\n")
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
    print("\n" + "=" * 70)
    print("  STARTING UVICORN SERVER")
    print("  Host: 0.0.0.0 | Port: 8000 | Reload: True")
    print("=" * 70 + "\n")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
