"""Pipeline to extract match data from Google Sheets and compute player rankings."""

from datetime import datetime
from sheets import extract_sheet
from rating import PlayerRatings


# Expected Google Sheet format (columns):
# | date       | team_a_players      | team_b_players      | team_a_score | team_b_score |
# |------------|---------------------|---------------------|------|---|
# | 2024-01-15 | Alice, Bob          | Charlie, Diana      | 15   | 12|
# | 2024-01-22 | Alice, Eve          | Bob, Frank          | 20   | 18|
#
# - date: Match date (YYYY-MM-DD)
# - team_a_players: Comma-separated player names for team A
# - team_b_players: Comma-separated player names for team B
# - team_a_score: Final score for team A
# - team_b_score: Final score for team B


def parse_players(player_string: str) -> list[str]:
    """Parse a comma-separated player string into a list of player names.

    Args:
        player_string: Comma-separated player names (e.g., "Alice, Bob, Charlie").

    Returns:
        List of stripped player names.
    """
    if not player_string or not player_string.strip():
        return []
    return [name.strip() for name in player_string.split(",") if name.strip()]


def parse_date(date_string: str) -> datetime:
    """Parse date string in YYYY-MM-DD format.

    Args:
        date_string: Date string.

    Returns:
        datetime object.

    Raises:
        ValueError: If date format is invalid.
    """
    return datetime.strptime(date_string.strip(), "%d.%m.%Y %H:%M:%S")


def process_matches(data: list[list[str]]) -> PlayerRatings:
    """Process match data and compute player ratings.

    Args:
        data: 2D array from extract_sheet. First row is assumed to be header.
              Expected columns: date, team_a_players, team_b_players, team_a_score, team_b_score

    Returns:
        PlayerRatings object with updated ratings for all players.
    """
    ratings = PlayerRatings()

    # Skip header row
    for row_idx, row in enumerate(data[1:], start=2):
        if len(row) < 5:
            print(
                f"Warning: Row {row_idx} has insufficient columns (need 5, got {len(row)}), skipping"
            )
            continue

        try:
            date_str = row[0].strip()
            team_a_str = row[1].strip()
            team_b_str = row[2].strip()
            score_a_str = row[3].strip()
            score_b_str = row[4].strip()

            # Parse components
            date = parse_date(date_str)
            team_a = parse_players(team_a_str)
            team_b = parse_players(team_b_str)

            if not team_a or not team_b:
                print(f"Warning: Row {row_idx} has empty team, skipping")
                continue

            score_a = float(score_a_str)
            score_b = float(score_b_str)

            # Record match
            ratings.record_match(team_a, team_b, score_a, score_b, date)

        except ValueError as e:
            print(f"Warning: Row {row_idx} parse error: {e}, skipping")
            continue
        except Exception as e:
            print(f"Error: Row {row_idx} processing error: {e}")
            raise

    return ratings


def compute_rankings_from_sheet(
    spreadsheet_id: str, sheet_name: str = "Sheet1"
) -> list[tuple[str, float, float, int]]:
    """Extract match data from Google Sheets and compute player rankings.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID.
        sheet_name: Name of the sheet tab (default: "Sheet1").

    Returns:
        List of (player_name, mu, sigma, match_count) tuples sorted by conservative rating.
    """
    # Extract data from sheet
    data = extract_sheet(spreadsheet_id, sheet_name)

    # Process matches and compute ratings
    ratings = process_matches(data)

    # Return leaderboard
    return ratings.get_leaderboard()


def print_rankings(rankings: list[tuple[str, float, float, int]]) -> None:
    """Print rankings in a formatted table.

    Args:
        rankings: List of (player_name, mu, sigma, match_count) tuples.
    """
    print(
        f"{'Rank':<6} {'Player':<20} {'Rating':<10} {'Uncertainty':<12} {'Matches':<8}"
    )
    print("-" * 70)

    for rank, (name, mu, sigma, matches) in enumerate(rankings, 1):
        conservative = mu - 3 * sigma
        print(
            f"{rank:<6} {name:<20} {conservative:<10.1f} ±{sigma:<11.1f} {matches:<8}"
        )


def main(spreadsheet_id: str, sheet_name: str = "Sheet1") -> None:
    """Main entry point: fetch data, compute rankings, display results.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID.
        sheet_name: Name of the sheet tab (default: "Sheet1").
    """
    rankings = compute_rankings_from_sheet(spreadsheet_id, sheet_name)
    print_rankings(rankings)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    sheet_name = os.environ.get("SHEET_NAME")
    if not spreadsheet_id:
        print("Error: SPREADSHEET_ID not set in environment")
        exit(1)

    main(spreadsheet_id, sheet_name)
