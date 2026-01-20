#!/bin/bash
set -e

cd /app/apps/backend
exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

