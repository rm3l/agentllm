#!/bin/bash
#
# Quick registration helper for Agno provider in LiteLLM
# This script copies the provider code and shows what manual changes are needed
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LITELLM_DIR="${PROJECT_DIR}/../litellm"

echo "🚀 AgentLLM → LiteLLM Registration Helper"
echo "=========================================="
echo ""

# Check if LiteLLM exists
if [ ! -d "$LITELLM_DIR" ]; then
    echo "❌ LiteLLM not found at: $LITELLM_DIR"
    echo ""
    echo "Please clone it first:"
    echo "  cd $(dirname "$PROJECT_DIR")"
    echo "  git clone https://github.com/BerriAI/litellm.git"
    echo ""
    exit 1
fi

echo "✅ Found LiteLLM at: $LITELLM_DIR"
echo ""

# Create directories
echo "📁 Creating directory structure..."
mkdir -p "$LITELLM_DIR/litellm/llms/agno/chat"
touch "$LITELLM_DIR/litellm/llms/agno/__init__.py"
touch "$LITELLM_DIR/litellm/llms/agno/chat/__init__.py"
echo "   ✅ Created litellm/llms/agno/chat/"
echo ""

# Copy provider
echo "📄 Copying provider code..."
cp "$PROJECT_DIR/src/agentllm/provider/transformation.py" \
   "$LITELLM_DIR/litellm/llms/agno/chat/"
echo "   ✅ Copied transformation.py"
echo ""

# Copy agent examples
echo "📄 Copying agent examples..."
mkdir -p "$LITELLM_DIR/litellm/llms/agno/agents"
cp "$PROJECT_DIR/src/agentllm/agents/examples.py" \
   "$LITELLM_DIR/litellm/llms/agno/agents/"
echo "   ✅ Copied agents/examples.py"
echo ""

# Fix imports in the copied file
echo "🔧 Fixing imports..."
sed -i.bak 's|from agentllm.agents.examples|from litellm.llms.agno.agents.examples|g' \
    "$LITELLM_DIR/litellm/llms/agno/chat/transformation.py"
rm "$LITELLM_DIR/litellm/llms/agno/chat/transformation.py.bak" 2>/dev/null || true
echo "   ✅ Updated import paths"
echo ""

echo "✨ File copy complete!"
echo ""
echo "⚠️  MANUAL STEPS REQUIRED"
echo "========================"
echo ""
echo "You need to manually edit 4 files in LiteLLM:"
echo ""

echo "1️⃣  litellm/constants.py"
echo "   Add 'agno' to LITELLM_CHAT_PROVIDERS:"
echo "   LITELLM_CHAT_PROVIDERS = ["
echo "       # ... existing providers ..."
echo "       \"agno\","
echo "   ]"
echo ""

echo "2️⃣  litellm/litellm_core_utils/get_llm_provider_logic.py"
echo "   Add in get_llm_provider() function:"
echo "   elif model.startswith(\"agno/\"):"
echo "       custom_llm_provider = \"agno\""
echo "       model = model.replace(\"agno/\", \"\")"
echo ""

echo "3️⃣  litellm/__init__.py"
echo "   Add import:"
echo "   from litellm.llms.agno.chat.transformation import AgnoChatConfig"
echo ""

echo "4️⃣  litellm/main.py"
echo "   Add routing (find similar provider code and adapt)"
echo ""

echo "📖 For detailed instructions, see:"
echo "   $PROJECT_DIR/scripts/register_provider.md"
echo ""

echo "🧪 After making changes, install modified LiteLLM:"
echo "   cd $LITELLM_DIR"
echo "   uv pip install -e ."
echo ""

echo "🚀 Then test the proxy:"
echo "   cd $PROJECT_DIR"
echo "   nox -s proxy"
echo ""
