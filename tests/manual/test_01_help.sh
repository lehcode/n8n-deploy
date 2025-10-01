#!/bin/bash
# CLI Help & Version Tests
# Part of n8n-deploy manual testing framework

# Source configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/lib.sh"

# Test function
test_cli_help_version() {
print_section "Test Category 1: CLI Help & Version"

    # Basic help
    run_test "CLI help" "$CLI_COMMAND --help" 0 "Display main CLI help"
    validate_output "CLI help content" "$CLI_COMMAND --help" "n8n-deploy - a simple N8N Workflow Manager"

    # Version
    run_test "CLI version" "$CLI_COMMAND --version" 0 "Display version information"
    validate_output "Version format" "$CLI_COMMAND --version" "version 2.0.0"

    # Invalid option
    run_test "Invalid option" "$CLI_COMMAND --invalid-option" 2 "Test invalid option handling"

    # Command help
    run_test "Workflow command help" "$CLI_COMMAND wf --help" 0 "Display wf command help"
    run_test "DB command help" "$CLI_COMMAND db --help" 0 "Display db command help"
    run_test "Apikey command help" "$CLI_COMMAND apikey --help" 0 "Display apikey command help"

    pause_if_requested
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_cli_help_version
    print_summary
    exit_code=$?
    exit $exit_code
fi
