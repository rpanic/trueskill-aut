"""Pipeline to extract match data from Google Sheets and compute player rankings."""

import os
from datetime import datetime
from sheets import extract_sheet
from sheets import extract_local_sheet
from sheets import write_sheet
from sheets import write_leaderboard_sheet
from sheets import write_player_history_sheet
from sheets import write_all_player_histories
from rating import PlayerRatings


# Expected Google Sheet format (columns):
# | date       | team_a_players      | team_b_players      | team_a_score | team_b_score |
# |------------|---------------------|---------------------|------|---|
# | 2024-01-15 12:00:00 | Alice, Bob          | Charlie, Diana      | 15   | 12|
# | 2024-01-22 11:50:00 | Alice, Eve          | Bob, Frank          | 20   | 18|
#
# - date: Match date (YYYY-MM-DD H:M:S)
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


def compute_ratings_from_sheet(
    spreadsheet_id: str, sheet_name: str = "Sheet1"
) -> PlayerRatings:
    """Extract match data from Google Sheets and compute player rankings.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID.
        sheet_name: Name of the sheet tab (default: "Sheet1").

    Returns:
        List of (player_name, mu, sigma, match_count) tuples sorted by conservative rating.
    """
    # Extract data from sheet
    if os.environ.get("MODE") == "online":
        data = extract_sheet(spreadsheet_id, sheet_name)
    else:
        data = extract_local_sheet("test_data.csv")

    # Process matches and compute ratings
    ratings = process_matches(data)

    # Return leaderboard
    return ratings


def print_rankings(rankings: list[tuple[str, float, float, int]]) -> None:
    """Print rankings in a formatted table.

    Args:
        rankings: List of (player_name, mu, sigma, match_count) tuples.
    """
    print(
        f"{'Rank':<6} {'Player':<20} {'Rating':<10} {'Uncertainty':<12} {'Matches':<8}"
    )
    print("-" * 70)

    # do we want conservatrive rating here? Displayed rating

    # In some deployments, a conservative skill estimate is displayed rather than the posterior mean. The TrueSkill paper describes displaying the 1% lower quantile of the belief distribution, which
    # for a Gaussian distribution is approximately μ − 3 σ. In plain terms, this is a value that the system expects the player's true skill to exceed about 99% of
    # the time, given the current uncertainty. As a result, a player with a high mean but large uncertainty (large σ {\displaystyle \sigma }) will have a lower displayed rating than a similarly
    # rated player whose skill is estimated more confidently.

    for rank, (name, mu, sigma, matches) in enumerate(rankings, 1):
        conservative = mu - 3 * sigma
        print(
            f"{rank:<6} {name:<20} {conservative:<10.1f} ±{sigma:<11.1f} {matches:<8}"
        )


def print_player_history(
    player_name: str, history: list[tuple[datetime, float, float]]
) -> None:
    print("-" * 70)
    print(f"{'Player':<6} {player_name:<20} ")
    print(f"{'Date':<6} {'Rating':<10} {'Uncertainty':<12}")
    print("-" * 70)
    for date, mu, sigma in history:
        conservative = mu - 3 * sigma
        print(f"{date.strftime('%Y-%m-%d'):<8} {conservative:<10.1f} ±{sigma:<11.1f} ")


def main(spreadsheet_id: str, sheet_name: str = "Sheet1") -> None:
    """Main entry point: fetch data, compute rankings, display results.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID.
        sheet_name: Name of the sheet tab (default: "Sheet1").
    """
    ratings = compute_ratings_from_sheet(spreadsheet_id, sheet_name)
    print_rankings(ratings.get_leaderboard())
    for player_name in ratings.player_history:
        print_player_history(player_name, ratings.get_player_history(player_name))

    write_all_player_histories_to_sheet(spreadsheet_id, ratings)
    write_leaderboard_to_sheet(spreadsheet_id, ratings)


def write_leaderboard_to_sheet(
    spreadsheet_id: str,
    ratings: PlayerRatings,
    sheet_name: str = "Leaderboard",
    min_matches: int = 0,
) -> dict:
    """Write player leaderboard to a Google Sheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID.
        ratings: PlayerRatings object with computed ratings.
        sheet_name: Name of the sheet tab to write to (default: "Leaderboard").
        min_matches: Only include players with at least this many matches.

    Returns:
        Response from the Google Sheets API.
    """
    leaderboard = ratings.get_leaderboard(min_matches=min_matches)
    return write_leaderboard_sheet(spreadsheet_id, leaderboard, sheet_name)


def write_player_history_to_sheet(
    spreadsheet_id: str,
    ratings: PlayerRatings,
    player_name: str,
    sheet_name: str = "Player History",
) -> dict:
    """Write single player's history to a Google Sheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID.
        ratings: PlayerRatings object with computed ratings.
        player_name: Name of the player to export.
        sheet_name: Name of the sheet tab to write to (default: "Player History").

    Returns:
        Response from the Google Sheets API.
    """
    history = ratings.get_player_history(player_name)
    return write_player_history_sheet(spreadsheet_id, player_name, history, sheet_name)


def write_all_player_histories_to_sheet(
    spreadsheet_id: str,
    ratings: PlayerRatings,
    sheet_name: str = "All Histories",
) -> dict:
    """Write all players' histories to a Google Sheet.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID.
        ratings: PlayerRatings object with computed ratings.
        sheet_name: Name of the sheet tab to write to (default: "All Histories").

    Returns:
        Response from the Google Sheets API.
    """
    player_histories = {
        name: ratings.get_player_history(name) for name in ratings.player_history
    }
    return write_all_player_histories(spreadsheet_id, player_histories, sheet_name)


def write_results_to_sheet(
    spreadsheet_id: str,
    ratings: PlayerRatings,
    leaderboard_sheet: str = "Leaderboard",
    histories_sheet: str = "All Histories",
    min_matches: int = 0,
) -> dict:
    """Write both leaderboard and all player histories to Google Sheets.

    Convenience function that writes both leaderboard and player history
    data in a single call.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID.
        ratings: PlayerRatings object with computed ratings.
        leaderboard_sheet: Name of the sheet tab for leaderboard (default: "Leaderboard").
        histories_sheet: Name of the sheet tab for histories (default: "All Histories").
        min_matches: Only include players in leaderboard with at least this many matches.

    Returns:
        Dict with keys "leaderboard" and "histories" containing API responses.
    """
    results = {}
    results["leaderboard"] = write_leaderboard_to_sheet(
        spreadsheet_id, ratings, leaderboard_sheet, min_matches
    )
    results["histories"] = write_all_player_histories_to_sheet(
        spreadsheet_id, ratings, histories_sheet
    )
    return results


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
