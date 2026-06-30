"""Unit tests for the MCP server tool registration and dispatch."""

import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "google-sheets-mcp"))

SPREADSHEET_ID = "test_id"


def _mock_sheets_client():
    return MagicMock()


@pytest.fixture(autouse=True)
def reset_server_state():
    """Reset the cached SheetsClient between tests."""
    import server
    original = server._sheets
    server._sheets = None
    yield
    server._sheets = original


class TestListTools:
    @pytest.mark.asyncio
    async def test_all_expected_tools_registered(self):
        import server
        tools = await server.list_tools()
        names = {t.name for t in tools}
        assert names == {
            "get_sheet_info",
            "read_sheet",
            "write_sheet",
            "append_rows",
            "clear_range",
            "find_associate",
        }

    @pytest.mark.asyncio
    async def test_each_tool_has_description_and_schema(self):
        import server
        tools = await server.list_tools()
        for tool in tools:
            assert tool.description, f"{tool.name} missing description"
            assert "properties" in tool.inputSchema, f"{tool.name} missing inputSchema properties"


class TestCallTool:
    def _patch_client(self, mock_client):
        return patch("server.get_sheets_client", return_value=mock_client)

    @pytest.mark.asyncio
    async def test_get_sheet_info_dispatches_correctly(self):
        import server
        mock = _mock_sheets_client()
        mock.get_info.return_value = {"title": "Test", "sheets": []}

        with self._patch_client(mock):
            result = await server.call_tool("get_sheet_info", {"spreadsheet_id": SPREADSHEET_ID})

        mock.get_info.assert_called_once_with(SPREADSHEET_ID)
        data = json.loads(result[0].text)
        assert data["title"] == "Test"

    @pytest.mark.asyncio
    async def test_read_sheet_dispatches_correctly(self):
        import server
        mock = _mock_sheets_client()
        mock.read.return_value = {"values": [["A", "B"]], "row_count": 1, "range": "Sheet1!A1:B1"}

        with self._patch_client(mock):
            result = await server.call_tool(
                "read_sheet", {"spreadsheet_id": SPREADSHEET_ID, "range": "Sheet1!A1:B1"}
            )

        mock.read.assert_called_once_with(SPREADSHEET_ID, "Sheet1!A1:B1")
        data = json.loads(result[0].text)
        assert data["row_count"] == 1

    @pytest.mark.asyncio
    async def test_write_sheet_dispatches_correctly(self):
        import server
        mock = _mock_sheets_client()
        mock.write.return_value = {"updated_cells": 4}

        with self._patch_client(mock):
            await server.call_tool(
                "write_sheet",
                {"spreadsheet_id": SPREADSHEET_ID, "range": "Sheet1!A1", "values": [["a", "b"]]},
            )

        mock.write.assert_called_once_with(SPREADSHEET_ID, "Sheet1!A1", [["a", "b"]])

    @pytest.mark.asyncio
    async def test_append_rows_dispatches_correctly(self):
        import server
        mock = _mock_sheets_client()
        mock.append.return_value = {"appended_rows": 1}

        with self._patch_client(mock):
            await server.call_tool(
                "append_rows",
                {"spreadsheet_id": SPREADSHEET_ID, "sheet_name": "Sheet1", "values": [["x"]]},
            )

        mock.append.assert_called_once_with(SPREADSHEET_ID, "Sheet1", [["x"]])

    @pytest.mark.asyncio
    async def test_clear_range_dispatches_correctly(self):
        import server
        mock = _mock_sheets_client()
        mock.clear.return_value = {"cleared_range": "Sheet1!A1:Z10"}

        with self._patch_client(mock):
            await server.call_tool(
                "clear_range", {"spreadsheet_id": SPREADSHEET_ID, "range": "Sheet1!A1:Z10"}
            )

        mock.clear.assert_called_once_with(SPREADSHEET_ID, "Sheet1!A1:Z10")

    @pytest.mark.asyncio
    async def test_find_associate_dispatches_correctly(self):
        import server
        mock = _mock_sheets_client()
        mock.find_associate.return_value = {"found": True, "count": 1, "results": []}

        with self._patch_client(mock):
            await server.call_tool(
                "find_associate",
                {
                    "spreadsheet_id": SPREADSHEET_ID,
                    "sheet_name": "Sheet1",
                    "associate_name": "Alice",
                    "name_column": 0,
                },
            )

        mock.find_associate.assert_called_once_with(SPREADSHEET_ID, "Sheet1", "Alice", 0)

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        import server
        mock = _mock_sheets_client()

        with self._patch_client(mock):
            result = await server.call_tool("nonexistent_tool", {})

        data = json.loads(result[0].text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_exception_from_client_returns_error(self):
        import server
        mock = _mock_sheets_client()
        mock.get_info.side_effect = Exception("API failure")

        with self._patch_client(mock):
            result = await server.call_tool("get_sheet_info", {"spreadsheet_id": SPREADSHEET_ID})

        data = json.loads(result[0].text)
        assert data["error"] == "API failure"
