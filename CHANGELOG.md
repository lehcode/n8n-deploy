# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-10-01

### Added

#### Testing Infrastructure
- **Modular Manual Test Framework** - Complete rewrite of manual testing system
  - Python test runner (`tests/manual/runner.py`) with streaming mode support
  - Real-time output display with `-s/--stream` flag
  - Fail-fast behavior: exits immediately on test failure
  - Proper exit code propagation (0 for success, 1 for failure)
  - 11 test categories with 107 total tests (57 implemented, 50 placeholders)
  - Modular bash scripts with shared configuration and utility library
  - Test categories: help, env, database, apikey, workflow, backup, server, formats, directories, errors, edge cases

- **Property-Based Testing with Hypothesis**
  - Automated hypothesis test generator (`tests/generators/hypothesis_generator.py`)
  - 755 test examples across 25 properties
  - Comprehensive CLI command and parameter validation
  - Added to GitHub Actions and GitLab CI pipelines

- **Automated Test Generation**
  - CLI introspection-based test generator (`tests/generators/test_generator.py`)
  - 1,099 auto-generated tests from CLI structure (`tests/generated/test_cli_generated.py`)
  - Automatic detection of commands, options, and parameters

- **Testing Documentation**
  - Comprehensive testing framework guide (`docs/TESTING_FRAMEWORK.md`)
  - 763 lines of testing strategy, tools, and best practices documentation

#### CLI Features
- **UTF-8 Workflow Name Support**
  - Allow full Unicode support in workflow names (emojis, international characters)
  - Support for spaces and special characters in workflow names
  - Examples: 'My Workflow 🚀', '日本語ワークフロー', 'Processus de données'
  - Only reject null bytes and path separators for security
  - Simplified validation from restrictive regex to minimal safety checks

- **Environment Configuration Display Command**
  - New `env` command to display all environment variables and their values
  - Support for JSON (`--format json`) and table (`--format table`) output
  - Shows configuration precedence and default values

- **Development Environment Support**
  - `.env.example` template file for local development
  - Development-only `.env` file loading (requires `ENVIRONMENT=development`)
  - Priority: CLI arguments > Environment variables > .env files

- **Interactive Database Initialization**
  - Interactive mode for database initialization with user prompts
  - New `--import` flag to accept existing databases without prompting
  - Replaces old `--force` flag for cleaner semantics

#### Test Coverage Improvements
- **E2E Tests**
  - Extended API key tests with 14 new comprehensive test cases
  - Extended database tests with JSON format and custom path testing
  - New environment command tests (`tests/integration/test_e2e_env.py`)
  - Enhanced server and workflow tests with additional scenarios

- **Integration Tests**
  - Comprehensive parameter combination testing for all database commands
  - All parameter variations for `db init`, `db status`, `db backup`, `db compact`
  - Test class filtering with `--class` parameter in `run_tests.py`

### Changed

#### CLI Breaking Changes
- **Command Renames** (to fix Click prefix matching conflicts)
  - `wf backup` → `wf createbackup` (create workflow backup)
  - `wf list-backups` → `wf backups` (list available backups)
  - `wf list-server` → `wf server` (list server workflows)
  - `wf verify-backup` → `wf verify` (verify backup integrity)

- **Environment Variable Standardization**
  - Renamed all environment variables to `N8N_DEPLOY_*` convention
  - `N8N_FLOW_DIR` → `N8N_DEPLOY_FLOW_DIR`
  - Added `N8N_DEPLOY_APP_DIR` for application directory
  - Added `N8N_DEPLOY_SERVER_URL` for n8n server URL

#### Code Quality Improvements
- **Database Code Refactoring**
  - Extracted base database class (`api/db/base.py`) to eliminate code duplication
  - Centralized database existence checks into reusable helper methods
  - Improved error handling with clean "Oops!" messages

- **Install Script Modernization**
  - Enhanced `install.py` with environment conflict detection
  - Better handling of existing installations
  - Improved user feedback and error messages

- **Click Framework Improvements**
  - Disabled Click prefix matching to prevent command routing conflicts
  - Custom command group with exact name matching
  - Fixed shadowing of Python `list()` builtin in workflow commands

### Fixed

- **Click Command Prefix Matching Bug**
  - Commands like `listbackups` were incorrectly routing to `list`
  - `list()` builtin was shadowed by Click's `list` command
  - Solution: Disabled prefix matching and renamed conflicting commands

- **Database Initialization**
  - Added missing `main()` entry point in CLI modules
  - Improved db status error handling for non-existent databases

- **Test Infrastructure**
  - Fixed E2E CLI tests to use correct commands and options
  - Updated all tests for renamed commands and environment variables
  - Increased deadline for multi-command hypothesis tests
  - Fixed hypothesis test syntax errors

- **JSON Output Validation**
  - Ensured JSON output from `env` command handles Unicode paths correctly
  - Fixed `list backups` command to return valid JSON arrays

### CI/CD

- **Pipeline Enhancements**
  - Added Hypothesis property-based testing to GitHub Actions workflow
  - Added Hypothesis testing to GitLab CI pipeline
  - Enforce sequential test execution with `-x` flag (exit on first failure)
  - APT proxy configuration for faster package installation

### Documentation

- **Updated Command Documentation**
  - Updated all help text for renamed commands
  - Clarified flow directory defaults to current directory
  - Improved directory configuration priority documentation

### Test Statistics

- **192** integration tests (E2E scenarios)
- **59** unit tests (core functionality)
- **107** manual tests (57 implemented, 50 placeholders)
- **755** hypothesis examples (property-based testing)
- **1,099** auto-generated tests (CLI introspection)
- **Total: 2,212 test cases** across all testing layers

### Developer Experience

- Run tests with streaming output: `python3 tests/manual/runner.py -s`
- Filter tests by class: `python run_tests.py --integration --class TestE2EDatabase`
- Generate CLI tests: `python tests/generators/test_generator.py`
- Run hypothesis tests: `pytest tests/generated/test_cli_generated.py`

---

## [2.0.0] - Previous Release

Initial modular architecture release with workflow management, database operations, and API key management.

[Unreleased]: https://github.com/lehcode/n8n-deploy/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/lehcode/n8n-deploy/releases/tag/v2.0.0
