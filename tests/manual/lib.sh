#!/bin/bash
# Utility functions for n8n-deploy manual testing framework
# Source this file after config.sh

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

setup_test_env() {
    log_info "Setting up test environment..."

    # Clean up any existing test directory
    if [[ -d "$TEST_BASE_DIR" ]]; then
        rm -rf "$TEST_BASE_DIR"
    fi

    # Create test directories
    mkdir -p "$TEST_BASE_DIR"/{app,flow,backup}

    # Create sample wf file (using wf ID as filename)
    create_sample_workflow "$TEST_BASE_DIR/flow/workflows"

    log_success "Test environment created at $TEST_BASE_DIR"
}

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

cleanup_test_env() {
    log_info "Cleaning up test environment..."
    if [[ -d "$TEST_BASE_DIR" ]]; then
        rm -rf "$TEST_BASE_DIR"
        log_success "Test environment cleaned up"
    fi
}

pause_if_requested() {
    if [[ $PAUSE_BETWEEN_SECTIONS == true ]]; then
        echo
        read -p "Press Enter to continue to next section..."
        echo
    fi
}

check_database_exists() {
    local app_dir="$1"
    local test_section="$2"
    if [[ ! -f "$app_dir/n8n-deploy.db" ]]; then
        log_warning "Database not initialized for $test_section tests"
        log_warning "Run 'db' test section first or manually run: n8n-deploy db init --data-dir $app_dir"
        return 1
    fi
    return 0
}

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
        echo -e "${CYAN}============================================================${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed. Review the output above for details.${NC}"
        echo -e "${CYAN}============================================================${NC}"
        return 1
    fi
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
    env                     Environment Configuration tests
    db                      Database Operations tests
    apikey                  API Key Management tests
    wf                Workflow Operations tests
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
    $0 --quick wf     # Run wf tests in quick mode
    $0 --clean              # Clean up test environment only

EOF
}
