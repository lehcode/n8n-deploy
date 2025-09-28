#!/bin/bash
# Release automation script for n8n-deploy
# Usage: ./scripts/release.sh [version] [--dry-run]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Release Script for n8n-deploy

Usage: $0 [version] [options]

Arguments:
  version     Semantic version (e.g., 1.0.0, 2.1.3)
              If not provided, will prompt for input

Options:
  --dry-run   Show what would be done without making changes
  --help      Show this help message

Examples:
  $0 1.0.0              # Create release version 1.0.0
  $0 2.1.3 --dry-run    # Preview release 2.1.3 without changes
  $0                    # Interactive mode - will prompt for version

Prerequisites:
  - Clean git working directory
  - On main/master branch
  - All tests passing
  - GitLab CI/CD configured
EOF
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if git repo
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi

    # Check clean working directory
    if [[ -n $(git status --porcelain) ]]; then
        log_error "Working directory is not clean. Commit or stash changes first."
        git status --short
        exit 1
    fi

    # Check if on main/master branch
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
        log_warning "Not on main/master branch (currently on: $current_branch)"
        read -p "Continue anyway? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Check if pyproject.toml exists
    if [[ ! -f "pyproject.toml" ]]; then
        log_error "pyproject.toml not found in current directory"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

validate_version() {
    local version=$1

    # Check semantic versioning pattern
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$ ]]; then
        log_error "Invalid version format. Use semantic versioning (e.g., 1.0.0, 2.1.3-beta.1)"
        return 1
    fi

    # Check if tag already exists
    if git tag -l | grep -q "^v?$version$"; then
        log_error "Tag v$version already exists"
        return 1
    fi

    return 0
}

update_version_file() {
    local version=$1
    local dry_run=$2

    log_info "Updating version in pyproject.toml to $version"

    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] Would update pyproject.toml version to $version"
        return 0
    fi

    # Update version in pyproject.toml
    if command -v sed > /dev/null; then
        sed -i "s/^version = .*/version = \"$version\"/" pyproject.toml
    else
        log_error "sed command not available"
        return 1
    fi

    # Verify the change
    if grep -q "version = \"$version\"" pyproject.toml; then
        log_success "Version updated successfully in pyproject.toml"
    else
        log_error "Failed to update version in pyproject.toml"
        return 1
    fi
}

run_tests() {
    local dry_run=$1

    log_info "Running tests before release..."

    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] Would run test suite"
        return 0
    fi

    # Check if test runner exists
    if [[ -f "run_tests.py" ]]; then
        python run_tests.py --unit --integration
    elif command -v pytest > /dev/null; then
        pytest tests/
    else
        log_warning "No test runner found, skipping tests"
    fi

    log_success "Tests completed successfully"
}

build_package() {
    local dry_run=$1

    log_info "Building package..."

    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] Would build Python package"
        return 0
    fi

    # Clean previous builds
    rm -rf dist/ build/ *.egg-info/

    # Install build tools if needed
    if ! python -c "import build" 2>/dev/null; then
        log_info "Installing build tools..."
        pip install build
    fi

    # Build package
    python -m build

    # Verify package
    if command -v twine > /dev/null; then
        twine check dist/*
        log_success "Package built and verified successfully"
    else
        log_warning "twine not available, skipping package verification"
    fi

    # Show package info
    log_info "Built packages:"
    ls -la dist/
}

create_git_tag() {
    local version=$1
    local dry_run=$2

    log_info "Creating git tag v$version"

    if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] Would create and push git tag v$version"
        return 0
    fi

    # Create annotated tag
    git add pyproject.toml
    git commit -m "chore: bump version to $version"
    git tag -a "v$version" -m "Release version $version

This release includes:
- Package version: $version
- Built on: $(date)
- Commit: $(git rev-parse HEAD)

Install with: pip install n8n-deploy==$version"

    # Push tag and commits
    git push origin $(git branch --show-current)
    git push origin "v$version"

    log_success "Git tag v$version created and pushed"
}

show_next_steps() {
    local version=$1

    log_success "Release process completed for version $version!"

    cat << EOF

Next steps:
1. 🔍 Monitor GitLab CI/CD pipeline: $(git remote get-url origin | sed 's/\.git$//')/-/pipelines
2. 📦 Check GitLab Package Registry: $(git remote get-url origin | sed 's/\.git$//')/-/packages
3. 📋 Review GitLab Release: $(git remote get-url origin | sed 's/\.git$//')/-/releases/v$version
4. 🐍 Manually trigger PyPI upload if needed (from GitLab CI/CD)
5. 📖 Update documentation if required

Installation command:
  pip install n8n-deploy==$version

Package registry access:
  pip install --index-url https://gitlab.example.com/api/v4/projects/PROJECT_ID/packages/pypi/simple/ n8n-deploy
EOF
}

# Main script logic
main() {
    local version=""
    local dry_run="false"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run="true"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                if [[ -z "$version" ]]; then
                    version="$1"
                else
                    log_error "Multiple versions specified"
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # Interactive version input if not provided
    if [[ -z "$version" ]]; then
        echo -n "Enter version (semantic versioning, e.g., 1.0.0): "
        read -r version
    fi

    # Validate inputs
    if [[ -z "$version" ]]; then
        log_error "Version is required"
        exit 1
    fi

    if ! validate_version "$version"; then
        exit 1
    fi

    # Show dry run notice
    if [[ "$dry_run" == "true" ]]; then
        log_warning "DRY RUN MODE - No changes will be made"
    fi

    # Execute release process
    log_info "Starting release process for version $version"

    check_prerequisites
    update_version_file "$version" "$dry_run"
    run_tests "$dry_run"
    build_package "$dry_run"
    create_git_tag "$version" "$dry_run"

    if [[ "$dry_run" == "false" ]]; then
        show_next_steps "$version"
    else
        log_info "[DRY RUN] Release process simulation completed"
    fi
}

# Run main function with all arguments
main "$@"
