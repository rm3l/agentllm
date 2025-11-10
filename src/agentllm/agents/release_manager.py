"""Release Manager agent for managing software releases and changelogs."""

import os
from pathlib import Path
from typing import Any

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.google import Gemini
from loguru import logger

from agentllm.agents.toolkit_configs import GoogleDriveConfig
from agentllm.agents.toolkit_configs.jira_config import JiraConfig
from agentllm.db import TokenStorage

# Map GEMINI_API_KEY to GOOGLE_API_KEY if not set
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

# Shared database for all agents to enable session management
DB_PATH = Path("tmp/agno_sessions.db")
DB_PATH.parent.mkdir(exist_ok=True)
shared_db = SqliteDb(db_file=str(DB_PATH))

# Create token storage using the shared database
# This stores Jira and Google Drive credentials in the same database
token_storage = TokenStorage(agno_db=shared_db)


class ReleaseManager:
    """Release Manager with toolkit configuration management.

    This class wraps an Agno agent and manages user-specific toolkit configurations
    (e.g., Google Drive OAuth, JIRA tokens). It intercepts run() and arun() calls to:
    1. Check if toolkits are configured for the user
    2. Extract configuration from user messages if provided
    3. Prompt users for missing configurations when they request toolkit features
    4. Delegate to the wrapped agent once configured

    The class maintains the same interface as Agno Agent, making it transparent
    to LiteLLM and other callers.

    Toolkit Configuration:
    ---------------------
    Toolkits are managed via composition using BaseToolkitConfig implementations.
    Each toolkit handles its own configuration flow, validation, and provisioning.

    Currently supported toolkits:
    - Google Drive: OAuth-based access to Google Docs, Sheets, and Presentations
    - JIRA: API token-based access to JIRA issues (optional, can be enabled)

    See individual toolkit config classes for setup instructions.
    """

    def __init__(
        self,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **model_kwargs,
    ):
        """Initialize the Release Manager with toolkit configurations.

        Args:
            temperature: Model temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            **model_kwargs: Additional model parameters
        """
        # Initialize toolkit configurations with shared token storage
        self.toolkit_configs = [
            GoogleDriveConfig(token_storage=token_storage),
            JiraConfig(token_storage=token_storage),
        ]

        # Store model parameters for later agent creation
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._model_kwargs = model_kwargs

        # Store agents per user_id (agents are not shared across users)
        self._agents: dict[str, Agent] = {}

        # Cache extended system prompts per user_id
        # Fetched from Google Docs and cached until agent invalidation
        self._system_prompts: dict[str, str] = {}

    def _invalidate_system_prompt(self, user_id: str) -> None:
        """Invalidate cached system prompt for a user.

        This clears the cached extended system prompt from Google Docs,
        forcing a fresh fetch on next agent creation.

        Args:
            user_id: User identifier
        """
        if user_id in self._system_prompts:
            logger.info(f"Invalidating cached system prompt for user {user_id}")
            del self._system_prompts[user_id]

    def _invalidate_agent(self, user_id: str) -> None:
        """Invalidate cached agent for a user.

        This forces agent recreation on next request, useful when
        user authorizes new tools (e.g., Google Drive).

        Args:
            user_id: User identifier
        """
        if user_id in self._agents:
            logger.info(f"Invalidating cached agent for user {user_id}")
            del self._agents[user_id]
        # Also invalidate the system prompt cache
        self._invalidate_system_prompt(user_id)

    def _check_and_invalidate_agent(self, config_name: str, user_id: str) -> None:
        """Check if config requires agent recreation and invalidate if needed.

        Args:
            config_name: Configuration name that was just stored
            user_id: User identifier
        """
        # Check if any toolkit config requires agent recreation for this config
        for config in self.toolkit_configs:
            if config.requires_agent_recreation(config_name):
                self._invalidate_agent(user_id)
                logger.info(f"Config '{config_name}' requires agent recreation for user {user_id}")
                break

    def _fetch_extended_system_prompt(self, user_id: str) -> str:
        """Fetch extended system prompt from Google Docs.

        This method retrieves additional system prompt instructions from a Google Doc
        specified by the RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL environment variable.
        The content is cached per user until agent invalidation.

        Args:
            user_id: User identifier

        Returns:
            Extended system prompt content as a string (markdown format)

        Raises:
            ValueError: If Google Drive is not configured for the user
            Exception: If document fetch fails (network error, permissions, invalid URL, etc.)
        """
        # Check cache first
        if user_id in self._system_prompts:
            logger.debug(f"Using cached system prompt for user {user_id}")
            return self._system_prompts[user_id]

        # Get the document URL from environment
        doc_url = os.getenv("RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL")
        if not doc_url:
            raise ValueError(
                "RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL environment variable not set"
            )

        logger.info(f"Fetching extended system prompt from Google Doc for user {user_id}")

        # Get Google Drive toolkit for this user
        gdrive_config = None
        for config in self.toolkit_configs:
            if isinstance(config, GoogleDriveConfig):
                gdrive_config = config
                break

        if not gdrive_config:
            raise ValueError("Google Drive config not found in toolkit configs")

        if not gdrive_config.is_configured(user_id):
            raise ValueError(
                f"Google Drive is not configured for user {user_id}. "
                "User must authorize Google Drive access before extended system prompt can be fetched."
            )

        # Get the toolkit instance
        toolkit = gdrive_config.get_toolkit(user_id)
        if not toolkit:
            raise ValueError(f"Failed to get Google Drive toolkit for user {user_id}")

        # Fetch the document content
        try:
            content = toolkit.get_document_content(doc_url)
            if not content:
                raise ValueError(f"Document at {doc_url} returned empty content")

            # Cache the content
            self._system_prompts[user_id] = content
            logger.info(
                f"Successfully fetched extended system prompt for user {user_id} "
                f"({len(content)} characters)"
            )

            return content

        except Exception as e:
            logger.error(
                f"Failed to fetch extended system prompt from {doc_url} for user {user_id}: {e}"
            )
            raise

    def _get_or_create_agent(self, user_id: str) -> Agent:
        """Get or create the underlying Agno agent for a specific user.

        Agents are created per-user and include their configured toolkits.

        Args:
            user_id: User identifier

        Returns:
            The Agno agent instance for this user
        """
        # Return existing agent for this user if available
        if user_id in self._agents:
            return self._agents[user_id]

        # Create the agent for this user
        model_params = {"id": "gemini-2.5-flash"}
        if self._temperature is not None:
            model_params["temperature"] = self._temperature
        if self._max_tokens is not None:
            model_params["max_tokens"] = self._max_tokens
        model_params.update(self._model_kwargs)

        # Collect all configured toolkits for this user
        tools = []
        for config in self.toolkit_configs:
            toolkit = config.get_toolkit(user_id)
            if toolkit:
                tools.append(toolkit)
                logger.info(
                    f"Adding {config.__class__.__name__} toolkit to agent for user {user_id}"
                )

        # Create base instructions
        instructions = [
            "You are a helpful AI assistant.",
            "Answer questions and help users with various tasks.",
            "Use markdown formatting for structured output.",
            "Be concise and clear in your responses.",
        ]

        # Fetch and append extended system prompt from Google Docs if configured
        doc_url = os.getenv("RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL")
        if doc_url:
            # Check if Google Drive is configured for this user
            gdrive_config = None
            for config in self.toolkit_configs:
                if isinstance(config, GoogleDriveConfig):
                    gdrive_config = config
                    break

            if gdrive_config and gdrive_config.is_configured(user_id):
                try:
                    extended_prompt = self._fetch_extended_system_prompt(user_id)
                    instructions.append(extended_prompt)
                    logger.info(
                        f"Appended extended system prompt to agent instructions for user {user_id}"
                    )
                except Exception as e:
                    # Let the exception bubble up - fail agent creation if prompt fetch fails
                    logger.error(
                        f"Failed to fetch extended system prompt for user {user_id}, "
                        f"aborting agent creation: {e}"
                    )
                    raise
            else:
                logger.info(
                    f"RELEASE_MANAGER_SYSTEM_PROMPT_GDRIVE_URL is set but Google Drive "
                    f"is not configured for user {user_id}, skipping extended prompt"
                )

        # Add toolkit-specific instructions
        for config in self.toolkit_configs:
            toolkit_instructions = config.get_agent_instructions(user_id)
            instructions.extend(toolkit_instructions)

        agent = Agent(
            name="release-manager",
            model=Gemini(**model_params),
            description="A helpful AI assistant",
            instructions=instructions,
            markdown=True,
            tools=tools if tools else None,
            # Session management
            db=shared_db,
            add_history_to_context=True,
            num_history_runs=10,  # Include last 10 messages
            read_chat_history=True,  # Allow agent to read full history
        )

        # Cache the agent for this user
        self._agents[user_id] = agent
        logger.info(f"Created agent for user {user_id} with {len(tools)} tools")

        return agent

    def _create_simple_response(self, content: str) -> Any:
        """Create a simple response object that mimics Agno's RunResponse.

        Args:
            content: Message content to return

        Returns:
            Response object with content attribute
        """

        class SimpleResponse:
            def __init__(self, content: str):
                self.content = content

            def __str__(self):
                return self.content

        return SimpleResponse(content)

    def _handle_configuration(self, message: str, user_id: str | None) -> Any | None:
        """Handle configuration extraction and validation.

        This method (in order):
        1. Tries to extract and store configuration from user message (OAuth codes, tokens, etc.)
        2. Checks if any required toolkit is not configured and prompts if needed
        3. Checks if any optional toolkit detects an authorization request and prompts if needed
        4. Returns None if no configuration handling needed (proceed to agent)

        The order is important: extraction must happen first so that when a user provides
        config, it gets stored before we check if required configs are missing.

        Args:
            message: User message
            user_id: User identifier

        Returns:
            Response with configuration message, or None if no config handling needed
        """
        if not user_id:
            return None

        # FIRST: Try to extract and store configuration from message
        # This must happen before checking required configs, so that if the user
        # provides config (e.g., OAuth code), it gets stored before we check again
        for config in self.toolkit_configs:
            try:
                confirmation = config.extract_and_store_config(message, user_id)
                if confirmation:
                    # Configuration was extracted and stored successfully
                    # Invalidate agent so it's recreated with new tools
                    self._invalidate_agent(user_id)
                    logger.info(
                        f"Configuration stored for {config.__class__.__name__}, "
                        f"agent invalidated for user {user_id}"
                    )
                    return self._create_simple_response(confirmation)
            except ValueError as e:
                # Configuration validation failed
                error_msg = (
                    f"❌ Configuration validation failed: {str(e)}\n\n"
                    "Please check your credentials and try again."
                )
                logger.warning(
                    f"Configuration validation failed for "
                    f"{config.__class__.__name__}, user {user_id}: {e}"
                )
                return self._create_simple_response(error_msg)

        # SECOND: Check if any REQUIRED toolkit is not configured
        # This happens after extraction, so if user provided config above, it's already stored
        for config in self.toolkit_configs:
            if config.is_required() and not config.is_configured(user_id):
                # Required toolkit not configured - prompt user
                prompt = config.get_config_prompt(user_id)
                if prompt:
                    logger.info(
                        f"User {user_id} needs to configure required toolkit: "
                        f"{config.__class__.__name__}"
                    )
                    return self._create_simple_response(prompt)

        # THIRD: Check if any OPTIONAL toolkit detects an authorization request
        # (e.g., user mentions the toolkit but hasn't authorized yet)
        for config in self.toolkit_configs:
            if not config.is_required():
                auth_prompt = config.check_authorization_request(message, user_id)
                if auth_prompt:
                    return self._create_simple_response(auth_prompt)

        # No configuration handling needed, proceed to agent
        return None

    def run(self, message: str, user_id: str | None = None, **kwargs) -> Any:
        """Run the agent with configuration management.

        Flow:
        1. Check if user is configured
        2. If not configured, handle configuration (extract tokens or prompt)
        3. If configured, create agent (if needed) and run it

        Args:
            message: User message
            user_id: User identifier from OpenWebUI
            **kwargs: Additional arguments to pass to wrapped agent

        Returns:
            RunResponse from agent or configuration prompt
        """
        # Check configuration and handle if needed
        config_response = self._handle_configuration(message, user_id)

        # If config_response is not None, user needs to configure
        if config_response is not None:
            return config_response

        # User is configured, get/create agent and run it
        if not user_id:
            error_msg = "❌ User ID is required to create an agent."
            logger.error("Cannot create agent: user_id is None")
            return self._create_simple_response(error_msg)

        try:
            agent = self._get_or_create_agent(user_id)
            return agent.run(message, user_id=user_id, **kwargs)
        except Exception as e:
            # Agent creation or execution failed
            error_msg = f"❌ Error: {str(e)}"
            logger.error(f"Failed to run agent for user {user_id}: {e}")
            return self._create_simple_response(error_msg)

    async def _arun_non_streaming(self, message: str, user_id: str | None = None, **kwargs):
        """Internal async method for non-streaming mode."""
        # Check configuration and handle if needed
        config_response = self._handle_configuration(message, user_id)

        if config_response is not None:
            return config_response

        if not user_id:
            error_msg = "❌ User ID is required to create an agent."
            logger.error("Cannot create agent: user_id is None")
            return self._create_simple_response(error_msg)

        try:
            agent = self._get_or_create_agent(user_id)
            return await agent.arun(message, user_id=user_id, **kwargs)
        except Exception as e:
            # Agent creation or execution failed
            error_msg = f"❌ Error: {str(e)}"
            logger.error(f"Failed to run agent for user {user_id}: {e}")
            return self._create_simple_response(error_msg)

    async def _arun_streaming(self, message: str, user_id: str | None = None, **kwargs):
        """Internal async generator for streaming mode."""
        # Check configuration and handle if needed
        config_response = self._handle_configuration(message, user_id)

        if config_response is not None:
            content = (
                config_response.content
                if hasattr(config_response, "content")
                else str(config_response)
            )
            yield content
            return

        if not user_id:
            error_msg = "❌ User ID is required to create an agent."
            logger.error("Cannot create agent: user_id is None")
            yield error_msg
            return

        try:
            agent = self._get_or_create_agent(user_id)

            # When streaming, agent.arun() returns an async generator directly
            # Don't await it, just iterate over it
            async for chunk in agent.arun(message, user_id=user_id, **kwargs):
                yield chunk
        except Exception as e:
            # Agent creation or execution failed
            error_msg = f"❌ Error: {str(e)}"
            logger.error(f"Failed to run agent for user {user_id}: {e}")
            yield error_msg

    def arun(self, message: str, user_id: str | None = None, **kwargs):
        """Async version of run() with same configuration management logic.

        Handles both streaming and non-streaming modes. Returns either a coroutine
        (non-streaming) or an async generator (streaming) based on the stream parameter.

        Args:
            message: User message
            user_id: User identifier from OpenWebUI
            **kwargs: Additional arguments to pass to wrapped agent

        Returns:
            Coroutine (non-streaming) or AsyncGenerator (streaming)
        """
        stream = kwargs.get("stream", False)

        if stream:
            # Return async generator for streaming
            return self._arun_streaming(message, user_id=user_id, **kwargs)
        else:
            # Return coroutine for non-streaming
            return self._arun_non_streaming(message, user_id=user_id, **kwargs)
