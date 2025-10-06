#!/bin/bash
# Edge Cases Tests
# Part of n8n-deploy manual testing framework

# Source configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/lib.sh"

# Test function
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
    run_test "Init empty DB" "$CLI_COMMAND db init --data-dir $empty_app_dir --import --no-emoji" 0 "Initialize empty database"
    run_test "List empty workflows" "$CLI_COMMAND wf list --data-dir $empty_app_dir --no-emoji" 0 "List workflows in empty database"

    # Test special characters in wf names (UTF-8 and spaces allowed, path separators rejected)
    local special_wf_id="special-test-id"
    local valid_special_name="Workflow with Spaces (test) & symbols! 日本語 🎉"
    local invalid_special_name="wf/with\\path"
    run_test "Add wf with UTF-8" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json '$valid_special_name' --data-dir $app_dir --flow-dir $flow_dir" 0 "Add wf with spaces, UTF-8, and special characters (should pass)"
    run_test "Add invalid char wf" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json '$invalid_special_name' --data-dir $app_dir --flow-dir $flow_dir" 1 "Add wf with path separators (should fail)"

    # Test very long arguments
    local long_description="This is a very long description that contains many words and should test the handling of lengthy input parameters in the CLI system to ensure robust operation"
    run_test "Long description" "echo '$SAMPLE_API_KEY' | $CLI_COMMAND apikey add - --name long_test_key --description '$long_description' --no-emoji" 0 "Test long description handling"

    # Test duplicate wf ID (first add the original, then try to add duplicate)
    run_test "Add original wf" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json '$SAMPLE_WF_NAME' --data-dir $app_dir --flow-dir $flow_dir" 0 "Add original wf for duplicate test"
    run_test "Duplicate wf ID" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json 'Duplicate Workflow' --data-dir $app_dir --flow-dir $flow_dir" 1 "Test duplicate wf ID handling"

    # Test operations on deactivated API keys
    run_test "Deactivate API key" "$CLI_COMMAND apikey deactivate long_test_key" 0 "Deactivate API key for testing"
    run_test "Test deactivated key" "$CLI_COMMAND apikey test long_test_key" 1 "Test deactivated API key"

    # Test wf file that exists but is invalid JSON
    local invalid_json_file="$flow_dir/workflows/invalid.json"
    echo "{ invalid json }" > "$invalid_json_file"
    run_test "Add invalid JSON wf" "$CLI_COMMAND wf add workflows/invalid.json 'invalid_json_workflow' --data-dir $app_dir --flow-dir $flow_dir" 1 "Add wf with invalid JSON (should fail)"


    pause_if_requested
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_edge_cases
    print_summary
    exit_code=$?
    exit $exit_code
fi
