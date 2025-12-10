# CI/Local Environment Parity Guide

This document maps GitLab CI pipeline jobs to equivalent local test commands, helping developers catch CI failures before pushing to remote.

## Quick Start: Run Tests Like CI

```bash
# Recommended: Use CI simulation script
./scripts/run-like-ci.sh

# Alternative: Use test runner in CI mode
python run_tests.py --all --ci-mode
```

## Environment Variables

### CI Environment
```bash
N8N_DEPLOY_TESTING=1       # Prevents default workflow initialization in tests
ENVIRONMENT=production      # Disables .env file loading
GIT_DEPTH=0                 # Full git history for version detection
PYTHON_VERSION=3.9          # Primary Python version for CI
```

### Local Environment (Default)
```bash
# Usually not set, or set differently
N8N_DEPLOY_TESTING=<not set>
ENVIRONMENT=<not set>       # May load .env files
GIT_DEPTH=<not applicable>  # Full clone by default
PYTHON_VERSION=<system default>
```

### Setting Up Local CI-like Environment
```bash
# Method 1: Export manually
export N8N_DEPLOY_TESTING=1
export ENVIRONMENT=production

# Method 2: Use --ci-mode flag
python run_tests.py --unit --ci-mode

# Method 3: Use CI simulation script
./scripts/run-like-ci.sh
```

## Pipeline Stages Mapped to Local Commands

### Stage 1: Security (Parallel Execution)

| CI Job | Local Command | Notes |
|--------|---------------|-------|
| `secret_detection` | `gitleaks git . --verbose --redact --config .gitleaks.toml` | Requires gitleaks installation |
| `dependency_scanning` | `pip-audit -r requirements.txt` | Part of pre-commit hooks |
| `security:bandit` | `bandit -r api/ -f json --exclude tests/` | Part of pre-commit hooks |
| `security:semgrep` | `semgrep --config=auto api/ --json --error` | **NEW**: Added to pre-commit hooks |

**Local equivalent (all security checks)**:
```bash
# Option 1: Run individually
gitleaks git . --verbose --redact --config .gitleaks.toml
pip-audit --strict -r requirements.txt
bandit -r api/ -f json --exclude tests/
semgrep --config=auto api/ --json --error

# Option 2: Use pre-commit hooks
pre-commit run --all-files

# Option 3: Use CI simulation script
./scripts/run-like-ci.sh  # Runs all security checks
```

### Stage 2: Quality (Parallel Execution)

| CI Job | Local Command | Notes |
|--------|---------------|-------|
| `quality:mypy` | `mypy api/ --strict --show-error-codes` | Part of pre-commit hooks |
| `quality:black` | `black --check api/` | Part of pre-commit hooks |

**Local equivalent**:
```bash
# Run quality checks
mypy api/ --strict --show-error-codes
black --check api/

# Or use test runner
python run_tests.py --quality
```

### Stage 3: Test (Parallel Execution)

| CI Job | Local Command | Notes |
|--------|---------------|-------|
| `test:unit` | `python run_tests.py --unit --no-deps-check --quiet` | 59 tests |
| `test:integration` | `python run_tests.py --integration --no-deps-check --quiet` | Integration tests excluding E2E |
| `test:hypothesis` | `python run_tests.py --hypothesis --no-deps-check` | Property-based testing (755 examples) |

**Local equivalent (CI mode)**:
```bash
# Run with CI environment settings
export N8N_DEPLOY_TESTING=1
python run_tests.py --unit --no-deps-check --quiet
python run_tests.py --integration --no-deps-check --quiet

# Or use --ci-mode flag
python run_tests.py --all --ci-mode

# Or use CI simulation script
./scripts/run-like-ci.sh
```

### Stage 4: Build Matrix (Parallel Execution)

| CI Job | Local Command | Notes |
|--------|---------------|-------|
| `build:python-matrix` (3.9) | `python3.9 -m build --wheel --sdist` | Requires Python 3.9 installed |
| `build:python-matrix` (3.10) | `python3.10 -m build --wheel --sdist` | Requires Python 3.10 installed |
| `build:python-matrix` (3.11) | `python3.11 -m build --wheel --sdist` | Requires Python 3.11 installed |
| `build:python-matrix` (3.12) | `python3.12 -m build --wheel --sdist` | Requires Python 3.12 installed |
| `build:python-matrix` (3.13) | `python3.13 -m build --wheel --sdist` | Requires Python 3.13 installed |

**Local equivalent**:
```bash
# Build with current Python version
python -m build --wheel --sdist

# Test installation
pip install dist/*.whl
n8n-deploy --version
```

## Common Issues and Solutions

### Issue 1: Version Detection Fails on CI

**Symptom**: Tests pass locally but fail on CI with version like `0.1.dev37` instead of expected version.

**Cause**: CI shallow clone prevents setuptools_scm from detecting git tags.

**Solution**:
```yaml
# .gitlab-ci.yml already has this fix
variables:
  GIT_DEPTH: 0  # Full clone with all tags
```

**Local testing**:
```bash
# Test version detection
python -c "from importlib.metadata import version; print(version('n8n-deploy'))"

# Run version detection tests
python -m pytest tests/unit/test_version_detection.py -v
```

### Issue 2: Integration Tests Fail on CI but Pass Locally

**Symptom**: Integration tests pass locally but fail on CI.

**Causes**:
1. N8N_DEPLOY_TESTING not set locally
2. Different .env file behavior
3. Git tags not available (shallow clone)

**Solutions**:
```bash
# Test with CI environment
export N8N_DEPLOY_TESTING=1
export ENVIRONMENT=production
python run_tests.py --integration --quiet

# Or use --ci-mode
python run_tests.py --integration --ci-mode

# Or use CI simulation script
./scripts/run-like-ci.sh
```

### Issue 3: Security Checks Missing Locally

**Symptom**: CI fails on semgrep or gitleaks checks not run locally.

**Cause**: Pre-commit hooks were missing semgrep and gitleaks.

**Solution**: Pre-commit hooks now updated (as of this commit):
```bash
# Install/update pre-commit hooks
pre-commit install
pre-commit install --hook-type pre-push

# Run all hooks manually
pre-commit run --all-files
```

### Issue 4: Python Version Differences

**Symptom**: Tests pass locally but fail on CI due to Python version differences.

**Cause**: Local Python version differs from CI (3.9).

**Solution**:
```bash
# Install pyenv for multiple Python versions
pyenv install 3.9.20
pyenv local 3.9.20

# Or use Docker
docker run -it python:3.9-slim bash
```

## Pre-commit Hooks vs CI Jobs

### Pre-commit Hooks (Local)
```yaml
# .pre-commit-config.yaml
- black                    # Code formatting
- trailing-whitespace      # Whitespace cleanup
- end-of-file-fixer        # EOF newlines
- check-yaml               # YAML validation
- check-added-large-files  # File size limit
- markdownlint             # Markdown linting
- bandit                   # Security (Python)
- gitleaks                 # Secret detection (NEW)
- semgrep                  # Pattern-based security (NEW)
- mypy-strict              # Type checking
- pip-audit                # Dependency vulnerabilities
```

### Pre-push Hooks (Local)
```yaml
- run-unit-tests           # python run_tests.py --unit
- run-integration-tests    # python run_tests.py --integration
```

### CI Jobs (Not in Pre-commit)
- `test:hypothesis` - Property-based testing (optional locally)
- `build:python-matrix` - Multi-version builds (requires multiple Python installations)

## Testing Workflow Recommendations

### Before Every Commit
```bash
# Auto-runs via pre-commit hooks
git add <files>
git commit -m "message"
# Hooks run: black, bandit, semgrep, gitleaks, mypy, pip-audit
```

### Before Every Push
```bash
# Auto-runs via pre-push hooks
git push
# Hooks run: unit tests, integration tests
```

### Before Creating MR/PR
```bash
# Run full CI simulation
./scripts/run-like-ci.sh

# Or manually run all stages
pre-commit run --all-files              # Security + quality
python run_tests.py --all --ci-mode     # All tests
python -m build --wheel --sdist         # Build check
```

### For Version-Sensitive Changes
```bash
# Test version detection
python -m pytest tests/unit/test_version_detection.py -v

# Check actual version
python -c "from importlib.metadata import version; print(version('n8n-deploy'))"
```

## Docker-Based CI Simulation (Optional)

For exact CI environment replication:

```bash
# Create docker-compose.test.yml (TODO: Phase 2)
docker-compose -f docker-compose.test.yml run test

# Or run in Docker manually
docker run -it --rm \
  -v $(pwd):/app \
  -w /app \
  python:3.9-slim \
  bash -c "
    apt-get update && apt-get install -y git
    pip install -e .[test,dev]
    export N8N_DEPLOY_TESTING=1
    python run_tests.py --all --quiet
  "
```

## Version Detection Patterns

Test patterns support multiple version formats:

| Format | Example | Context |
|--------|---------|---------|
| Standard release | `2.0.3` | Production releases |
| Dev version | `2.0.3.dev42` | Development builds |
| RC version | `2.3.0-rc1` | Release candidates (hyphen format) |
| CI fallback | `0.1.dev37` | Shallow clone fallback |
| Dev fallback | `0.0.0` | No git metadata |

**Pattern used in tests**:
```python
r"\d+\.\d+(\.\d+)?(\.dev\d+|-rc\d+)?"
```

## GitLab Runner Local Execution (Advanced)

Install and configure gitlab-runner for exact CI replication:

```bash
# Install gitlab-runner
# See: https://docs.gitlab.com/runner/install/

# Validate CI configuration
gitlab-ci-lint .gitlab-ci.yml

# Run specific job locally
gitlab-runner exec docker test:unit

# Run with specific Python version
gitlab-runner exec docker test:unit --docker-image python:3.9-slim
```

## Summary Table: Local vs CI

| Aspect | Local | CI | How to Sync |
|--------|-------|----|----|
| Git depth | Full | Full (`GIT_DEPTH=0`) | Already synced |
| N8N_DEPLOY_TESTING | Not set | `1` | Use `--ci-mode` or export manually |
| ENVIRONMENT | Not set | `production` | Use `--ci-mode` or export manually |
| Python version | System | 3.9-3.13 matrix | Use pyenv or Docker |
| Pre-commit hooks | Configured | N/A | Keep `.pre-commit-config.yaml` updated |
| Security scans | Partial | Full | **NOW SYNCED** (semgrep + gitleaks added) |
| Test verbosity | Default `-v` | `--quiet` | Use `--ci-mode` flag |
| Package installation | `uv` or `pip` | `uv` | Use same tools |

## Quick Reference

```bash
# Full CI simulation (recommended)
./scripts/run-like-ci.sh

# Run tests in CI mode
python run_tests.py --all --ci-mode

# Run specific tests in CI mode
python run_tests.py --unit --ci-mode
python run_tests.py --integration --ci-mode

# Check version detection
python -m pytest tests/unit/test_version_detection.py -v

# Run all pre-commit hooks
pre-commit run --all-files

# Build package
python -m build --wheel --sdist
pip install dist/*.whl
n8n-deploy --version
```

## Files Added/Modified for CI/Local Parity

1. **scripts/run-like-ci.sh** - CI simulation script (new)
2. **.pre-commit-config.yaml** - Added semgrep and gitleaks hooks
3. **tests/unit/test_version_detection.py** - Version detection tests (new)
4. **run_tests.py** - Added `--ci-mode` flag
5. **docs/CI_LOCAL_PARITY.md** - This documentation (new)

## Next Steps

After synchronizing your local environment:

1. Run `./scripts/run-like-ci.sh` before every push
2. Fix any failures locally before pushing
3. Monitor CI pipelines for any remaining discrepancies
4. Update this document if new differences are found

## Support

If you encounter CI failures that don't reproduce locally:

1. Check this document for known issues
2. Run `./scripts/run-like-ci.sh` to simulate CI
3. Enable verbose output: `python run_tests.py --all` (without `--quiet`)
4. Compare environment variables: `env | grep N8N_DEPLOY`
5. Check git tags available: `git describe --tags --always`
