---
layout: default
title: Developer Guide
nav_order: 9
has_children: true
permalink: /developers
description: "Comprehensive guide for developers working with n8n-deploy"
---

# n8n-deploy Developer Documentation

{: .warning }
> **Warning**: These docs are for developers who want to understand, modify, or contribute to the n8n-deploy project.

## Introduction

n8n-deploy is a powerful Python CLI tool for managing n8n workflows with a SQLite metadata store. This developer guide provides comprehensive information about the project's architecture, development practices, and contribution guidelines.

{: .note }
> "Programming is the art of telling another human what one wants the computer to do." — Donald Knuth

## Quick Links

### Documentation
- [System Architecture](architecture/)
- [Contributing Guidelines](contributing/)
- [Testing Framework](testing/)
- [Testing Guide (Comprehensive)](testing-framework/)
- [CI/CD Troubleshooting](ci-cd-troubleshooting/)
- [API Reference](api-reference/)
- [Database Schema](../core-features/database/)
- [Local GitHub Pages Testing](local-github-pages-testing/)

### Project Resources
- [CONTRIBUTING.md](https://github.com/lehcode/n8n-deploy/blob/master/CONTRIBUTING.md) - Full contribution guide
- [CODE_OF_CONDUCT.md](https://github.com/lehcode/n8n-deploy/blob/master/CODE_OF_CONDUCT.md) - Community guidelines
- [CHANGELOG.md](https://github.com/lehcode/n8n-deploy/blob/master/CHANGELOG.md) - Version history
- [TODO.md](https://github.com/lehcode/n8n-deploy/blob/master/TODO.md) - Planned features and roadmap

## Key Project Goals

- Provide flexible, database-first workflow management
- Support remote n8n servers without web UI access
- Maintain clean, modular, and type-safe code
- Ensure comprehensive test coverage

## Compatibility

- **Python**: 3.8+
- **n8n**: Latest versions (check documentation)
- **Platforms**: Linux, macOS, Windows Subsystem for Linux (WSL)

{: .tip }
> Before diving in, make sure you have the latest version of the project and its dependencies installed.