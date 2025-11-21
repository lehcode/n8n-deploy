# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.3] - 2024-11-22

- **Changed**: CI/CD pipelines now trigger deployments only on version tags, preventing accidental releases from branch pushes
- **Changed**: Pre-release tags (`-rc`, `-beta`, `-alpha`) deploy to TestPyPI; stable tags deploy to PyPI
- **Fixed**: Hypothesis test deadline increased to 10 seconds for CI environment stability
- **Fixed**: CLI test assertions updated for consistent validation across execution contexts

## [2.2.1] - 2024-11-20

- **Added**: Primary API key selection for servers, simplifying authentication in multi-key setups
- **Fixed**: `--flow-dir` option now properly respected during push operations
- **Fixed**: Git installation added to SAST and dependency scanning jobs for setuptools-scm compatibility
- **Changed**: CI pipeline optimized to run tests only on merge requests, master branch, and tags
- **Changed**: Removed redundant build:production and deploy stages from pipeline

## [2.2.0] - 2024-11-15

- **Added**: API key activate command for re-enabling deactivated keys
- **Added**: Enhanced apikey test and delete commands with improved UX
- **Added**: `--unmask` flag for displaying actual API key credentials (with security warning)
- **Added**: Environment configuration display command (`env`) with JSON and table output
- **Added**: Development environment support with `.env` file loading
- **Added**: Interactive database initialization with `--import` flag
- **Changed**: Standardized environment variable to `N8N_DEPLOY_DATA_DIR`
- **Changed**: Improved apikey list table layout with better formatting
- **Changed**: Extracted API key SQL operations to dedicated database CRUD layer
- **Removed**: `apikey get` command removed for enhanced credential protection
- **Removed**: `--data-dir` option removed from apikey commands (uses global config)
- **Security**: Enhanced credential protection by removing direct key retrieval

## [2.1.0] - 2024-11-10

- **Added**: GitHub Pages deployment with Google Analytics support
- **Added**: Font Awesome social icons in site footer
- **Added**: SEO enhancements for search engines and social media
- **Added**: Comprehensive testing framework documentation
- **Changed**: Navigation structure reorganized for better discoverability
- **Changed**: Documentation refactored into modular structure

## [2.0.2] - 2024-10-30

- **Fixed**: Default setuptools-scm version scheme for stable releases
- **Fixed**: Git history fetching for accurate version detection
- **Fixed**: Hypothesis tests no longer pollute project database
- **Fixed**: Deprecated `repository_url` updated to `repository-url` in PyPI publish action
- **Fixed**: GitHub Pages workflow updated to latest action versions
- **Changed**: GitLab CI/CD strategy aligned with GitHub Actions for consistency
- **Changed**: Build artifacts changed from `.venv` to `dist` directory
- **Changed**: CI/CD trigger strategy updated for branch-based workflows

## [2.0.1] - 2024-10-28

- **Fixed**: JSON output no longer contaminated by wrapper script stdout
- **Fixed**: Auto-server creation removed from apikey add command
- **Fixed**: Concurrent operations test stability improved
- **Fixed**: Invalid pull_policy removed from GitLab CI default section
- **Changed**: Docker MTU and registry mirror configuration added to CI

## [2.0.0] - 2024-10-25

- **Added**: Complete rewrite with modular architecture
- **Added**: SQLite database as single source of truth for workflow metadata
- **Added**: API key management with lifecycle support (create, deactivate, delete, test)
- **Added**: Server management for multiple n8n instances
- **Added**: Workflow push/pull operations with n8n server API integration
- **Added**: Database backup and restore functionality with SHA256 verification
- **Added**: Rich CLI output with emoji tables (optional `--no-emoji` for scripts)
- **Added**: Flexible base folder configuration via CLI or environment variables
- **Added**: Comprehensive type annotations with strict mypy compliance
- **Added**: Property-based testing with Hypothesis framework
- **Added**: Modular manual test framework with 107 tests across 11 categories
- **Added**: UTF-8 workflow name support (emojis, international characters)
- **Changed**: Migrated from JSON config files to SQLite database
- **Changed**: Reorganized CLI into command groups (wf, db, apikey, server, env)
- **Changed**: Configuration now requires explicit paths (no implicit defaults)
- **Changed**: Environment variables standardized with `_DIR` suffix
- **Changed**: Python 3.12+ compatibility with timezone-aware datetime handling
- **Removed**: Legacy JSON-based configuration system
- **Removed**: Implicit default directories

---

[2.2.3]: https://github.com/lehcode/n8n-deploy/compare/v2.2.1...v2.2.3
[2.2.1]: https://github.com/lehcode/n8n-deploy/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/lehcode/n8n-deploy/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/lehcode/n8n-deploy/compare/v2.0.2...v2.1.0
[2.0.2]: https://github.com/lehcode/n8n-deploy/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/lehcode/n8n-deploy/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/lehcode/n8n-deploy/releases/tag/v2.0.0
