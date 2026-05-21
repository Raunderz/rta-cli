#!/bin/bash

# Rta Mobile Backend Setup Script for Debian/Ubuntu

set -e

echo "🚀 Starting Rta Mobile Backend Setup..."

# 1. Install Dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y curl wget git docker.io golang-go

# 2. Setup Docker
echo "🐳 Setting up Docker..."
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
echo "⚠️  Note: You might need to log out and back in for docker group changes to take effect."

# 3. Build Sandbox Image
echo "🏗️  Building Docker sandbox image (tempdev:latest)..."
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
USER_NAME=$(whoami)
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
echo "✅ Setup complete!"
echo "To start service: sudo systemctl enable --now rta-mobile-backend"
echo "To view logs: journalctl -u rta-mobile-backend -f"
