# Registering the Agno Provider in LiteLLM

## Prerequisites

1. Fork or clone the LiteLLM repository:
```bash
git clone https://github.com/BerriAI/litellm.git
cd litellm
```

## Registration Steps

According to the [LiteLLM Provider Registration Docs](https://docs.litellm.ai/docs/provider_registration/), you need to modify 4 files:

### 1. Copy Provider Code

```bash
# From the agentllm project directory
cp -r src/agentllm/provider/transformation.py litellm/llms/agno/chat/
# Create necessary __init__.py files
mkdir -p litellm/llms/agno/chat
touch litellm/llms/agno/__init__.py
touch litellm/llms/agno/chat/__init__.py
```

### 2. Update `litellm/__init__.py`

Add imports for Agno configuration:

```python
# Around line 50-100 where other providers are imported
from litellm.llms.agno.chat.transformation import AgnoChatConfig
```

### 3. Update `litellm/constants.py`

Add `agno` to the LITELLM_CHAT_PROVIDERS list:

```python
LITELLM_CHAT_PROVIDERS = [
    # ... existing providers ...
    "agno",
]
```

### 4. Update `litellm/litellm_core_utils/get_llm_provider_logic.py`

Add model prefix detection for Agno models (around where other providers check their prefixes):

```python
# In the get_llm_provider function
elif model.startswith("agno/"):
    custom_llm_provider = "agno"
    model = model.replace("agno/", "")
```

### 5. Update `litellm/main.py`

Add routing logic for the Agno provider (look for similar provider routing code):

```python
# In the appropriate routing function
if custom_llm_provider == "agno":
    from litellm.llms.agno.chat.transformation import AgnoChatConfig
    config = AgnoChatConfig()
    # Use the config for handling requests
```

## Testing Your Changes

1. Install your modified LiteLLM:
```bash
cd litellm
pip install -e .
```

2. Test with the agentllm proxy:
```bash
cd ../agentllm
nox -s proxy
```

3. Make a test request:
```bash
curl -X POST http://localhost:8890/v1/chat/completions \
  -H "Authorization: Bearer sk-agno-test-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agno/echo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Alternative: Runtime Monkey Patch (For POC Only)

See `scripts/monkey_patch_litellm.py` for a temporary solution that patches LiteLLM at runtime.
This is NOT recommended for production but can help test the integration quickly.

## Contributing Back

If you want to contribute this provider to LiteLLM:

1. Follow their [contribution guidelines](https://github.com/BerriAI/litellm/blob/main/CONTRIBUTING.md)
2. Create a PR with:
   - The provider code
   - Tests
   - Documentation
   - Example usage

## Resources

- [LiteLLM Provider Registration](https://docs.litellm.ai/docs/provider_registration/)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [Agno Framework](https://github.com/agno-agi/agno)
