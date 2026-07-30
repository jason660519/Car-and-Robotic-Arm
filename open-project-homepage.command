#!/bin/bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
URL="http://127.0.0.1:4321/Car-and-Robotic-Arm/"
TMP_ROOT="${TMPDIR:-/tmp}"
LOG_FILE="${TMP_ROOT%/}/car-and-robotic-arm-astro-dev.log"

homepage_ready() {
  curl -fsS "$URL" 2>/dev/null | grep -q "Smart Car + Robotic Concept Project"
}

echo "Project directory: $PROJECT_DIR"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is not installed. Please install Node.js first."
  exit 1
fi

if [ ! -d "$PROJECT_DIR/node_modules" ]; then
  echo "node_modules not found. Running npm install..."
  npm install --prefix "$PROJECT_DIR"
fi

if homepage_ready; then
  echo "Astro dev server is already running."
else
  echo "Starting Astro dev server..."
  nohup npm run dev --prefix "$PROJECT_DIR" -- --host 127.0.0.1 >"$LOG_FILE" 2>&1 &
  SERVER_PID=$!

  for _ in {1..30}; do
    if homepage_ready; then
      echo "Astro dev server started (PID: $SERVER_PID)."
      break
    fi
    sleep 1
  done

  if ! homepage_ready; then
    echo "The homepage did not become ready in time."
    echo "Check the log: $LOG_FILE"
    exit 1
  fi
fi

open "$URL"
echo "Opened: $URL"
echo "Dev server log: $LOG_FILE"
