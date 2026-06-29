"""
Thin wrapper around the Google Sheets v4 API using a service account.
"""

from __future__ import annotations

from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetsClient:
    def __init__(self, credentials_file: str) -> None:
        creds = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=SCOPES
        )
        self._service = build("sheets", "v4", credentials=creds)
        self._sheets = self._service.spreadsheets()

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_info(self, spreadsheet_id: str) -> dict[str, Any]:
        meta = self._sheets.get(spreadsheetId=spreadsheet_id).execute()
        sheets_info = [
            {
                "title": s["properties"]["title"],
                "sheet_id": s["properties"]["sheetId"],
                "row_count": s["properties"]["gridProperties"]["rowCount"],
                "column_count": s["properties"]["gridProperties"]["columnCount"],
            }
            for s in meta.get("sheets", [])
        ]
        return {
            "title": meta["properties"]["title"],
            "spreadsheet_id": spreadsheet_id,
            "sheets": sheets_info,
        }

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(self, spreadsheet_id: str, range_: str) -> dict[str, Any]:
        result = (
            self._sheets.values()
            .get(spreadsheetId=spreadsheet_id, range=range_)
            .execute()
        )
        values = result.get("values", [])
        return {
            "range": result.get("range"),
            "row_count": len(values),
            "values": values,
        }

    # ------------------------------------------------------------------
    # Write (overwrite a range)
    # ------------------------------------------------------------------

    def write(
        self,
        spreadsheet_id: str,
        range_: str,
        values: list[list[Any]],
    ) -> dict[str, Any]:
        body = {"values": values}
        result = (
            self._sheets.values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        return {
            "updated_range": result.get("updatedRange"),
            "updated_rows": result.get("updatedRows"),
            "updated_columns": result.get("updatedColumns"),
            "updated_cells": result.get("updatedCells"),
        }

    # ------------------------------------------------------------------
    # Append rows
    # ------------------------------------------------------------------

    def append(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        values: list[list[Any]],
    ) -> dict[str, Any]:
        # Using the full-column range so the API finds the first empty row
        range_ = f"{sheet_name}!A:A"
        body = {"values": values}
        result = (
            self._sheets.values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )
        updates = result.get("updates", {})
        return {
            "updated_range": updates.get("updatedRange"),
            "appended_rows": updates.get("updatedRows"),
            "appended_cells": updates.get("updatedCells"),
        }

    # ------------------------------------------------------------------
    # Find associate by name
    # ------------------------------------------------------------------

    def find_associate(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        associate_name: str,
        name_column: int = 0,
    ) -> dict[str, Any]:
        range_ = f"{sheet_name}!A:Z"
        result = (
            self._sheets.values()
            .get(spreadsheetId=spreadsheet_id, range=range_)
            .execute()
        )
        rows = result.get("values", [])
        if not rows:
            return {"found": False, "message": f'The associate name "{associate_name}" is not in the list.'}

        headers = rows[0] if rows else []
        name_lower = associate_name.strip().lower()

        matches = []
        for row in rows[1:]:
            if name_column < len(row) and row[name_column].strip().lower() == name_lower:
                record = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
                matches.append(record)

        if not matches:
            return {"found": False, "message": f'The associate name "{associate_name}" is not in the list.'}

        return {"found": True, "count": len(matches), "results": matches}

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def clear(self, spreadsheet_id: str, range_: str) -> dict[str, Any]:
        result = (
            self._sheets.values()
            .clear(spreadsheetId=spreadsheet_id, range=range_)
            .execute()
        )
        return {
            "cleared_range": result.get("clearedRange"),
        }
