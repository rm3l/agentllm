"""Base class for toolkit configuration managers.

This module provides the abstract base class for toolkit configuration.
Each toolkit (Google Drive, Jira, etc.) implements this interface to handle
its own configuration flow and toolkit provisioning.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseToolkitConfig(ABC):
    """Abstract base class for toolkit configuration managers.

    This class defines the interface for managing toolkit configuration
    in a service-agnostic way. Each toolkit implements this interface
    to handle its specific configuration requirements.

    Architecture:
        - Each config class is instantiated once per ReleaseManager
        - Config classes manage per-user configuration data internally
        - ReleaseManager calls generic methods without knowing service details
    """

    def __init__(self):
        """Initialize the configuration manager.

        Subclasses should initialize:
        - Per-user configuration storage
        - Per-user toolkit instances
        - Any service-specific settings
        """
        # Store per-user configurations
        self._user_configs: dict[str, dict[str, str]] = {}

    def is_required(self) -> bool:
        """Check if this toolkit configuration is required.

        Required toolkits will prompt users for configuration immediately.
        Optional toolkits only prompt when the user requests their features.

        Returns:
            True if required (default), False if optional
        """
        return True  # Default: all toolkits are required

    @abstractmethod
    def is_configured(self, user_id: str) -> bool:
        """Check if this toolkit is fully configured for a user.

        Args:
            user_id: User identifier

        Returns:
            True if all required configuration is present, False otherwise
        """
        pass

    @abstractmethod
    def extract_and_store_config(self, message: str, user_id: str) -> str | None:
        """Try to extract configuration from user message and store it.

        This method should:
        1. Check if configuration tokens/codes are present in the message
        2. Extract and validate them
        3. Store the configuration if valid
        4. Return a confirmation message

        Args:
            message: User message that may contain configuration
            user_id: User identifier

        Returns:
            Confirmation message if config was extracted and stored,
            None if no configuration found in message

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    @abstractmethod
    def get_config_prompt(self, user_id: str) -> str | None:
        """Get prompt for missing configuration.

        This method should return a user-friendly prompt explaining
        what configuration is needed and how to provide it.

        Args:
            user_id: User identifier

        Returns:
            Prompt string if configuration is needed, None if fully configured
        """
        pass

    @abstractmethod
    def get_toolkit(self, user_id: str) -> Any | None:
        """Get toolkit instance for user if configured.

        Args:
            user_id: User identifier

        Returns:
            Toolkit instance if user is configured, None otherwise
        """
        pass

    @abstractmethod
    def check_authorization_request(self, message: str, user_id: str) -> str | None:
        """Check if message requests this toolkit and handle authorization.

        This method should:
        1. Detect if the message mentions this toolkit's features
        2. Check if user is already authorized
        3. Return authorization prompt if needed

        Args:
            message: User message
            user_id: User identifier

        Returns:
            Authorization prompt if user needs to authorize,
            None if already authorized or message doesn't mention this toolkit
        """
        pass

    def requires_agent_recreation(self, config_name: str) -> bool:
        """Check if storing this config requires recreating the agent.

        Override this to return True for configurations that add new tools
        to the agent (e.g., OAuth completion that enables toolkit).

        Args:
            config_name: Name of the configuration being stored

        Returns:
            True if agent should be recreated, False otherwise
        """
        return False

    def get_agent_instructions(self, user_id: str) -> list[str]:
        """Get agent instructions based on toolkit configuration.

        Override this to provide toolkit-specific instructions when configured.

        Args:
            user_id: User identifier

        Returns:
            List of instruction strings to add to agent
        """
        return []
