#!/bin/bash

# Rta Mobile Backend Setup Script for AWS (Amazon Linux 2023)

set -e

echo "🚀 Starting Rta Mobile Backend Setup for AWS..."

# 1. Install Dependencies
echo "📦 Installing system dependencies..."
sudo dnf update -y
sudo dnf install -y curl wget git docker golang

# 2. Setup Docker
echo "🐳 Setting up Docker..."
sudo systemctl enable --now docker
ACTUAL_USER=${SUDO_USER:-$(whoami)}
sudo usermod -aG docker $ACTUAL_USER
echo "⚠️  Note: You might need to log out and back in for docker group changes to take effect."

# 3. Build Sandbox Image
echo "🏗️  Building Docker sandbox image (tempdev:latest)..."
# Ensure we are in the script's directory
cd "$(dirname "$0")"
docker build -t tempdev:latest .

# 4. Environment Config
if [ ! -f .env ]; then
    echo "📄 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env to set your BACKEND_URL."
fi

# 5. Build Go Backend
echo "🔨 Building Go backend binary..."
go mod download
go build -o mobile_backend_service *.go

# 6. Create Systemd Service
echo "⚙️  Creating systemd service..."
USER_NAME=${SUDO_USER:-$(whoami)}
WORKING_DIR=$(pwd)

sudo bash -c "cat > /etc/systemd/system/rta-mobile-backend.service <<EOF
[Unit]
Description=Rta Mobile Backend Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$WORKING_DIR
ExecStart=$WORKING_DIR/mobile_backend_service
Restart=always
EnvironmentFile=$WORKING_DIR/.env

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable --now rta-mobile-backend

echo "✅ Setup complete!"
echo "🚀 Service is now running."
echo "To view logs: journalctl -u rta-mobile-backend -f"
