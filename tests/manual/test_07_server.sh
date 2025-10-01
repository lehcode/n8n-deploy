#!/bin/bash
# Server Integration Tests
# Part of n8n-deploy manual testing framework

# Source configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/lib.sh"

# Test function
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
    run_test "List server (no URL)" "$CLI_COMMAND wf server --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 1 "List server workflows without URL"

    # Test list-server with unreachable server
    run_test "List server (unreachable)" "$CLI_COMMAND wf server --server-url $mock_server --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 1 "List server workflows with unreachable server"

    # Test pull with unreachable server
    run_test "Pull workflow (unreachable)" "$CLI_COMMAND wf pull $SAMPLE_WF_ID --server-url $mock_server --app-dir $app_dir --flow-dir $flow_dir" 1 "Pull workflow from unreachable server"

    # Test push with unreachable server
    run_test "Push workflow (unreachable)" "$CLI_COMMAND wf push $SAMPLE_WF_ID --server-url $mock_server --app-dir $app_dir --flow-dir $flow_dir" 1 "Push workflow to unreachable server"

    # Test with skip SSL verify flag
    run_test "List server (skip SSL)" "$CLI_COMMAND wf server --server-url $mock_server --skip-ssl-verify --app-dir $app_dir --flow-dir $flow_dir --no-emoji" 1 "List server with SSL verification disabled"

    log_warning "Server integration tests use mock/unreachable endpoints - real server testing requires manual setup"

    pause_if_requested
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_server_integration
    print_summary
    exit_code=$?
    exit $exit_code
fi
