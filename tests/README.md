# n8n-deploy Test Suite

Test suite for n8n-deploy n8n workflow manager using assertpy assertions and pytest patterns.

## Quick Start

### Using the Test Runner (Recommended)

```bash
# Run unit tests
python run_tests.py --unit

# Run integration tests
python run_tests.py --integration

# Run with coverage
python run_tests.py --unit --coverage
```

### Direct pytest Commands

```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
N8N_DEPLOY_TESTING=1 python -m pytest tests/integration/ -v

# Current status: Clean output, all tests pass
```

## Test Commands

### Test Runner Script

```bash
python run_tests.py --unit                    # Unit tests only
python run_tests.py --integration            # Integration tests only
python run_tests.py --fast                   # Fast tests (no slow tests)
python run_tests.py --quality                # Code quality checks
python run_tests.py --report                 # Generate comprehensive report
python run_tests.py --specific tests/unit/test_api_keys.py  # Run specific test
```

**Note**: Test type is required - you must specify `--unit`, `--integration`, `--fast`, `--quality`, `--report`, or `--specific`

### Direct pytest Commands

```bash
python -m pytest tests/unit/ -v                    # All unit tests
python -m pytest tests/unit/test_api_keys.py -v    # Specific file
N8N_DEPLOY_TESTING=1 python -m pytest tests/integration/ -v  # Integration tests
```

### Focused Testing

```bash
python -m pytest tests/unit/ --lf                  # Last failed
python -m pytest tests/unit/ --tb=short            # Clean output
python -m pytest tests/unit/ --collect-only -q     # Count tests
```

### Coverage & Analysis

```bash
python -m pytest tests/unit/ --cov=api --cov-report=html
mypy tests/ --strict
```

### Specific Tests

```bash
# Test class
python -m pytest tests/unit/test_api_keys.py::TestAddApiKey -v

# Test method
python -m pytest tests/unit/test_api_keys.py::TestAddApiKey::test_add_api_key_variations -v
```

## Test Structure

```
tests/
├── unit/                      # Unit tests
│   ├── test_api_keys.py      # n8n API key tests
│   ├── test_models.py        # Pydantic model tests
│   ├── test_config.py        # Configuration tests
│   ├── test_manager.py       # Workflow manager tests
│   ├── test_cli.py           # CLI interface tests
│   └── test_n8n_deploy_db.py # Database tests
└── integration/               # Integration tests
    ├── test_workflow_lifecycle.py
    └── test_backup_restore.py
```

## Core Patterns

### Assertions (assertpy)

```python
from assertpy import assert_that

assert_that(result).is_not_none()
assert_that(result).is_equal_to("expected")
assert_that(items).contains("item")
assert_that(count).is_greater_than(0)
```

### Test Utilities

```python
from tests.test_utils import TestAssertions, TestDataFactory, UtilityPatterns

# Data creation
workflow = TestDataFactory.create_workflow()
api_key_data = TestDataFactory.create_test_api_key_data()

# Assertions
TestAssertions.assert_datetime_recent(workflow.created_at)
TestAssertions.assert_workflow_valid(workflow)

# Patterns
UtilityPatterns.test_model_creation(Workflow, data)
UtilityPatterns.test_enum_values(WorkflowType, ["main", "subflow", "utility"])
```

## Fixtures

### Core

- `temp_dir: Path` - Temporary directory
- `test_config: N8nDeployConfig` - Test configuration
- `test_db: N8nDeployDB` - Test database
- `test_manager: WorkflowManager` - Workflow manager
- `test_api_key_manager: ApiKeyManager` - n8n API key manager
- `cli_runner: CliRunner` - CLI test runner

### Data

- `test_api_key_data: Dict` - Test n8n API key data
- `mock_workflow_data: Dict` - Mock workflow data
- `sample_workflow_json: Dict` - Sample n8n workflow JSON

## Functionality Coverage

- ✅ Pydantic models with type safety
- ✅ Enum serialization
- ✅ Configuration resolution
- ✅ Database operations
- ✅ Add/retrieve/delete API keys
- ✅ Plain text key storage
- ✅ Expiration handling

## Expected Results

### Clean Test Output

Tests now run with clean, warning-free output thanks to pytest warning filters:

```bash
# Unit tests (45 tests)
python run_tests.py --unit
🧪 Running unit tests...
✅ Unit tests passed

# Integration tests (24 tests)
python run_tests.py --integration
🔗 Running integration tests...
✅ Integration tests passed
```

### Direct pytest Output

```bash
# Unit tests: Clean output, no warnings
python -m pytest tests/unit/ -q
.............................................                            [100%]

# Integration tests: Clean output, no warnings
N8N_DEPLOY_TESTING=1 python -m pytest tests/integration/ -q
........................                                                 [100%]
```

**Note**: Pydantic deprecation warnings are filtered out in `pyproject.toml` for cleaner test output.

## Development Notes

- **Type hints required** on all test functions
- **UTC datetime** usage (not deprecated utcnow())
- **assertpy** for consistent assertion patterns
- **Streamlined API** for API key management tests
- **String returns** from get_api_key() (not objects)
