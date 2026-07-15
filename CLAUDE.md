# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This workspace is for learning Claude AI and the Anthropic SDK. The main active project is `google-sheets-mcp/` — a Python MCP server that exposes Google Sheets operations as tools for Claude Desktop.

## Setup

```bash
# Install runtime dependencies
pip install -r google-sheets-mcp/requirements.txt

# Install dev/test dependencies (includes pytest)
pip install -r requirements-dev.txt

# Required env var pointing to a Google service account JSON key
export GOOGLE_SERVICE_ACCOUNT_FILE="/path/to/credentials.json"
```

Use Python 3.11 (`/opt/homebrew/bin/python3.11`) — the system Python 3.9 does not have the dependencies installed.

## Running the MCP Server

```bash
python google-sheets-mcp/server.py
```

The server communicates over stdio (MCP protocol). It is not invoked directly in normal use — Claude Desktop launches it via the config below.

## Claude Desktop Integration

Copy `google-sheets-mcp/claude_desktop_config_example.json` into `~/Library/Application Support/Claude/claude_desktop_config.json`, updating the absolute path and `GOOGLE_SERVICE_ACCOUNT_FILE` env var. Restart Claude Desktop to pick up the server.

## Testing

Tests live in `tests/` and use `pytest` with `unittest.mock` — no real Google API calls are made.

```bash
# Run all tests
/opt/homebrew/bin/python3.11 -m pytest tests/ -v

# Run a single test file
/opt/homebrew/bin/python3.11 -m pytest tests/test_sheets_client.py -v

# Run with coverage report
/opt/homebrew/bin/python3.11 -m pytest tests/ --cov=google-sheets-mcp --cov-report=term-missing

# Generate HTML coverage report
/opt/homebrew/bin/python3.11 -m pytest tests/ --cov=google-sheets-mcp --cov-report=html
open htmlcov/index.html
```

**Coverage:** 91% overall — `sheets_client.py` is at 100%. The uncovered lines in `server.py` are the lazy `SheetsClient` init (always mocked in tests) and the `main()` / `__main__` entry point (requires a live stdio server).

**Pre-push hook:** `.git/hooks/pre-push` runs the full test suite before every `git push`. The push is blocked if any test fails.

## Security

**Pre-commit hook:** `.git/hooks/pre-commit` scans staged changes for likely secrets (AWS keys, PEM private key blocks, Anthropic/OpenAI-style API keys, Google service account JSON, and generic `key = "long-value"` assignments) before every `git commit`. The commit is blocked if anything secret-shaped is found; false positives can be bypassed with `git commit --no-verify`.

Before pushing any commit, also scan the diff and any new/modified files for API keys, tokens, service account credentials, or other secrets the hook might miss. If a sensitive file type is found that isn't already covered, add a pattern for it to `.gitignore` rather than committing it.

## Architecture

**Two-file design:**

- `server.py` — MCP layer. Defines and registers tools (`get_sheet_info`, `list_sheets`, `read_sheet`, `write_sheet`, `append_rows`, `clear_range`, `find_associate`), dispatches calls to `SheetsClient`, and serializes results as JSON `TextContent`.
- `sheets_client.py` — Google Sheets API wrapper. `SheetsClient` authenticates via a service account, wraps the Sheets v4 REST API, and returns plain dicts. All API calls live here; `server.py` contains no API logic.

**Auth:** A single service account credential file is loaded lazily on first tool call (via `get_sheets_client()`). The spreadsheet must be shared with the service account email.

**`find_associate` tool:** Domain-specific tool that searches a sheet for a row by name (case-insensitive), returning the full row keyed by header column names.
