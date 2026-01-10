# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2026-01-09

### Added

- **Multi-workflow push/pull support** - Push or pull multiple workflows in a single command
  - `n8n-deploy wf push wf1 wf2 wf3 --remote myserver`
  - `n8n-deploy wf pull wf1 wf2 wf3 --remote myserver`
  - Progress indicators `[1/3]`, `[2/3]`, `[3/3]` for batch operations
  - Summary table showing OK/FAIL status for each workflow
  - Continue processing all workflows even if some fail
  - Exit code 1 if any workflow fails, 0 if all succeed
  - Full backwards compatibility with single workflow usage
- **Per-server SSL verification** - Configure SSL settings per server (schema v8)
  - `n8n-deploy server ssl <name> --skip-verify` to disable verification
  - `n8n-deploy server ssl <name> --verify` to enable verification
  - Priority: CLI flag > server setting > default (verify)
- **Workflow link command** - Update workflow metadata without push/pull
  - `n8n-deploy wf link <workflow> --flow-dir <path>` to update stored path
  - `n8n-deploy wf link <workflow> --server <name>` to change linked server
- **Smart workflow lookup** - Flexible workflow name matching
  - Case-insensitive matching: `my workflow` finds `My Workflow`
  - Slug-style matching: `my-workflow` finds `My Workflow`
  - Auto-append `.json` for filename lookup
  - Priority: ID → exact name → case-insensitive → slug → filename
- `--non-interactive` flag for `wf pull` to suppress prompts in automation
- `--db` and `--server` flags for `wf delete` for granular control

### Changed

- **BREAKING**: `wf delete` now requires `--db` and/or `--server` flags
  - `--db`: remove from local database only
  - `--server`: delete from n8n server only
  - Both flags: delete from server first, then database
  - Local JSON files are never deleted
- `--filename` option for `wf pull` only works with single workflow (warning shown if used with multiple)
- Default filenames (`{workflow_id}.json`) used for multi-workflow pulls

### Removed

- Script synchronization feature (--scripts flags removed from wf push)

## [0.2.0] - 2025-12-08

### Added

- **Folder synchronization system** for managing n8n folders
  - `folder` CLI command group for folder sync operations
  - `FolderSyncManager` for bidirectional folder sync between local and remote
  - `N8nInternalClient` for n8n internal REST API integration
  - `FolderDB` class for folder CRUD operations
  - Database schema v6 with new tables: `n8n_folders`, `folder_mappings`
- **Enhanced CLI verbosity**
  - Global `--verbose`/`-v` flag for HTTP request logging
  - Extended `-vv` verbosity for detailed debugging output
  - New `api/cli/verbose.py` module for verbose output formatting
- HTTP client abstraction layer (`api/workflow/http_client.py`)
- Server resolver for flexible server selection (`api/workflow/server_resolver.py`)
- Shared CLI output formatting utilities (`api/cli/output.py`)
- Accept workflows without `id` field - auto-generates `draft_{uuid}` temporary ID (ND-47)
- Automatic ID replacement with server-assigned ID after first successful push
- Workflow file renaming from `draft_*.json` to `{server_id}.json` on push
- Custom workflow filename support with basename matching (ND-50)

### Changed

- **BREAKING**: `wf remove` command replaced with `wf delete`
- **BREAKING**: Removed `server set-primary` command from server group
- API field filtering now uses whitelist approach for n8n API operations
- Refactored CLI modules to reduce cyclomatic complexity

### Fixed

- Workflow duplication on 404 errors during push operations
- Invalid settings fields filtered before push to n8n API
- Workflow active state preserved during push operations
- n8n internal API authentication and cookie handling
- Strip readonly fields before creating/updating workflows on n8n server
- Basename matching for filename lookup in push command (ND-50)
- Import paths updated from `api.wf` to `api.workflow`

## [0.1.7] - 2025-11-26

### Changed

- CI: use `github.ref_name` for PEP 440 tag detection
- CI: enable build-matrix on tag push
- CI: configure pipeline stages per trigger type
- Test subprocess timeouts increased for CI stability

### Fixed

- Respect `--flow-dir` in push operations
- Remove auto-server creation from `apikey add` command
- JSON output contaminated by wrapper script stdout

## [0.1.5] - 2024-11-27

### Added

- Initial release with fresh versioning
- SQLite database as single source of truth for workflow metadata
- API key management with lifecycle support (create, deactivate, delete, test)
- Server management for multiple n8n instances
- Workflow push/pull operations with n8n server API integration
- Database backup functionality with SHA256 verification
- Rich CLI output with emoji tables (optional `--no-emoji` for scripts)
- Flexible base folder configuration via CLI or environment variables
- Comprehensive type annotations with strict mypy compliance
- Property-based testing with Hypothesis framework

### Changed

- Development status changed to Beta
- Tag format updated to PEP 440 compliant (v0.1.5rc1 instead of v0.1.5-rc1)

---

[0.9.0]: https://github.com/lehcode/n8n-deploy/compare/v0.2.0...v0.9.0
[0.2.0]: https://github.com/lehcode/n8n-deploy/compare/v0.1.7...v0.2.0
[0.1.7]: https://github.com/lehcode/n8n-deploy/compare/v0.1.5...v0.1.7
[0.1.5]: https://github.com/lehcode/n8n-deploy/releases/tag/v0.1.5
