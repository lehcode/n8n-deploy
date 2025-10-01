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

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_edge_cases
    print_summary
    exit_code=$?
    exit $exit_code
fi
