#!/bin/bash
# Error Handling Tests
# Part of n8n-deploy manual testing framework

# Source configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/lib.sh"

# Test function
test_error_handling() {
print_section "Test Category 9: Error Handling"

    local app_dir="$TEST_BASE_DIR/app"
    local flow_dir="$TEST_BASE_DIR/flow"
    local invalid_dir="/dev/null/invalid_path"

    # Test invalid commands
    run_test "Invalid command" "$CLI_COMMAND invalid-command" 2 "Test invalid command handling"
    run_test "Invalid subcommand" "$CLI_COMMAND db invalid-subcommand" 2 "Test invalid subcommand handling"

    # Test missing required arguments
    run_test "Missing wf ID" "$CLI_COMMAND wf add" 2 "Test missing required arguments"
    run_test "Missing API key name" "$CLI_COMMAND apikey add testkey" 2 "Test missing API key name"

    # Test invalid directory paths
    run_test "Invalid app dir" "$CLI_COMMAND db status --data-dir $invalid_dir" 1 "Test invalid app directory"
    run_test "Invalid flow dir" "$CLI_COMMAND wf list --data-dir $app_dir --flows-dir $invalid_dir --no-emoji" 1 "Test invalid flow directory (creates directory, fails)"

    # Test non-existent database operations
    local nonexistent_dir="$TEST_BASE_DIR/nonexistent"
    run_test "Non-existent DB status" "$CLI_COMMAND db status --data-dir $nonexistent_dir" 1 "Test operations on non-existent database"

    # Setup database for remove tests
    "$CLI_COMMAND" db init --data-dir "$app_dir" --import --no-emoji > /dev/null 2>&1
    create_sample_workflow "$flow_dir/workflows"
    "$CLI_COMMAND" wf add "workflows/${SAMPLE_WF_ID}.json" "$SAMPLE_WF_NAME" --data-dir "$app_dir" --flows-dir "$flow_dir" --no-emoji > /dev/null 2>&1

    # Test remove wf with confirmation (should succeed with 'n' response)
    run_test "Remove without confirmation" "echo 'n' | $CLI_COMMAND wf remove $SAMPLE_WF_ID --data-dir $app_dir --flows-dir $flow_dir" 0 "Test remove wf without confirmation (cancels)"

    # Test remove wf with --yes flag (should succeed)
    run_test "Remove with --yes flag" "$CLI_COMMAND wf remove $SAMPLE_WF_ID --yes --data-dir $app_dir --flows-dir $flow_dir" 0 "Test remove wf with --yes flag"

    # Test backup to invalid directory (succeeds with 0 workflows)
    run_test "Backup to invalid dir" "$CLI_COMMAND wf createbackup --backup-dir $invalid_dir --data-dir $app_dir --flows-dir $flow_dir" 0 "Test backup to invalid directory (succeeds with 0 workflows)"

    pause_if_requested
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_error_handling
    print_summary
    exit_code=$?
    exit $exit_code
fi
