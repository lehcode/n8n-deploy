# Security Policy

## Supported Versions

Security updates are provided for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | ✅ Yes             |
| 1.x.x   | ❌ No longer supported |

## Security Design

n8n-deploy is designed with security as a priority:

### Local-Only Data Storage

- **No cloud services**: All data stored locally on your machine
- **No network transmission**: API keys never leave your system
- **SQLite database**: Local file storage only
- **File-based backups**: No external dependencies

### API Key Management

- **Local storage only**: API keys stored in local SQLite database
- **No encryption complexity**: Simple, transparent storage
- **User-controlled**: You control where and how keys are stored
- **No key transmission**: Keys never sent over network

### Minimal Attack Surface

- **No web interface**: CLI-only tool
- **No server component**: No daemon or background services
- **Minimal dependencies**: Reduces potential vulnerabilities
- **Read-only n8n interaction**: Only reads workflow data from n8n

## Reporting Security Vulnerabilities

### For Security Issues

If you discover a security vulnerability, please report it responsibly:

**🔒 Private Disclosure (Preferred)**

- Email: [security contact - update with actual email]
- Subject: "n8n-deploy Security Issue"
- Include detailed reproduction steps
- Allow reasonable time for assessment and fix

**📋 Public Issues (For Non-Security Bugs)**

- Use GitHub Issues for general bugs
- **Do not** use public issues for security vulnerabilities

### What to Include

When reporting security issues, please provide:

1. **Description**: Clear description of the vulnerability
2. **Impact**: Potential impact and attack scenarios
3. **Reproduction**: Step-by-step reproduction instructions
4. **Environment**: OS, Python version, n8n-deploy version
5. **Logs**: Relevant error messages or logs (redact sensitive data)

### Response Process

1. **Acknowledgment**: We'll acknowledge receipt within 48 hours
2. **Assessment**: Initial assessment within 5 business days
3. **Fix Development**: Coordinated fix development
4. **Disclosure**: Coordinated public disclosure after fix
5. **Credit**: Public credit for responsible disclosure (if desired)

## Security Best Practices

### For Users

**Installation Security**

```bash
# Install from official sources only
pip install n8n-deploy

# Verify installation
n8n-deploy --version
```

**API Key Security**

```bash
# Use environment variables for automation
export N8N_API_KEY="your-key-here"

# Set restrictive file permissions on config directory
chmod 700 ~/.n8n-deploy/

# Regular key rotation
n8n-deploy apikey add new_key
n8n-deploy apikey delete old_key --confirm
```

**File System Security**

```bash
# Secure your data directory
chmod 700 /path/to/n8n-deploy-data/

# Regular backups to secure location
n8n-deploy backup-workflows --backup-dir /secure/backup/location/
```

### For Developers

**Code Contributions**

- Never commit API keys, passwords, or sensitive data
- Use environment variables for testing
- Follow secure coding practices
- Run security tools: `bandit -r api/`

**Dependency Management**

- Keep dependencies updated
- Run security audits: `safety check`
- Review new dependency security advisories

## Security Monitoring

### Automated Security Checks

Our CI/CD pipeline includes:

- **Dependency scanning**: Automatic vulnerability detection
- **Static analysis**: Code security analysis with Bandit
- **Dependency audit**: Safety checks for known vulnerabilities

### Regular Updates

- Dependencies reviewed and updated regularly
- Security advisories monitored
- Automated security scanning in CI/CD

## Threat Model

### What We Protect Against

- **Local data compromise**: Secure local storage practices
- **Dependency vulnerabilities**: Regular updates and scanning
- **Code injection**: Input validation and safe practices
- **Information disclosure**: No sensitive data in logs or outputs

### What Users Must Protect

- **Physical access**: Secure your local machine
- **File permissions**: Proper filesystem permissions
- **API key security**: Secure handling of n8n API keys
- **Backup security**: Secure storage of backup files

## Security Limitations

### Known Limitations

- **Local storage**: Data security depends on local machine security
- **API keys**: Stored in local database (user responsibility to secure)
- **No encryption**: Trade-off for simplicity and transparency
- **File permissions**: Relies on filesystem security

### Not Covered

- **n8n server security**: Security of your n8n instance
- **Network security**: Security of connections to n8n
- **Host security**: Security of the machine running n8n-deploy

## Security Updates

### Update Process

1. Security fixes released as patch versions
2. Updates announced via GitHub releases
3. Critical fixes may warrant immediate releases
4. Users notified through standard update channels

### Staying Updated

```bash
# Check for updates
pip list --outdated | grep n8n-deploy

# Update to latest version
pip install --upgrade n8n-deploy

# Verify update
n8n-deploy --version
```

## Contact Information

- **Security Issues**: [Update with security contact email]
- **General Questions**: Use GitHub Issues
- **Documentation**: See README.md and doc/ directory

---

**Note**: This security policy applies to n8n-deploy only. For n8n server security, consult the [n8n security documentation](https://docs.n8n.io/).

Last updated: December 2024
