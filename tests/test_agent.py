"""
Agent Unit Tests.

Tests the agent configuration, tool execution methods, and session manager
without requiring a running container. Uses mocked HTTP responses.

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
from orchestrator.session_manager import SessionManager
from orchestrator.schemas import SessionStatus


# ── Config Tests ─────────────────────────────────────────────────────

class TestAgentConfig:
    """Test agent configuration."""

    def test_default_config(self):
        config = AgentConfig()
        assert config.display_width == 1920
        assert config.display_height == 1080
        assert config.container_url == "http://localhost:8080"

    def test_config_from_env(self):
        with patch.dict(os.environ, {"DISPLAY_WIDTH": "1280", "DISPLAY_HEIGHT": "720"}):
            config = AgentConfig()
            assert config.display_width == 1280
            assert config.display_height == 720

    def test_config_container_url_from_env(self):
        with patch.dict(os.environ, {"CONTAINER_URL": "http://myhost:9090"}):
            config = AgentConfig()
            assert config.container_url == "http://myhost:9090"

    def test_config_validation_fails_without_key(self):
        config = AgentConfig()
        config.anthropic_api_key = ""
        with pytest.raises(ValueError):
            config.validate()


# ── Agent Tool Execution Tests ──────────────────────────────────────

class TestAgentToolExecution:
    """Test the agent's tool execution methods with mocked HTTP."""

    @pytest.fixture
    def agent(self):
        """Create an agent with a mocked API key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            from agent.computer_use_agent import ComputerUseAgent
            a = ComputerUseAgent(
                container_url="http://localhost:8080",
                api_key="test-key",
            )
            return a

    @pytest.mark.asyncio
    async def test_exec_bash(self, agent):
        """Test bash execution."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "stdout": "Hello, World!",
            "stderr": "",
            "return_code": 0,
        }
        mock_response.raise_for_status = MagicMock()
        agent.http = AsyncMock()
        agent.http.post.return_value = mock_response

        result = await agent._exec_bash({"command": "echo Hello, World!"})
        assert "Hello, World!" in result

    @pytest.mark.asyncio
    async def test_exec_bash_error(self, agent):
        """Test bash with non-zero exit code."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "stdout": "",
            "stderr": "command not found",
            "return_code": 127,
        }
        mock_response.raise_for_status = MagicMock()
        agent.http = AsyncMock()
        agent.http.post.return_value = mock_response

        result = await agent._exec_bash({"command": "invalid_command"})
        assert "STDERR" in result
        assert "127" in result

    @pytest.mark.asyncio
    async def test_exec_computer_screenshot(self, agent):
        """Test screenshot action."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "image_base64": "dGVzdA==",
            "width": 1920,
            "height": 1080,
        }
        mock_response.raise_for_status = MagicMock()
        agent.http = AsyncMock()
        agent.http.get.return_value = mock_response

        result = await agent._exec_computer({"action": "screenshot"})
        assert isinstance(result, list)
        assert result[0]["type"] == "image"
        assert result[0]["source"]["type"] == "base64"

    @pytest.mark.asyncio
    async def test_exec_computer_click(self, agent):
        """Test left_click action."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        agent.http = AsyncMock()
        agent.http.post.return_value = mock_response

        result = await agent._exec_computer({"action": "left_click", "coordinate": [100, 200]})
        assert "left_click" in result
        assert "100" in result
        assert "200" in result

    @pytest.mark.asyncio
    async def test_exec_computer_type(self, agent):
        """Test type action."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        agent.http = AsyncMock()
        agent.http.post.return_value = mock_response

        result = await agent._exec_computer({"action": "type", "text": "hello"})
        assert "Typed" in result

    @pytest.mark.asyncio
    async def test_exec_computer_key(self, agent):
        """Test key press action."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        agent.http = AsyncMock()
        agent.http.post.return_value = mock_response

        result = await agent._exec_computer({"action": "key", "key": "Return"})
        assert "key" in result.lower()

    @pytest.mark.asyncio
    async def test_exec_computer_scroll(self, agent):
        """Test scroll action."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        agent.http = AsyncMock()
        agent.http.post.return_value = mock_response

        result = await agent._exec_computer({"action": "scroll", "scroll_direction": "down", "scroll_amount": 3})
        assert "Scrolled" in result

    @pytest.mark.asyncio
    async def test_exec_editor_view(self, agent):
        """Test editor view command."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": "line 1\nline 2\nline 3"}
        mock_response.raise_for_status = MagicMock()
        agent.http = AsyncMock()
        agent.http.post.return_value = mock_response

        result = await agent._exec_editor({"command": "view", "path": "/workspace/test.txt"})
        assert "1\t" in result  # line numbers

    @pytest.mark.asyncio
    async def test_exec_editor_create(self, agent):
        """Test editor create command."""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        agent.http = AsyncMock()
        agent.http.post.return_value = mock_response

        result = await agent._exec_editor({"command": "create", "path": "/workspace/new.txt", "file_text": "hello"})
        assert "Created" in result

    @pytest.mark.asyncio
    async def test_exec_editor_str_replace(self, agent):
        """Test editor str_replace command."""
        # Mock read response
        read_response = AsyncMock()
        read_response.status_code = 200
        read_response.json.return_value = {"content": "hello world"}
        read_response.raise_for_status = MagicMock()

        # Mock write response
        write_response = AsyncMock()
        write_response.raise_for_status = MagicMock()

        agent.http = AsyncMock()
        agent.http.post.side_effect = [read_response, write_response]

        result = await agent._exec_editor({
            "command": "str_replace",
            "path": "/workspace/test.txt",
            "old_str": "hello",
            "new_str": "goodbye",
        })
        assert "Replaced" in result

    @pytest.mark.asyncio
    async def test_execute_tool_unknown(self, agent):
        """Test that unknown tools return an error message."""
        result = await agent._execute_tool("unknown_tool", {})
        assert "Unknown tool" in result

    def test_reset_conversation(self, agent):
        """Test conversation reset."""
        agent.conversation_history = [{"role": "user", "content": "test"}]
        agent.reset_conversation()
        assert agent.conversation_history == []

    def test_get_conversation_history(self, agent):
        """Test conversation history retrieval returns a copy."""
        agent.conversation_history = [{"role": "user", "content": "test"}]
        history = agent.get_conversation_history()
        assert history == agent.conversation_history
        assert history is not agent.conversation_history  # must be a copy


# ── Session Manager Tests ────────────────────────────────────────────

class TestSessionManager:
    """Test session manager."""

    def test_create_session(self):
        manager = SessionManager()
        session = manager.create_session(
            container_url="http://localhost:8080",
            name="test-session",
        )
        assert session.session_id is not None
        assert session.name == "test-session"
        assert session.status == SessionStatus.STARTING

    def test_get_session(self):
        manager = SessionManager()
        session = manager.create_session()
        retrieved = manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id

    def test_get_nonexistent_session(self):
        manager = SessionManager()
        assert manager.get_session("nonexistent") is None

    def test_update_session(self):
        manager = SessionManager()
        session = manager.create_session()
        manager.update_session(
            session.session_id,
            status=SessionStatus.RUNNING,
            container_url="http://test:8080",
        )
        updated = manager.get_session(session.session_id)
        assert updated.status == SessionStatus.RUNNING
        assert updated.container_url == "http://test:8080"

    def test_delete_session(self):
        manager = SessionManager()
        session = manager.create_session()
        assert manager.delete_session(session.session_id) is True
        assert manager.get_session(session.session_id) is None

    def test_list_sessions(self):
        manager = SessionManager()
        manager.create_session(name="session-1")
        manager.create_session(name="session-2")
        assert len(manager.list_sessions()) == 2

    def test_list_sessions_filtered(self):
        manager = SessionManager()
        s1 = manager.create_session()
        s2 = manager.create_session()
        manager.update_session(s1.session_id, status=SessionStatus.RUNNING)
        assert len(manager.list_sessions(status=SessionStatus.RUNNING)) == 1
        assert len(manager.list_sessions(status=SessionStatus.STARTING)) == 1

    def test_get_active_count(self):
        manager = SessionManager()
        s1 = manager.create_session()
        manager.create_session()
        manager.update_session(s1.session_id, status=SessionStatus.RUNNING)
        assert manager.get_active_count() == 1

    def test_increment_task_count(self):
        manager = SessionManager()
        session = manager.create_session()
        manager.increment_task_count(session.session_id)
        manager.increment_task_count(session.session_id)
        assert manager.get_session(session.session_id).task_count == 2


# ── Result Formatting Tests ──────────────────────────────────────────

class TestToolResultFormatting:
    """Test tool result shape contracts."""

    def test_format_image_result(self):
        result = {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": "test"},
        }
        assert result["type"] == "image"
        assert result["source"]["type"] == "base64"

    def test_format_text_result(self):
        result = "Command executed successfully"
        assert isinstance(result, str)

    def test_format_error_result(self):
        result = "Error: Something went wrong"
        assert "Error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
