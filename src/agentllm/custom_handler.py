"""Custom LiteLLM handler for Agno provider using dynamic registration."""

import logging
import time
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

import litellm
from litellm import CustomLLM
from litellm.types.utils import Choices, Message, ModelResponse
from agno.db.sqlite import SqliteDb

from agentllm.agents.examples import get_agent

# Configure logging for our custom handler
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File handler for detailed logs
file_handler = logging.FileHandler('agno_handler.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Console handler for important logs only
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '[AGNO] %(levelname)s: %(message)s'
))

logger.addHandler(file_handler)
logger.addHandler(console_handler)


class AgnoCustomLLM(CustomLLM):
    """Custom LiteLLM handler for Agno agents.

    This allows dynamic registration without modifying LiteLLM source code.
    Supports Agno session management for conversation continuity.
    """

    def _extract_session_info(self, kwargs: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """Extract session_id and user_id from request kwargs.

        OpenWebUI and other clients may send session identifiers in different ways:
        - metadata.session_id
        - user (email or username)
        - Custom headers passed through

        Args:
            kwargs: Request parameters

        Returns:
            Tuple of (session_id, user_id)
        """
        # Try to extract user_id from metadata or user field
        user_id = kwargs.get("user")
        if not user_id and "metadata" in kwargs:
            user_id = kwargs["metadata"].get("user_id") or kwargs["metadata"].get("user")

        # Try to extract session_id from metadata
        session_id = None
        if "metadata" in kwargs:
            session_id = kwargs["metadata"].get("session_id") or kwargs["metadata"].get("conversation_id")

        # If no session_id, we could use user_id as base for session
        # Agno will auto-generate session_id if not provided

        logger.debug(f"Extracted session info: user_id={user_id}, session_id={session_id}")
        return session_id, user_id

    def completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        api_base: Optional[str] = None,
        custom_llm_provider: str = "agno",
        **kwargs
    ) -> ModelResponse:
        """Handle completion requests for Agno agents.

        Args:
            model: Model name (e.g., "agno/echo" or just "echo")
            messages: OpenAI-format messages
            api_base: API base URL (not used for in-process)
            custom_llm_provider: Provider name
            **kwargs: Additional parameters (stream, temperature, etc.)

        Returns:
            ModelResponse object
        """
        logger.info(f"completion() called with model={model}")
        logger.info(f"kwargs: {kwargs}")
        logger.info(f"messages: {messages}")

        # Extract agent name from model (handle both "agno/echo" and "echo")
        agent_name = model.replace("agno/", "")

        # Extract OpenAI parameters to pass to agent
        temperature = kwargs.get("temperature")
        max_tokens = kwargs.get("max_tokens")

        # Get the agent with model parameters
        try:
            agent = get_agent(
                agent_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except KeyError as e:
            raise Exception(f"Agent '{agent_name}' not found. {e}")

        # Extract user message from messages (last user message)
        user_message = self._extract_user_message(messages)

        # Extract session info for conversation continuity
        session_id, user_id = self._extract_session_info(kwargs)

        # Check if streaming is requested
        stream = kwargs.get("stream", False)

        if stream:
            # Return streaming iterator
            return self.streaming(
                model=model,
                messages=messages,
                api_base=api_base,
                custom_llm_provider=custom_llm_provider,
                **kwargs
            )

        # Run the agent with session management
        # Agno will automatically handle conversation history with add_history_to_context=True
        response = agent.run(
            user_message,
            stream=False,
            session_id=session_id,
            user_id=user_id
        )

        # Extract content from response
        content = response.content if hasattr(response, "content") else str(response)

        # Build ModelResponse with proper types
        message = Message(role="assistant", content=content)
        choice = Choices(
            finish_reason="stop",
            index=0,
            message=message
        )

        model_response = ModelResponse()
        model_response.model = model
        model_response.choices = [choice]
        model_response.usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        return model_response

    def streaming(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        api_base: Optional[str] = None,
        custom_llm_provider: str = "agno",
        **kwargs
    ) -> Iterator[Dict[str, Any]]:
        """Handle streaming requests for Agno agents.

        Note: Streaming is not fully supported in sync mode.
        Returns a single complete response instead of chunks.
        For true streaming, use async requests which will call astreaming().

        Args:
            model: Model name
            messages: OpenAI-format messages
            api_base: API base URL (not used)
            custom_llm_provider: Provider name
            **kwargs: Additional parameters

        Yields:
            GenericStreamingChunk dictionary with text field
        """
        # Get the complete response
        result = self.completion(
            model=model,
            messages=messages,
            api_base=api_base,
            custom_llm_provider=custom_llm_provider,
            **{k: v for k, v in kwargs.items() if k != 'stream'}
        )

        # Extract content from the ModelResponse
        content = ""
        if result.choices and len(result.choices) > 0:
            content = result.choices[0].message.content or ""

        # Return as GenericStreamingChunk format (required by CustomLLM interface)
        yield {
            "text": content,
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "tool_use": None,
            "usage": {
                "completion_tokens": result.usage.get("completion_tokens", 0) if result.usage else 0,
                "prompt_tokens": result.usage.get("prompt_tokens", 0) if result.usage else 0,
                "total_tokens": result.usage.get("total_tokens", 0) if result.usage else 0,
            },
        }

    async def acompletion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        api_base: Optional[str] = None,
        custom_llm_provider: str = "agno",
        **kwargs
    ) -> ModelResponse:
        """Async completion using agent.arun().

        Args:
            model: Model name (e.g., "agno/echo" or just "echo")
            messages: OpenAI-format messages
            api_base: API base URL (not used for in-process)
            custom_llm_provider: Provider name
            **kwargs: Additional parameters (stream, temperature, etc.)

        Returns:
            ModelResponse object
        """
        logger.info(f"acompletion() called with model={model}")
        logger.info(f"kwargs: {kwargs}")
        logger.info(f"messages: {messages}")

        # Extract agent name from model
        agent_name = model.replace("agno/", "")

        # Extract OpenAI parameters to pass to agent
        temperature = kwargs.get("temperature")
        max_tokens = kwargs.get("max_tokens")

        # Get the agent with model parameters
        try:
            agent = get_agent(
                agent_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except KeyError as e:
            raise Exception(f"Agent '{agent_name}' not found. {e}")

        # Extract user message
        user_message = self._extract_user_message(messages)

        # Extract session info for conversation continuity
        session_id, user_id = self._extract_session_info(kwargs)

        # Run the agent asynchronously with session management
        response = await agent.arun(
            user_message,
            stream=False,
            session_id=session_id,
            user_id=user_id
        )

        # Extract content from response
        content = response.content if hasattr(response, "content") else str(response)

        # Build ModelResponse with proper types
        message = Message(role="assistant", content=content)
        choice = Choices(
            finish_reason="stop",
            index=0,
            message=message
        )

        model_response = ModelResponse()
        model_response.model = model
        model_response.choices = [choice]
        model_response.usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        return model_response

    async def astreaming(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        api_base: Optional[str] = None,
        custom_llm_provider: str = "agno",
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """Async streaming using Agno's native streaming support.

        Args:
            model: Model name
            messages: OpenAI-format messages
            api_base: API base URL (not used)
            custom_llm_provider: Provider name
            **kwargs: Additional parameters

        Yields:
            GenericStreamingChunk dictionaries with text field
        """
        logger.info(f"astreaming() called with model={model}")
        logger.info(f"kwargs: {kwargs}")
        logger.info(f"messages: {messages}")

        # Extract agent name
        agent_name = model.replace("agno/", "")

        # Extract OpenAI parameters
        temperature = kwargs.get("temperature")
        max_tokens = kwargs.get("max_tokens")

        # Get the agent with model parameters
        try:
            agent = get_agent(
                agent_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except KeyError as e:
            raise Exception(f"Agent '{agent_name}' not found. {e}")

        # Extract user message
        user_message = self._extract_user_message(messages)

        # Extract session info for conversation continuity
        session_id, user_id = self._extract_session_info(kwargs)

        # Use Agno's real async streaming with session management
        chunk_count = 0

        async for chunk in agent.arun(
            user_message,
            stream=True,
            session_id=session_id,
            user_id=user_id
        ):
            # Extract content from chunk
            content = chunk.content if hasattr(chunk, "content") else str(chunk)

            if not content:
                continue

            # Yield GenericStreamingChunk format
            yield {
                "text": content,
                "finish_reason": None,
                "index": 0,
                "is_finished": False,
                "tool_use": None,
                "usage": {
                    "completion_tokens": 0,
                    "prompt_tokens": 0,
                    "total_tokens": 0,
                },
            }
            chunk_count += 1

        # Send final chunk with finish_reason
        yield {
            "text": "",
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "tool_use": None,
            "usage": {
                "completion_tokens": chunk_count,
                "prompt_tokens": 0,
                "total_tokens": chunk_count,
            },
        }

    def _extract_user_message(self, messages: List[Dict[str, Any]]) -> str:
        """Extract the last user message from messages list.

        Args:
            messages: OpenAI-format messages

        Returns:
            User message content
        """
        # Find the last user message
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")

        # If no user message found, concatenate all messages
        return " ".join(msg.get("content", "") for msg in messages)

    # Note: _add_messages_to_agent() method removed
    # Agno now handles conversation history automatically via:
    # - db=shared_db (enables session storage)
    # - add_history_to_context=True (adds previous messages to context)
    # - session_id/user_id passed to agent.run()


# Create a singleton instance
agno_handler = AgnoCustomLLM()


# Register the handler
def register_agno_provider():
    """Register the Agno provider with LiteLLM.

    Call this before using the proxy or making completion calls.
    """
    litellm.custom_provider_map = [
        {"provider": "agno", "custom_handler": agno_handler}
    ]
    print("✅ Registered Agno provider with LiteLLM")


if __name__ == "__main__":
    # Auto-register when run as script
    register_agno_provider()
    print("\n🚀 Agno provider registered!")
    print("   You can now use models like: agno/echo, agno/assistant")
