"""Google Sheets API integration."""

import os
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_sheets_service():
    """Create and return a Google Sheets API service.

    Requires a service account credentials JSON file.
    Set the path via GOOGLE_APPLICATION_CREDENTIALS environment variable,
    or defaults to 'credentials.json' in the project root.

    Returns:
        Authorized Google Sheets service object.
    """
    creds_path = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS",
        str(Path(__file__).parent.parent.parent.parent / "credentials.json"),
    )

    credentials = service_account.Credentials.from_service_account_file(
        creds_path, scopes=SCOPES
    )

    service = build("sheets", "v4", credentials=credentials)
    return service


def extract_sheet(spreadsheet_id: str, range_name: str) -> list[list[str]]:
    """Extract data from a Google Sheet into a 2D array of strings.

    Args:
        spreadsheet_id: The ID of the spreadsheet (from the URL).
            Example: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit
        range_name: A1 notation range (e.g., 'Sheet1!A1:B10', 'Sheet1', 'A:Z').

    Returns:
        2D list where each row is a list of string values.
        Empty cells are represented as empty strings.
        Rows may have different lengths if the sheet is ragged.
    """
    service = get_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )

    raw_values = result.get("values", [])
    # Convert all values to strings
    return [
        [str(cell) if cell is not None else "" for cell in row] for row in raw_values
    ]


def extract_all(spreadsheet_id: str, sheet_name: str = "Sheet1") -> list[list[str]]:
    """Extract all data from a specific sheet tab.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        sheet_name: Name of the sheet tab (default: "Sheet1").

    Returns:
        2D list of all cell values as strings.
    """
    return extract_sheet(spreadsheet_id, sheet_name)

