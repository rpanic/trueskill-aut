# Elo Rating System

A Python project using TrueSkill Through Time for rating calculations with Google Sheets integration.

## Setup

### 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Google Sheets API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Google Sheets API
4. Create a Service Account:
   - IAM & Admin > Service Accounts > Create Service Account
   - Create and download JSON credentials
5. Save credentials file as `credentials.json` in project root
6. Share your Google Sheet with the service account email

### 3. Environment Variables

```bash
cp .env.example .env
# Edit .env with your spreadsheet ID
```

## Usage

```python
from elo.sheets import read_all
from elo.rating import PlayerRatings

# Read match data from Google Sheets
spreadsheet_id = "your-spreadsheet-id"
data = read_all(spreadsheet_id, "Matches")

# Calculate ratings
ratings = PlayerRatings()
for row in data[1:]:  # Skip header
    winner, loser = row[0], row[1]
    ratings.record_match(winner, loser)

# View leaderboard
for name, mu, sigma in ratings.get_leaderboard():
    print(f"{name}: {mu:.1f} ± {sigma:.1f}")
```

## Project Structure

```
elo/
├── src/elo/
│   ├── __init__.py
│   ├── sheets.py      # Google Sheets integration
│   └── rating.py      # TrueSkill Through Time logic
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```