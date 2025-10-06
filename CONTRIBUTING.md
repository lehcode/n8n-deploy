# Contributing to n8n-deploy

> "If builders built buildings the way programmers wrote programs, then the first woodpecker that came along would destroy civilization." — Gerald Weinberg

Thank you for considering contributing to n8n-deploy! This document provides guidelines and workflows for contributing to the project.

## Quick Start

1. **Fork and Clone**

   ```bash
   git clone https://github.com/YOUR_USERNAME/n8n-deploy.git
   cd n8n-deploy
   ```

2. **Set Up Development Environment**

   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Create Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Code Standards

- **Formatting**: Use `black` for code formatting
- **Type Safety**: All code must pass `mypy --strict`
- **Testing**: Write tests for new functionality
- **Documentation**: Update relevant documentation

### Running Tests

```bash
# All tests
python run_tests.py --all

# Specific test suites
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --e2e

# Type checking
mypy api/ --strict
```

### Commit Guidelines

Use clear, descriptive commit messages in imperative mood:

```bash
# Good
git commit -m "Add workflow backup compression feature"
git commit -m "Fix database initialization race condition"

# Avoid
git commit -m "Added stuff"
git commit -m "Fixed bug"
```

### Pull Request Process

1. **Ensure All Tests Pass**
   - Run full test suite
   - Verify type checking passes
   - Check code formatting

2. **Update Documentation**
   - Add/update docstrings
   - Update relevant markdown files
   - Add examples where helpful

3. **Submit PR**
   - Provide clear description
   - Reference related issues
   - Wait for review feedback

## Code of Conduct

All contributors must follow our [Code of Conduct](CODE_OF_CONDUCT.md). Be respectful, inclusive, and constructive.

## Testing Philosophy

- **Test Horizontally**: Run commands with all parameter combinations
- **Environment Variables**: Use `N8N_DEPLOY_TESTING=1` during tests
- **No Functional Changes**: Modify tests, not code, to make tests pass
- **Permission-Agnostic**: Design tests that work in any environment

## Areas for Contribution

### High-Priority

- Bug fixes and issue resolution
- Test coverage improvements
- Documentation enhancements
- Performance optimizations

### Feature Development

- New CLI commands
- Enhanced n8n server integration
- Additional backup formats
- Workflow validation tools

### Documentation

- User guides and tutorials
- Developer documentation
- Code examples
- Troubleshooting guides

## Getting Help

- **Documentation**: [Full docs](https://lehcode.github.io/n8n-deploy/)
- **Issues**: [GitHub Issues](https://github.com/lehcode/n8n-deploy/issues)
- **Discussions**: GitHub Discussions (for questions and ideas)

## Detailed Guidelines

For comprehensive development guidelines, architecture details, and testing strategies, see:

- [Developer Guide](docs/developers/index.md)
- [Architecture Overview](docs/developers/architecture.md)
- [Testing Framework](docs/developers/testing.md)
- [Detailed Contributing Guide](docs/developers/contributing.md)

## License

By contributing to n8n-deploy, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to n8n-deploy!** Every contribution, no matter how small, helps improve the project.
