---
layout: default
title: Testing Framework
parent: Developer Guide
nav_order: 6
description: "Comprehensive testing framework guide for n8n-deploy"
---

# Testing Framework Guide

Comprehensive guide to testing n8n-deploy using multiple testing approaches.

## Table of Contents

- [Overview](#overview/)
- [Test Types](#test-types/)
- [Quick Start](#quick-start/)
- [Manual Testing](#manual-testing/)
- [Automated Testing](#automated-testing/)
- [Property-Based Testing](#property-based-testing/)
- [Test Generation](#test-generation/)
- [Best Practices](#best-practices/)

---

## Overview

n8n-deploy uses a **hybrid testing approach** that combines:

1. **Manual Testing Scripts** - Bash-based interactive testing
2. **Unit Tests** - pytest-based component testing
3. **Integration Tests** - End-to-end workflow testing
4. **Property-Based Tests** - Hypothesis-based generative testing
5. **Auto-Generated Tests** - Tests generated from CLI introspection

### Test Coverage Strategy

**Property-Based Tests** - Replace repetitive E2E tests:
- Format validation (JSON/table/plain text consistency)
- Path handling (Unicode, special chars, deep nesting)
- Input sanitization (SQL injection, command injection)
- Help output consistency (all commands and subcommands)
- Option combinations (all valid flag combinations)

**E2E Tests** - Business logic and integration:
- Workflow lifecycle (add → update → delete → restore)
- Database migrations and schema upgrades
- Backup/restore with SHA256 integrity checks
- API key rotation and expiration logic
- n8n server integration (push/pull workflows)
- Multi-step scenarios (init DB → add workflow → backup → restore)

```
tests/
├── manual_test_cli.sh          # Interactive manual testing
├── unit/                       # Unit tests
├── integration/                # Integration & E2E tests
│   ├── test_e2e_*.py          # E2E tests for business logic
│   └── ...                     # Integration tests
├── generators/                 # Test generation tools
│   ├── test_generator.py       # CLI introspection → pytest
│   └── hypothesis_generator.py # Property-based tests
└── generated/                  # Auto-generated tests (gitignored)
    └── test_cli_generated.py   # Generated test scenarios
```

---

## Test Types

### 1. Manual Testing (Bash Script)

**Purpose:** Quick smoke testing and visual verification

**Use when:**
- Testing emoji/color output
- Verifying user experience
- Quick regression checks
- Development debugging

**Example:**
```bash
# Run all tests
./tests/manual_test_cli.sh

# Run specific sections
./tests/manual_test_cli.sh help env db

# Verbose mode with pauses
./tests/manual_test_cli.sh -v -p workflow
```

### 2. Unit Tests (pytest)

**Purpose:** Test individual components in isolation

**Use when:**
- Testing functions/methods
- Testing error handling
- Testing edge cases
- CI/CD pipelines

**Example:**
```bash
# Run all unit tests
python run_tests.py --unit

# Run specific test file
pytest tests/unit/test_config.py -v

# Run with coverage
python run_tests.py --unit --coverage
```

### 3. Integration Tests (pytest)

**Purpose:** Test component interactions and workflows

**Use when:**
- Testing CLI commands end-to-end
- Testing database operations
- Testing file I/O
- Pre-release validation

**Example:**
```bash
# Run all integration tests
python run_tests.py --integration

# Run specific integration test
pytest tests/integration/test_e2e_cli.py -v
```

### 4. Property-Based Tests (Hypothesis)

**Purpose:** Automatically generate hundreds of test cases

**Use when:**
- Finding edge cases
- Testing input validation
- Security testing (injection attacks)
- Fuzzing CLI inputs

**Example:**
```bash
# Install hypothesis
pip install hypothesis

# Run property-based tests
pytest tests/generators/hypothesis_generator.py -v

# See example inputs Hypothesis would generate
python tests/generators/hypothesis_generator.py --examples
```

### 5. Auto-Generated Tests

**Purpose:** Generate tests from CLI command definitions

**Use when:**
- Adding new CLI commands
- Ensuring all commands are tested
- Regression testing after CLI changes

**Example:**
```bash
# Generate tests from CLI introspection
python tests/generators/test_generator.py

# Run generated tests
pytest tests/generated/test_cli_generated.py -v
```

---

## Quick Start

### Install Dependencies

```bash
# Core testing
pip install pytest pytest-cov

# Property-based testing (optional)
pip install hypothesis

# For development
pip install -e ".[dev]"
```

### Run All Tests

```bash
# Comprehensive test run
python run_tests.py --all

# With coverage report
python run_tests.py --all --coverage --report
```

### Run Manual Tests

```bash
# Interactive manual testing
./tests/manual_test_cli.sh

# Automated but visible (no pauses)
./tests/manual_test_cli.sh -v
```

---

## Manual Testing

### Running Manual Tests

The manual test script provides multiple test categories covering all CLI functionality:

```bash
# Show available test sections
./tests/manual_test_cli.sh -h

# Run all tests
./tests/manual_test_cli.sh

# Run specific sections
./tests/manual_test_cli.sh help env db apikey

# Verbose mode (shows command output)
./tests/manual_test_cli.sh -v

# Pause between sections (for review)
./tests/manual_test_cli.sh -p

# Quick mode (skip slower tests)
./tests/manual_test_cli.sh -q
```

### Test Sections

1. **help** - CLI Help & Version
2. **env** - Environment Configuration
3. **db** - Database Operations
4. **apikey** - API Key Management
5. **workflow** - Workflow Operations
6. **backup** - Backup Operations
7. **server** - Server Integration
8. **format** - Output Formats
9. **directory** - Directory Options
10. **error** - Error Handling
11. **edge** - Edge Cases

### Example Output

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Test Category 2: Database Operations
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Test 1: DB init ... PASS
Test 2: DB init with --import (existing) ... PASS
Test 3: DB init JSON format ... PASS
Test 4: DB status table ... PASS
```

---

## Automated Testing

### Unit Tests

Test individual functions and methods:

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test class
pytest tests/unit/test_config.py::TestGetConfig -v

# Run with coverage
pytest tests/unit/ --cov=api --cov-report=html
```

### Integration Tests

Test complete workflows:

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run E2E CLI tests
pytest tests/integration/test_e2e_cli.py -v

# Run database integration tests
pytest tests/integration/database/ -v
```

### Test Environment Variables

```bash
# Set testing mode (prevents default workflow init)
export N8N_DEPLOY_TESTING=1

# Run tests
pytest tests/unit/ -v
```

---

## Property-Based Testing

### Using Hypothesis

Property-based testing uses Hypothesis to generate test cases automatically by defining **properties** that should always hold true.

Instead of writing specific test cases, you define **properties** that should always be true:

**Traditional Test:**
```python
def test_env_with_tmp():
    result = run_cli(["env", "--data-dir", "/tmp"])
    assert result.returncode == 0
```

**Property-Based Test:**
```python
@given(path=st.text(min_size=1, max_size=100))
def test_env_with_any_path(path):
    result = run_cli(["env", "--data-dir", path])
    assert result.returncode in [0, 1, 2]  # Never crash
```

Hypothesis automatically generates test cases including edge cases like:
- Empty strings
- Unicode characters: `"/tmp/测试/🎉"`
- Path traversal: `"../../etc/passwd"`
- SQL injection: `"'; DROP TABLE--"`
- Command injection: `"$(rm -rf /)"`
- Buffer overflow: Very long strings

### Running Hypothesis Tests

```bash
# Install Hypothesis
pip install hypothesis

# Run property-based tests
pytest tests/generators/hypothesis_generator.py -v

# Run with statistics
pytest tests/generators/hypothesis_generator.py -v --hypothesis-show-statistics

# See what inputs Hypothesis generates
python tests/generators/hypothesis_generator.py --examples
```

### Writing Your Own Property Tests

```python
from hypothesis import given, strategies as st
import subprocess

@given(
    workflow_name=st.text(min_size=1, max_size=50),
    tags=st.lists(st.text(min_size=1, max_size=20), max_size=5)
)
def test_workflow_search_never_crashes(workflow_name, tags):
    """Property: Search should handle any input gracefully"""
    result = subprocess.run(
        ["n8n-deploy", "wf", "search", workflow_name],
        capture_output=True,
        timeout=5
    )
    # Should never crash
    assert result.returncode in [0, 1, 2]
    # Should never expose stack traces to users
    assert "Traceback" not in result.stderr
```

---

## Test Generation

### Generating Tests from CLI

The test generator introspects your Click commands and automatically generates test scenarios:

```bash
# Generate tests
python tests/generators/test_generator.py

# Run generated tests
pytest tests/generated/test_cli_generated.py -v
```

### What Gets Generated

For each CLI command, the generator creates tests for:

- **Help option** - `command --help`
- **No arguments** - `command` (if all args optional)
- **Each parameter** - Valid and invalid values
- **String parameters** - Empty strings, long strings
- **Path parameters** - Valid paths, invalid paths, non-existent paths
- **Boolean flags** - Flag present/absent
- **Choice parameters** - All valid choices

### Example Generated Test

```python
def test_env_help():
    """Run env --help"""
    result = subprocess.run(
        CLI_COMMAND + ['env', '--help'],
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode in [0], (
        f"Command failed with exit code {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
    assert "Usage:" in result.stdout

def test_env_format_table():
    """Test env with --format=table"""
    result = subprocess.run(
        CLI_COMMAND + ['env', '--table'],
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode in [0]

def test_env_format_json():
    """Test env with --format=json"""
    result = subprocess.run(
        CLI_COMMAND + ['env', '--json'],
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode in [0]
```

### Regenerating Tests

Regenerate tests whenever you:
- Add new CLI commands
- Add new options to existing commands
- Change command behavior

```bash
# Regenerate all tests
python tests/generators/test_generator.py

# Run to verify CLI hasn't broken
pytest tests/generated/ -v
```

---

## E2E Testing Strategy

### Which E2E Tests to Keep

Keep E2E tests for **business logic and integration scenarios** that involve:

**✓ Keep E2E Tests For:**
- **Workflow Lifecycle**: Add → List → Update → Delete → Restore sequences
- **Database Migrations**: Schema upgrades, data integrity across versions
- **Backup/Restore**: SHA256 checksums, tar.gz integrity, restore verification
- **API Key Management**: Creation, expiration, deactivation, rotation logic
- **Server Integration**: n8n API push/pull operations, authentication flows
- **Multi-Step Scenarios**: Complex workflows with state changes
- **Data Persistence**: Database operations with commit/rollback verification
- **File Operations**: Workflow file creation, modification, deletion with sync

**Example E2E Tests to Keep:**
```python
# tests/integration/test_e2e_workflows.py
def test_workflow_lifecycle_complete():
    """Test: Add → Update → Backup → Delete → Restore"""
    # 1. Add workflow
    add_workflow("test_workflow")
    assert workflow_exists("test_workflow")

    # 2. Update metadata
    update_workflow("test_workflow", tags=["prod"])

    # 3. Backup with checksum
    backup_file = create_backup()
    assert verify_sha256(backup_file)

    # 4. Delete workflow
    delete_workflow("test_workflow")
    assert not workflow_exists("test_workflow")

    # 5. Restore from backup
    restore_backup(backup_file)
    assert workflow_exists("test_workflow")
    assert has_tag("test_workflow", "prod")
```

### Which E2E Tests to Replace with Hypothesis

Replace repetitive E2E tests with property-based tests for:

**✗ Replace with Hypothesis:**
- **Format Validation**: JSON/table/plain text output for all commands
- **Path Handling**: Unicode paths, special characters, deep nesting
- **Input Sanitization**: SQL injection, command injection, XSS attempts
- **Help Output**: All commands have help, usage information present
- **Option Combinations**: All valid flag combinations work together
- **Error Handling**: Invalid inputs produce graceful errors
- **Edge Cases**: Empty strings, very long inputs, special characters

**Before (Repetitive E2E):**
```python
# Multiple E2E tests like this
def test_env_json_format():
    result = run_cli(["env", "--json"])
    assert valid_json(result.stdout)

def test_env_json_with_path():
    result = run_cli(["env", "--data-dir", "/tmp", "--json"])
    assert valid_json(result.stdout)

def test_env_json_with_unicode_path():
    result = run_cli(["env", "--data-dir", "/tmp/测试", "--json"])
    assert valid_json(result.stdout)
```

**After (One Hypothesis Property):**
```python
# Single test generates many examples automatically
@given(app_dir=paths, flow_dir=paths, format_choice=formats)
def test_env_json_always_valid(app_dir, flow_dir, format_choice):
    """Property: env --format json always produces valid JSON"""
    result = run_cli(["env", "--data-dir", app_dir, "--flow-dir", flow_dir, ("--json" if format_choice == "json" else "--table")])
    if format_choice == "json" and result.returncode == 0:
        assert valid_json(result.stdout)
```

## Best Practices

### When to Use Each Test Type

| Test Type | Use For | Frequency |
|-----------|---------|-----------|
| Manual | Visual verification, emoji output, UX | During development |
| Unit | Function logic, edge cases | Every commit |
| Integration | Workflows, database operations | Before merge |
| Property-Based | Security, input validation, edge cases | Weekly / Before release |
| Generated | Regression testing, new commands | After CLI changes |

### Test-Driven Development (TDD)

1. **Write property test first** (defines expected behavior)
2. **Generate test scenarios** (covers all cases)
3. **Run tests** (should fail)
4. **Implement feature**
5. **Run tests again** (should pass)

### Example TDD Workflow

```bash
# 1. Write property test
vim tests/generators/hypothesis_generator.py
# Add: test_new_feature_property()

# 2. Generate test scenarios
python tests/generators/test_generator.py

# 3. Run tests (expect failures)
pytest tests/generated/ -v
# ❌ test_new_feature... FAILED

# 4. Implement feature
vim api/cli/new_feature.py

# 5. Run tests (expect passes)
pytest tests/generated/ -v
# ✅ test_new_feature... PASSED
```

### CI/CD Integration

```yaml
# .gitlab-ci.yml or .github/workflows/test.yml

test:unit:
  script:
    - python run_tests.py --unit --coverage

test:integration:
  script:
    - python run_tests.py --integration

test:property-based:
  script:
    - pip install hypothesis
    - pytest tests/generators/hypothesis_generator.py -v

test:generated:
  script:
    - python tests/generators/test_generator.py
    - pytest tests/generated/ -v
```

### Code Coverage

```bash
# Generate coverage report
python run_tests.py --unit --coverage

# View HTML report
open htmlcov/index.html

# Check coverage percentage
coverage report --fail-under=80
```

---

## Troubleshooting

### Hypothesis finds a failing case

```bash
# Hypothesis will show the minimal failing example
pytest tests/generators/hypothesis_generator.py -v

# Output:
# Falsifying example: test_env_command_never_crashes(
#     app_dir='/tmp/../../../etc/passwd'
# )
```

**Fix:** Update your code to handle path traversal

### Generated tests fail after CLI changes

```bash
# Regenerate tests to match new CLI
python tests/generators/test_generator.py

# Run again
pytest tests/generated/ -v
```

### Manual tests hang

```bash
# Run with timeout
timeout 300 ./tests/manual_test_cli.sh

# Or run specific sections
./tests/manual_test_cli.sh help env db
```

---

## Advanced Usage

### Custom Test Generators

Create your own test generator for specific patterns:

```python
# tests/generators/custom_generator.py
def generate_security_tests():
    """Generate tests for common security vulnerabilities"""
    injection_patterns = [
        "'; DROP TABLE--",
        "$(rm -rf /)",
        "../../../etc/passwd",
        "<script>alert('XSS')</script>",
    ]

    tests = []
    for pattern in injection_patterns:
        tests.append({
            'name': f'test_rejects_injection_{hash(pattern)}',
            'command': ['wf', 'search', pattern],
            'expected_exit_code': [0, 1],  # Should handle gracefully
            'assert_no_error': True,
        })

    return tests
```

### Hypothesis Stateful Testing

Test sequences of commands:

```python
from hypothesis.stateful import RuleBasedStateMachine, rule, precondition

class CLIStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.workflows = []

    @rule(name=st.text(min_size=1, max_size=50))
    def add_workflow(self, name):
        result = run_cli(["wf", "add", "test.json", name])
        if result.returncode == 0:
            self.workflows.append(name)

    @rule()
    @precondition(lambda self: len(self.workflows) > 0)
    def list_workflows(self):
        result = run_cli(["wf", "list"])
        assert result.returncode == 0
        for wf in self.workflows:
            assert wf in result.stdout

TestCLI = CLIStateMachine.TestCase
```

---

## Resources

### Documentation
- [pytest documentation](https://docs.pytest.org/)
- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
- [Click testing](https://click.palletsprojects.com/en/8.1.x/testing/)

### Related Files
- `tests/manual_test_cli.sh` - Manual testing script
- `run_tests.py` - Test runner
- `tests/generators/` - Test generation tools
- `CLAUDE.md` - Project development guide

### Further Reading
- [Property-Based Testing with Hypothesis](https://hypothesis.works/)
- [Effective Python Testing](https://realpython.com/python-testing/)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html/)

---

## Summary

n8n-deploy uses a **comprehensive testing strategy**:

1. ✅ **Manual tests** for UX and visual verification
2. ✅ **Unit tests** for component logic
3. ✅ **Integration tests** for workflows
4. ✅ **Property-based tests** for edge cases and security
5. ✅ **Generated tests** for regression and coverage

**Run all tests before release:**
```bash
# Complete test suite
./tests/manual_test_cli.sh && \
python run_tests.py --all --coverage && \
pytest tests/generators/hypothesis_generator.py -v && \
python tests/generators/test_generator.py && \
pytest tests/generated/ -v
```

**Quick smoke test:**
```bash
./tests/manual_test_cli.sh -q && \
python run_tests.py --unit
```
