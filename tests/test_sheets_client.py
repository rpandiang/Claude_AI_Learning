"""Unit tests for SheetsClient — all Google API calls are mocked."""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "google-sheets-mcp"))

SPREADSHEET_ID = "test_spreadsheet_id"


def _make_client():
    """Return a SheetsClient with the Google API fully mocked out."""
    with patch("sheets_client.service_account.Credentials.from_service_account_file"), \
         patch("sheets_client.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        from sheets_client import SheetsClient
        client = SheetsClient(credentials_file="fake_creds.json")
        client._sheets = mock_service.spreadsheets.return_value
        return client


class TestGetInfo:
    def test_returns_title_and_sheets(self):
        client = _make_client()
        client._sheets.get.return_value.execute.return_value = {
            "properties": {"title": "My Sheet"},
            "sheets": [
                {
                    "properties": {
                        "title": "Sheet1",
                        "sheetId": 0,
                        "gridProperties": {"rowCount": 1000, "columnCount": 26},
                    }
                }
            ],
        }

        result = client.get_info(SPREADSHEET_ID)

        assert result["title"] == "My Sheet"
        assert result["spreadsheet_id"] == SPREADSHEET_ID
        assert len(result["sheets"]) == 1
        assert result["sheets"][0]["title"] == "Sheet1"
        assert result["sheets"][0]["row_count"] == 1000

    def test_empty_sheets_list(self):
        client = _make_client()
        client._sheets.get.return_value.execute.return_value = {
            "properties": {"title": "Empty"},
            "sheets": [],
        }

        result = client.get_info(SPREADSHEET_ID)
        assert result["sheets"] == []


class TestListSheets:
    def test_returns_sheet_names_only(self):
        client = _make_client()
        client._sheets.get.return_value.execute.return_value = {
            "properties": {"title": "My Sheet"},
            "sheets": [
                {
                    "properties": {
                        "title": "Sheet1",
                        "sheetId": 0,
                        "gridProperties": {"rowCount": 1000, "columnCount": 26},
                    }
                },
                {
                    "properties": {
                        "title": "Sheet2",
                        "sheetId": 1,
                        "gridProperties": {"rowCount": 500, "columnCount": 10},
                    }
                },
            ],
        }

        result = client.list_sheets(SPREADSHEET_ID)

        assert result == {
            "spreadsheet_id": SPREADSHEET_ID,
            "sheet_names": ["Sheet1", "Sheet2"],
        }

    def test_empty_sheets_list(self):
        client = _make_client()
        client._sheets.get.return_value.execute.return_value = {
            "properties": {"title": "Empty"},
            "sheets": [],
        }

        result = client.list_sheets(SPREADSHEET_ID)

        assert result["sheet_names"] == []


class TestRead:
    def test_returns_values_and_row_count(self):
        client = _make_client()
        client._sheets.values.return_value.get.return_value.execute.return_value = {
            "range": "Sheet1!A1:B2",
            "values": [["Name", "Age"], ["Alice", "30"]],
        }

        result = client.read(SPREADSHEET_ID, "Sheet1!A1:B2")

        assert result["row_count"] == 2
        assert result["values"][0] == ["Name", "Age"]
        assert result["range"] == "Sheet1!A1:B2"

    def test_empty_range_returns_zero_rows(self):
        client = _make_client()
        client._sheets.values.return_value.get.return_value.execute.return_value = {
            "range": "Sheet1!A1",
        }

        result = client.read(SPREADSHEET_ID, "Sheet1!A1")
        assert result["row_count"] == 0
        assert result["values"] == []


class TestWrite:
    def test_returns_update_stats(self):
        client = _make_client()
        client._sheets.values.return_value.update.return_value.execute.return_value = {
            "updatedRange": "Sheet1!A1:B2",
            "updatedRows": 2,
            "updatedColumns": 2,
            "updatedCells": 4,
        }

        result = client.write(SPREADSHEET_ID, "Sheet1!A1", [["Name", "Age"], ["Alice", "30"]])

        assert result["updated_rows"] == 2
        assert result["updated_cells"] == 4
        assert result["updated_range"] == "Sheet1!A1:B2"

    def test_calls_user_entered_value_input_option(self):
        client = _make_client()
        client._sheets.values.return_value.update.return_value.execute.return_value = {
            "updatedRange": "Sheet1!A1", "updatedRows": 1, "updatedColumns": 1, "updatedCells": 1
        }

        client.write(SPREADSHEET_ID, "Sheet1!A1", [["hello"]])

        call_kwargs = client._sheets.values.return_value.update.call_args.kwargs
        assert call_kwargs["valueInputOption"] == "USER_ENTERED"


class TestAppend:
    def test_returns_appended_stats(self):
        client = _make_client()
        client._sheets.values.return_value.append.return_value.execute.return_value = {
            "updates": {
                "updatedRange": "Sheet1!A5:B5",
                "updatedRows": 1,
                "updatedCells": 2,
            }
        }

        result = client.append(SPREADSHEET_ID, "Sheet1", [["Bob", "25"]])

        assert result["appended_rows"] == 1
        assert result["appended_cells"] == 2
        assert "Sheet1" in result["updated_range"]


class TestClear:
    def test_returns_cleared_range(self):
        client = _make_client()
        client._sheets.values.return_value.clear.return_value.execute.return_value = {
            "clearedRange": "Sheet1!A2:Z100"
        }

        result = client.clear(SPREADSHEET_ID, "Sheet1!A2:Z100")
        assert result["cleared_range"] == "Sheet1!A2:Z100"


class TestFindAssociate:
    def _setup_rows(self, client, rows):
        client._sheets.values.return_value.get.return_value.execute.return_value = {
            "values": rows
        }

    def test_finds_existing_associate(self):
        client = _make_client()
        self._setup_rows(client, [
            ["Name", "Score", "Level"],
            ["Alice Smith", "95", "Senior"],
            ["Bob Jones", "80", "Junior"],
        ])

        result = client.find_associate(SPREADSHEET_ID, "Sheet1", "Alice Smith")

        assert result["found"] is True
        assert result["count"] == 1
        assert result["results"][0]["Name"] == "Alice Smith"
        assert result["results"][0]["Score"] == "95"

    def test_case_insensitive_match(self):
        client = _make_client()
        self._setup_rows(client, [
            ["Name", "Score"],
            ["Alice Smith", "95"],
        ])

        result = client.find_associate(SPREADSHEET_ID, "Sheet1", "alice smith")
        assert result["found"] is True

    def test_name_not_found_returns_helpful_message(self):
        client = _make_client()
        self._setup_rows(client, [
            ["Name", "Score"],
            ["Alice Smith", "95"],
        ])

        result = client.find_associate(SPREADSHEET_ID, "Sheet1", "Charlie Brown")

        assert result["found"] is False
        assert "Charlie Brown" in result["message"]

    def test_empty_sheet_returns_not_found(self):
        client = _make_client()
        client._sheets.values.return_value.get.return_value.execute.return_value = {"values": []}

        result = client.find_associate(SPREADSHEET_ID, "Sheet1", "Anyone")
        assert result["found"] is False

    def test_multiple_matches_returned(self):
        client = _make_client()
        self._setup_rows(client, [
            ["Name", "Score"],
            ["Alice Smith", "95"],
            ["Alice Smith", "88"],
        ])

        result = client.find_associate(SPREADSHEET_ID, "Sheet1", "Alice Smith")
        assert result["count"] == 2
