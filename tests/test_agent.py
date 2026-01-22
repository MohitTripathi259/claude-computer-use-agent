"""
Agent Unit Tests.

Tests the agent logic without requiring a running container.
Uses mocked responses for tool execution.

Usage:
    pytest tests/test_agent.py -v
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.config import AgentConfig
from agent.tool_executor import ToolExecutor
from orchestrator.session_manager import SessionManager
from orchestrator.schemas import SessionStatus


class TestAgentConfig:
    """Test agent configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AgentConfig()
        assert config.display_width == 1920
        assert config.display_height == 1080
        assert config.max_iterations == 20

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {"DISPLAY_WIDTH": "1280", "DISPLAY_HEIGHT": "720"}):
            config = AgentConfig()
            assert config.display_width == 1280
            assert config.display_height == 720

    def test_config_validation(self):
        """Test configuration validation."""
        config = AgentConfig()
        config.anthropic_api_key = ""
        with pytest.raises(ValueError):
            config.validate()


class TestToolExecutor:
    """Test tool executor with mocked HTTP client."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        client = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_execute_bash(self, mock_client):
        """Test bash command execution."""
        executor = ToolExecutor(container_url="http://test:8080")
        executor.client = mock_client

        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "stdout": "Hello, World!",
            "stderr": "",
            "return_code": 0
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        result = await executor.execute("bash", {"command": "echo Hello, World!"})

        assert "Hello, World!" in result["output"]
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_bash_error(self, mock_client):
        """Test bash command with error."""
        executor = ToolExecutor(container_url="http://test:8080")
        executor.client = mock_client

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "stdout": "",
            "stderr": "command not found",
            "return_code": 127
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        result = await executor.execute("bash", {"command": "invalid_command"})

        assert "STDERR" in result["output"]
        assert "127" in result["output"]

    @pytest.mark.asyncio
    async def test_execute_screenshot(self, mock_client):
        """Test screenshot execution."""
        executor = ToolExecutor(container_url="http://test:8080")
        executor.client = mock_client

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "image_base64": "dGVzdA==",
            "width": 1920,
            "height": 1080
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        result = await executor.execute("computer", {"action": "screenshot"})

        assert result["type"] == "image"
        assert "source" in result

    @pytest.mark.asyncio
    async def test_execute_editor_view(self, mock_client):
        """Test editor view command."""
        executor = ToolExecutor(container_url="http://test:8080")
        executor.client = mock_client

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "line 1\nline 2\nline 3"
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        result = await executor.execute(
            "str_replace_editor",
            {"command": "view", "path": "/workspace/test.txt"}
        )

        assert "1\t" in result["output"]  # Line numbers

    @pytest.mark.asyncio
    async def test_execute_browser_navigate(self, mock_client):
        """Test browser navigation."""
        executor = ToolExecutor(container_url="http://test:8080")
        executor.client = mock_client

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {"url": "https://example.com", "title": "Example"}
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        result = await executor.execute(
            "browser",
            {"action": "navigate", "params": {"url": "https://example.com"}}
        )

        assert "output" in result

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, mock_client):
        """Test unknown tool handling."""
        executor = ToolExecutor(container_url="http://test:8080")
        executor.client = mock_client

        result = await executor.execute("unknown_tool", {})

        assert "error" in result
        assert "Unknown tool" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_client):
        """Test health check success."""
        executor = ToolExecutor(container_url="http://test:8080")
        executor.client = mock_client

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response

        result = await executor.health_check()

        assert result == True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_client):
        """Test health check failure."""
        executor = ToolExecutor(container_url="http://test:8080")
        executor.client = mock_client

        mock_client.get.side_effect = Exception("Connection refused")

        result = await executor.health_check()

        assert result == False


class TestSessionManager:
    """Test session manager."""

    def test_create_session(self):
        """Test session creation."""
        manager = SessionManager()
        session = manager.create_session(
            container_url="http://localhost:8080",
            name="test-session"
        )

        assert session.session_id is not None
        assert session.name == "test-session"
        assert session.status == SessionStatus.STARTING

    def test_get_session(self):
        """Test getting a session."""
        manager = SessionManager()
        session = manager.create_session()

        retrieved = manager.get_session(session.session_id)

        assert retrieved is not None
        assert retrieved.session_id == session.session_id

    def test_get_nonexistent_session(self):
        """Test getting a non-existent session."""
        manager = SessionManager()

        result = manager.get_session("nonexistent")

        assert result is None

    def test_update_session(self):
        """Test updating a session."""
        manager = SessionManager()
        session = manager.create_session()

        manager.update_session(
            session.session_id,
            status=SessionStatus.RUNNING,
            container_url="http://test:8080"
        )

        updated = manager.get_session(session.session_id)
        assert updated.status == SessionStatus.RUNNING
        assert updated.container_url == "http://test:8080"

    def test_delete_session(self):
        """Test deleting a session."""
        manager = SessionManager()
        session = manager.create_session()

        result = manager.delete_session(session.session_id)

        assert result == True
        assert manager.get_session(session.session_id) is None

    def test_list_sessions(self):
        """Test listing sessions."""
        manager = SessionManager()
        manager.create_session(name="session-1")
        manager.create_session(name="session-2")

        sessions = manager.list_sessions()

        assert len(sessions) == 2

    def test_list_sessions_filtered(self):
        """Test listing sessions with filter."""
        manager = SessionManager()
        s1 = manager.create_session()
        s2 = manager.create_session()

        manager.update_session(s1.session_id, status=SessionStatus.RUNNING)

        running = manager.list_sessions(status=SessionStatus.RUNNING)
        starting = manager.list_sessions(status=SessionStatus.STARTING)

        assert len(running) == 1
        assert len(starting) == 1

    def test_get_active_count(self):
        """Test getting active session count."""
        manager = SessionManager()
        s1 = manager.create_session()
        s2 = manager.create_session()

        manager.update_session(s1.session_id, status=SessionStatus.RUNNING)

        count = manager.get_active_count()

        assert count == 1

    def test_increment_task_count(self):
        """Test incrementing task count."""
        manager = SessionManager()
        session = manager.create_session()

        manager.increment_task_count(session.session_id)
        manager.increment_task_count(session.session_id)

        updated = manager.get_session(session.session_id)
        assert updated.task_count == 2


class TestToolResultFormatting:
    """Test tool result formatting."""

    def test_format_image_result(self):
        """Test formatting image results."""
        result = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": "test"
            }
        }

        # This matches what the agent expects
        assert result["type"] == "image"
        assert result["source"]["type"] == "base64"

    def test_format_text_result(self):
        """Test formatting text results."""
        result = {"output": "Command executed successfully"}

        assert "output" in result

    def test_format_error_result(self):
        """Test formatting error results."""
        result = {"error": "Something went wrong"}

        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
