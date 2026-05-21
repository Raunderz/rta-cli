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

echo "✅ Setup complete!"
echo "To start the service: ./mobile_backend_service"
echo "Make sure your main Rta backend is reachable at the URL in .env"
