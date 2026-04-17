# Google Sheets Write Integration

## Overview

Added methods to `src/elo/sheets.py` and `src/elo/pipeline.py` to write leaderboard and player history data to Google Spreadsheets.

## Changes to `sheets.py`

### Updated Scope
- Changed from `read-only` to `read-write` scope to enable writing:
  ```python
  SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
  ```

### New Core Write Methods

#### `write_sheet(spreadsheet_id, range_name, data, value_input_option)`
Generic method to write any 2D array data to a Google Sheet.

**Parameters:**
- `spreadsheet_id`: The spreadsheet ID
- `range_name`: A1 notation (e.g., 'Sheet1!A1', 'Leaderboard')
- `data`: 2D list of values to write
- `value_input_option`: "USER_ENTERED" (default) or "RAW"

**Returns:** API response

#### `clear_sheet(spreadsheet_id, range_name)`
Clear data from a specific range in a Google Sheet.

**Parameters:**
- `spreadsheet_id`: The spreadsheet ID
- `range_name`: A1 notation range

**Returns:** API response

#### `write_leaderboard_sheet(spreadsheet_id, leaderboard, sheet_name)`
Write leaderboard data to a sheet with formatted columns.

**Parameters:**
- `spreadsheet_id`: The spreadsheet ID
- `leaderboard`: List of (name, mu, sigma, match_count) tuples
- `sheet_name`: Sheet tab name (default: "Leaderboard")

**Output Format:**
| Rank | Player | Rating | Uncertainty | Matches |
|------|--------|--------|-------------|---------|

**Returns:** API response

#### `write_player_history_sheet(spreadsheet_id, player_name, history, sheet_name)`
Write a single player's skill history to a sheet.

**Parameters:**
- `spreadsheet_id`: The spreadsheet ID
- `player_name`: Name of the player
- `history`: List of (date, mu, sigma) tuples
- `sheet_name`: Sheet tab name (default: "Player History")

**Output Format:**
| Player | Date | Rating | Uncertainty | Mu | Sigma |
|--------|------|--------|-------------|----|----|

**Returns:** API response

#### `write_all_player_histories(spreadsheet_id, player_histories, sheet_name)`
Write all players' histories in a single sheet (one row per history entry).

**Parameters:**
- `spreadsheet_id`: The spreadsheet ID
- `player_histories`: Dict mapping player name → list of (date, mu, sigma) tuples
- `sheet_name`: Sheet tab name (default: "All Histories")

**Output Format:** Same as single player history (repeats player name for each entry)

**Returns:** API response

---

## Changes to `pipeline.py`

### Updated Imports
Added imports for new write functions:
```python
from sheets import write_sheet
from sheets import write_leaderboard_sheet
from sheets import write_player_history_sheet
from sheets import write_all_player_histories
```

### New Pipeline Functions

#### `write_leaderboard_to_sheet(spreadsheet_id, ratings, sheet_name, min_matches)`
Write player leaderboard to a Google Sheet.

**Parameters:**
- `spreadsheet_id`: The Google Sheets ID
- `ratings`: PlayerRatings object with computed ratings
- `sheet_name`: Sheet tab name (default: "Leaderboard")
- `min_matches`: Filter players by minimum matches (default: 0)

**Returns:** API response

**Example:**
```python
ratings = compute_ratings_from_sheet(spreadsheet_id, "Sheet1")
write_leaderboard_to_sheet(spreadsheet_id, ratings, min_matches=5)
```

#### `write_player_history_to_sheet(spreadsheet_id, ratings, player_name, sheet_name)`
Write a single player's history to a Google Sheet.

**Parameters:**
- `spreadsheet_id`: The Google Sheets ID
- `ratings`: PlayerRatings object
- `player_name`: Name of the player to export
- `sheet_name`: Sheet tab name (default: "Player History")

**Returns:** API response

**Example:**
```python
write_player_history_to_sheet(spreadsheet_id, ratings, "Alice")
```

#### `write_all_player_histories_to_sheet(spreadsheet_id, ratings, sheet_name)`
Write all players' histories to a Google Sheet.

**Parameters:**
- `spreadsheet_id`: The Google Sheets ID
- `ratings`: PlayerRatings object
- `sheet_name`: Sheet tab name (default: "All Histories")

**Returns:** API response

**Example:**
```python
write_all_player_histories_to_sheet(spreadsheet_id, ratings)
```

#### `write_results_to_sheet(spreadsheet_id, ratings, leaderboard_sheet, histories_sheet, min_matches)`
Convenience method to write both leaderboard and player histories in one call.

**Parameters:**
- `spreadsheet_id`: The Google Sheets ID
- `ratings`: PlayerRatings object
- `leaderboard_sheet`: Sheet name for leaderboard (default: "Leaderboard")
- `histories_sheet`: Sheet name for histories (default: "All Histories")
- `min_matches`: Filter for leaderboard (default: 0)

**Returns:** Dict with keys "leaderboard" and "histories" containing API responses

**Example:**
```python
ratings = compute_ratings_from_sheet(spreadsheet_id, "Sheet1")
results = write_results_to_sheet(spreadsheet_id, ratings)
print(f"Leaderboard written: {results['leaderboard']}")
print(f"Histories written: {results['histories']}")
```

---

## Usage Example

```python
from elo.pipeline import compute_ratings_from_sheet, write_results_to_sheet
import os

# Compute ratings from matches
spreadsheet_id = os.environ.get("SPREADSHEET_ID")
ratings = compute_ratings_from_sheet(spreadsheet_id, "Sheet1")

# Write results to output sheets
results = write_results_to_sheet(
    spreadsheet_id, 
    ratings,
    leaderboard_sheet="Leaderboard",
    histories_sheet="All Histories",
    min_matches=3
)

print("✓ Leaderboard exported to 'Leaderboard' sheet")
print("✓ Player histories exported to 'All Histories' sheet")
```

---

## Rating Format

All rating values are displayed using the **conservative rating** (TrueSkill's 1% lower quantile):
- **Conservative Rating = μ - 3σ**

This represents a value the system expects the player's true skill to exceed ~99% of the time, accounting for uncertainty.

The data includes both the conservative rating and raw mu/sigma values for flexibility.

---

## Permissions

The service account used must have write access to the Google Spreadsheet. Update credentials with appropriate scopes if needed.

## Authentication

The code uses the same credentials mechanism as existing read functionality:
- Environment variable: `GOOGLE_APPLICATION_CREDENTIALS`
- Default path: `credentials.json` in project root
