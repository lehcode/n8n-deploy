# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Accept workflows without `id` field - auto-generates `draft_{uuid}` temporary ID (ND-47)
- Automatic ID replacement with server-assigned ID after first successful push
- Workflow file renaming from `draft_*.json` to `{server_id}.json` on push

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

- Test subprocess timeouts increased from 30s to 60s for CI stability
- Development status changed to Beta
- Tag format updated to PEP 440 compliant (v0.1.5rc1 instead of v0.1.5-rc1)

### Fixed

- GitHub CI: use `github.ref_name` for PEP 440 tag detection (was matching "refs/tags/")

---

[Unreleased]: https://github.com/lehcode/n8n-deploy/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/lehcode/n8n-deploy/releases/tag/v0.1.5
