#!/bin/bash
# Workflow Operations Tests
# Part of n8n-deploy manual testing framework

# Source configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/lib.sh"

# Test function
test_workflow_operations() {
print_section "Test Category 4: Workflow Operations"

    local app_dir="$TEST_BASE_DIR/app"
    local flow_dir="$TEST_BASE_DIR/flow"
    local workflow_file="$flow_dir/workflows/${SAMPLE_WF_ID}.json"

    # Check database exists (must be initialized with 'db init' first)
    if ! check_database_exists "$app_dir" "Workflow"; then
        ((SKIPPED_TESTS+=10))  # Skip all wf tests
        ((TOTAL_TESTS+=10))
        return
    fi

    # Add wf
    run_test "Add wf" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json '$SAMPLE_WF_NAME' --data-dir $app_dir --flow-dir $flow_dir" 0 "Add wf to database"

    # List workflows
    run_test "List workflows table" "$CLI_COMMAND wf list --data-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "List workflows in table format"
    run_test "List workflows JSON" "$CLI_COMMAND wf list --data-dir $app_dir --flow-dir $flow_dir --format json" 0 "List workflows in JSON format"
    validate_output "Workflow list content" "$CLI_COMMAND wf list --data-dir $app_dir --flow-dir $flow_dir --no-emoji" "$SAMPLE_WF_NAME"

    # List backupable workflows only
    run_test "List backupable only" "$CLI_COMMAND wf list --only --data-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "List only backupable workflows"

    # Test add wf with JSON format output
    run_test "Add wf JSON output" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json 'Second Test Workflow' --data-dir $app_dir --flow-dir $flow_dir --format json" 0 "Add wf with JSON output"

    # Search workflows
    run_test "Search workflows by name" "$CLI_COMMAND wf search 'test' --data-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "Search workflows by name"
    validate_output "Search results" "$CLI_COMMAND wf search 'test' --data-dir $app_dir --flow-dir $flow_dir --no-emoji" "$SAMPLE_WF_NAME"
    run_test "Search workflows by ID" "$CLI_COMMAND wf search '$SAMPLE_WF_ID' --data-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "Search workflows by wf ID"
    run_test "Search workflows JSON" "$CLI_COMMAND wf search 'test' --data-dir $app_dir --flow-dir $flow_dir --format json" 0 "Search workflows with JSON output"

    # Get wf stats
    run_test "Workflow stats table" "$CLI_COMMAND wf stats $SAMPLE_WF_ID --data-dir $app_dir --flow-dir $flow_dir" 0 "Get wf statistics"
    run_test "Workflow stats JSON" "$CLI_COMMAND wf stats $SAMPLE_WF_ID --data-dir $app_dir --flow-dir $flow_dir --format json" 0 "Get wf statistics in JSON"

    # Test non-existent wf
    run_test "Non-existent wf" "$CLI_COMMAND wf stats 'non-existent-id' --data-dir $app_dir --flow-dir $flow_dir" 1 "Test non-existent wf handling"

    # Test wf without file
    rm "$workflow_file"
    run_test "Workflow without file" "$CLI_COMMAND wf list --data-dir $app_dir --flow-dir $flow_dir --no-emoji" 0 "List workflows when file missing"

    # Recreate file for further tests
    create_sample_workflow "$flow_dir/workflows"

    pause_if_requested
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_workflow_operations
    print_summary
    exit_code=$?
    exit $exit_code
fi
