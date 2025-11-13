# AGENTS.md

This file provides guidance to Claude Code when working with this repository.

## Overview

AgentLLM: LiteLLM custom provider exposing Agno agents via OpenAI-compatible API.

Architecture: `[Client] -> [LiteLLM Proxy :8890] -> [Agno Provider] -> [Agno Agent] -> [Gemini API]`

## Common Commands

```bash
# Testing
nox -s test                                    # Unit tests
nox -s integration                             # Integration tests (needs running proxy)
uv run pytest tests/test_custom_handler.py -v  # Specific test

# Development (most common)
nox -s proxy                                   # Terminal 1: local proxy with hot reload
nox -s dev_local_proxy                         # Terminal 2: OpenWebUI container

# Full container stack
nox -s dev                                     # Quick start (reuses images)
nox -s dev_build                               # Force rebuild
nox -s dev_logs                                # View logs

# Code quality
nox -s format                                  # Format
make lint                                      # Lint
```

## Critical Architecture Patterns

### Custom Handler Path Resolution (GOTCHA!)

LiteLLM uses **file-based resolution**, not Python imports:

```
project_root/
├── proxy_config.yaml          # LiteLLM loads from here
├── custom_handler.py           # Stub that imports from src/
└── src/agentllm/
    └── custom_handler.py       # Actual implementation
```

**Why:** `custom_handler.agno_handler` in config → LiteLLM looks for `./custom_handler.py` → stub imports from `agentllm.custom_handler`

### Agent Wrapper Pattern

Agents use wrapper classes (see `ReleaseManager`, `DemoAgent`):
- Intercept `run()`/`arun()` to handle toolkit configuration
- Extract credentials from messages (OAuth codes, API tokens)
- Prompt for missing required configurations
- Per-user isolation with agent caching: `(agent_name, temperature, max_tokens, user_id)`
- Invalidate cache when toolkits are reconfigured

### Toolkit Configuration System

Base class: `BaseToolkitConfig` (`src/agentllm/agents/toolkit_configs/base.py`)

Key methods:
- `is_configured(user_id)` - Check if toolkit is ready
- `extract_and_store_config(message, user_id)` - Parse and save credentials
- `get_config_prompt()` - Return prompt for missing config
- `get_toolkit(user_id)` - Return configured toolkit instance
- `is_required()` - Required toolkits prompt immediately, optional toolkits only when mentioned

### Streaming Format (CRITICAL!)

LiteLLM `CustomLLM` requires **GenericStreamingChunk**, NOT `ModelResponse`:

```python
{
    "text": "content",              # "text" not "content"!
    "finish_reason": "stop" or None,
    "is_finished": True or False,
    ...
}
```

## Adding New Agents

1. Create `src/agentllm/agents/my_agent.py`:
   - Follow wrapper pattern (see `demo_agent.py` for reference)
   - Use `shared_db` for session memory
   - Pass through `temperature` and `max_tokens` to model

2. Import in `src/agentllm/custom_handler.py`

3. Add to `proxy_config.yaml`:
   ```yaml
   - model_name: agno/my-agent
     litellm_params:
       model: agno/my-agent
       custom_llm_provider: agno
   ```

## Key Files

```
src/agentllm/
├── custom_handler.py              # LiteLLM CustomLLM (caching, streaming)
├── agents/
│   ├── release_manager.py         # Production agent wrapper
│   ├── demo_agent.py              # Reference implementation
│   └── toolkit_configs/           # Toolkit config implementations
├── tools/                         # Agno toolkits
└── db/token_storage.py            # SQLite credential storage
```

## Environment

```bash
GEMINI_API_KEY=...                 # Required
LITELLM_MASTER_KEY=...             # Proxy auth (default: sk-agno-test-key-12345)
```

See `.env.secrets.template` for full config.

## TDD Workflow

1. Write failing test
2. Implement feature
3. `nox -s test`
4. Refactor

Always use `uv run` for Python commands.
