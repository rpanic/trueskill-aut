"""TrueSkill Through Time rating calculations."""

from trueskillthroughtime import Rating, TrueSkill


class PlayerRatings:
    """Manage player ratings using TrueSkill Through Time."""

    def __init__(self, mu: float = 25.0, sigma: float = 8.333, beta: float = 4.167):
        """Initialize the rating system.

        Args:
            mu: Initial mean rating (default 25.0).
            sigma: Initial rating uncertainty (default mu/3).
            beta: Skill uncertainty parameter (default mu/6).
        """
        self.trueskill = TrueSkill(mu=mu, sigma=sigma, beta=beta)
        self.players: dict[str, Rating] = {}

    def get_or_create_player(self, name: str) -> Rating:
        """Get existing player rating or create a new one.

        Args:
            name: Player identifier.

        Returns:
            Player's Rating object.
        """
        if name not in self.players:
            self.players[name] = self.trueskill.rating()
        return self.players[name]

    def record_match(self, winner: str, loser: str) -> tuple[Rating, Rating]:
        """Record a match result and update ratings.

        Args:
            winner: Name of the winning player.
            loser: Name of the losing player.

        Returns:
            Tuple of updated (winner_rating, loser_rating).
        """
        winner_rating = self.get_or_create_player(winner)
        loser_rating = self.get_or_create_player(loser)

        # Update ratings based on match outcome
        winner_rating, loser_rating = self.trueskill.rate_1vs1(
            winner_rating, loser_rating
        )

        self.players[winner] = winner_rating
        self.players[loser] = loser_rating

        return winner_rating, loser_rating

    def get_leaderboard(self) -> list[tuple[str, float, float]]:
        """Get all players sorted by conservative rating (mu - 3*sigma).

        Returns:
            List of (name, mu, sigma) tuples sorted by conservative rating.
        """
        leaderboard = [
            (name, rating.mu, rating.sigma) for name, rating in self.players.items()
        ]
        # Sort by conservative estimate (mu - 3*sigma)
        leaderboard.sort(key=lambda x: x[1] - 3 * x[2], reverse=True)
        return leaderboard