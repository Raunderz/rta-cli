FROM ubuntu:22.04

# ============================================================================
# System Setup & Core Tools
# ============================================================================

RUN apt-get update && apt-get install -y \
    curl wget git vim nano htop tmux tree \
    build-essential pkg-config \
    openssh-client openssh-server \
    sudo \
    ca-certificates \
    fastfetch \
    python3 python3-pip python3-venv python3-dev \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# ttyd (terminal over WebSocket)
# ============================================================================

RUN curl -fsSL https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64 \
    -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

# ============================================================================
# Rta CLI
# ============================================================================

RUN curl -fsSL https://rta-three.vercel.app/rta -o /usr/local/bin/rta && chmod +x /usr/local/bin/rta

# ============================================================================
# cloudflared (tunneling)
# ============================================================================

RUN curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o /usr/local/bin/cloudflared && \
    chmod +x /usr/local/bin/cloudflared

# ============================================================================
# Security Hardening
# ============================================================================

RUN useradd -m -s /bin/bash -u 1000 dev && \
    mkdir -p /home/dev/.config && \
    chown -R dev:dev /home/dev

RUN chmod 1777 /tmp && chmod 1777 /var/tmp

# ============================================================================
# Workspace Setup
# ============================================================================

WORKDIR /home/dev
RUN mkdir -p /home/dev/projects /home/dev/.ssh && \
    chown -R dev:dev /home/dev

USER dev

# ============================================================================
# Entry Point
# ============================================================================

CMD ["/bin/bash"]
