# Quick Reference: Google Sheets Write Methods

## In `sheets.py`

### Core Methods

| Method | Purpose |
|--------|---------|
| `write_sheet()` | Generic 2D array writer to any sheet range |
| `clear_sheet()` | Clear data from a sheet range |
| `write_leaderboard_sheet()` | Write formatted leaderboard |
| `write_player_history_sheet()` | Write single player's history |
| `write_all_player_histories()` | Write all players' histories |

---

## In `pipeline.py`

### Pipeline Integration Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `write_leaderboard_to_sheet()` | Export leaderboard with filters | API response |
| `write_player_history_to_sheet()` | Export one player's history | API response |
| `write_all_player_histories_to_sheet()` | Export all histories | API response |
| `write_results_to_sheet()` | Export both in one call | Dict with both responses |

---

## Simplest Usage Pattern

```python
from elo.pipeline import compute_ratings_from_sheet, write_results_to_sheet
import os

# 1. Compute ratings
ratings = compute_ratings_from_sheet(
    os.environ.get("SPREADSHEET_ID"),
    "Sheet1"
)

# 2. Write results
write_results_to_sheet(
    os.environ.get("SPREADSHEET_ID"),
    ratings
)

# Done! Creates two sheets: "Leaderboard" and "All Histories"
```

---

## Output Sheet Formats

### Leaderboard Sheet

| Rank | Player | Rating | Uncertainty | Matches |
|------|--------|--------|-------------|---------|
| 1    | Alice  | 35.2   | ±3.5        | 12      |
| 2    | Bob    | 28.1   | ±4.2        | 8       |

### Player History Sheet

| Player | Date | Rating | Uncertainty | Mu | Sigma |
|--------|------|--------|-------------|----|----|
| Alice | 2024-01-15 14:30:00 | 24.5 | ±8.3 | 49.4 | 8.3 |
| Alice | 2024-01-22 10:15:00 | 28.3 | ±7.1 | 50.8 | 7.1 |

---

## Key Features

✓ **Conservative Rating Display**: Uses μ - 3σ (99th percentile) for visible ratings  
✓ **Full Skill Data**: Also includes raw mu and sigma values  
✓ **Flexible Filtering**: Filter leaderboard by minimum matches  
✓ **Batch Operations**: Export multiple filtered views and histories  
✓ **Google Sheets Native**: Uses official Google Sheets API v4  
✓ **Error Handling**: Built-in validation and error messages  

---

## Integration with Existing Pipeline

All new functions work seamlessly with existing code:

```python
# Old pipeline still works unchanged
ratings = compute_ratings_from_sheet(spreadsheet_id, sheet_name)
print_rankings(ratings.get_leaderboard())

# New: Just add this to also write to sheets
write_results_to_sheet(spreadsheet_id, ratings)
```

---

## Authentication Setup

Requires Google Service Account credentials:

1. Create service account in Google Cloud Console
2. Generate JSON key file
3. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
4. Or place `credentials.json` in project root

See: `SHEETS_INTEGRATION.md` for detailed documentation
