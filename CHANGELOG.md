# Changelog

All notable changes to n8n-deploy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-09-27

### 🎉 Major Release - Production Ready

Version 2.0.0 represents a complete architectural overhaul focused on **modularity**, **privacy**, and **user experience**. This is a mature, production-ready tool for managing n8n workflows.

> *"The best way to make something reliable is to make it simple."* - Donald A. Norman

### ✨ Features

#### 🔒 Privacy-First Architecture
- **Zero data collection** - No analytics, tracking, or telemetry
- **Local-only storage** - Everything stored in SQLite on your machine
- **Transparent operation** - Only communicates with YOUR n8n server when YOU request it
- **Open source transparency** - Complete source code visibility

#### 🚀 Simplified Installation & Setup
- **One-command installation** via PyPI: `pip install n8n-deploy`
- **No-installation option** - Clone and use `./n8n-deploy` wrapper script
- **Smart defaults** - Works out of the box with minimal configuration
- **Three optional environment variables** for customization

#### 🎨 Enhanced User Experience
- **Beautiful, colorful CLI output** with rich formatting and emojis
- **Script-friendly mode** with `--no-emoji` flag for automation
- **Consistent command structure** across all operations
- **Helpful error messages** without Python tracebacks
- **Progress indicators** for long-running operations

#### 🗄️ Advanced Database Management
- **SQLite backend** - Fast, reliable, and portable
- **Schema versioning** with automatic migrations
- **Database optimization** tools (compact)
- **Backup and restore** capabilities for the database itself
- **Integrity verification** for all operations

#### 🔐 Secure API Key Management
- **Local storage** of n8n API keys (plain text in local database)
- **Multiple server support** - Store keys for different n8n instances
- **Key lifecycle management** - Add, list, test, deactivate, delete
- **JWT validation** to ensure proper n8n API key format
- **Usage tracking** with created/last used timestamps

#### 💾 Comprehensive Backup System
- **Compressed tar.gz backups** with metadata preservation
- **SHA256 integrity verification** for all backup files
- **Selective restoration** - Choose what to restore
- **Backup verification** tools to ensure data integrity
- **Database tracking** of backup metadata

#### 🌐 Enhanced Server Integration
- **Push/pull workflows** to/from any n8n server
- **SSL verification** with optional skip for development
- **Server URL override** via command-line flags
- **Live server browsing** without leaving terminal
- **Environment variable support** for server configuration

### 🏗️ Architectural Improvements

#### Modular Code Organization
- **Separated CLI commands** into focused modules
- **Database operations** split into core, backup, and schema components
- **Workflow management** organized into CRUD, API, and backup modules
- **Clean separation of concerns** across all components

#### Modern Python Practices
- **Type safety** with comprehensive annotations and mypy compliance
- **Pydantic models** for data validation and serialization
- **Modern packaging** with pyproject.toml and PEP 621 metadata
- **Comprehensive testing** with unit, integration, and E2E tests

#### Configuration System
- **Hierarchical configuration** with clear precedence rules
- **Environment variable support** for all options
- **Command-line overrides** for flexible usage patterns
- **Smart path resolution** with helpful error messages

### 🔄 Changed

#### Breaking Changes from 1.x
- **Renamed project** from "elektronik" to "n8n-deploy"
- **Simplified API key storage** - No encryption complexity
- **Removed service categorization** - Designed specifically for n8n
- **Updated database schema** with migration support
- **New command structure** with grouped commands

#### Command Structure Updates
- **Grouped commands** - `db`, `apikey` command groups for better organization
- **Consistent option naming** across all commands
- **Global flag handling** - Options like `--no-emoji` work everywhere
- **Improved help text** with usage examples

#### Enhanced Output Formats
- **Rich table formatting** with colors and styling
- **JSON output support** for machine parsing
- **Script-friendly options** for automation use cases
- **Consistent emoji usage** with disable option

### 🐛 Fixed

- **Resolved CLI entry point issues** in CI/CD environments
- **Fixed path resolution** edge cases with relative paths
- **Improved error handling** with user-friendly messages
- **Fixed database initialization** race conditions
- **Resolved SSL verification** issues with self-signed certificates

### 🚀 Performance

- **Faster database operations** with optimized queries
- **Reduced memory usage** for large workflow collections
- **Efficient backup creation** with streaming compression
- **Optimized file I/O** operations throughout

### 🔧 Developer Experience

#### Testing Infrastructure
- **88 comprehensive E2E tests** covering all functionality
- **Unit and integration test** separation
- **Real subprocess testing** for authentic CLI validation
- **Coverage reporting** with detailed metrics
- **Quality checks** with black, mypy, and security scanning

#### CI/CD Pipeline
- **GitLab CI integration** with efficient resource usage
- **Multi-version Python testing** (3.8-3.12)
- **Docker containerization** for consistent builds
- **Automated security scanning** and dependency checks
- **Package deployment** automation

#### Documentation
- **Comprehensive API documentation** with type hints
- **User-focused README** with practical examples
- **Developer setup guides** with multiple installation options
- **Architecture documentation** for contributors

### 📦 Dependencies

#### Core Dependencies
- **click ≥8.0.0** - Command-line interface framework
- **rich ≥13.0.0** - Rich text and beautiful formatting
- **pydantic ≥2.0.0** - Data validation and settings management
- **requests ≥2.28.0** - HTTP library for n8n API communication
- **python-dateutil ≥2.8.0** - Date/time utilities
- **tabulate ≥0.9.0** - Table formatting
- **colorama ≥0.4.0** - Cross-platform colored terminal text

#### Development Dependencies
- **pytest** - Testing framework
- **black** - Code formatting
- **mypy** - Static type checking
- **pre-commit** - Git hooks for quality assurance

### 🔮 Future Enhancements

While 2.0.0 is feature-complete and production-ready, planned future enhancements include:

- **Workflow templates** - Save and reuse workflow patterns
- **Diff visualization** - Visual comparison of workflow changes
- **Batch operations** - Mass operations on multiple workflows
- **Plugin system** - Extensibility for custom integrations
- **Web UI** - Optional web interface for visual management

## [1.x.x] - Legacy Versions

Earlier versions were development releases. Version 2.0.0 represents the first stable, production-ready release under the "n8n-deploy" name with complete architectural redesign.

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## Support

- **Documentation**: [GitHub Wiki](https://github.com/lehcode/n8n-deploy/wiki)
- **Issues**: [GitHub Issues](https://github.com/lehcode/n8n-deploy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/lehcode/n8n-deploy/discussions)

---

**Thank you to all contributors who made 2.0.0 possible!** 🎉