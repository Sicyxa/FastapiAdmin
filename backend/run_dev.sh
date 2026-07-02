#!/usr/bin/env zsh
set -e

cd "$(dirname "$0")"
export ENVIRONMENT=dev
exec .venv/bin/python -m uvicorn main:create_app --factory --host localhost --port 8001
