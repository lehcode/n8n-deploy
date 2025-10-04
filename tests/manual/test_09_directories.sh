#!/bin/bash
# Directory Options Tests
# Part of n8n-deploy manual testing framework

# Source configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/lib.sh"

# Test function
test_directory_options() {
print_section "Test Category 8: Directory Options"

    local app_dir1="$TEST_BASE_DIR/app"
    local app_dir2="$TEST_BASE_DIR/app2"
    local flow_dir1="$TEST_BASE_DIR/flow"
    local flow_dir2="$TEST_BASE_DIR/flow2"

    # Create second set of directories
    mkdir -p "$app_dir2" "$flow_dir2/workflows"

    # Initialize second database
    run_test "Init second DB" "$CLI_COMMAND db init --data-dir $app_dir2 --import --no-emoji" 0 "Initialize second database"

    # Test app-dir option
    validate_output "Different app dir" "$CLI_COMMAND db status --data-dir $app_dir2" "$app_dir2"

    # Test flow-dir option
    create_sample_workflow "$flow_dir2/workflows"
    run_test "Add workflow different dirs" "$CLI_COMMAND wf add workflows/${SAMPLE_WF_ID}.json '$SAMPLE_WF_NAME' --data-dir $app_dir2 --flows-dir $flow_dir2" 0 "Add workflow with different directories"

    # Test environment variable (simulate)
    export N8N_DEPLOY_FLOW_DIR="$flow_dir2"
    validate_output "Environment variable flow dir" "$CLI_COMMAND wf list --data-dir $app_dir2 --no-emoji" "$SAMPLE_WF_ID"
    unset N8N_DEPLOY_FLOW_DIR

    # Test directory precedence - CLI option should override environment
    export N8N_DEPLOY_FLOW_DIR="$flow_dir1"
    run_test "Directory precedence" "$CLI_COMMAND wf list --data-dir $app_dir2 --flows-dir $flow_dir2 --no-emoji" 0 "Test directory option precedence"
    unset N8N_DEPLOY_FLOW_DIR

    pause_if_requested
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_directory_options
    print_summary
    exit_code=$?
    exit $exit_code
fi
