FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Display / Virtual framebuffer
    xvfb \
    x11vnc \
    fluxbox \
    # Browser dependencies for Playwright
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    # Common utilities the agent might use
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    iputils-ping \
    jq \
    unzip \
    # Screenshot tools
    scrot \
    imagemagick \
    # Process management
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install fonts and additional Playwright dependencies manually
# (playwright install-deps doesn't work well on newer Debian)
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-unifont \
    libxshmfence1 \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright and browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Create workspace directory for agent operations
RUN mkdir -p /workspace && chmod 777 /workspace

# Create directory for screenshots
RUN mkdir -p /tmp/screenshots && chmod 777 /tmp/screenshots

# Expose ports
# 8080 - Tool API server
# 5900 - VNC server (for debugging/viewing)
EXPOSE 8080 5900

# Copy and set up entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
