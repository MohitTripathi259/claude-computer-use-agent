"""
Pydantic schemas for the Orchestrator API.

Defines request/response models for all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SessionStatus(str, Enum):
    """Status of an agent session."""
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class CreateSessionRequest(BaseModel):
    """Request to create a new agent session."""
    name: Optional[str] = Field(
        None,
        description="Optional friendly name for the session"
    )
    container_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional container configuration overrides"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "my-research-session"
            }
        }


class CreateSessionResponse(BaseModel):
    """Response with created session details."""
    session_id: str = Field(..., description="Unique session identifier")
    status: SessionStatus = Field(..., description="Current session status")
    container_url: Optional[str] = Field(
        None,
        description="URL of the container's tool server"
    )
    created_at: datetime = Field(..., description="Session creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc12345",
                "status": "running",
                "container_url": "http://localhost:8080",
                "created_at": "2025-01-20T12:00:00Z"
            }
        }


class RunTaskRequest(BaseModel):
    """Request to run a task in a session."""
    task: str = Field(
        ...,
        description="Task description for the agent",
        min_length=1,
        max_length=10000
    )
    # Note: max_iterations is NOT needed with Claude Agent SDK
    # The SDK handles the agentic loop internally

    class Config:
        json_schema_extra = {
            "example": {
                "task": "Navigate to example.com and take a screenshot"
            }
        }


class TaskResult(BaseModel):
    """Result from a completed task."""
    output: str = Field(..., description="Final agent output")
    iterations: int = Field(..., description="Number of iterations used")
    tool_calls: List[str] = Field(
        default_factory=list,
        description="List of tools called during execution"
    )


class RunTaskResponse(BaseModel):
    """Response from running a task."""
    session_id: str = Field(..., description="Session ID")
    task: str = Field(..., description="Original task description")
    result: str = Field(..., description="Final result from the agent")
    tool_calls: int = Field(0, description="Number of tool calls made (approximate)")
    status: str = Field(..., description="Task completion status")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc12345",
                "task": "Navigate to example.com",
                "result": "Successfully navigated to example.com and captured the page.",
                "tool_calls": 5,
                "status": "completed"
            }
        }


class SessionInfo(BaseModel):
    """Detailed information about a session."""
    session_id: str = Field(..., description="Unique session identifier")
    name: Optional[str] = Field(None, description="Friendly name")
    status: SessionStatus = Field(..., description="Current status")
    container_url: Optional[str] = Field(None, description="Container URL")
    task_arn: Optional[str] = Field(None, description="ECS task ARN (if using ECS)")
    created_at: datetime = Field(..., description="Creation timestamp")
    task_count: int = Field(0, description="Number of tasks executed")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc12345",
                "name": "research-session",
                "status": "running",
                "container_url": "http://localhost:8080",
                "created_at": "2025-01-20T12:00:00Z",
                "task_count": 3,
                "last_activity": "2025-01-20T12:15:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service health status")
    version: str = Field("1.0.0", description="API version")
    sessions_active: int = Field(0, description="Number of active sessions")


class ContainerHealthResponse(BaseModel):
    """Container health check response."""
    session_id: str
    container_url: str
    healthy: bool
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")
