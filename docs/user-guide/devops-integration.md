---
layout: default
title: DevOps Integration
parent: User Guide
nav_order: 4
description: "Integrating n8n-deploy with DevOps workflows and CI/CD pipelines"
---

# DevOps Integration

> "Automation applied to an efficient operation will magnify the efficiency. Automation applied to an inefficient operation will magnify the inefficiency." — Bill Gates (via Murphy's Laws)

## 🎯 Overview

This guide demonstrates integrating n8n-deploy into DevOps workflows, CI/CD pipelines, and infrastructure automation.

---

## 🔧 Git

Ops Workflow Integration

### Version Control Strategy

Manage workflow JSON files with git:

```bash
# Initialize workflow repository
mkdir n8n-workflows && cd n8n-workflows
git init
export N8N_DEPLOY_FLOWS_DIR=$(pwd)

# Initialize n8n-deploy database
n8n-deploy db init

# Pull workflows from server
n8n-deploy --server-url http://n8n.example.com wf pull-all

# Commit to version control
git add *.json
git commit -m "feat: initial workflow import from n8n server"
git push origin main
```

### Branching Strategy

```bash
# Feature development
git checkout -b feature/new-workflow
# ... edit workflows ...
git commit -m "feat: add customer onboarding workflow"
git push origin feature/new-workflow

# Create pull request
gh pr create --title "New Customer Onboarding Workflow" --body "Adds automated customer onboarding"

# After merge, deploy to staging
git checkout main && git pull
n8n-deploy --server-url http://n8n-staging:5678 wf push "Customer Onboarding"

# Deploy to production
n8n-deploy --server-url https://n8n.company.com wf push "Customer Onboarding"
```

---

## 🚀 CI/CD Pipeline Integration

### GitHub Actions

```yaml
name: n8n Workflow Deployment

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install n8n-deploy
        run: pip install n8n-deploy

      - name: Validate workflow JSON
        run: |
          for workflow in *.json; do
            jq empty "$workflow" || exit 1
          done

      - name: Initialize database
        run: n8n-deploy db init --no-emoji

  deploy-staging:
    runs-on: ubuntu-latest
    needs: validate
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install n8n-deploy
        run: pip install n8n-deploy

      - name: Deploy to Staging
        env:
          N8N_STAGING_KEY: ${{ secrets.N8N_STAGING_KEY }}
        run: |
          n8n-deploy db init --no-emoji
          echo "$N8N_STAGING_KEY" | n8n-deploy apikey add - --name staging_ci --no-emoji
          n8n-deploy --server-url ${{ vars.N8N_STAGING_URL }} wf push-all --no-emoji

  deploy-production:
    runs-on: ubuntu-latest
    needs: validate
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install n8n-deploy
        run: pip install n8n-deploy

      - name: Deploy to Production
        env:
          N8N_PROD_KEY: ${{ secrets.N8N_PROD_KEY }}
        run: |
          n8n-deploy db init --no-emoji
          echo "$N8N_PROD_KEY" | n8n-deploy apikey add - --name prod_ci --no-emoji
          n8n-deploy --server-url ${{ vars.N8N_PROD_URL }} wf push-all --no-emoji

      - name: Notify deployment
        run: |
          echo "✅ Deployed to production: $(date)"
```

### GitLab CI/CD

```yaml
stages:
  - validate
  - deploy-staging
  - deploy-production

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

.n8n_setup:
  image: python:3.11-slim
  before_script:
    - pip install n8n-deploy
    - n8n-deploy db init --no-emoji

validate:
  extends: .n8n_setup
  stage: validate
  script:
    - |
      for workflow in *.json; do
        echo "Validating $workflow"
        jq empty "$workflow" || exit 1
      done
    - n8n-deploy wf list --no-emoji

deploy:staging:
  extends: .n8n_setup
  stage: deploy-staging
  script:
    - echo "$N8N_STAGING_KEY" | n8n-deploy apikey add - --name staging_ci --no-emoji
    - n8n-deploy --server-url $N8N_STAGING_URL wf push-all --no-emoji
  environment:
    name: staging
  only:
    - develop

deploy:production:
  extends: .n8n_setup
  stage: deploy-production
  script:
    - echo "$N8N_PROD_KEY" | n8n-deploy apikey add - --name prod_ci --no-emoji
    - n8n-deploy --server-url $N8N_PROD_URL wf push-all --no-emoji
  environment:
    name: production
  only:
    - master
  when: manual
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    environment {
        VENV = "${WORKSPACE}/venv"
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv $VENV
                    . $VENV/bin/activate
                    pip install n8n-deploy
                '''
            }
        }

        stage('Validate Workflows') {
            steps {
                sh '''
                    . $VENV/bin/activate
                    n8n-deploy db init --no-emoji
                    n8n-deploy wf list --no-emoji
                '''
            }
        }

        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                withCredentials([string(credentialsId: 'n8n-staging-key', variable: 'N8N_KEY')]) {
                    sh '''
                        . $VENV/bin/activate
                        echo "$N8N_KEY" | n8n-deploy apikey add - --name staging_ci --no-emoji
                        n8n-deploy --server-url ${N8N_STAGING_URL} wf push-all --no-emoji
                    '''
                }
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
                withCredentials([string(credentialsId: 'n8n-prod-key', variable: 'N8N_KEY')]) {
                    sh '''
                        . $VENV/bin/activate
                        echo "$N8N_KEY" | n8n-deploy apikey add - --name prod_ci --no-emoji
                        n8n-deploy --server-url ${N8N_PROD_URL} wf push-all --no-emoji
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'rm -rf $VENV'
        }
    }
}
```

---

## 🐳 Docker Integration

### Dockerfile for n8n-deploy

```dockerfile
FROM python:3.11-slim

# Install n8n-deploy
RUN pip install --no-cache-dir n8n-deploy

# Set working directory
WORKDIR /workflows

# Copy workflow files
COPY *.json ./

# Set environment variables
ENV N8N_DEPLOY_FLOWS_DIR=/workflows
ENV N8N_DEPLOY_DATA_DIR=/data

# Create data directory
RUN mkdir -p /data

# Initialize database
RUN n8n-deploy db init --no-emoji

# Default command
CMD ["n8n-deploy", "wf", "list", "--no-emoji"]
```

### Docker Compose Setup

```yaml
version: '3.8'

services:
  n8n-deploy:
    build: .
    volumes:
      - ./workflows:/workflows:ro
      - n8n-deploy-data:/data
    environment:
      - N8N_SERVER_URL=${N8N_SERVER_URL}
      - N8N_DEPLOY_DATA_DIR=/data
      - N8N_DEPLOY_FLOWS_DIR=/workflows
    command: >
      sh -c "
        echo '${N8N_API_KEY}' | n8n-deploy apikey add - --name deploy_key --no-emoji &&
        n8n-deploy wf push-all --no-emoji
      "

volumes:
  n8n-deploy-data:
```

---

## ☸️ Kubernetes Integration

### ConfigMap for Workflows

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: n8n-workflows
  namespace: n8n
data:
  workflow1.json: |
    {
      "name": "Production Workflow",
      "nodes": []
    }
```

### Deployment with Init Container

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: n8n-deployment
  namespace: n8n
spec:
  replicas: 1
  selector:
    matchLabels:
      app: n8n
  template:
    metadata:
      labels:
        app: n8n
    spec:
      initContainers:
        - name: workflow-sync
          image: python:3.11-slim
          command:
            - /bin/sh
            - -c
            - |
              pip install n8n-deploy
              n8n-deploy db init --no-emoji
              echo "$N8N_API_KEY" | n8n-deploy apikey add - --name k8s_sync --no-emoji
              n8n-deploy --server-url $N8N_SERVER_URL wf push-all --no-emoji
          env:
            - name: N8N_SERVER_URL
              value: "http://n8n-service:5678"
            - name: N8N_API_KEY
              valueFrom:
                secretKeyRef:
                  name: n8n-secrets
                  key: api-key
            - name: N8N_DEPLOY_FLOWS_DIR
              value: "/workflows"
          volumeMounts:
            - name: workflows
              mountPath: /workflows
      containers:
        - name: n8n
          image: n8nio/n8n:latest
          # ... n8n container config ...
      volumes:
        - name: workflows
          configMap:
            name: n8n-workflows
```

### CronJob for Scheduled Sync

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: n8n-workflow-sync
  namespace: n8n
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: sync
              image: python:3.11-slim
              command:
                - /bin/sh
                - -c
                - |
                  pip install n8n-deploy
                  n8n-deploy db init --no-emoji
                  echo "$N8N_API_KEY" | n8n-deploy apikey add - --name cron_sync --no-emoji
                  n8n-deploy --server-url $N8N_SERVER_URL wf pull-all --no-emoji
              env:
                - name: N8N_SERVER_URL
                  value: "http://n8n-service:5678"
                - name: N8N_API_KEY
                  valueFrom:
                    secretKeyRef:
                      name: n8n-secrets
                      key: api-key
              volumeMounts:
                - name: workflows
                  mountPath: /workflows
          restartPolicy: OnFailure
          volumes:
            - name: workflows
              persistentVolumeClaim:
                claimName: n8n-workflows-pvc
```

---

## 🔐 Secrets Management

### HashiCorp Vault Integration

```bash
#!/bin/bash
# vault-integration.sh

# Retrieve API key from Vault
N8N_API_KEY=$(vault kv get -field=api_key secret/n8n/production)

# Use with n8n-deploy
echo "$N8N_API_KEY" | n8n-deploy apikey add - --name vault_key --no-emoji
n8n-deploy --server-url https://n8n.company.com wf push-all --no-emoji

# Clean up
n8n-deploy apikey delete vault_key --confirm --no-emoji
```

### AWS Secrets Manager

```bash
#!/bin/bash
# aws-secrets.sh

# Retrieve from AWS Secrets Manager
N8N_API_KEY=$(aws secretsmanager get-secret-value \
    --secret-id n8n/prod/api-key \
    --query SecretString \
    --output text)

# Deploy workflows
n8n-deploy db init --no-emoji
echo "$N8N_API_KEY" | n8n-deploy apikey add - --name aws_key --no-emoji
n8n-deploy --server-url $N8N_PROD_URL wf push-all --no-emoji
```

---

## 📊 Monitoring and Alerting

### Prometheus Metrics Export

```python
#!/usr/bin/env python3
# n8n_deploy_exporter.py

import json
import subprocess
from prometheus_client import start_http_server, Gauge
import time

# Define metrics
workflow_count = Gauge('n8n_workflows_total', 'Total number of workflows')
db_size_kb = Gauge('n8n_db_size_kb', 'Database size in KB')

def collect_metrics():
    # Get workflow count
    result = subprocess.run(
        ['n8n-deploy', 'wf', 'list', '--json', '--no-emoji'],
        capture_output=True,
        text=True
    )
    workflows = json.loads(result.stdout)
    workflow_count.set(len(workflows))

    # Get database status
    result = subprocess.run(
        ['n8n-deploy', 'db', 'status', '--json', '--no-emoji'],
        capture_output=True,
        text=True
    )
    db_status = json.loads(result.stdout)
    db_size_kb.set(db_status.get('size_kb', 0))

if __name__ == '__main__':
    start_http_server(9090)
    while True:
        collect_metrics()
        time.sleep(60)
```

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

set -e

# Check database integrity
if ! n8n-deploy db status --no-emoji > /dev/null 2>&1; then
    echo "❌ Database health check failed"
    exit 1
fi

# Check workflow count
WORKFLOW_COUNT=$(n8n-deploy wf list --json --no-emoji | jq 'length')
if [ "$WORKFLOW_COUNT" -lt 1 ]; then
    echo "⚠️  Warning: No workflows found"
fi

# Check API key validity
if ! n8n-deploy apikey test prod_key --no-emoji > /dev/null 2>&1; then
    echo "❌ API key validation failed"
    exit 1
fi

echo "✅ All health checks passed"
exit 0
```

---

## 🔄 Automated Backup Strategies

### Daily Backup Script

```bash
#!/bin/bash
# daily-backup.sh

BACKUP_DIR="/backups/n8n-deploy"
DATE=$(date +%Y%m%d)
RETENTION_DAYS=30

# Create backup
mkdir -p "$BACKUP_DIR"
n8n-deploy db backup "$BACKUP_DIR/n8n-deploy-$DATE.db" --no-emoji

# Verify backup
if [ ! -f "$BACKUP_DIR/n8n-deploy-$DATE.db" ]; then
    echo "❌ Backup failed"
    exit 1
fi

# Compact database (first day of month)
if [ "$(date +%d)" = "01" ]; then
    n8n-deploy db compact --no-emoji
fi

# Cleanup old backups
find "$BACKUP_DIR" -name "n8n-deploy-*.db" -mtime +$RETENTION_DAYS -delete

# Upload to S3 (optional)
# aws s3 cp "$BACKUP_DIR/n8n-deploy-$DATE.db" s3://my-backups/n8n-deploy/

echo "✅ Backup completed: n8n-deploy-$DATE.db"
```

### Systemd Timer

```ini
# /etc/systemd/system/n8n-deploy-backup.service
[Unit]
Description=n8n-deploy database backup
After=network.target

[Service]
Type=oneshot
User=n8n-deploy
ExecStart=/usr/local/bin/daily-backup.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/n8n-deploy-backup.timer
[Unit]
Description=Daily n8n-deploy backup timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl enable n8n-deploy-backup.timer
sudo systemctl start n8n-deploy-backup.timer
sudo systemctl status n8n-deploy-backup.timer
```

---

## 📖 Related Documentation

- [Database Management](../core-features/database/) - Database operations
- [API Key Management](../core-features/apikeys/) - Secure key handling
- [Server Management](../core-features/servers/) - Multi-server configuration
- [Configuration](../configuration/) - Environment setup

---

**Last Updated**: October 2025
