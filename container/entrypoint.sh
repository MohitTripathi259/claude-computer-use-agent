#!/bin/bash
set -e

echo "=== Starting Computer-Use Container ==="

# Start Xvfb (virtual display)
echo "Starting Xvfb virtual display..."
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!
sleep 2

# Verify Xvfb is running
if ! kill -0 $XVFB_PID 2>/dev/null; then
    echo "ERROR: Xvfb failed to start"
    exit 1
fi
echo "✓ Xvfb running on display :99"

# Start fluxbox window manager (lightweight)
echo "Starting Fluxbox window manager..."
fluxbox &
sleep 1
echo "✓ Fluxbox started"

# Optional: Start VNC server for debugging (allows viewing what's happening)
if [ "${ENABLE_VNC:-true}" = "true" ]; then
    echo "Starting VNC server on port 5900..."
    x11vnc -display :99 -forever -nopw -shared -rfbport 5900 &
    sleep 1
    echo "✓ VNC server running (connect with VNC viewer to port 5900)"
fi

echo "=== Environment Ready ==="
echo "Display: $DISPLAY"
echo "Workspace: /workspace"
echo ""

# Start the tool server
echo "Starting Tool API server on port 8080..."
exec uvicorn server:app --host 0.0.0.0 --port 8080 --log-level info
