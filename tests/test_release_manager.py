"""Tests for the ReleaseManager agent.

Tests both the agent's sync and async methods, including streaming functionality.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from agentllm.agents.release_manager import ReleaseManager

# Load .env file for tests
load_dotenv()

# Map GEMINI_API_KEY to GOOGLE_API_KEY if needed
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]


class TestReleaseManager:
    """Tests for ReleaseManager agent."""

    @pytest.fixture
    def configured_agent(self):
        """Fixture that provides a ReleaseManager with pre-configured user."""
        agent = ReleaseManager()
        # Mock Jira toolkit validation to avoid real connections in tests
        with patch("agentllm.agents.release_manager.JiraTools") as mock_jira:
            mock_toolkit = MagicMock()
            mock_toolkit.validate_connection.return_value = (True, "Connected successfully")
            mock_jira.return_value = mock_toolkit
            # Pre-configure test user with Jira token
            agent.store_config("test-user", "jira_token", "test-token-12345")
        return agent

    def test_create_agent(self):
        """Test that ReleaseManager can be instantiated."""
        agent = ReleaseManager()
        assert agent is not None

    def test_create_agent_with_params(self):
        """Test that ReleaseManager accepts model parameters."""
        agent = ReleaseManager(temperature=0.5, max_tokens=100)
        assert agent is not None
        assert agent._temperature == 0.5
        assert agent._max_tokens == 100

    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    def test_sync_run(self, configured_agent):
        """Test synchronous run() method."""
        response = configured_agent.run("Hello! Can you help me?", user_id="test-user")

        assert response is not None
        assert hasattr(response, "content")
        assert len(str(response.content)) > 0

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    async def test_async_non_streaming(self, configured_agent):
        """Test async arun() without streaming."""
        response = await configured_agent.arun(
            "Hello! Can you help me?", user_id="test-user", stream=False
        )

        assert response is not None
        assert hasattr(response, "content")
        assert len(str(response.content)) > 0

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    async def test_async_streaming(self, configured_agent):
        """Test async arun() WITH streaming.

        This is the critical test that ensures streaming works correctly.
        The arun() method should return an async generator when stream=True.
        """
        # Call arun with streaming enabled
        result = configured_agent.arun("Hello! Can you help me?", user_id="test-user", stream=True)

        # Verify it's an async generator
        assert hasattr(result, "__aiter__"), "Result should be an async generator"

        # Iterate and collect chunks
        chunks = []
        async for chunk in result:
            chunks.append(chunk)

        # Verify we got chunks
        assert len(chunks) > 0, "Should receive at least one chunk"

        # Verify chunks have content
        for chunk in chunks:
            assert hasattr(chunk, "content") or hasattr(
                chunk, "__str__"
            ), "Chunks should have content"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    async def test_streaming_returns_async_generator_not_coroutine(self, configured_agent):
        """Test that arun(stream=True) returns an async generator, not a coroutine.

        This test specifically checks the issue we fixed: when streaming is enabled,
        the method should return an async generator that can be directly iterated,
        not a coroutine that needs to be awaited first.
        """
        result = configured_agent.arun("Test message", user_id="test-user", stream=True)

        # Should be an async generator, not a coroutine
        assert hasattr(result, "__aiter__"), "Should have __aiter__ (async generator)"
        assert not hasattr(result, "__await__") or hasattr(
            result, "__aiter__"
        ), "Should be iterable without await"

        # Should be directly iterable with async for
        chunk_count = 0
        async for chunk in result:
            chunk_count += 1
            # Just verify we can iterate
            if chunk_count >= 3:
                break

        assert chunk_count > 0, "Should receive chunks"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    async def test_non_streaming_returns_awaitable(self, configured_agent):
        """Test that arun(stream=False) returns a coroutine that can be awaited."""
        result = configured_agent.arun("Test message", user_id="test-user", stream=False)

        # Should be awaitable
        assert hasattr(result, "__await__"), "Should be awaitable (coroutine)"

        # Should be able to await it
        response = await result
        assert response is not None
        assert hasattr(response, "content")

    @patch("agentllm.agents.release_manager.JiraTools")
    def test_agent_cache_per_user(self, mock_jira_class):
        """Test that agents are cached per user."""
        # Mock successful validation
        mock_toolkit = MagicMock()
        mock_toolkit.validate_connection.return_value = (True, "Connected")
        mock_jira_class.return_value = mock_toolkit

        manager1 = ReleaseManager()
        manager2 = ReleaseManager()

        # Configure both managers
        manager1.store_config("user1", "jira_token", "token1-123456789012345678901234567890")
        manager2.store_config("user2", "jira_token", "token2-123456789012345678901234567890")

        # Create agents for different users
        agent1 = manager1._get_or_create_agent()
        agent2 = manager2._get_or_create_agent()

        # Both should create underlying agents
        assert agent1 is not None
        assert agent2 is not None

        # Calling again on same manager should return cached agent
        agent1_again = manager1._get_or_create_agent()
        assert agent1_again is agent1, "Should return cached agent"


class TestReleaseManagerConfiguration:
    """Tests for ReleaseManager configuration management."""

    def test_unconfigured_user_gets_prompt(self):
        """Test that unconfigured users receive a configuration prompt."""
        agent = ReleaseManager()

        response = agent.run("Hello!", user_id="new-user")

        # Should get a prompt for configuration
        assert response is not None
        content = str(response.content) if hasattr(response, "content") else str(response)
        assert "jira" in content.lower()
        assert "token" in content.lower()

    @patch("agentllm.agents.release_manager.JiraTools")
    def test_provide_jira_token(self, mock_jira_class):
        """Test providing Jira token in natural language."""
        agent = ReleaseManager()

        # Mock successful validation with a specific message
        mock_toolkit = MagicMock()
        mock_toolkit.validate_connection.return_value = (
            True,
            "Successfully connected to Jira as Test User"
        )
        mock_jira_class.return_value = mock_toolkit

        # Provide token
        response = agent.run(
            "My Jira token is test-token-12345", user_id="config-user"
        )

        # Should show the validation message from Jira connection
        content = str(response.content) if hasattr(response, "content") else str(response)
        assert "connected" in content.lower()
        assert "test user" in content.lower()

        # Verify user is now configured
        assert agent.is_configured("config-user")

    @pytest.mark.skipif(
        "GOOGLE_API_KEY" not in os.environ,
        reason="GOOGLE_API_KEY not set",
    )
    def test_configured_user_uses_agent(self):
        """Test that configured users can use the agent normally."""
        agent = ReleaseManager()

        # Pre-configure with mocked validation
        with patch("agentllm.agents.release_manager.JiraTools") as mock_jira:
            mock_toolkit = MagicMock()
            mock_toolkit.validate_connection.return_value = (True, "Connected")
            mock_jira.return_value = mock_toolkit
            agent.store_config("ready-user", "jira_token", "my-token")

        # Now use agent
        response = agent.run("Hello!", user_id="ready-user")

        # Should get actual agent response, not config prompt
        assert response is not None
        assert hasattr(response, "content")
        # Agent response should be substantial, not a config message
        assert len(str(response.content)) > 50

    def test_extract_token_patterns(self):
        """Test that various token input patterns are recognized."""
        agent = ReleaseManager()

        patterns = [
            "my jira token is abc123",
            "jira token: xyz789",
            "set jira token to token-456",
            "My Jira token is SECRET_TOKEN",
        ]

        for pattern in patterns:
            extracted = agent.extract_token_from_message(pattern)
            assert extracted is not None, f"Failed to extract from: {pattern}"
            assert "jira_token" in extracted
            assert len(extracted["jira_token"]) > 0

    def test_missing_configs(self):
        """Test getting list of missing configurations."""
        agent = ReleaseManager()

        # New user should have missing config
        missing = agent.get_missing_configs("unconfig-user")
        assert "jira_token" in missing

        # Configured user should have no missing configs
        with patch("agentllm.agents.release_manager.JiraTools") as mock_jira:
            mock_toolkit = MagicMock()
            mock_toolkit.validate_connection.return_value = (True, "Connected")
            mock_jira.return_value = mock_toolkit
            agent.store_config("full-user", "jira_token", "token")
        missing = agent.get_missing_configs("full-user")
        assert len(missing) == 0

    def test_extract_long_alphanumeric_token(self):
        """Test extraction of long alphanumeric tokens (30+ characters)."""
        agent = ReleaseManager()

        # Test with example token from user
        message = "FAKE_TEST_TOKEN_PLACEHOLDER_12345678901234567890123456789012"
        extracted = agent.extract_token_from_message(message)

        assert extracted is not None, "Should extract standalone token"
        assert "jira_token" in extracted
        assert extracted["jira_token"] == "FAKE_TEST_TOKEN_PLACEHOLDER_12345678901234567890123456789012"

    def test_extract_long_token_with_base64_chars(self):
        """Test extraction of tokens with base64-like characters."""
        agent = ReleaseManager()

        # Test with token containing +, /, = characters
        tokens = [
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
            "aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5zA==",
        ]

        for token in tokens:
            extracted = agent.extract_token_from_message(token)
            assert extracted is not None, f"Should extract token: {token}"
            assert "jira_token" in extracted
            assert extracted["jira_token"] == token

    def test_no_extraction_for_short_tokens(self):
        """Test that short strings are not extracted as tokens."""
        agent = ReleaseManager()

        # Tokens that are too short
        short_strings = [
            "abc123",
            "shorttoken",
            "ThisIsTooShort12345",
        ]

        for short_str in short_strings:
            extracted = agent.extract_token_from_message(short_str)
            # Should either be None or not extract from short string
            if extracted:
                assert "jira_token" not in extracted or extracted["jira_token"] != short_str

    @patch("agentllm.agents.release_manager.JiraTools")
    def test_token_validation_success(self, mock_jira_class):
        """Test successful token validation."""
        agent = ReleaseManager()

        # Mock successful validation
        mock_toolkit = MagicMock()
        mock_toolkit.validate_connection.return_value = (True, "Connected as user@example.com")
        mock_jira_class.return_value = mock_toolkit

        # Store config (which triggers validation)
        agent.store_config("test-user", "jira_token", "valid-token-123456789012345678901234567890")

        # Verify validation was called
        mock_jira_class.assert_called_once()
        mock_toolkit.validate_connection.assert_called_once()

        # Verify toolkit was stored
        assert agent._jira_toolkit is not None
        assert agent.is_configured("test-user")

    @patch("agentllm.agents.release_manager.JiraTools")
    def test_token_validation_failure(self, mock_jira_class):
        """Test failed token validation."""
        agent = ReleaseManager()

        # Mock failed validation
        mock_toolkit = MagicMock()
        mock_toolkit.validate_connection.return_value = (False, "Invalid credentials")
        mock_jira_class.return_value = mock_toolkit

        # Store config should raise ValueError
        with pytest.raises(ValueError, match="Invalid Jira token"):
            agent.store_config("test-user", "jira_token", "invalid-token-123456789012345678901234567890")

        # Verify user is not configured
        assert not agent.is_configured("test-user")
        assert agent._jira_toolkit is None

    @patch("agentllm.agents.release_manager.JiraTools")
    def test_validation_error_handling_in_run(self, mock_jira_class):
        """Test that validation errors are handled gracefully in run()."""
        agent = ReleaseManager()

        # Mock failed validation
        mock_toolkit = MagicMock()
        mock_toolkit.validate_connection.return_value = (False, "Connection timeout")
        mock_jira_class.return_value = mock_toolkit

        # Try to configure with invalid token (must include "jira token" in message)
        response = agent.run(
            "My jira token is invalidtoken123456789012345678901234567890",
            user_id="test-user"
        )

        # Should return error message, not raise exception
        content = str(response.content) if hasattr(response, "content") else str(response)
        assert "validation failed" in content.lower() or "failed" in content.lower()
        assert not agent.is_configured("test-user")

    @patch("agentllm.agents.release_manager.JiraTools")
    def test_toolkit_passed_to_agent(self, mock_jira_class):
        """Test that Jira toolkit is passed to the agent when configured."""
        agent = ReleaseManager()

        # Mock successful validation
        mock_toolkit = MagicMock()
        mock_toolkit.validate_connection.return_value = (True, "Connected")
        mock_jira_class.return_value = mock_toolkit

        # Configure
        agent.store_config("test-user", "jira_token", "valid-token-123456789012345678901234567890")

        # Create agent
        underlying_agent = agent._get_or_create_agent()

        # Verify toolkit is stored
        assert agent._jira_toolkit is not None
        # Note: We can't easily verify it's passed to Agent without inspecting internals
        # But we can verify the agent was created
        assert underlying_agent is not None

    @patch("agentllm.agents.release_manager.JiraTools")
    def test_validation_message_displayed_to_user(self, mock_jira_class):
        """Test that the validation message from Jira is displayed to the user."""
        agent = ReleaseManager()

        # Mock successful validation with a custom message
        mock_toolkit = MagicMock()
        custom_message = "Successfully connected to Jira as john.doe@example.com"
        mock_toolkit.validate_connection.return_value = (True, custom_message)
        mock_jira_class.return_value = mock_toolkit

        # Provide token via run()
        response = agent.run(
            "My Jira token is abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
            user_id="test-user"
        )

        # Verify the custom validation message appears in the response
        content = str(response.content) if hasattr(response, "content") else str(response)
        assert custom_message in content
        assert "john.doe@example.com" in content

    def test_agent_creation_fails_without_toolkit(self):
        """Test that agent creation fails gracefully if toolkit is missing."""
        agent = ReleaseManager()

        # Manually mark user as configured but don't set toolkit
        # This simulates an edge case where config exists but toolkit wasn't created
        agent._user_configs["test-user"] = {"jira_token": "some-token"}

        # Try to create agent - should raise RuntimeError
        with pytest.raises(RuntimeError, match="Jira toolkit is not configured"):
            agent._get_or_create_agent()

    def test_run_handles_missing_toolkit_gracefully(self):
        """Test that run() handles missing toolkit with user-friendly error."""
        agent = ReleaseManager()

        # Manually mark user as configured but don't set toolkit
        agent._user_configs["test-user"] = {"jira_token": "some-token"}

        # Try to run - should return error message, not raise exception
        response = agent.run("Hello!", user_id="test-user")

        content = str(response.content) if hasattr(response, "content") else str(response)
        assert "configuration error" in content.lower()
        assert "toolkit is not configured" in content.lower()


class TestReleaseManagerSessionManagement:
    """Tests for ReleaseManager session and user management."""

    def test_session_id_and_user_id_passed_through(self):
        """Test that session_id and user_id are passed to underlying agent."""
        agent = ReleaseManager()
        # Pre-configure to avoid config prompt with mocked validation
        with patch("agentllm.agents.release_manager.JiraTools") as mock_jira:
            mock_toolkit = MagicMock()
            mock_toolkit.validate_connection.return_value = (True, "Connected")
            mock_jira.return_value = mock_toolkit
            agent.store_config("test-user", "jira_token", "test-token")

        # This should not raise an error
        # The actual session behavior is tested in integration tests
        try:
            response = agent.run(
                "Test message", user_id="test-user", session_id="test-session"
            )
            # If we have API key, verify response
            if "GOOGLE_API_KEY" in os.environ:
                assert response is not None
        except Exception as e:
            # If no API key, we expect model provider error
            if "GOOGLE_API_KEY" not in os.environ:
                assert "api_key" in str(e).lower()
            else:
                raise
