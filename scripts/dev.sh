#!/usr/bin/env bash
# Convenience runner for local dev. Intentionally minimal.
set -euo pipefail

case "${1:-help}" in
  api)     uvicorn app.main:app --reload ;;
  ui)      streamlit run ui/streamlit_app.py ;;
  mcp)     python -m app.mcp.echo_server ;;
  test)    pytest -q ;;
  lint)    ruff check . && mypy app ;;
  *)
    echo "usage: $0 {api|ui|mcp|test|lint}"
    exit 1
    ;;
esac
