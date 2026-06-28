"""
Google Sheets MCP Server

Exposes tools to read and write Google Sheets data using a service account.
Set GOOGLE_SERVICE_ACCOUNT_FILE env var to the path of your credentials JSON.
"""

import os
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from sheets_client import SheetsClient

server = Server("Cognizant AI score MCP Server")
_sheets: SheetsClient | None = None


def get_sheets_client() -> SheetsClient:
    global _sheets
    if _sheets is None:
        creds_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json")
        _sheets = SheetsClient(credentials_file=creds_file)
    return _sheets


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_sheet_info",
            description=(
                "Get metadata about a Google Spreadsheet: its title and the list of "
                "sheet tabs with their row/column dimensions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "The spreadsheet ID from its URL (/d/<ID>/edit).",
                    }
                },
                "required": ["spreadsheet_id"],
            },
        ),
        Tool(
            name="read_sheet",
            description=(
                "Read cell values from a Google Sheet range. "
                "Returns a 2-D array of values (rows → columns). "
                "Range format: 'Sheet1!A1:D10' or just 'A1:D10' for the first sheet."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "The spreadsheet ID.",
                    },
                    "range": {
                        "type": "string",
                        "description": "A1 notation range, e.g. 'Sheet1!A1:E20'.",
                    },
                },
                "required": ["spreadsheet_id", "range"],
            },
        ),
        Tool(
            name="write_sheet",
            description=(
                "Write values to a specific range in a Google Sheet. "
                "Overwrites existing data in that range. "
                "Values is a 2-D array: outer list = rows, inner list = columns."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range": {
                        "type": "string",
                        "description": "A1 notation range for the top-left anchor, e.g. 'Sheet1!A1'.",
                    },
                    "values": {
                        "type": "array",
                        "items": {"type": "array"},
                        "description": "2-D array of values. E.g. [['Name','Age'],['Alice',30]].",
                    },
                },
                "required": ["spreadsheet_id", "range", "values"],
            },
        ),
        Tool(
            name="append_rows",
            description=(
                "Append rows to the bottom of an existing table in a Google Sheet. "
                "Finds the first empty row after the last row of data and writes there."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "sheet_name": {
                        "type": "string",
                        "description": "Name of the sheet tab, e.g. 'Sheet1'.",
                    },
                    "values": {
                        "type": "array",
                        "items": {"type": "array"},
                        "description": "2-D array of rows to append.",
                    },
                },
                "required": ["spreadsheet_id", "sheet_name", "values"],
            },
        ),
        Tool(
            name="clear_range",
            description="Clear (erase) all values in a given range without deleting the cells.",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range": {
                        "type": "string",
                        "description": "A1 notation range to clear, e.g. 'Sheet1!A2:Z100'.",
                    },
                },
                "required": ["spreadsheet_id", "range"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        sheets = get_sheets_client()
        if name == "get_sheet_info":
            result = sheets.get_info(arguments["spreadsheet_id"])
        elif name == "read_sheet":
            result = sheets.read(arguments["spreadsheet_id"], arguments["range"])
        elif name == "write_sheet":
            result = sheets.write(
                arguments["spreadsheet_id"],
                arguments["range"],
                arguments["values"],
            )
        elif name == "append_rows":
            result = sheets.append(
                arguments["spreadsheet_id"],
                arguments["sheet_name"],
                arguments["values"],
            )
        elif name == "clear_range":
            result = sheets.clear(arguments["spreadsheet_id"], arguments["range"])
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as exc:
        result = {"error": str(exc)}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
