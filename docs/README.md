# n8n-deploy Developer Documentation

## Overview

This documentation suite provides comprehensive guidance for developers working with n8n-deploy, from understanding the architecture to contributing code and troubleshooting issues.

## Documentation Structure

### 📋 Core Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep dive into system design, component interactions, and architectural patterns
- **[API_REFERENCE.md](API_REFERENCE.md)** - Comprehensive API documentation with type signatures and examples
- **[DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md)** - Complete development environment setup and workflow guide

### 🧪 Development Process

- **[TESTING.md](TESTING.md)** - Testing strategies, framework usage, and CI/CD integration
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Code standards, git workflow, and contribution guidelines
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Diagnostic procedures and issue resolution

## Quick Start for Developers

### 1. Understanding the System
Start with [ARCHITECTURE.md](ARCHITECTURE.md) to understand:
- Component relationships and data flow
- Database schema and design decisions
- Error handling and security model
- Performance considerations

### 2. Setting Up Development Environment
Follow [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for:
- Python environment configuration
- Dependency management with uv or pip
- IDE setup and development tools
- Multi-version testing setup

### 3. Working with the Codebase
Use [API_REFERENCE.md](API_REFERENCE.md) to understand:
- Core modules and their responsibilities
- Type-safe API patterns
- Configuration system hierarchy
- CLI command structure

### 4. Testing and Quality Assurance
Reference [TESTING.md](TESTING.md) for:
- 3-tier testing strategy (Unit/Integration/E2E)
- Custom test runner usage
- CI/CD pipeline understanding
- Test development patterns

### 5. Contributing Code
Follow [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style and type safety requirements
- Git workflow and branch management
- Pull request process
- Release procedures

### 6. Resolving Issues
Use [TROUBLESHOOTING.md](TROUBLESHOOTING.md) when encountering:
- Installation and setup problems
- Runtime and configuration issues
- Testing and development challenges
- Performance and deployment problems

## Key Project Characteristics

### Technical Excellence
- **Type Safety**: Strict mypy compliance across entire codebase
- **Test Coverage**: 3-tier testing with 88 comprehensive E2E tests
- **Modern Python**: Python 3.8-3.12 support with contemporary patterns
- **Developer Experience**: Rich terminal output, verbose testing, clear error messages

### Architecture Highlights
- **Database-First**: SQLite as single source of truth for workflow metadata
- **Privacy-First**: Zero data collection, local-only storage
- **Modular Design**: Focused components with clear separation of concerns
- **CLI-Centric**: Command-line interface optimized for both interactive and scripted use

### Development Workflow
- **GitLab CI/CD**: Efficient MR-only pipeline pattern
- **Quality Gates**: Black formatting, mypy type checking, comprehensive testing
- **Multi-Version Testing**: Automated testing across Python 3.8-3.12
- **Documentation-Driven**: Comprehensive docs with code examples

## Common Development Tasks

### Adding New Features
```bash
# 1. Read architecture to understand component relationships
# 2. Set up development environment
# 3. Create feature branch following naming conventions
# 4. Implement with type safety and error handling
# 5. Add comprehensive tests (unit/integration/E2E)
# 6. Update documentation
# 7. Follow contribution workflow
```

### Debugging Issues
```bash
# 1. Use troubleshooting guide for common issues
# 2. Check system health with diagnostic commands
# 3. Use testing framework for isolated reproduction
# 4. Leverage type checking and code quality tools
# 5. Follow debugging patterns in documentation
```

### Understanding Existing Code
```bash
# 1. Start with architecture overview
# 2. Use API reference for specific components
# 3. Read type annotations and docstrings
# 4. Study test files for usage examples
# 5. Run code locally with verbose output
```

## Documentation Philosophy

This documentation follows several key principles:

### 1. **Practical Examples**
Every concept includes working code examples that you can run and modify.

### 2. **Troubleshooting-First**
Common issues are addressed proactively with step-by-step solutions.

### 3. **Type Safety Focus**
Documentation emphasizes the project's commitment to type safety and shows proper annotation patterns.

### 4. **Developer Experience**
Procedures are optimized for developer productivity with fast feedback cycles.

### 5. **Real-World Context**
Examples and explanations reflect actual development scenarios and workflows.

## Getting Help

### For Architecture Questions
- Start with [ARCHITECTURE.md](ARCHITECTURE.md) component diagrams
- Review data flow patterns and design decisions
- Check performance considerations and security model

### For Development Issues
- Use [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for environment problems
- Reference [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for specific errors
- Check [TESTING.md](TESTING.md) for test-related issues

### For Code Integration
- Follow [CONTRIBUTING.md](CONTRIBUTING.md) for workflow guidance
- Use [API_REFERENCE.md](API_REFERENCE.md) for implementation details
- Study existing code patterns and test examples

### For Advanced Usage
- Review CLI command patterns in API reference
- Understand configuration hierarchy and override patterns
- Study error handling and type safety implementations

## Contributing to Documentation

The documentation itself follows the same standards as the codebase:

### Standards
- **Clarity**: Write for developers who are new to the project
- **Completeness**: Include working examples and troubleshooting steps
- **Accuracy**: Keep documentation synchronized with code changes
- **Searchability**: Use clear headings and cross-references

### Process
1. Follow the contributing guide for documentation changes
2. Test all code examples before including them
3. Update cross-references when adding new sections
4. Include troubleshooting information for complex procedures

---

*This documentation represents the current state of n8n-deploy and is actively maintained to reflect the evolving codebase. Happy coding!*
