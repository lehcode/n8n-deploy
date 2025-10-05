#!/bin/bash
# Environment Configuration Tests
# Part of n8n-deploy manual testing framework

# Source configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/lib.sh"

# Test function
test_env_configuration() {
print_section "Test Category 1.5: Environment Configuration"

    local app_dir="$TEST_BASE_DIR/app"
    local flow_dir="$TEST_BASE_DIR/flow"

    # Basic help
    run_test "Env help" "$CLI_COMMAND env --help" 0 "Display env command help"
    validate_output "Env help content" "$CLI_COMMAND env --help" "Show environment configuration"

    # Test default plain text format
    run_test "Env default format" "$CLI_COMMAND env --data-dir $app_dir" 0 "Display env config in default plain text format"
    validate_output "Env default content" "$CLI_COMMAND env --data-dir $app_dir" "=== Environment Configuration ==="
    validate_output "Env shows variables" "$CLI_COMMAND env --data-dir $app_dir" "N8N_DEPLOY_DATA"
    validate_output "Env shows priority" "$CLI_COMMAND env --data-dir $app_dir" "Priority Order"

    # Test table format with emojis
    run_test "Env table format" "$CLI_COMMAND env --format table --data-dir $app_dir" 0 "Display env config in table format"
    validate_output "Env table emojis" "$CLI_COMMAND env --format table --data-dir $app_dir" "🌍"

    # Test JSON format
    run_test "Env JSON format" "$CLI_COMMAND env --format json --data-dir $app_dir" 0 "Display env config in JSON format"
    validate_output "Env JSON content" "$CLI_COMMAND env --format json --data-dir $app_dir" '"variables"'
    validate_output "Env JSON priority" "$CLI_COMMAND env --format json --data-dir $app_dir" '"priority_order"'

    # Test with multiple directory options
    run_test "Env with dirs" "$CLI_COMMAND env --data-dir $app_dir --flows-dir $flow_dir" 0 "Display env with both app and flow dirs"
    validate_output "Env shows app-dir" "$CLI_COMMAND env --data-dir $app_dir --flows-dir $flow_dir" "$app_dir"
    validate_output "Env shows flow-dir" "$CLI_COMMAND env --data-dir $app_dir --flows-dir $flow_dir" "$flow_dir"

    # Test with server URL
    local test_server="http://test.example.com:5678"
    run_test "Env with server" "$CLI_COMMAND env --remote $test_server" 0 "Display env with server URL"
    validate_output "Env shows server" "$CLI_COMMAND env --remote $test_server" "$test_server"

    # Test environment variable detection
    export N8N_DEPLOY_DATA="$app_dir"
    run_test "Env detects env var" "$CLI_COMMAND env" 0 "Detect N8N_DEPLOY_DATA environment variable"
    validate_output "Env shows env source" "$CLI_COMMAND env" "N8N_DEPLOY_DATA"
    unset N8N_DEPLOY_DATA

    # Test .env file detection (should show not found in test environment)
    validate_output "Env .env detection" "$CLI_COMMAND env" ".env file"

    pause_if_requested
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_env_configuration
    print_summary
    exit_code=$?
    exit $exit_code
fi
