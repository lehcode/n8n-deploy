#!/bin/bash
# Database Operations Tests
# Part of n8n-deploy manual testing framework

# Source configuration and utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
source "$SCRIPT_DIR/lib.sh"

# Test function
test_database_operations() {
print_section "Test Category 2: Database Operations"

    local app_dir="$TEST_BASE_DIR/app"

    # === DB INIT - All parameter combinations ===

    # Basic init
    run_test "DB init basic" "$CLI_COMMAND db init --app-dir $app_dir --no-emoji --import" 0 "Initialize database"

    # With --import flag (existing database)
    run_test "DB init --import (existing)" "$CLI_COMMAND db init --app-dir $app_dir --import --no-emoji" 0 "Import existing database without prompt"

    # With --format json
    run_test "DB init --format json" "$CLI_COMMAND db init --app-dir $app_dir --format json --import" 0 "Initialize with JSON output"
    validate_output "DB init JSON content" "$CLI_COMMAND db init --app-dir $app_dir --format json --import" '"success": true'

    # With --format table (explicit)
    run_test "DB init --format table" "$CLI_COMMAND db init --app-dir $app_dir --format table --import --no-emoji" 0 "Initialize with table output"

    # All flags combined
    run_test "DB init all flags" "$CLI_COMMAND db init --app-dir $app_dir --format json --no-emoji --import" 0 "Initialize with all flags"

    # === DB STATUS - All parameter combinations ===

    # Basic status
    run_test "DB status basic" "$CLI_COMMAND db status --app-dir $app_dir --no-emoji" 0 "Check database status"
    validate_output "DB status content" "$CLI_COMMAND db status --app-dir $app_dir --no-emoji" "Database Path"

    # With --format json
    run_test "DB status --format json" "$CLI_COMMAND db status --app-dir $app_dir --format json" 0 "Check database status in JSON"

    # With emoji (default)
    run_test "DB status with emoji" "$CLI_COMMAND db status --app-dir $app_dir" 0 "Check database status with emoji"

    # === DB COMPACT - All parameter combinations ===

    # Basic compact
    run_test "DB compact basic" "$CLI_COMMAND db compact --app-dir $app_dir --no-emoji" 0 "Compact database"

    # With emoji (default)
    run_test "DB compact with emoji" "$CLI_COMMAND db compact --app-dir $app_dir" 0 "Compact database with emoji output"

    # === DB BACKUP - All parameter combinations ===

    # Basic backup
    local backup_file="$TEST_BASE_DIR/backup/test_backup.db"
    run_test "DB backup basic" "$CLI_COMMAND db backup $backup_file --app-dir $app_dir" 0 "Create database backup"

    # Test backup file exists
    if [[ -f "$backup_file" ]]; then
        log_success "Backup file created successfully"
        ((PASSED_TESTS++))
    else
        log_error "Backup file not created"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))

    # Backup with custom path
    local backup_file2="$TEST_BASE_DIR/backup/custom_backup.db"
    run_test "DB backup custom path" "$CLI_COMMAND db backup $backup_file2 --app-dir $app_dir" 0 "Create database backup with custom path"

    pause_if_requested
}

# Run tests if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_test_env
    test_database_operations
    print_summary
    exit_code=$?
    exit $exit_code
fi
