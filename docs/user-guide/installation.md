# Installation & Setup

Get n8n-deploy running on your system in minutes.

## Installation Methods

### Option 1: PyPI (Recommended)

Install from Python Package Index – the easiest method for most users:

```bash
pip install n8n-deploy
```

Verify installation:

```bash
n8n-deploy --version
```

### Option 2: From GitHub

Get the latest development version:

```bash
pip install git+https://github.com/lehcode/n8n-deploy.git
```

### Option 3: No Installation Required

Clone and run directly – perfect for development or trying it out:

```bash
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy
./n8n-deploy --help  # Works immediately
```

The wrapper script automatically creates a virtual environment on first run.

### Option 4: Development Setup

For contributors or advanced users:

```bash
git clone https://github.com/lehcode/n8n-deploy.git
cd n8n-deploy

# Using uv (faster)
uv venv --python /usr/bin/python3 .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## System Requirements

### Python Version

- **Python 3.8 or higher** (tested on 3.8, 3.9, 3.10, 3.11, 3.12)
- Check your version: `python --version`

### Operating Systems

- ✅ Linux (Ubuntu, Debian, Fedora, Arch, etc.)
- ✅ macOS (10.14+)
- ✅ Windows (via WSL2)

### Dependencies

Core dependencies are automatically installed:

- **click** - CLI framework
- **rich** - Terminal formatting
- **pydantic** - Data validation
- **requests** - HTTP client for n8n API
- **python-dotenv** - Environment file support (dev only)

## Initial Configuration

### Step 1: Set Up Directories

Choose where to store your data and wf files:

```bash
# Application data (database, backups)
export N8N_DEPLOY_DATA=~/n8n-data

# Workflow JSON files
export N8N_DEPLOY_FLOW_DIR=~/workflows
```

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`) for persistence.

### Step 2: Initialize Database

Create the SQLite database:

```bash
n8n-deploy db init
```

If a database already exists:

```bash
n8n-deploy db init --import  # Accept existing database
```

### Step 3: Verify Setup

Check your installation:

```bash
n8n-deploy db status
n8n-deploy env  # Show current configuration
```

## Optional: n8n Server Setup

If you plan to sync with a remote n8n server:

```bash
# Set server URL
export N8N_SERVER_URL=https://n8n.example.com

# Add API key
echo "your-api-key-here" | n8n-deploy apikey add production

# Test connection
n8n-deploy wf server list
```

## Development Environment (.env file)

For development, create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
ENVIRONMENT=development
N8N_DEPLOY_DATA=/home/user/n8n-data
N8N_DEPLOY_FLOW_DIR=/home/user/workflows
N8N_SERVER_URL=http://localhost:5678
```

**Note**: `.env` files only work when `ENVIRONMENT=development`. Production environments should use system environment variables.

## Verification Checklist

✅ Python 3.8+ installed
✅ n8n-deploy command available
✅ Database initialized successfully
✅ Directories configured (via env vars or CLI flags)
✅ API key added (if using remote server)

## Troubleshooting Installation

### Command Not Found

If `n8n-deploy` isn't found after pip install:

```bash
# Check if it's installed
pip show n8n-deploy

# Try with python -m
python -m n8n_deploy --help

# Or use full path
~/.local/bin/n8n-deploy --help
```

Add `~/.local/bin` to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Permission Errors

On some systems, use `--user` flag:

```bash
pip install --user n8n-deploy
```

### Version Conflicts

Create a fresh virtual environment:

```bash
python -m venv n8n-env
source n8n-env/bin/activate
pip install n8n-deploy
```

## Next Steps

- **[Configuration Guide](configuration.md)** - Detailed configuration options
- **[Getting Started](getting-started.md)** - Your first workflows
- **[Troubleshooting](troubleshooting.md)** - Common issues

---

Installation complete! Move on to **[Getting Started](getting-started.md)** to manage your first wf.
