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
        ((SKIPPED_TESTS+=10))  # Skip all API key tests
        ((TOTAL_TESTS+=10))
        return
    fi

    # Add API key
    run_test "Add API key" "echo '$SAMPLE_API_KEY' | $CLI_COMMAND apikey add - --name test_key --no-emoji" 0 "Add new API key"

    # List API keys (credentials masked by default)
    run_test "List API keys table" "$CLI_COMMAND apikey list --no-emoji" 0 "List API keys in table format"
    run_test "List API keys JSON" "$CLI_COMMAND apikey list --format json" 0 "List API keys in JSON format"
    validate_output "API key list content" "$CLI_COMMAND apikey list --no-emoji" "test_key"

    # List API keys with credentials unmasked (SECURITY WARNING)
    run_test "List API keys (unmask)" "$CLI_COMMAND apikey list --unmask --no-emoji" 0 "List API keys showing actual credentials"

    # Test API key
    run_test "Test API key" "$CLI_COMMAND apikey test test_key" 0 "Test API key validity"

    # Add another key for testing
    run_test "Add second API key" "echo '$SAMPLE_API_KEY' | $CLI_COMMAND apikey add - --name test_key2 --description 'Second test key' --expires-in 30 --no-emoji" 0 "Add second API key with expiration"

    # Deactivate API key
    run_test "Deactivate API key" "$CLI_COMMAND apikey deactivate test_key2" 0 "Deactivate API key"

    # Delete API key
    run_test "Delete API key" "$CLI_COMMAND apikey delete test_key2 --confirm" 0 "Delete API key"

    # Test with invalid key name
    run_test "Invalid key name" "echo '$SAMPLE_API_KEY' | $CLI_COMMAND apikey add - --name 'invalid key!'" 1 "Test invalid key name handling"

    # Test with invalid JWT format
    run_test "Invalid JWT format" "echo 'not.a.valid.jwt.format' | $CLI_COMMAND apikey add - --name invalid_jwt" 1 "Test invalid JWT format handling"

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
