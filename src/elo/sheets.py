"""Google Sheets API integration."""

import os
import csv
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


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


def extract_local_sheet(spreadsheet_path: str) -> list[list[str]]:
    """Extract data from a local Excel file.

    Args:
        spreadsheet_path: Path to the local Excel file.

    """

    raw_values = []
    with open(spreadsheet_path, newline="") as csvfile:
        test_data = csv.reader(csvfile, delimiter=",", quotechar='"')
        for row in test_data:
            raw_values.append(row)
    # Convert all values to strings
    return [
        [str(cell) if cell is not None else "" for cell in row] for row in raw_values
    ]


def write_local_sheet(spreadsheet_path: str, data: list[list[str]]) -> None:
    """Write data to a local CSV file.

    Args:
        spreadsheet_path: Path to the local CSV file.
        data: 2D list of cell values to write.
    """
    with open(spreadsheet_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)


def write_sheet(
    spreadsheet_id: str,
    range_name: str,
    data: list[list],
    value_input_option: str = "RAW",
) -> dict:
    """Write data to a Google Sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        range_name: A1 notation range (e.g., 'Sheet1!A1', 'Leaderboard').
        data: 2D list of values to write (each row is a list).
        value_input_option: How to interpret input values. Use "USER_ENTERED" for
            formulas, "RAW" for literal values.

    Returns:
        Response from the API.
    """
    service = get_sheets_service()
    body = {"values": data}
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=body,
        )
        .execute()
    )
    return result


def clear_sheet(spreadsheet_id: str, range_name: str) -> dict:
    """Clear data from a Google Sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        range_name: A1 notation range (e.g., 'Sheet1', 'A:Z').

    Returns:
        Response from the API.
    """
    service = get_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .clear(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )
    return result


def write_leaderboard_sheet(
    spreadsheet_id: str,
    leaderboard: list[tuple[str, float, float, int]],
    sheet_name: str = "Leaderboard",
) -> dict:
    """Write leaderboard data to a Google Sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        leaderboard: List of (name, mu, sigma, match_count) tuples.
        sheet_name: Name of the sheet tab to write to.

    Returns:
        Response from the API.
    """
    # Build header row
    headers = [
        "Rank",
        "Player",
        "Rating",
        "Conservative Rating",
        "Uncertainty",
        "Matches",
    ]

    # Build data rows with rank and conservative rating (mu - 3*sigma)
    data = [headers]
    for rank, (name, mu, sigma, matches) in enumerate(leaderboard, 1):
        conservative_rating = mu - 3 * sigma
        data.append(
            [
                str(rank),
                name,
                f"{mu:.1f}",
                f"{conservative_rating:.1f}",
                f"{sigma:.1f}",
                str(matches),
            ]
        )

    # Write to sheet (clear first if it exists)
    range_name = f"{sheet_name}!A1"
    clear_sheet(spreadsheet_id, sheet_name)
    return write_sheet(spreadsheet_id, range_name, data)


def write_player_history_sheet(
    spreadsheet_id: str,
    player_name: str,
    history: list[tuple],
    sheet_name: str = "Player History",
) -> dict:
    """Write player history data to a Google Sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        player_name: Name of the player.
        history: List of (date, mu, sigma) tuples in chronological order.
        sheet_name: Name of the sheet tab to write to.

    Returns:
        Response from the API.
    """
    # Build header row
    headers = [
        "Player",
        "Date",
        "Conservative Rating",
        "Uncertainty",
        "Mu (Actual Rating)",
        "Sigma",
    ]

    # Build data rows
    data = [headers]
    for date, mu, sigma in history:
        conservative_rating = mu - 3 * sigma
        date_str = date.strftime("%Y-%m-%d %H:%M:%S")
        data.append(
            [
                player_name,
                date_str,
                f"{conservative_rating:.1f}",
                f"{sigma:.1f}",
                f"{mu:.1f}",
                f"{sigma:.1f}",
            ]
        )

    # Write to sheet
    range_name = f"{sheet_name}!A1"
    clear_sheet(spreadsheet_id, sheet_name)
    return write_sheet(spreadsheet_id, range_name, data)


def write_all_player_histories(
    spreadsheet_id: str,
    player_histories: dict[str, list[tuple]],
    sheet_name: str = "All Histories",
) -> dict:
    """Write all player histories to a Google Sheet (one row per history entry).

    Args:
        spreadsheet_id: The ID of the spreadsheet.
        player_histories: Dict mapping player name to list of (date, mu, sigma) tuples.
        sheet_name: Name of the sheet tab to write to.

    Returns:
        Response from the API.
    """
    # Build header row
    headers = ["Player", "Date", "Rating", "Uncertainty", "Mu", "Sigma"]

    # Build data rows for all players
    data = [headers]
    for player_name, history in player_histories.items():
        for date, mu, sigma in history:
            conservative_rating = mu - 3 * sigma
            date_str = date.strftime("%Y-%m-%d %H:%M:%S")
            data.append(
                [
                    player_name,
                    date_str,
                    f"{conservative_rating:.1f}",
                    f"{sigma:.1f}",
                    f"{mu:.1f}",
                    f"{sigma:.1f}",
                ]
            )

    # Write to sheet
    range_name = f"{sheet_name}!A1"
    clear_sheet(spreadsheet_id, range_name)
    return write_sheet(spreadsheet_id, range_name, data)
