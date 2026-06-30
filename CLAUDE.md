# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This workspace is for learning Claude AI and the Anthropic SDK. The main active project is `google-sheets-mcp/` — a Python MCP server that exposes Google Sheets operations as tools for Claude Desktop.

## Setup

```bash
# Install dependencies
pip install -r google-sheets-mcp/requirements.txt

# Required env var pointing to a Google service account JSON key
export GOOGLE_SERVICE_ACCOUNT_FILE="/path/to/credentials.json"
```

## Running the MCP Server

```bash
python google-sheets-mcp/server.py
```

The server communicates over stdio (MCP protocol). It is not invoked directly in normal use — Claude Desktop launches it via the config below.

## Claude Desktop Integration

Copy `google-sheets-mcp/claude_desktop_config_example.json` into `~/Library/Application Support/Claude/claude_desktop_config.json`, updating the absolute path and `GOOGLE_SERVICE_ACCOUNT_FILE` env var. Restart Claude Desktop to pick up the server.

## Architecture

**Two-file design:**

- `server.py` — MCP layer. Defines and registers tools (`get_sheet_info`, `read_sheet`, `write_sheet`, `append_rows`, `clear_range`, `find_associate`), dispatches calls to `SheetsClient`, and serializes results as JSON `TextContent`.
- `sheets_client.py` — Google Sheets API wrapper. `SheetsClient` authenticates via a service account, wraps the Sheets v4 REST API, and returns plain dicts. All API calls live here; `server.py` contains no API logic.

**Auth:** A single service account credential file is loaded lazily on first tool call (via `get_sheets_client()`). The spreadsheet must be shared with the service account email.

**`find_associate` tool:** Domain-specific tool that searches a sheet for a row by name (case-insensitive), returning the full row keyed by header column names.
