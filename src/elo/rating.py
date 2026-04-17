"""TrueSkill Through Time rating calculations with score-aware updates."""

from datetime import datetime
from typing import Optional
from trueskillthroughtime import Gaussian, Player, Game


class PlayerRatings:
    """Manage player ratings using TrueSkill Through Time with score awareness."""

    def __init__(
        self,
        mu: float = 25.0,
        sigma: float = 8.333,
        beta: float = 4.167,
        gamma: float = 0.03,
    ):
        """Initialize the rating system.

        Args:
            mu: Initial mean rating (default 25.0).
            sigma: Initial rating uncertainty (default mu/3).
            beta: Skill uncertainty parameter (performance variance, default mu/6).
            gamma: Temporal decay rate per year (default 0.03).
        """
        self.initial_mu = mu
        self.initial_sigma = sigma
        self.beta = beta
        self.gamma = gamma

        # Player skill history: {name: [(date, skill_gaussian), ...]}
        self.player_history: dict[str, list[tuple[datetime, Gaussian]]] = {}

        # Match records for analysis
        self.matches: list[dict] = []

    def _get_elapsed_years(self, date1: datetime, date2: datetime) -> float:
        """Calculate years elapsed between two dates."""
        delta = abs((date2 - date1).total_seconds())
        return delta / (365.25 * 24 * 3600)

    def get_skill_at_date(self, name: str, at_date: datetime) -> Gaussian:
        """Get player's skill at a specific date with temporal decay.

        Args:
            name: Player name.
            at_date: Date to get skill for.

        Returns:
            Player's skill as Gaussian (mu, sigma).
        """
        if name not in self.player_history:
            self.player_history[name] = []

        history = self.player_history[name]

        # No history: return initial rating
        if not history:
            return Gaussian(self.initial_mu, self.initial_sigma)

        # Get most recent rating before or at requested date
        applicable_skills = [(d, s) for d, s in history if d <= at_date]

        if not applicable_skills:
            # All matches are in future (shouldn't happen in practice)
            return Gaussian(self.initial_mu, self.initial_sigma)

        last_date, last_skill = applicable_skills[-1]

        # Apply temporal decay from last match to requested date
        elapsed_years = self._get_elapsed_years(last_date, at_date)

        if elapsed_years > 0:
            # Skill uncertainty increases over time (learning is forgotten)
            decayed_skill = last_skill.forget(self.gamma, elapsed_years)
            return decayed_skill
        else:
            return last_skill

    def record_match(
        self,
        team_a_players: list[str],
        team_b_players: list[str],
        team_a_score: float,
        team_b_score: float,
        date: datetime,
    ) -> dict:
        """Record a match with score-aware skill updates.

        Args:
            team_a_players: List of team A player names.
            team_b_players: List of team B player names.
            team_a_score: Team A final score.
            team_b_score: Team B final score.
            date: Match date.

        Returns:
            Match record dictionary with details.

        Raises:
            ValueError: If data is invalid.
        """
        # Validate input
        if not team_a_players or not team_b_players:
            raise ValueError("Both teams must have players")

        # Validate and normalize scores
        try:
            team_a_score = max(0.0, float(team_a_score))
            team_b_score = max(0.0, float(team_b_score))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid scores: {e}")

        # Get current skills for all players (with temporal decay)
        team_a_skills = [self.get_skill_at_date(name, date) for name in team_a_players]
        team_b_skills = [self.get_skill_at_date(name, date) for name in team_b_players]

        # Create Player objects
        team_a_player_objs = [Player(prior=skill) for skill in team_a_skills]
        team_b_player_objs = [Player(prior=skill) for skill in team_b_skills]

        # Create Game with teams and score differences
        # Scores are passed directly to result parameter for ranking
        teams = [team_a_player_objs, team_b_player_objs]
        game = Game(teams, result=[team_a_score, team_b_score], p_draw=0.0)

        # Extract updated skills from game posteriors
        posteriors = game.posteriors()

        # Store updated skills in history
        for team_idx, team_players in enumerate([team_a_players, team_b_players]):
            for player_idx, player_name in enumerate(team_players):
                new_skill = posteriors[team_idx][player_idx]
                self.player_history[player_name].append((date, new_skill))

        # Record match for analysis
        margin = abs(team_a_score - team_b_score)
        winner = (
            "A"
            if team_a_score > team_b_score
            else ("B" if team_b_score > team_a_score else "Draw")
        )

        match_record = {
            "date": date,
            "team_a_players": team_a_players,
            "team_b_players": team_b_players,
            "team_a_score": team_a_score,
            "team_b_score": team_b_score,
            "margin": margin,
            "winner": winner,
            "evidence": game.evidence,
        }
        self.matches.append(match_record)

        return match_record

    def get_current_rating(self, player_name: str) -> tuple[float, float]:
        """Get player's current mu and sigma.

        Returns:
            (mu, sigma) tuple.
        """
        if (
            player_name not in self.player_history
            or not self.player_history[player_name]
        ):
            return self.initial_mu, self.initial_sigma

        _, skill = self.player_history[player_name][-1]
        return skill.mu, skill.sigma

    def get_leaderboard(
        self, min_matches: int = 0
    ) -> list[tuple[str, float, float, int]]:
        """Get leaderboard sorted by conservative rating (mu - 3*sigma).

        Args:
            min_matches: Only include players with at least this many matches.

        Returns:
            List of (name, mu, sigma, match_count) sorted by conservative rating.
        """
        leaderboard = []

        for name, history in self.player_history.items():
            if not history or len(history) < min_matches:
                continue

            mu, sigma = history[-1][1].mu, history[-1][1].sigma
            match_count = len(history)

            leaderboard.append((name, mu, sigma, match_count))

        # Sort by conservative estimate (mu - 3*sigma)
        leaderboard.sort(key=lambda x: x[1] - 3 * x[2], reverse=True)

        return leaderboard

    def get_player_history(
        self, player_name: str
    ) -> list[tuple[datetime, float, float]]:
        """Get full skill evolution for a player.

        Returns:
            List of (date, mu, sigma) tuples in chronological order.
        """
        if player_name not in self.player_history:
            return []

        return [
            (date, skill.mu, skill.sigma)
            for date, skill in self.player_history[player_name]
        ]
