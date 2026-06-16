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
    python3 python3-pip python3-venv python3-dev \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# fastfetch (system info tool)
# ============================================================================

RUN curl -fsSL https://github.com/fastfetch-cli/fastfetch/releases/latest/download/fastfetch-linux-amd64.deb -o /tmp/fastfetch.deb \
    && curl -fsSL https://github.com/fastfetch-cli/fastfetch/releases/latest/download/fastfetch-linux-amd64.deb.sha256 -o /tmp/fastfetch.deb.sha256 \
    && echo "$(cat /tmp/fastfetch.deb.sha256)  /tmp/fastfetch.deb" | sha256sum -c - \
    && apt-get update && apt-get install -y /tmp/fastfetch.deb \
    && rm /tmp/fastfetch.deb /tmp/fastfetch.deb.sha256 \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# ttyd (terminal over WebSocket)
# ============================================================================

RUN curl -fsSL https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64 \
    -o /usr/local/bin/ttyd && \
    curl -fsSL https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64.sha256 \
    -o /tmp/ttyd.sha256 && \
    echo "$(awk '{print $1}' /tmp/ttyd.sha256)  /usr/local/bin/ttyd" | sha256sum -c - && \
    chmod +x /usr/local/bin/ttyd && \
    rm /tmp/ttyd.sha256

# ============================================================================
# Rta CLI
# ============================================================================

ARG RTA_SHA256=948e21281a18efa3331b957cd32aa3eff63be8014ffec6fe61216fb967397db9
RUN curl -fsSL https://rta-three.vercel.app/rta -o /tmp/rta && \
    echo "${RTA_SHA256}  /tmp/rta" | sha256sum -c - && \
    mv /tmp/rta /usr/local/bin/rta && chmod +x /usr/local/bin/rta

# ============================================================================
# cloudflared (tunneling)
# ============================================================================

RUN curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o /usr/local/bin/cloudflared && \
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.sha256 \
    -o /tmp/cloudflared.sha256 && \
    echo "$(awk '{print $1}' /tmp/cloudflared.sha256)  /usr/local/bin/cloudflared" | sha256sum -c - && \
    chmod +x /usr/local/bin/cloudflared && \
    rm /tmp/cloudflared.sha256

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
