"""
Local Integration Tests.

Tests the full agent flow using local docker-compose containers.
Run docker-compose up -d before running these tests.

Usage:
    pytest tests/test_local.py -v
"""

import pytest
import httpx
import asyncio
import os

# Configuration
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
CONTAINER_URL = os.getenv("CONTAINER_URL", "http://localhost:8080")


@pytest.fixture
def anyio_backend():
    return "asyncio"


class TestContainerHealth:
    """Test container health and basic operations."""

    @pytest.mark.asyncio
    async def test_container_health(self):
        """Test that the container is healthy."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{CONTAINER_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "display" in data

    @pytest.mark.asyncio
    async def test_container_root(self):
        """Test container root endpoint."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{CONTAINER_URL}/")
            assert response.status_code == 200
            data = response.json()
            assert "endpoints" in data

    @pytest.mark.asyncio
    async def test_bash_command(self):
        """Test bash command execution."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CONTAINER_URL}/tools/bash",
                json={"command": "echo 'Hello, World!'"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "Hello, World!" in data["stdout"]
            assert data["return_code"] == 0

    @pytest.mark.asyncio
    async def test_file_operations(self):
        """Test file read/write operations."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Write file
            test_content = "Test content for file operations"
            write_response = await client.post(
                f"{CONTAINER_URL}/tools/file/write",
                json={"path": "/workspace/test_file.txt", "content": test_content}
            )
            assert write_response.status_code == 200

            # Read file
            read_response = await client.post(
                f"{CONTAINER_URL}/tools/file/read",
                json={"path": "/workspace/test_file.txt"}
            )
            assert read_response.status_code == 200
            data = read_response.json()
            assert data["content"] == test_content

            # List directory
            list_response = await client.get(
                f"{CONTAINER_URL}/tools/file/list",
                params={"path": "/workspace"}
            )
            assert list_response.status_code == 200
            files = list_response.json()["files"]
            assert any(f["name"] == "test_file.txt" for f in files)

    @pytest.mark.asyncio
    async def test_screenshot(self):
        """Test screenshot capture."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{CONTAINER_URL}/tools/screenshot")
            assert response.status_code == 200
            data = response.json()
            assert "image_base64" in data
            assert data["width"] > 0
            assert data["height"] > 0


class TestOrchestratorHealth:
    """Test orchestrator API health."""

    @pytest.mark.asyncio
    async def test_orchestrator_health(self):
        """Test that the orchestrator is healthy."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_orchestrator_root(self):
        """Test orchestrator root endpoint."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/")
            assert response.status_code == 200
            data = response.json()
            assert "name" in data


class TestSessionManagement:
    """Test session creation and management."""

    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test session creation."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/sessions",
                json={"name": "test-session"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert data["status"] == "running"

            # Clean up
            session_id = data["session_id"]
            await client.delete(f"{ORCHESTRATOR_URL}/sessions/{session_id}")

    @pytest.mark.asyncio
    async def test_list_sessions(self):
        """Test listing sessions."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/sessions")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_session_lifecycle(self):
        """Test full session lifecycle."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Create session
            create_response = await client.post(
                f"{ORCHESTRATOR_URL}/sessions",
                json={"name": "lifecycle-test"}
            )
            assert create_response.status_code == 200
            session_id = create_response.json()["session_id"]

            # Get session
            get_response = await client.get(
                f"{ORCHESTRATOR_URL}/sessions/{session_id}"
            )
            assert get_response.status_code == 200
            assert get_response.json()["session_id"] == session_id

            # Check container health
            health_response = await client.get(
                f"{ORCHESTRATOR_URL}/sessions/{session_id}/container-health"
            )
            assert health_response.status_code == 200
            assert health_response.json()["healthy"] == True

            # Delete session
            delete_response = await client.delete(
                f"{ORCHESTRATOR_URL}/sessions/{session_id}"
            )
            assert delete_response.status_code == 200

            # Verify deleted
            get_response = await client.get(
                f"{ORCHESTRATOR_URL}/sessions/{session_id}"
            )
            assert get_response.status_code == 404


class TestBrowserOperations:
    """Test browser operations via container."""

    @pytest.mark.asyncio
    async def test_browser_navigate(self):
        """Test browser navigation."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{CONTAINER_URL}/tools/browser",
                json={
                    "action": "navigate",
                    "params": {"url": "https://example.com"}
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "example.com" in data["data"]["url"]

    @pytest.mark.asyncio
    async def test_browser_get_content(self):
        """Test getting page content."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # First navigate
            await client.post(
                f"{CONTAINER_URL}/tools/browser",
                json={
                    "action": "navigate",
                    "params": {"url": "https://example.com"}
                }
            )

            # Get content
            response = await client.post(
                f"{CONTAINER_URL}/tools/browser",
                json={
                    "action": "get_content",
                    "params": {"text": True}
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "Example Domain" in data["data"]["text_content"]

    @pytest.mark.asyncio
    async def test_browser_screenshot(self):
        """Test browser screenshot."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Navigate first
            await client.post(
                f"{CONTAINER_URL}/tools/browser",
                json={
                    "action": "navigate",
                    "params": {"url": "https://example.com"}
                }
            )

            # Take screenshot
            response = await client.post(
                f"{CONTAINER_URL}/tools/browser",
                json={"action": "screenshot", "params": {}}
            )
            assert response.status_code == 200
            data = response.json()
            assert "image_base64" in data["data"]


# Skip the full agent test by default (requires API key)
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestAgentExecution:
    """Test full agent execution (requires API key)."""

    @pytest.mark.asyncio
    async def test_run_simple_task(self):
        """Test running a simple agent task."""
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Create session
            create_response = await client.post(
                f"{ORCHESTRATOR_URL}/sessions",
                json={"name": "agent-test"}
            )
            assert create_response.status_code == 200
            session_id = create_response.json()["session_id"]

            try:
                # Run a simple task
                task_response = await client.post(
                    f"{ORCHESTRATOR_URL}/sessions/{session_id}/run",
                    json={
                        "task": "Run 'echo Hello' in the terminal and tell me what you see.",
                        "max_iterations": 5
                    }
                )
                assert task_response.status_code == 200
                data = task_response.json()
                assert data["status"] in ["completed", "error"]

            finally:
                # Clean up
                await client.delete(f"{ORCHESTRATOR_URL}/sessions/{session_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
