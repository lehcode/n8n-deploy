#!/bin/bash
# API Key Management Tests
# Part of n8n-deploy manual testing framework

# Source configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/lib.sh"

# Test function
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
    run_test "Add API key" "echo '$SAMPLE_API_KEY' | $CLI_COMMAND apikey add - --name test_key --data-dir $app_dir --no-emoji" 0 "Add new API key"

    # List API keys
    run_test "List API keys table" "$CLI_COMMAND apikey list --data-dir $app_dir --no-emoji" 0 "List API keys in table format"
    run_test "List API keys JSON" "$CLI_COMMAND apikey list --data-dir $app_dir --format json" 0 "List API keys in JSON format"
    validate_output "API key list content" "$CLI_COMMAND apikey list --data-dir $app_dir --no-emoji" "test_key"

    # Get API key (without showing key)
    run_test "Get API key (no show)" "$CLI_COMMAND apikey get test_key --data-dir $app_dir --no-emoji" 0 "Get API key without showing key"

    # Get API key (with key)
    run_test "Get API key (show)" "$CLI_COMMAND apikey get test_key --show-key --data-dir $app_dir --no-emoji" 0 "Get API key showing actual key"

    # Test API key
    run_test "Test API key" "$CLI_COMMAND apikey test test_key --data-dir $app_dir" 0 "Test API key validity"

    # Add another key for testing
    run_test "Add second API key" "echo '$SAMPLE_API_KEY' | $CLI_COMMAND apikey add - --name test_key2 --description 'Second test key' --expires-in 30 --data-dir $app_dir --no-emoji" 0 "Add second API key with expiration"

    # Deactivate API key
    run_test "Deactivate API key" "$CLI_COMMAND apikey deactivate test_key2 --data-dir $app_dir" 0 "Deactivate API key"

    # Delete API key
    run_test "Delete API key" "$CLI_COMMAND apikey delete test_key2 --confirm --data-dir $app_dir" 0 "Delete API key"

    # Test with invalid key name
    run_test "Invalid key name" "echo '$SAMPLE_API_KEY' | $CLI_COMMAND apikey add - --name 'invalid key!' --data-dir $app_dir" 1 "Test invalid key name handling"

    # Test with invalid JWT format
    run_test "Invalid JWT format" "echo 'not.a.valid.jwt.format' | $CLI_COMMAND apikey add - --name invalid_jwt --data-dir $app_dir" 1 "Test invalid JWT format handling"

    pause_if_requested
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_api_key_management
    print_summary
    exit_code=$?
    exit $exit_code
fi
