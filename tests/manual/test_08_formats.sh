#!/bin/bash
# Output Formats Tests
# Part of n8n-deploy manual testing framework

# Source configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/lib.sh"

# Test function
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
    validate_output "Emoji output" "$CLI_COMMAND wf list --data-dir $app_dir --flows-dir $flow_dir" "📋"
    validate_output "No emoji output" "$CLI_COMMAND wf list --data-dir $app_dir --flows-dir $flow_dir --no-emoji" "Workflows"

    # Test table vs JSON formats
    validate_output "Table format" "$CLI_COMMAND wf list --data-dir $app_dir --flows-dir $flow_dir --format table" "Name"
    validate_output "JSON format" "$CLI_COMMAND wf list --data-dir $app_dir --flows-dir $flow_dir --format json" "\\["

    # Test database status formats
    validate_output "DB status table" "$CLI_COMMAND db status --data-dir $app_dir --format table" "Database Path"
    validate_output "DB status JSON" "$CLI_COMMAND db status --data-dir $app_dir --format json" "database_path"

    # Test API key formats
    validate_output "API key table" "$CLI_COMMAND apikey list --data-dir $app_dir --no-emoji" "Name"
    validate_output "API key JSON" "$CLI_COMMAND apikey list --data-dir $app_dir --format json" "\\["

    pause_if_requested
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_output_formats
    print_summary
    exit_code=$?
    exit $exit_code
fi
