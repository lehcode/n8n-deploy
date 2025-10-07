#!/bin/bash
# 🎭 n8n Workflow Manager Setup Script
# Quick setup script for bash/zsh environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎭 n8n Workflow Manager Setup${NC}"
echo "=================================================="

# Check Python version
echo "🐍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "  ✅ Python ${PYTHON_VERSION} found"

# Check if pip is available
if ! python3 -m pip --version &> /dev/null; then
    echo -e "${RED}❌ pip is required but not available${NC}"
    exit 1
fi

# Run Python installer
echo "🔧 Running Python installer..."
python3 "${SCRIPT_DIR}/install.py"

# Verify installation
echo "🧪 Quick verification..."
if command -v n8n-deploy &> /dev/null; then
    echo -e "  ✅ 'n8n-deploy' command available"
else
    echo -e "  ${YELLOW}⚠️  'n8n-deploy' command not found in PATH${NC}"
    echo "     You may need to restart your shell or add ~/.local/bin to PATH"
fi

echo -e "${GREEN}✅ Setup completed!${NC}"
echo ""
echo "Quick start commands:"
echo "  n8n-deploy --help          # Show help"
echo "  n8n-deploy db init         # Initialize database"
echo "  n8n-deploy wf list         # List workflows"
echo "  n8n-deploy db status       # Database statistics"
echo "  n8n-deploy apikey list     # List API keys"
echo ""
echo "For more information:"
echo "  n8n-deploy --help"
echo "  cat README.md"
