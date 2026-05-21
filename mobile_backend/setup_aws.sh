#!/bin/bash

# Rta Mobile Backend Setup Script for AWS (Amazon Linux 2023)

set +e

echo "🚀 Starting Rta Mobile Backend Setup for AWS..."

# 1. Install Dependencies
echo "📦 Installing system dependencies..."
sudo dnf update -y --skip-broken
sudo dnf install -y --skip-broken curl wget git docker golang

# Ensure Go 1.26.1 (repo version may be too old)
if /usr/local/go/bin/go version 2>/dev/null | grep -q "go1.26"; then
    export PATH=/usr/local/go/bin:$PATH
else
    echo "📦 Installing Go 1.26.1..."
    wget -q https://go.dev/dl/go1.26.1.linux-amd64.tar.gz -O /tmp/go1.26.1.linux-amd64.tar.gz
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf /tmp/go1.26.1.linux-amd64.tar.gz
    rm /tmp/go1.26.1.linux-amd64.tar.gz
    echo 'export PATH=/usr/local/go/bin:$PATH' | sudo tee /etc/profile.d/go.sh > /dev/null
    export PATH=/usr/local/go/bin:$PATH
fi

# 2. Setup Docker
echo "🐳 Setting up Docker..."
if ! systemctl is-active --quiet docker 2>/dev/null; then
    sudo systemctl enable --now docker
else
    echo "✅ Docker already running."
fi
ACTUAL_USER=${SUDO_USER:-$(whoami)}
sudo usermod -aG docker $ACTUAL_USER 2>/dev/null
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

if [ ! -f /etc/systemd/system/rta-mobile-backend.service ]; then
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
else
    echo "✅ Service file already exists."
fi

if ! systemctl is-enabled --quiet rta-mobile-backend 2>/dev/null; then
    sudo systemctl enable rta-mobile-backend
else
    echo "✅ Service already enabled."
fi

if ! systemctl is-active --quiet rta-mobile-backend 2>/dev/null; then
    sudo systemctl start rta-mobile-backend
    echo "🚀 Service started."
else
    echo "✅ Service already running."
fi

echo "✅ Setup complete!"
echo "To view logs: journalctl -u rta-mobile-backend -f"
