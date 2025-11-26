#!/bin/bash
#
# Simulate GitLab CI Environment Locally
# Run this script before pushing to catch CI failures early
#

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔧 Running in CI simulation mode...${NC}"
echo ""

# ============================================
# Push Debug Information
# ============================================
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}  Debug: Push Context${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"

# Git state
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")
CURRENT_COMMIT=$(git rev-parse --short HEAD)
CURRENT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "none")

echo -e "${BLUE}Branch:${NC} $CURRENT_BRANCH"
echo -e "${BLUE}Commit:${NC} $CURRENT_COMMIT"
echo -e "${BLUE}Tag:${NC} $CURRENT_TAG"

# Remote tracking
if [ "$CURRENT_BRANCH" != "detached" ]; then
    UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "none")
    if [ "$UPSTREAM" != "none" ]; then
        AHEAD=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "?")
        BEHIND=$(git rev-list --count HEAD..@{u} 2>/dev/null || echo "?")
        echo -e "${BLUE}Upstream:${NC} $UPSTREAM (ahead: $AHEAD, behind: $BEHIND)"
    else
        echo -e "${BLUE}Upstream:${NC} not set"
    fi
fi

# Uncommitted changes
STAGED=$(git diff --cached --name-only | wc -l)
UNSTAGED=$(git diff --name-only | wc -l)
UNTRACKED=$(git ls-files --others --exclude-standard | wc -l)
echo -e "${BLUE}Working tree:${NC} staged=$STAGED, unstaged=$UNSTAGED, untracked=$UNTRACKED"
echo ""

# Simulate CI environment variables
export N8N_DEPLOY_TESTING=1
export GIT_DEPTH=0  # CI uses full git history
export ENVIRONMENT=production  # CI doesn't load .env files

# Check if we're in a git repository with tags
echo -e "${YELLOW}📋 Checking git environment...${NC}"
if ! git describe --tags --always >/dev/null 2>&1; then
    echo -e "${RED}⚠️  Warning: No git tags found. Version detection may fail like in CI shallow clones.${NC}"
    echo -e "${YELLOW}   Run: git fetch --tags${NC}"
fi

# Check Python version (CI uses 3.9)
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo -e "${GREEN}✓${NC} Python version: $PYTHON_VERSION (CI uses 3.9)"

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Warning: No virtual environment detected. Activating .venv...${NC}"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}✗ No .venv found. Create with: uv venv --python python3 .venv${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Phase 1: Security Checks${NC}"
echo -e "${YELLOW}════════════════════════════════════════${NC}"

echo -e "\n${GREEN}Running secret detection with gitleaks...${NC}"
if command -v gitleaks >/dev/null 2>&1; then
    gitleaks git . --verbose --redact --config .gitleaks.toml || {
        echo -e "${RED}✗ Secret detection failed${NC}"
        exit 1
    }
else
    echo -e "${YELLOW}⚠️  gitleaks not installed. Skipping (CI requires it).${NC}"
fi

echo -e "\n${GREEN}Running security scan with bandit...${NC}"
bandit -r api/ -f json --exclude tests/ >/dev/null || {
    echo -e "${RED}✗ Bandit security scan failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Bandit passed${NC}"

echo -e "\n${GREEN}Running pattern-based security with semgrep...${NC}"
if command -v semgrep >/dev/null 2>&1; then
    semgrep --config=auto api/ --json --error >/dev/null || {
        echo -e "${RED}✗ Semgrep scan failed${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Semgrep passed${NC}"
else
    echo -e "${YELLOW}⚠️  semgrep not installed. Skipping (CI requires it).${NC}"
fi

echo ""
echo -e "${YELLOW}════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Phase 2: Quality Checks${NC}"
echo -e "${YELLOW}════════════════════════════════════════${NC}"

echo -e "\n${GREEN}Running type checking with mypy...${NC}"
mypy api/ --strict --show-error-codes || {
    echo -e "${RED}✗ Type checking failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Type checking passed${NC}"

echo -e "\n${GREEN}Checking code formatting with black...${NC}"
if ! black --check api/ >/dev/null 2>&1; then
    echo -e "${RED}✗ Code not formatted. Run 'black api/' before pushing.${NC}"
    echo -e "${YELLOW}   Tip: Pre-commit hook should auto-format on commit.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Code formatting OK${NC}"

echo ""
echo -e "${YELLOW}════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Phase 3: Tests${NC}"
echo -e "${YELLOW}════════════════════════════════════════${NC}"

echo -e "\n${GREEN}Running unit tests...${NC}"
python run_tests.py --unit --no-deps-check --quiet || {
    echo -e "${RED}✗ Unit tests failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Unit tests passed${NC}"

echo -e "\n${GREEN}Running integration tests...${NC}"
python run_tests.py --integration --no-deps-check --quiet || {
    echo -e "${RED}✗ Integration tests failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Integration tests passed${NC}"

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ All CI checks passed!${NC}"
echo -e "${GREEN}  Safe to push to remote${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
