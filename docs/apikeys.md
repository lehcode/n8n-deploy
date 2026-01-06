---
layout: default
title: API Key Management
nav_order: 5
---

## API Key Management

n8n-deploy provides a simple and secure way to manage API keys for n8n server interactions.

## 🔑 API Key Operations

### Add API Key
```bash
# Add API key from stdin
echo "your_n8n_api_key" | n8n-deploy apikey add - --name my_key

# Add API key and link to server
echo "your_n8n_api_key" | n8n-deploy apikey add - --name my_key --server my_server
```

### List API Keys
```bash
# Show all stored API keys
n8n-deploy apikey list
```

### Get Specific API Key
```bash
# Retrieve details for a specific key
n8n-deploy apikey get my_server
```

### Delete API Key
```bash
# Remove an API key (with confirmation)
n8n-deploy apikey delete my_server --confirm
```

### Test API Key
```bash
# Validate API key with n8n server
n8n-deploy apikey test my_server --server-url http://n8n.example.com:5678
```

## 🔒 API Key Security

- Stored in plain text SQLite database
- No complex encryption
- Designed specifically for n8n API keys
- Created/last used timestamps tracked

## 💡 Best Practices

- Use unique, descriptive names for API keys
- Rotate keys periodically
- Use environment variables or .env files for sensitive keys
- Avoid sharing API keys publicly

## 📋 API Key Database Schema

```
Table: api_keys
Columns:
- name: Key identifier
- api_key: Plain text API key
- created_at: Creation timestamp
- last_used_at: Last usage timestamp
```

## 🆘 Troubleshooting

- Verify key matches n8n server requirements
- Check server URL
- Ensure key has necessary permissions
- Use `apikey test` to validate key

## 📖 Related Guides

- [Configuration](configuration.md)
- [Workflow Management](workflows.md)
- [Troubleshooting](troubleshooting.md)

## 💻 API Key Management Workflow

```bash
# Create servers first
n8n-deploy server create production http://prod.n8n.com
n8n-deploy server create staging http://staging.n8n.com

# Add API keys and link to servers
echo "production_key" | n8n-deploy apikey add - --name prod_key --server production
echo "staging_key" | n8n-deploy apikey add - --name staging_key --server staging

# List and verify keys
n8n-deploy apikey list

# Test keys with specific servers
n8n-deploy apikey test prod_key --server-url http://prod.n8n.com
n8n-deploy apikey test staging_key --server-url http://staging.n8n.com

# Remove unused key
n8n-deploy apikey delete old_key --confirm
```