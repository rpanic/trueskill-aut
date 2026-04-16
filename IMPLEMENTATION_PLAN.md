# Simplified Score-Aware TrueSkill Implementation Plan

## Discovery

The `trueskillthroughtime` library already supports score differences directly via the `result` parameter in the `Game` class:
- `result=[0, 1]` (binary)
- `result=[5, 2]` (score differences)
- `result=[15, 10]` (actual scores)

The library uses scores for **ranking** (higher score = winner) and **margin interpretation** (larger margins increase certainty).

## Simplified Implementation

### Changes Required

#### 1. **Data Format (Google Sheets)**
```
OLD: | date | team_a_players | team_b_players | winner |
NEW: | date | team_a_players | team_b_players | team_a_score | team_b_score |
```

#### 2. **rating.py Rewrite**
Replace the broken `TrueSkill`/`Rating` wrapper with direct `trueskillthroughtime` API usage:

```python
from trueskillthroughtime import Gaussian, Player, Game

class PlayerRatings:
    def __init__(self, mu=25.0, sigma=8.333, beta=4.167, gamma=0.03):
        self.initial_mu = mu
        self.initial_sigma = sigma
        self.beta = beta
        self.gamma = gamma
        self.player_history: dict = {}  # {name: [(date, skill), ...]}
        self.matches: list = []
    
    def record_match(self, team_a_players, team_b_players, 
                     team_a_score, team_b_score, date):
        """Record match with actual scores"""
        # Get current skills (with temporal decay)
        team_a_skills = [self.get_skill_at_date(name, date) 
                        for name in team_a_players]
        team_b_skills = [self.get_skill_at_date(name, date) 
                        for name in team_b_players]
        
        # Create Player and Game objects
        teams = [[Player(prior=skill) for skill in team_a_skills],
                 [Player(prior=skill) for skill in team_b_skills]]
        
        # Pass scores directly to result parameter
        game = Game(teams, result=[team_a_score, team_b_score])
        
        # Extract and store updated skills
        posteriors = game.posteriors()
        for team_idx, players in enumerate([team_a_players, team_b_players]):
            for player_idx, player_name in enumerate(players):
                new_skill = posteriors[team_idx][player_idx]
                self.player_history[player_name].append((date, new_skill))
```

#### 3. **pipeline.py Update**
```python
def process_matches(data):
    """Process match data with score-aware updates"""
    ratings = PlayerRatings()
    for row in data[1:]:  # Skip header
        date = datetime.strptime(row[0], "%Y-%m-%d")
        team_a = parse_players(row[1])
        team_b = parse_players(row[2])
        score_a = float(row[3])
        score_b = float(row[4])
        
        ratings.record_match(team_a, team_b, score_a, score_b, date)
    
    return ratings
```

### What We DON'T Need

❌ ScoreMapper class (library handles ranking)
❌ Custom weight calculations (library uses scores for weighting)
❌ Custom margin logic (library considers score differences)
❌ Complex likelihood computation (library does it)

### What We DO Need

✅ Temporal decay (skill uncertainty increases over time)
✅ History tracking (see player progression)
✅ Data validation (scores are numeric, non-negative)
✅ Leaderboard generation (sorted by conservative rating)

## Implementation Steps

### Step 1: Fix rating.py
- Replace broken TrueSkill/Rating wrapper
- Use actual trueskillthroughtime API: Gaussian, Player, Game
- Implement temporal decay via `skill.forget(gamma, elapsed_years)`
- Store player history as list of (date, skill) tuples

### Step 2: Update pipeline.py
- Change column parsing from 4 to 5 columns
- Add score parsing (convert to float)
- Call updated record_match() with scores

### Step 3: Add helper modules
- Create `analysis.py` for insights (history, volatility, upsets)
- Update error handling and validation

### Step 4: Test and validate
- Unit tests for rating updates
- Integration tests with sample Google Sheets
- Verify temporal decay works correctly

## Benefits

✅ **Simpler implementation** (~300 lines instead of 800)
✅ **Leverages library features** (no custom weighting needed)
✅ **Score differences matter** (library considers margins for ranking)
✅ **Temporal decay** (realistic skill erosion)
✅ **Multi-team support** (Game handles N teams)
✅ **Backward compatible** (old binary data can be migrated)

## Estimated Effort

- **rating.py rewrite**: 2 hours
- **pipeline.py update**: 1 hour
- **analysis.py creation**: 2 hours
- **Testing**: 2 hours
- **Documentation**: 1 hour

**Total: ~8 hours**

