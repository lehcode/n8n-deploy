#!/bin/bash
# Backup Operations Tests
# Part of n8n-deploy manual testing framework

# Source configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/lib.sh"

# Test function
test_backup_operations() {
print_section "Test Category 5: Backup Operations"

    local app_dir="$TEST_BASE_DIR/app"
    local flow_dir="$TEST_BASE_DIR/flow"
    local backup_dir="$TEST_BASE_DIR/backup"

    # Check database exists (must be initialized with 'db init' first)
    if ! check_database_exists "$app_dir" "Backup"; then
        ((SKIPPED_TESTS+=6))  # Skip all backup tests
        ((TOTAL_TESTS+=6))
        return
    fi

    # Create wf backup
    run_test "Create wf backup" "$CLI_COMMAND wf createbackup --backup-dir $backup_dir --data-dir $app_dir --flows-dir $flow_dir --no-emoji" 0 "Create tar.gz backup of workflows"

    # List backups
    run_test "List backups table" "$CLI_COMMAND wf backups --backup-dir $backup_dir --data-dir $app_dir --flows-dir $flow_dir" 0 "List backup files"
    run_test "List backups JSON" "$CLI_COMMAND wf backups --backup-dir $backup_dir --data-dir $app_dir --flows-dir $flow_dir --format json" 0 "List backup files in JSON"

    # Find the backup file
    local backup_file
    backup_file=$(find "$backup_dir" -name "*.tar.gz" | head -1)

    if [[ -n "$backup_file" && -f "$backup_file" ]]; then
        log_success "Backup file found: $backup_file"

        # Verify backup integrity
        run_test "Verify backup integrity" "$CLI_COMMAND wf verify '$backup_file' --data-dir $app_dir --flows-dir $flow_dir --no-emoji" 0 "Verify backup file integrity"

        # Test restore
        run_test "Restore workflows" "$CLI_COMMAND wf restore '$backup_file' --data-dir $app_dir --flows-dir $flow_dir" 0 "Restore workflows from backup"
    else
        log_error "No backup file found to test verification and restore"
        ((FAILED_TESTS += 2))
        ((TOTAL_TESTS += 2))
    fi

    pause_if_requested
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_backup_operations
    print_summary
    exit_code=$?
    exit $exit_code
fi
