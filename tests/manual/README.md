# n8n-deploy Manual Test Suite

Modular manual testing framework for comprehensive CLI validation.

## Structure

```
tests/manual/
├── README.md              # This file
├── config.sh              # Configuration and constants
├── lib.sh                 # Shared utility functions
├── runner.py              # Python test runner
├── test_01_help.sh        # Help & version tests (6 tests)
├── test_02_env.sh         # Environment tests (7 tests)
├── test_03_database.sh    # Database tests (16 tests)
├── test_04_apikey.sh      # API key tests (11 tests)
├── test_05_workflow.sh    # Workflow tests (12 tests)
├── test_06_backup.sh      # Backup tests (5 tests)
├── test_07_server.sh      # Server integration tests (5 tests)
├── test_08_formats.sh     # Output format tests
├── test_09_directories.sh # Directory option tests (3 tests)
├── test_10_errors.sh      # Error handling tests (10 tests)
└── test_11_edge_cases.sh  # Edge case tests (10 tests)
```

## Usage

### Run All Tests

```bash
# Using Python runner (recommended - buffered output with summary)
python3 tests/manual/runner.py

# With verbose output (shows full test output)
python3 tests/manual/runner.py -v

# With streaming output (real-time, fails fast)
python3 tests/manual/runner.py -s

# In parallel (faster, not compatible with streaming)
python3 tests/manual/runner.py -p

# Recommended for manual E2E testing
python3 tests/manual/runner.py -s -f test_03
```

### Run Individual Test Files

```bash
# Run specific test category directly
./tests/manual/test_03_database.sh

# Or using Python runner with filter
python3 tests/manual/runner.py -f test_03

# Stream output for specific test
python3 tests/manual/runner.py -s -f database
```

### List Available Tests

```bash
python3 tests/manual/runner.py --list
```

## Test Categories

1. **Help & Version** (`test_01_help.sh`)
   - CLI help output
   - Version information
   - Invalid options

2. **Environment** (`test_02_env.sh`)
   - Environment variable display
   - Configuration precedence
   - Format options

3. **Database** (`test_03_database.sh`)
   - Database initialization
   - Status checking
   - Backup and compact operations
   - All parameter combinations

4. **API Keys** (`test_04_apikey.sh`)
   - Add, list, get, deactivate, delete
   - Key validation
   - Format options

5. **Workflows** (`test_05_workflow.sh`)
   - Add, list, remove, search, stats
   - File operations
   - Format options

6. **Backups** (`test_06_backup.sh`)
   - Create, list, restore, verify
   - Backup integrity

7. **Server Integration** (`test_07_server.sh`)
   - Server connections
   - Push/pull operations
   - Error handling

8. **Output Formats** (`test_08_formats.sh`)
   - Table and JSON outputs
   - Emoji/no-emoji modes

9. **Directory Options** (`test_09_directories.sh`)
   - app-dir, flow-dir handling
   - Path resolution

10. **Error Handling** (`test_10_errors.sh`)
    - Invalid inputs
    - Missing files
    - Permission errors

11. **Edge Cases** (`test_11_edge_cases.sh`)
    - Boundary conditions
    - Special characters
    - Concurrent operations

## Development

### Adding New Tests

1. Add test to appropriate `test_XX_*.sh` file using `run_test` function:
   ```bash
   run_test "Test description" "$CLI_COMMAND command --options" 0 "Expected behavior"
   ```

2. Update test count in README if needed

### Utility Functions

Available in `lib.sh`:
- `run_test` - Execute test and track results
- `validate_output` - Check for expected output
- `log_*` - Colored logging functions
- `setup_test_env` - Initialize test environment
- `cleanup_test_env` - Clean up after tests

## CI Integration

The Python runner provides exit codes for CI:
- `0` - All tests passed
- `1` - Some tests failed

Example in `.gitlab-ci.yml`:
```yaml
manual-tests:
  script:
    - python3 tests/manual/runner.py
  allow_failure: true  # Manual tests are informational
```

## Benefits

✅ Modular - Easy to maintain individual test categories
✅ Isolated - Each category can run independently
✅ Parallel - Run tests concurrently for speed
✅ Comprehensive - 85+ tests covering all CLI commands
✅ Reusable - Shared utilities in lib.sh
✅ CI-ready - Python runner with proper exit codes
