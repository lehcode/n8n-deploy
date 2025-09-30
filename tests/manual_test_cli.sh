#!/bin/bash
# n8n-deploy Manual CLI Testing Script
# Comprehensive testing suite for all n8n-deploy CLI functionality

# set -e removed to allow expected test failures

# Test configuration
readonly TEST_BASE_DIR="/tmp/n8n-deploy-manual-test"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CLI_COMMAND="$SCRIPT_DIR/../n8n-deploy"
readonly TEST_TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# Color constants
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Test counters
declare -i TOTAL_TESTS=0
declare -i PASSED_TESTS=0
declare -i FAILED_TESTS=0
declare -i SKIPPED_TESTS=0

# Test configuration flags
PAUSE_BETWEEN_SECTIONS=false
VERBOSE_OUTPUT=false
QUICK_MODE=false
TEST_SECTIONS=()

# Sample data
readonly SAMPLE_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkNGEyODkxMy04ODQxLTRhMTAtODIzNC1iODQ2OTE1MmJhZTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU4NzY3MDI4LCJleHAiOjE3NjEyNzg0MDB9.d9u2SovTMfUGZ8EzD4SDLYNUTBarHpdwhv96pO-5imE"
readonly SAMPLE_WF_ID="deAVBp391wvomsWY"
readonly SAMPLE_WF_NAME="Test Workflow Manual"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

print_banner() {
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  n8n-deploy Manual CLI Testing Suite${NC}"
    echo -e "${CYAN}  Test Run: ${TEST_TIMESTAMP}${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo
}

print_section() {
    echo
    echo -e "${PURPLE}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${NC}"
    echo -e "${PURPLE}┃  $1${NC}"
    echo -e "${PURPLE}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${NC}"
    echo
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
}

# Test execution wrapper
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit_code="${3:-0}"
    local description="${4:-}"

    ((TOTAL_TESTS++))

    if [[ $VERBOSE_OUTPUT == true ]]; then
        echo -e "${CYAN}Test $TOTAL_TESTS:${NC} $test_name"
        [[ -n "$description" ]] && echo -e "  ${BLUE}Description:${NC} $description"
        echo -e "  ${BLUE}Command:${NC} $test_command"
    else
        echo -n -e "${CYAN}Test $TOTAL_TESTS:${NC} $test_name ... "
    fi

    # Execute the command and capture output
    local output
    local exit_code
    if output=$(eval "$test_command" 2>&1); then
        exit_code=0
    else
        exit_code=$?
    fi

    # Check result
    if [[ $exit_code -eq $expected_exit_code ]]; then
        ((PASSED_TESTS++))
        if [[ $VERBOSE_OUTPUT == true ]]; then
            log_success "PASSED"
            [[ -n "$output" ]] && echo "  Output: $output"
        else
            echo -e "${GREEN}PASS${NC}"
        fi
        return 0
    else
        ((FAILED_TESTS++))
        if [[ $VERBOSE_OUTPUT == true ]]; then
            log_error "FAILED (exit code: $exit_code, expected: $expected_exit_code)"
            [[ -n "$output" ]] && echo "  Output: $output"
        else
            echo -e "${RED}FAIL${NC}"
            echo "    Expected exit code: $expected_exit_code, got: $exit_code"
            [[ -n "$output" ]] && echo "    Output: $output"
        fi
        return 1
    fi
}

# Validate command output
validate_output() {
    local test_name="$1"
    local command="$2"
    local expected_pattern="$3"
    local description="${4:-}"

    ((TOTAL_TESTS++))

    if [[ $VERBOSE_OUTPUT == true ]]; then
        echo -e "${CYAN}Test $TOTAL_TESTS:${NC} $test_name"
        [[ -n "$description" ]] && echo -e "  ${BLUE}Description:${NC} $description"
        echo -e "  ${BLUE}Command:${NC} $command"
        echo -e "  ${BLUE}Expected Pattern:${NC} $expected_pattern"
    else
        echo -n -e "${CYAN}Test $TOTAL_TESTS:${NC} $test_name ... "
    fi

    local output
    if output=$(eval "$command" 2>&1); then
        if echo "$output" | grep -q "$expected_pattern"; then
            ((PASSED_TESTS++))
            if [[ $VERBOSE_OUTPUT == true ]]; then
                log_success "PASSED"
                echo "  Output: $output"
            else
                echo -e "${GREEN}PASS${NC}"
            fi
            return 0
        else
            ((FAILED_TESTS++))
            if [[ $VERBOSE_OUTPUT == true ]]; then
                log_error "FAILED (pattern not found)"
                echo "  Output: $output"
            else
                echo -e "${RED}FAIL${NC}"
                echo "    Pattern '$expected_pattern' not found in output"
                echo "    Output: $output"
            fi
            return 1
        fi
    else
        ((FAILED_TESTS++))
        local exit_code=$?
        if [[ $VERBOSE_OUTPUT == true ]]; then
            log_error "FAILED (command failed with exit code: $exit_code)"
            echo "  Output: $output"
        else
            echo -e "${RED}FAIL${NC}"
            echo "    Command failed with exit code: $exit_code"
            echo "    Output: $output"
        fi
        return 1
    fi
}

# Setup test environment
setup_test_env() {
    log_info "Setting up test environment..."

    # Clean up any existing test directory
    if [[ -d "$TEST_BASE_DIR" ]]; then
        rm -rf "$TEST_BASE_DIR"
    fi

    # Create test directories
    mkdir -p "$TEST_BASE_DIR"/{app,flow,backup}

    # Create sample workflow file (using workflow ID as filename)
    create_sample_workflow "$TEST_BASE_DIR/flow/workflows"

    log_success "Test environment created at $TEST_BASE_DIR"
}

# Create sample workflow JSON file
create_sample_workflow() {
    local workflow_dir="$1"
    mkdir -p "$workflow_dir"

    cat > "$workflow_dir/${SAMPLE_WF_ID}.json" << 'EOF'
{
  "id": "deAVBp391wvomsWY",
  "name": "Test Workflow Manual",
  "active": false,
  "nodes": [
    {
      "id": "node1",
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "position": [250, 300],
      "parameters": {}
    },
    {
      "id": "node2",
      "name": "Set",
      "type": "n8n-nodes-base.set",
      "position": [450, 300],
      "parameters": {
        "values": {
          "string": [
            {
              "name": "message",
              "value": "Hello from manual test!"
            }
          ]
        }
      }
    }
  ],
  "connections": {
    "Start": {
      "main": [
        [
          {
            "node": "Set",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "createdAt": "2024-01-01T00:00:00.000Z",
  "updatedAt": "2024-01-01T00:00:00.000Z",
  "settings": {},
  "staticData": null,
  "tags": []
}
EOF
}

# Cleanup test environment
cleanup_test_env() {
    log_info "Cleaning up test environment..."
    if [[ -d "$TEST_BASE_DIR" ]]; then
        rm -rf "$TEST_BASE_DIR"
        log_success "Test environment cleaned up"
    fi
}

# Pause between sections if requested
pause_if_requested() {
    if [[ $PAUSE_BETWEEN_SECTIONS == true ]]; then
        echo
        read -p "Press Enter to continue to next section..."
        echo
    fi
}

# Check if database exists (must be initialized with 'db init' first)
check_database_exists() {
    local app_dir="$1"
    local test_section="$2"
    if [[ ! -f "$app_dir/n8n-deploy.db" ]]; then
        log_warning "Database not initialized for $test_section tests"
        log_warning "Run 'db' test section first or manually run: n8n-deploy db init --app-dir $app_dir"
        return 1
    fi
    return 0
}

# =============================================================================
# TEST CATEGORIES
# =============================================================================

# Test 1: CLI Help & Version
test_cli_help_version() {
    print_section "Test Category 1: CLI Help & Version"

    # Basic help
    run_test "CLI help" "$CLI_COMMAND --help" 0 "Display main CLI help"
    validate_output "CLI help content" "$CLI_COMMAND --help" "n8n-deploy - a simple N8N Workflow Manager"

    # Version
    run_test "CLI version" "$CLI_COMMAND --version" 0 "Display version information"
    validate_output "Version format" "$CLI_COMMAND --version" "version 2.0.0"

    # Invalid option
    run_test "Invalid option" "$CLI_COMMAND --invalid-option" 2 "Test invalid option handling"

    # Command help
    run_test "Workflow command help" "$CLI_COMMAND wf --help" 0 "Display wf command help"
    run_test "DB command help" "$CLI_COMMAND db --help" 0 "Display db command help"
    run_test "Apikey command help" "$CLI_COMMAND apikey --help" 0 "Display apikey command help"

    pause_if_requested
}

# Test 2: Database Operations
test_database_operations() {
    print_section "Test Category 2: Database Operations"

    local app_dir="$TEST_BASE_DIR/app"

    # Database initialization
    run_test "DB init" "$CLI_COMMAND db init --app-dir $app_dir --no-emoji --import" 0 "Initialize database"

    # Test --import flag with existing database
    run_test "DB init with --import (existing)" "$CLI_COMMAND db init --app-dir $app_dir --import --no-emoji" 0 "Import existing database without prompt"

    # Test JSON format output
    run_test "DB init JSON format" "$CLI_COMMAND db init --app-dir $app_dir --format json --import" 0 "Initialize with JSON output"
    validate_output "DB init JSON content" "$CLI_COMMAND db init --app-dir $app_dir --format json --import" '"success": true'

    # Database status
    run_test "DB status table" "$CLI_COMMAND db status --app-dir $app_dir --no-emoji" 0 "Check database status"
    run_test "DB status JSON" "$CLI_COMMAND db status --app-dir $app_dir --format json --no-emoji" 0 "Check database status in JSON"
    validate_output "DB status content" "$CLI_COMMAND db status --app-dir $app_dir --no-emoji" "Database Path"

    # Database maintenance
    run_test "DB compact" "$CLI_COMMAND db compact --app-dir $app_dir --no-emoji" 0 "Compact database"
    run_test "DB compact with emoji" "$CLI_COMMAND db compact --app-dir $app_dir" 0 "Compact database with emoji output"

    # Database backup
    local backup_file="$TEST_BASE_DIR/backup/test_backup.db"
    run_test "DB backup" "$CLI_COMMAND db backup $backup_file --app-dir $app_dir --no-emoji" 0 "Create database backup"

    # Test backup file exists
    if [[ -f "$backup_file" ]]; then
        log_success "Backup file created successfully"
        ((PASSED_TESTS++))
    else
        log_error "Backup file not created"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))

    pause_if_requested
}

# Test 3: API Key Management
test_api_key_management() {
    print_section "Test Category 3: API Key Management"

    local app_dir="$TEST_BASE_DIR/app"

    # Check database exists (must be initialized with 'db init' first)
    if ! check_database_exists "$app_dir" "API Key"; then
        ((SKIPPED_TESTS+=12))  # Skip all API key tests
        ((TOTAL_TESTS+=12))
        return
    fi

    # Add API key
    run_test "Add API key" "echo '$SAMPLE_API_KEY' | $CLI_COMMAND apikey add - --name test_key --app-dir $app_dir --no-emoji" 0 "Add new API key"

    # List API keys
    run_test "List API keys table" "$CLI_COMMAND apikey list --app-dir $app_dir --no-emoji" 0 "List API keys in table format"
    run_test "List API keys JSON" "$CLI_COMMAND apikey list --app-dir $app_dir --format json" 0 "List API keys in JSON format"
    validate_output "API key list content" "$CLI_COMMAND apikey list --app-dir $app_dir --no-emoji" "test_key"

    # Get API key (without showing key)
    run_test "Get API key (no show)" "$CLI_COMMAND apikey get test_key --app-dir $app_dir --no-emoji" 0 "Get API key without showing key"

    # Get API key (with key)
    run_test "Get API key (show)" "$CLI_COMMAND apikey get test_key --show-key --app-dir $app_dir --no-emoji" 0 "Get API key showing actual key"

    # Test API key
    run_test "Test API key" "$CLI_COMMAND apikey test test_key --app-dir $app_dir" 0 "Test API key validity"

    # Add another key for testing
    run_test "Add second API key" "echo '$SAMPLE_API_KEY' | $CLI_COMMAND apikey add - --name test_key2 --description 'Second test key' --expires-in 30 --app-dir $app_dir --no-emoji" 0 "Add second API key with expiration"

    # Deactivate API key
    run_test "Deactivate API key" "$CLI_COMMAND apikey deactivate test_key2 --app-dir $app_dir" 0 "Deactivate API key"

    # Delete API key
    run_test "Delete API key" "$CLI_COMMAND apikey delete test_key2 --confirm --app-dir $app_dir" 0 "Delete API key"

    # Test with invalid key name
    run_test "Invalid key name" "echo '$SAMPLE_API_KEY' | $CLI_COMMAND apikey add - --name 'invalid key!' --app-dir $app_dir" 1 "Test invalid key name handling"

    # Test with invalid JWT format
    run_test "Invalid JWT format" "echo 'not.a.valid.jwt.format' | $CLI_COMMAND apikey add - --name invalid_jwt --app-dir $app_dir" 1 "Test invalid JWT format handling"

    pause_if_requested
}

# Test 4: Workflow Operations
test_workflow_operations() {
    print_section "Test Category 4: Workflow Operations"

    local app_dir="$TEST_BASE_DIR/app"
    local flow_dir="$TEST_BASE_DIR/flow"
    local workflow_file="$flow_dir/workflows/${SAMPLE_WF_ID}.json"

    # Check database exists (must be initialized with 'db init' first)
    if ! check_database_exists "$app_dir" "Workflow"; then
        ((SKIPPED_TESTS+=10))  # Skip all workflow tests
        ((TOTAL_TESTS+=10))
        return
    fi

    # Add workflow
    run_test "Add workflow" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json '$SAMPLE_WF_NAME' --app-dir $app_dir --flow-dir $flow_dir" 0 "Add workflow to database"

    # List workflows
    run_test "List workflows table" "$CLI_COMMAND wf list --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "List workflows in table format"
    run_test "List workflows JSON" "$CLI_COMMAND wf list --app-dir $app_dir --flow-dir $flow_dir --format json" 0 "List workflows in JSON format"
    validate_output "Workflow list content" "$CLI_COMMAND wf list --app-dir $app_dir --flow-dir $flow_dir --no-emoji" "$SAMPLE_WF_NAME"

    # List backupable workflows only
    run_test "List backupable only" "$CLI_COMMAND wf list --only --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "List only backupable workflows"

    # Test add workflow with JSON format output
    run_test "Add workflow JSON output" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json 'Second Test Workflow' --app-dir $app_dir --flow-dir $flow_dir --format json" 0 "Add workflow with JSON output"

    # Search workflows
    run_test "Search workflows by name" "$CLI_COMMAND wf search 'test' --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "Search workflows by name"
    validate_output "Search results" "$CLI_COMMAND wf search 'test' --app-dir $app_dir --flow-dir $flow_dir --no-emoji" "$SAMPLE_WF_NAME"
    run_test "Search workflows by ID" "$CLI_COMMAND wf search '$SAMPLE_WF_ID' --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "Search workflows by workflow ID"
    run_test "Search workflows JSON" "$CLI_COMMAND wf search 'test' --app-dir $app_dir --flow-dir $flow_dir --format json" 0 "Search workflows with JSON output"

    # Get workflow stats
    run_test "Workflow stats table" "$CLI_COMMAND wf stats $SAMPLE_WF_ID --app-dir $app_dir --flow-dir $flow_dir" 0 "Get workflow statistics"
    run_test "Workflow stats JSON" "$CLI_COMMAND wf stats $SAMPLE_WF_ID --app-dir $app_dir --flow-dir $flow_dir --format json" 0 "Get workflow statistics in JSON"

    # Test non-existent workflow
    run_test "Non-existent workflow" "$CLI_COMMAND wf stats 'non-existent-id' --app-dir $app_dir --flow-dir $flow_dir" 1 "Test non-existent workflow handling"

    # Test workflow without file
    rm "$workflow_file"
    run_test "Workflow without file" "$CLI_COMMAND wf list --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "List workflows when file missing"

    # Recreate file for further tests
    create_sample_workflow "$flow_dir/workflows"

    pause_if_requested
}

# Test 5: Backup Operations
test_backup_operations() {
    print_section "Test Category 5: Backup Operations"

    local app_dir="$TEST_BASE_DIR/app"
    local flow_dir="$TEST_BASE_DIR/flow"
    local backup_dir="$TEST_BASE_DIR/backup"

    # Check database exists (must be initialized with 'db init' first)
    if ! check_database_exists "$app_dir" "Backup"; then
        ((SKIPPED_TESTS+=6))  # Skip all backup tests
        ((TOTAL_TESTS+=6))
        return
    fi

    # Create workflow backup
    run_test "Create workflow backup" "$CLI_COMMAND wf backup --backup-dir $backup_dir --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "Create tar.gz backup of workflows"

    # List backups
    run_test "List backups table" "$CLI_COMMAND wf list-backups --backup-dir $backup_dir --app-dir $app_dir --flow-dir $flow_dir" 0 "List backup files"
    run_test "List backups JSON" "$CLI_COMMAND wf list-backups --backup-dir $backup_dir --app-dir $app_dir --flow-dir $flow_dir --format json" 0 "List backup files in JSON"

    # Find the backup file
    local backup_file=$(find "$backup_dir" -name "*.tar.gz" | head -1)

    if [[ -n "$backup_file" && -f "$backup_file" ]]; then
        log_success "Backup file found: $backup_file"

        # Verify backup integrity
        run_test "Verify backup integrity" "$CLI_COMMAND wf verify-backup '$backup_file' --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "Verify backup file integrity"

        # Test restore
        run_test "Restore workflows" "$CLI_COMMAND wf restore '$backup_file' --app-dir $app_dir --flow-dir $flow_dir" 0 "Restore workflows from backup"
    else
        log_error "No backup file found to test verification and restore"
        ((FAILED_TESTS += 2))
        ((TOTAL_TESTS += 2))
    fi

    pause_if_requested
}

# Test 6: Server Integration (Mock scenarios)
test_server_integration() {
    print_section "Test Category 6: Server Integration (Mock scenarios)"

    local app_dir="$TEST_BASE_DIR/app"
    local flow_dir="$TEST_BASE_DIR/flow"
    local mock_server="http://localhost:12345"  # Non-existent server for testing

    # Check database exists (must be initialized with 'db init' first)
    if ! check_database_exists "$app_dir" "Server Integration"; then
        ((SKIPPED_TESTS+=5))  # Skip all server integration tests
        ((TOTAL_TESTS+=5))
        return
    fi

    # Test list-server with no server
    run_test "List server (no URL)" "$CLI_COMMAND wf list-server --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 1 "List server workflows without URL"

    # Test list-server with unreachable server
    run_test "List server (unreachable)" "$CLI_COMMAND wf list-server --server-url $mock_server --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 1 "List server workflows with unreachable server"

    # Test pull with unreachable server
    run_test "Pull workflow (unreachable)" "$CLI_COMMAND wf pull $SAMPLE_WF_ID --server-url $mock_server --app-dir $app_dir --flow-dir $flow_dir" 1 "Pull workflow from unreachable server"

    # Test push with unreachable server
    run_test "Push workflow (unreachable)" "$CLI_COMMAND wf push $SAMPLE_WF_ID --server-url $mock_server --app-dir $app_dir --flow-dir $flow_dir" 1 "Push workflow to unreachable server"

    # Test with skip SSL verify flag
    run_test "List server (skip SSL)" "$CLI_COMMAND wf list-server --server-url $mock_server --skip-ssl-verify --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 1 "List server with SSL verification disabled"

    log_warning "Server integration tests use mock/unreachable endpoints - real server testing requires manual setup"

    pause_if_requested
}

# Test 7: Output Formats
test_output_formats() {
    print_section "Test Category 7: Output Formats"

    local app_dir="$TEST_BASE_DIR/app"
    local flow_dir="$TEST_BASE_DIR/flow"

    # Check database exists (must be initialized with 'db init' first)
    if ! check_database_exists "$app_dir" "Output Format"; then
        ((SKIPPED_TESTS+=6))  # Skip all output format tests
        ((TOTAL_TESTS+=6))
        return
    fi

    # Test emoji vs no-emoji output
    validate_output "Emoji output" "$CLI_COMMAND wf list --app-dir $app_dir --flow-dir $flow_dir" "📋"
    validate_output "No emoji output" "$CLI_COMMAND wf list --app-dir $app_dir --flow-dir $flow_dir --no-emoji" "Workflows"

    # Test table vs JSON formats
    validate_output "Table format" "$CLI_COMMAND wf list --app-dir $app_dir --flow-dir $flow_dir --format table" "Name"
    validate_output "JSON format" "$CLI_COMMAND wf list --app-dir $app_dir --flow-dir $flow_dir --format json" "\\["

    # Test database status formats
    validate_output "DB status table" "$CLI_COMMAND db status --app-dir $app_dir --format table" "Database Path"
    validate_output "DB status JSON" "$CLI_COMMAND db status --app-dir $app_dir --format json" "database_path"

    # Test API key formats
    validate_output "API key table" "$CLI_COMMAND apikey list --app-dir $app_dir --no-emoji" "Name"
    validate_output "API key JSON" "$CLI_COMMAND apikey list --app-dir $app_dir --format json" "\\["

    pause_if_requested
}

# Test 8: Directory Options
test_directory_options() {
    print_section "Test Category 8: Directory Options"

    local app_dir1="$TEST_BASE_DIR/app"
    local app_dir2="$TEST_BASE_DIR/app2"
    local flow_dir1="$TEST_BASE_DIR/flow"
    local flow_dir2="$TEST_BASE_DIR/flow2"

    # Create second set of directories
    mkdir -p "$app_dir2" "$flow_dir2/workflows"

    # Initialize second database
    run_test "Init second DB" "$CLI_COMMAND db init --app-dir $app_dir2 --import --no-emoji" 0 "Initialize second database"

    # Test app-dir option
    validate_output "Different app dir" "$CLI_COMMAND db status --app-dir $app_dir2" "$app_dir2"

    # Test flow-dir option
    create_sample_workflow "$flow_dir2/workflows"
    run_test "Add workflow different dirs" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json '$SAMPLE_WF_NAME' --app-dir $app_dir2 --flow-dir $flow_dir2" 0 "Add workflow with different directories"

    # Test environment variable (simulate)
    export N8N_FLOW_DIR="$flow_dir2"
    validate_output "Environment variable flow dir" "$CLI_COMMAND wf list --app-dir $app_dir2 --no-emoji" "Flow directory"
    unset N8N_FLOW_DIR

    # Test directory precedence - CLI option should override environment
    export N8N_FLOW_DIR="$flow_dir1"
    run_test "Directory precedence" "$CLI_COMMAND wf list --app-dir $app_dir2 --flow-dir $flow_dir2 --no-emoji" 0 "Test directory option precedence"
    unset N8N_FLOW_DIR

    pause_if_requested
}

# Test 9: Error Handling
test_error_handling() {
    print_section "Test Category 9: Error Handling"

    local app_dir="$TEST_BASE_DIR/app"
    local flow_dir="$TEST_BASE_DIR/flow"
    local invalid_dir="/dev/null/invalid_path"

    # Test invalid commands
    run_test "Invalid command" "$CLI_COMMAND invalid-command" 2 "Test invalid command handling"
    run_test "Invalid subcommand" "$CLI_COMMAND db invalid-subcommand" 2 "Test invalid subcommand handling"

    # Test missing required arguments
    run_test "Missing workflow ID" "$CLI_COMMAND wf add" 2 "Test missing required arguments"
    run_test "Missing API key name" "$CLI_COMMAND apikey add testkey" 2 "Test missing API key name"

    # Test invalid directory paths
    run_test "Invalid app dir" "$CLI_COMMAND db status --app-dir $invalid_dir" 1 "Test invalid app directory"
    run_test "Invalid flow dir" "$CLI_COMMAND wf list --app-dir $app_dir --flow-dir $invalid_dir --no-emoji" 0 "Test invalid flow directory (should not fail list)"

    # Test non-existent database operations
    local nonexistent_dir="$TEST_BASE_DIR/nonexistent"
    run_test "Non-existent DB status" "$CLI_COMMAND db status --app-dir $nonexistent_dir" 1 "Test operations on non-existent database"

    # Test remove workflow with confirmation (should fail without --yes)
    run_test "Remove without confirmation" "echo 'n' | $CLI_COMMAND wf remove $SAMPLE_WF_ID --app-dir $app_dir --flow-dir $flow_dir" 1 "Test remove workflow without confirmation"

    # Test remove workflow with --yes flag (should succeed)
    run_test "Remove with --yes flag" "$CLI_COMMAND wf remove $SAMPLE_WF_ID --yes --app-dir $app_dir --flow-dir $flow_dir" 0 "Test remove workflow with --yes flag"

    # Test backup to invalid directory
    run_test "Backup to invalid dir" "$CLI_COMMAND wf backup --backup-dir $invalid_dir --app-dir $app_dir --flow-dir $flow_dir" 1 "Test backup to invalid directory"

    pause_if_requested
}

# Test 10: Edge Cases
test_edge_cases() {
    print_section "Test Category 10: Edge Cases"

    local app_dir="$TEST_BASE_DIR/app"
    local flow_dir="$TEST_BASE_DIR/flow"

    # Check database exists (must be initialized with 'db init' first)
    if ! check_database_exists "$app_dir" "Edge Cases"; then
        ((SKIPPED_TESTS+=11))  # Skip all edge case tests
        ((TOTAL_TESTS+=11))
        return
    fi

    # Test empty database operations
    local empty_app_dir="$TEST_BASE_DIR/empty_app"
    mkdir -p "$empty_app_dir"
    run_test "Init empty DB" "$CLI_COMMAND db init --app-dir $empty_app_dir --import --no-emoji" 0 "Initialize empty database"
    run_test "List empty workflows" "$CLI_COMMAND wf list --app-dir $empty_app_dir --no-emoji" 0 "List workflows in empty database"

    # Test special characters in workflow names (spaces now allowed, but some symbols should still fail)
    local special_wf_id="special-test-id"
    local valid_special_name="Workflow with Spaces (test)"
    local invalid_special_name="workflow@with#invalid&symbols!"
    run_test "Add workflow with spaces" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json '$valid_special_name' --app-dir $app_dir --flow-dir $flow_dir" 0 "Add workflow with spaces and parentheses (should pass)"
    run_test "Add invalid char workflow" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json '$invalid_special_name' --app-dir $app_dir --flow-dir $flow_dir" 1 "Add workflow with invalid characters (should fail)"

    # Test very long arguments
    local long_description="This is a very long description that contains many words and should test the handling of lengthy input parameters in the CLI system to ensure robust operation"
    run_test "Long description" "echo '$SAMPLE_API_KEY' | $CLI_COMMAND apikey add - --name long_test_key --description '$long_description' --app-dir $app_dir --no-emoji" 0 "Test long description handling"

    # Test duplicate workflow ID (first add the original, then try to add duplicate)
    run_test "Add original workflow" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json '$SAMPLE_WF_NAME' --app-dir $app_dir --flow-dir $flow_dir" 0 "Add original workflow for duplicate test"
    run_test "Duplicate workflow ID" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json 'Duplicate Workflow' --app-dir $app_dir --flow-dir $flow_dir" 1 "Test duplicate workflow ID handling"

    # Test operations on deactivated API keys
    run_test "Deactivate API key" "$CLI_COMMAND apikey deactivate long_test_key --app-dir $app_dir" 0 "Deactivate API key for testing"
    run_test "Test deactivated key" "$CLI_COMMAND apikey test long_test_key --app-dir $app_dir" 1 "Test deactivated API key"

    # Test workflow file that exists but is invalid JSON
    local invalid_json_file="$flow_dir/workflows/invalid.json"
    echo "{ invalid json }" > "$invalid_json_file"
    run_test "Add invalid JSON workflow" "$CLI_COMMAND wf add workflows/invalid.json 'invalid_json_workflow' --app-dir $app_dir --flow-dir $flow_dir" 1 "Add workflow with invalid JSON (should fail)"


    pause_if_requested
}

# =============================================================================
# MAIN EXECUTION FUNCTIONS
# =============================================================================

print_summary() {
    echo
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  TEST SUMMARY${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${BLUE}Total Tests:${NC}   $TOTAL_TESTS"
    echo -e "${GREEN}Passed:${NC}        $PASSED_TESTS"
    echo -e "${RED}Failed:${NC}        $FAILED_TESTS"
    echo -e "${YELLOW}Skipped:${NC}       $SKIPPED_TESTS"
    echo

    local success_rate=0
    if [[ $TOTAL_TESTS -gt 0 ]]; then
        success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    fi

    echo -e "${BLUE}Success Rate:${NC}  ${success_rate}%"
    echo

    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
    else
        echo -e "${RED}❌ Some tests failed. Review the output above for details.${NC}"
    fi
    echo -e "${CYAN}============================================================${NC}"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [TEST_SECTIONS...]

Manual CLI testing script for n8n-deploy.

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -p, --pause             Pause between test sections
    -q, --quick             Quick mode (skip some slower tests)
    -c, --clean             Clean up test environment and exit

TEST_SECTIONS (run specific sections only):
    help                    CLI Help & Version tests
    db                      Database Operations tests
    apikey                  API Key Management tests
    workflow                Workflow Operations tests
    backup                  Backup Operations tests
    server                  Server Integration tests
    format                  Output Format tests
    directory               Directory Options tests
    error                   Error Handling tests
    edge                    Edge Cases tests

If no sections specified, all tests will be run.

EXAMPLES:
    $0                      # Run all tests
    $0 -v                   # Run all tests with verbose output
    $0 -p help db           # Run help and database tests with pauses
    $0 --quick workflow     # Run workflow tests in quick mode
    $0 --clean              # Clean up test environment only

EOF
}

run_selected_tests() {
    local sections=("$@")

    # If no sections specified, run all
    if [[ ${#sections[@]} -eq 0 ]]; then
        sections=(help db apikey workflow backup server format directory error edge)
    fi

    for section in "${sections[@]}"; do
        case "$section" in
            help)       test_cli_help_version ;;
            db)         test_database_operations ;;
            apikey)     test_api_key_management ;;
            workflow)   test_workflow_operations ;;
            backup)     test_backup_operations ;;
            server)     test_server_integration ;;
            format)     test_output_formats ;;
            directory)  test_directory_options ;;
            error)      test_error_handling ;;
            edge)       test_edge_cases ;;
            *)
                log_warning "Unknown test section: $section"
                ((SKIPPED_TESTS++))
                ;;
        esac
    done
}

# Main function
main() {
    local clean_only=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE_OUTPUT=true
                shift
                ;;
            -p|--pause)
                PAUSE_BETWEEN_SECTIONS=true
                shift
                ;;
            -q|--quick)
                QUICK_MODE=true
                shift
                ;;
            -c|--clean)
                clean_only=true
                shift
                ;;
            -*)
                echo "Unknown option: $1" >&2
                show_usage >&2
                exit 1
                ;;
            *)
                TEST_SECTIONS+=("$1")
                shift
                ;;
        esac
    done

    # Validate CLI command exists
    if [[ ! -x "$CLI_COMMAND" ]]; then
        log_error "CLI command not found or not executable: $CLI_COMMAND"
        log_info "Make sure you're running this script from the n8n-deploy project root"
        exit 1
    fi

    # Clean up and exit if requested
    if [[ $clean_only == true ]]; then
        cleanup_test_env
        exit 0
    fi

    # Set up signal handlers for cleanup
    trap cleanup_test_env EXIT INT TERM

    print_banner

    log_info "CLI Command: $CLI_COMMAND"
    log_info "Test Base Directory: $TEST_BASE_DIR"
    log_info "Verbose Output: $VERBOSE_OUTPUT"
    log_info "Pause Between Sections: $PAUSE_BETWEEN_SECTIONS"
    log_info "Quick Mode: $QUICK_MODE"
    echo

    # Setup test environment
    setup_test_env

    # Run tests
    if [[ ${#TEST_SECTIONS[@]} -gt 0 ]]; then
        log_info "Running selected test sections: ${TEST_SECTIONS[*]}"
    else
        log_info "Running all test sections"
    fi
    echo

    run_selected_tests "${TEST_SECTIONS[@]}"

    # Print summary
    print_summary

    # Exit with appropriate code
    if [[ $FAILED_TESTS -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
