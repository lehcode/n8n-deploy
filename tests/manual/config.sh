#!/bin/bash
# Configuration for n8n-deploy manual testing framework

# Test environment
readonly TEST_BASE_DIR="/tmp/n8n-deploy-manual-test"
__temp_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly MANUAL_TEST_DIR="$__temp_script_dir"
readonly PROJECT_ROOT="$(cd "$MANUAL_TEST_DIR/../.." && pwd)"
readonly CLI_COMMAND="$PROJECT_ROOT/n8n-deploy"
__temp_timestamp="$(date +%Y%m%d_%H%M%S)"
readonly TEST_TIMESTAMP="$__temp_timestamp"

# Color constants
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Test counters (will be exported for subshells)
declare -i TOTAL_TESTS=0
declare -i PASSED_TESTS=0
declare -i FAILED_TESTS=0
declare -i SKIPPED_TESTS=0

# Sample test data
readonly SAMPLE_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkNGEyODkxMy04ODQxLTRhMTAtODIzNC1iODQ2OTE1MmJhZTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU4NzY3MDI4LCJleHAiOjE3NjEyNzg0MDB9.d9u2SovTMfUGZ8EzD4SDLYNUTBarHpdwhv96pO-5imE"
readonly SAMPLE_WF_ID="deAVBp391wvomsWY"
readonly SAMPLE_WF_NAME="Test Workflow Manual"

# Test configuration flags
PAUSE_BETWEEN_SECTIONS=false
VERBOSE_OUTPUT=false
QUICK_MODE=false
