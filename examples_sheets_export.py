"""
Example: Writing Leaderboard and Player History to Google Sheets

This example demonstrates how to use the new write functions to export
computed ratings to Google Spreadsheets.
"""

import os
from elo.pipeline import (
    compute_ratings_from_sheet,
    write_results_to_sheet,
    write_leaderboard_to_sheet,
    write_all_player_histories_to_sheet,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
SHEET_NAME = os.environ.get("SHEET_NAME", "Sheet1")

if not SPREADSHEET_ID:
    print("Error: SPREADSHEET_ID not set in environment")
    exit(1)


def example_1_write_all_results():
    """Example 1: Write leaderboard and histories in a single call."""
    print("=" * 60)
    print("Example 1: Write All Results to Google Sheets")
    print("=" * 60)

    # Compute ratings from match data
    ratings = compute_ratings_from_sheet(SPREADSHEET_ID, SHEET_NAME)

    # Write both leaderboard and player histories to output sheets
    results = write_results_to_sheet(
        SPREADSHEET_ID,
        ratings,
        leaderboard_sheet="Leaderboard",
        histories_sheet="All Histories",
        min_matches=0,  # Include all players
    )

    print(f"✓ Leaderboard exported")
    print(f"  - Updated cells: {results['leaderboard'].get('updatedCells')}")
    print(f"  - Updated ranges: {results['leaderboard'].get('updatedRange')}")

    print(f"\n✓ Player histories exported")
    print(f"  - Updated cells: {results['histories'].get('updatedCells')}")
    print(f"  - Updated ranges: {results['histories'].get('updatedRange')}")


def example_2_write_leaderboard_only():
    """Example 2: Write only leaderboard to a specific sheet."""
    print("\n" + "=" * 60)
    print("Example 2: Write Leaderboard Only (Minimum Matches Filter)")
    print("=" * 60)

    ratings = compute_ratings_from_sheet(SPREADSHEET_ID, SHEET_NAME)

    # Write leaderboard with a minimum matches requirement
    result = write_leaderboard_to_sheet(
        SPREADSHEET_ID,
        ratings,
        sheet_name="Top Players",
        min_matches=5,  # Only players with 5+ matches
    )

    print(f"✓ Leaderboard (5+ matches) exported to 'Top Players' sheet")
    print(f"  - Updated cells: {result.get('updatedCells')}")


def example_3_write_individual_histories():
    """Example 3: Write individual player histories to separate sheets."""
    print("\n" + "=" * 60)
    print("Example 3: Export Individual Player Histories")
    print("=" * 60)

    ratings = compute_ratings_from_sheet(SPREADSHEET_ID, SHEET_NAME)

    # Get list of all players
    leaderboard = ratings.get_leaderboard()
    top_players = [name for name, _, _, _ in leaderboard[:3]]  # Top 3 players

    print(f"Exporting histories for top 3 players: {top_players}")

    for player_name in top_players:
        history = ratings.get_player_history(player_name)

        if history:
            # You could write each to a separate sheet with the player's name
            from elo.sheets import write_player_history_sheet

            result = write_player_history_sheet(
                SPREADSHEET_ID,
                player_name,
                history,
                sheet_name=player_name,  # Sheet named after player
            )
            print(f"  ✓ {player_name}: {result.get('updatedCells')} cells updated")


def example_4_batch_export_with_filters():
    """Example 4: Export with various filters and custom organization."""
    print("\n" + "=" * 60)
    print("Example 4: Batch Export with Custom Filtering")
    print("=" * 60)

    ratings = compute_ratings_from_sheet(SPREADSHEET_ID, SHEET_NAME)

    # Write multiple filtered versions
    filters = [
        {"name": "All Players", "min_matches": 0},
        {"name": "Active (5+ matches)", "min_matches": 5},
        {"name": "Core (10+ matches)", "min_matches": 10},
    ]

    for filter_config in filters:
        result = write_leaderboard_to_sheet(
            SPREADSHEET_ID,
            ratings,
            sheet_name=filter_config["name"],
            min_matches=filter_config["min_matches"],
        )
        print(f"✓ {filter_config['name']}: {result.get('updatedCells')} cells")

    # Also export all histories
    result = write_all_player_histories_to_sheet(
        SPREADSHEET_ID, ratings, sheet_name="Skill Evolution"
    )
    print(f"\n✓ Skill Evolution: {result.get('updatedCells')} cells")


if __name__ == "__main__":
    print("\nTrueSkill Google Sheets Export Examples\n")

    # Run all examples
    try:
        example_1_write_all_results()
        example_2_write_leaderboard_only()
        example_3_write_individual_histories()
        example_4_batch_export_with_filters()

        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
