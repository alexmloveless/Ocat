# Ocat Deployment Guide for 192.168.1.122

## Overview
This guide documents the transfer of the Ocat project (LLM Chat CLI) to the remote server at 192.168.1.122, including the vector store and local configuration.

## What Was Transferred
✅ **Completed Automatically:**
- Full source code repository (~/apps/ocat)
- Vector stores (Ada & default collections)
- Configuration files (.env, environment.yml)
- Docker configuration (Dockerfile, docker-compose.yml)
- All project documentation and development tools

## What Needs Manual Installation

### 1. Install Docker & Docker Compose
SSH into the server and run these commands:

```bash
ssh alex@192.168.1.122

# Install Docker and Docker Compose
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin

# Add user to docker group (avoid needing sudo for docker commands)
sudo usermod -aG docker $USER

# Apply group membership (logout/login or use newgrp)
newgrp docker

# Verify installation
docker --version
docker compose version
```

### 2. Build and Start Ocat

```bash
cd ~/apps/ocat

# Build the Docker image
docker compose --profile production build

# Start the service
docker compose --profile production up -d
```

### 3. Verify Installation

```bash
# Test version
docker compose run --rm ocat --version

# Test basic functionality (requires valid API keys in .env)
docker compose run --rm ocat

# Test vector store (headless mode)
docker compose run --rm --profile headless ocat-headless --query-vector-store "hello"
```

## Configuration Files

The `.env` file was transferred but contains placeholder API keys. Update it with real keys:

```bash
cd ~/apps/ocat
nano .env
```

Required API keys:
- `OPENAI_API_KEY=your_actual_key_here`
- `ANTHROPIC_API_KEY=your_actual_key_here` 
- `GOOGLE_API_KEY=your_actual_key_here`

## Alternative: Non-Docker Setup (Optional)

If you prefer to run without Docker, you can recreate the conda environment:

```bash
# Install conda/miniconda if not present
# Then:
conda env create -f ~/apps/ocat/environment.yml
conda activate Ocat
cd ~/apps/ocat
poetry run ocat --help
```

## Vector Store Locations

- **In Docker**: `/app/vector_stores` (mapped to named volume `ocat_vectors`)
- **On Host**: `~/apps/ocat/vector_stores/`
  - Ada collection: `~/apps/ocat/vector_stores/Ada/`
  - Default collection: `~/apps/ocat/vector_stores/default/`

## Usage

### Docker Mode (Recommended)

```bash
# Interactive chat
docker compose run --rm ocat

# Run specific commands
docker compose run --rm ocat --help

# Headless vector operations
docker compose run --rm --profile headless ocat-headless --query-vector-store "your query"
```

### Direct Mode (if conda env created)

```bash
conda activate Ocat
cd ~/apps/ocat
poetry run ocat
```

## Auto-Start on Boot (Optional)

To start Ocat automatically on system boot, create a systemd service:

```bash
sudo nano /etc/systemd/system/ocat.service
```

Content:
```ini
[Unit]
Description=Ocat LLM Chat CLI
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/alex/apps/ocat
ExecStart=/usr/bin/docker compose --profile production up -d
ExecStop=/usr/bin/docker compose --profile production down
User=alex

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ocat.service
sudo systemctl start ocat.service
```

## Troubleshooting

### Docker Permission Issues
```bash
# If getting permission errors
sudo usermod -aG docker $USER
newgrp docker
```

### Vector Store Issues
```bash
# Check vector store data
ls -la ~/apps/ocat/vector_stores/
docker compose run --rm ocat-headless --query-vector-store "test"
```

### API Key Issues
```bash
# Verify .env file
cat ~/apps/ocat/.env
# Make sure keys don't have quotes or extra spaces
```

## Transfer Summary

**Completed Steps:**
- ✅ Verified SSH connectivity to 192.168.1.122
- ✅ Created deployment directory ~/apps/ocat
- ✅ Transferred full project codebase (61MB)
- ✅ Transferred vector stores (Ada & default collections)
- ✅ Transferred configuration files
- ✅ Created this deployment documentation

**Manual Steps Required:**
- ⏳ Install Docker & Docker Compose (see Section 1)
- ⏳ Update .env with real API keys
- ⏳ Build and start Docker services (see Section 2)
- ⏳ Run verification tests (see Section 3)

## Files & Directories

```
~/apps/ocat/
├── Dockerfile                 # Docker build configuration
├── docker-compose.yml         # Service orchestration
├── .env                      # API keys (UPDATE REQUIRED)
├── environment.yml           # Conda environment spec
├── vector_stores/            # Vector database
│   ├── Ada/                  # Ada embedding collection
│   └── default/              # Default embedding collection
├── src/ocat/                 # Python source code
├── Project/                  # Documentation
└── ... (other project files)
```

The server hostname is "Bastard" running Ubuntu 24.04 LTS.

---

*This deployment was completed on August 3, 2025*
