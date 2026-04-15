"""Pipeline to extract match data from Google Sheets and compute player rankings."""

from .sheets import extract_sheet
from .rating import PlayerRatings


# Expected Google Sheet format (columns):
# | date       | team_a_players      | team_b_players      | winner |
# |------------|---------------------|---------------------|--------|
# | 2024-01-15 | Alice, Bob          | Charlie, Diana      | A      |
# | 2024-01-22 | Alice, Eve          | Bob, Frank          | B      |
#
# - date: Match date (YYYY-MM-DD)
# - team_a_players: Comma-separated player names for team A
# - team_b_players: Comma-separated player names for team B
# - winner: "A" if team A won, "B" if team B won


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


def process_matches(data: list[list[str]]) -> PlayerRatings:
    """Process match data and compute player ratings.

    Args:
        data: 2D array from extract_sheet. First row is assumed to be header.
              Expected columns: date, team_a_players, team_b_players, winner

    Returns:
        PlayerRatings object with updated ratings for all players.
    """
    ratings = PlayerRatings()

    # Skip header row
    for row in data[1:]:
        if len(row) < 4:
            continue

        team_a_players = parse_players(row[1])
        team_b_players = parse_players(row[2])
        winner = row[3].strip().upper()

        if not team_a_players or not team_b_players:
            continue

        if winner == "A":
            winning_team = team_a_players
            losing_team = team_b_players
        elif winner == "B":
            winning_team = team_b_players
            losing_team = team_a_players
        else:
            continue

        # Record individual matchups (each winner beats each loser)
        # This is a simplification - TrueSkill has better team handling
        # but this approach works for demonstration
        for winner_name in winning_team:
            for loser_name in losing_team:
                ratings.record_match(winner_name, loser_name)

    return ratings


def compute_rankings_from_sheet(spreadsheet_id: str, sheet_name: str = "Sheet1") -> list[tuple[str, float, float]]:
    """Extract match data from Google Sheets and compute player rankings.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID.
        sheet_name: Name of the sheet tab (default: "Sheet1").

    Returns:
        List of (player_name, mu, sigma) tuples sorted by conservative rating.
    """
    # Extract data from sheet
    data = extract_sheet(spreadsheet_id, sheet_name)

    # Process matches and compute ratings
    ratings = process_matches(data)

    # Return leaderboard
    return ratings.get_leaderboard()


def print_rankings(rankings: list[tuple[str, float, float]]) -> None:
    """Print rankings in a formatted table.

    Args:
        rankings: List of (player_name, mu, sigma) tuples.
    """
    print(f"{'Rank':<6} {'Player':<20} {'Rating':<10} {'Uncertainty':<12} {'Conservative':<12}")
    print("-" * 60)

    for rank, (name, mu, sigma) in enumerate(rankings, 1):
        conservative = mu - 3 * sigma
        print(f"{rank:<6} {name:<20} {mu:<10.2f} {sigma:<12.2f} {conservative:<12.2f}")


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
    if not spreadsheet_id:
        print("Error: SPREADSHEET_ID not set in environment")
        exit(1)

    main(spreadsheet_id)