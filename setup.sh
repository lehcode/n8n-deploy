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
if command -v elek-n8n &> /dev/null; then
    echo -e "  ✅ 'elek-n8n' command available"
else
    echo -e "  ${YELLOW}⚠️  'elek-n8n' command not found in PATH${NC}"
    echo "     You may need to restart your shell or add ~/.local/bin to PATH"
fi

# Create quick-start aliases for current session
echo "📝 Setting up temporary aliases for current session..."
alias elek-n8n="python3 ${SCRIPT_DIR}/api/cli.py"
alias elek-n8n-db="python3 ${SCRIPT_DIR}/api/cli.py db"

echo -e "${GREEN}✅ Setup completed!${NC}"
echo ""
echo "Quick start commands:"
echo "  elek-n8n --help        # Show help"
echo "  elek-n8n-db-init       # Initialize database"
echo "  elek-n8n-list          # List workflows"
echo "  elek-n8n-db-status     # Database statistics"
echo ""
echo "To make aliases permanent, restart your shell or run:"
echo "  source ~/.bashrc   # or ~/.zshrc"
