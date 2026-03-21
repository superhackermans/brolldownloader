#!/bin/bash
# run.sh - Build and run HTML-to-4K-Video pipeline in Docker
#
# Mounts:
#   $(pwd) -> /app                            Entire repo (edits sync both ways)
#   ~/.claude -> /home/claude/.claude          Auth data + history
#   ~/.claude/.claude.json -> ~/.claude.json   Config file (Claude expects this at HOME root)
#
# Usage:
#   ./run.sh                       Launch Claude Code
#   ./run.sh node record.js        Run a command directly

cd "$(dirname "$0")"

docker build -t html-to-video .

if [ $# -eq 0 ]; then
  # No args: launch Claude Code
  docker run -it \
    --entrypoint claude \
    -u "$(id -u):$(id -g)" \
    -v "$(pwd):/app" \
    -v "$HOME/.claude:/home/claude/.claude" \
    -v "$HOME/.claude/.claude.json:/home/claude/.claude.json" \
    -e HOME=/home/claude \
    html-to-video \
    --dangerously-skip-permissions
else
  # Args provided: run that command
  docker run -it \
    --entrypoint "$1" \
    -u "$(id -u):$(id -g)" \
    -v "$(pwd):/app" \
    -v "$HOME/.claude:/home/claude/.claude" \
    -v "$HOME/.claude/.claude.json:/home/claude/.claude.json" \
    -e HOME=/home/claude \
    html-to-video \
    "${@:2}"
fi
