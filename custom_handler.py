"""Custom handler entry point for LiteLLM proxy.

This file sits at the root so LiteLLM can find it when loading the config.
"""

from agentllm.custom_handler import agno_handler

# Export for LiteLLM to import
__all__ = ["agno_handler"]
