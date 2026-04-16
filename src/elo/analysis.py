"""Analysis utilities for player ratings and match insights."""

import math
from datetime import datetime
from .rating import PlayerRatings


def get_player_rating_change(
    ratings: PlayerRatings,
    player_name: str
) -> tuple[float, float]:
    """Calculate rating change from first to last match.
    
    Args:
        ratings: PlayerRatings instance.
        player_name: Player name.
    
    Returns:
        (mu_change, sigma_change) tuple.
    """
    history = ratings.get_player_history(player_name)
    
    if len(history) < 2:
        return 0.0, 0.0
    
    first_mu, first_sigma = history[0][1], history[0][2]
    last_mu, last_sigma = history[-1][1], history[-1][2]
    
    return last_mu - first_mu, last_sigma - first_sigma


def find_closest_matches(ratings: PlayerRatings, threshold: float = 1.0) -> list[dict]:
    """Find matches with very close scores (within threshold).
    
    Args:
        ratings: PlayerRatings instance.
        threshold: Maximum score difference to consider "close".
    
    Returns:
        List of close match records.
    """
    close_matches = []
    
    for match in ratings.matches:
        if match['margin'] <= threshold:
            close_matches.append(match)
    
    return sorted(close_matches, key=lambda m: m['margin'])


def find_upsets(ratings: PlayerRatings, rating_threshold: float = 5.0) -> list[dict]:
    """Find matches where lower-rated team won.
    
    Args:
        ratings: PlayerRatings instance.
        rating_threshold: Minimum rating difference to consider an upset.
    
    Returns:
        List of upset match records with rating context.
    """
    upsets = []
    
    for match in ratings.matches:
        if match['winner'] == 'Draw':
            continue
        
        # Calculate average team ratings at match time
        team_a_skills = []
        for p in match['team_a_players']:
            history = ratings.get_player_history(p)
            if history:
                # Get skill at or before match date
                applicable = [s for d, s, _ in history if d <= match['date']]
                if applicable:
                    team_a_skills.append(applicable[-1])
        
        team_b_skills = []
        for p in match['team_b_players']:
            history = ratings.get_player_history(p)
            if history:
                applicable = [s for d, s, _ in history if d <= match['date']]
                if applicable:
                    team_b_skills.append(applicable[-1])
        
        if not team_a_skills or not team_b_skills:
            continue
        
        team_a_avg = sum(team_a_skills) / len(team_a_skills)
        team_b_avg = sum(team_b_skills) / len(team_b_skills)
        
        rating_diff = abs(team_a_avg - team_b_avg)
        
        # Check if lower-rated team won
        team_a_won = match['winner'] == 'A'
        
        if rating_diff >= rating_threshold:
            if (team_a_won and team_b_avg > team_a_avg) or \
               (not team_a_won and team_a_avg > team_b_avg):
                upsets.append({
                    'date': match['date'],
                    'teams': (match['team_a_players'], match['team_b_players']),
                    'score': (match['team_a_score'], match['team_b_score']),
                    'winner': match['winner'],
                    'rating_diff': rating_diff
                })
    
    return sorted(upsets, key=lambda x: x['rating_diff'], reverse=True)


def predict_match_outcome(
    ratings: PlayerRatings,
    team_a: list[str],
    team_b: list[str]
) -> dict:
    """Predict match outcome probabilities based on current ratings.
    
    Args:
        ratings: PlayerRatings instance.
        team_a: Team A player names.
        team_b: Team B player names.
    
    Returns:
        Dictionary with prediction info.
    """
    if not team_a or not team_b:
        raise ValueError("Both teams must have players")
    
    # Get current ratings
    team_a_ratings = [ratings.get_current_rating(p) for p in team_a]
    team_b_ratings = [ratings.get_current_rating(p) for p in team_b]
    
    # Calculate averages
    team_a_mu = sum(mu for mu, _ in team_a_ratings) / len(team_a_ratings)
    team_b_mu = sum(mu for mu, _ in team_b_ratings) / len(team_b_ratings)
    
    team_a_sigma = sum(sigma for _, sigma in team_a_ratings) / len(team_a_ratings)
    team_b_sigma = sum(sigma for _, sigma in team_b_ratings) / len(team_b_ratings)
    
    # Prediction: higher mu team is favored
    rating_diff = team_a_mu - team_b_mu
    combined_uncertainty = (team_a_sigma ** 2 + team_b_sigma ** 2) ** 0.5
    
    # Probability estimate using sigmoid function
    if combined_uncertainty > 0:
        z = rating_diff / combined_uncertainty
        prob_a_wins = 1.0 / (1.0 + math.exp(-z))
    else:
        prob_a_wins = 1.0 if rating_diff > 0 else 0.0
    
    return {
        'team_a_expected_rating': team_a_mu,
        'team_b_expected_rating': team_b_mu,
        'rating_diff': rating_diff,
        'combined_uncertainty': combined_uncertainty,
        'prob_team_a_wins': prob_a_wins,
        'prob_team_b_wins': 1.0 - prob_a_wins,
        'favorite': 'A' if rating_diff > 0 else ('B' if rating_diff < 0 else 'Even')
    }


def get_player_stats(ratings: PlayerRatings, player_name: str) -> dict:
    """Get comprehensive statistics for a player.
    
    Args:
        ratings: PlayerRatings instance.
        player_name: Player name.
    
    Returns:
        Dictionary with player statistics.
    """
    history = ratings.get_player_history(player_name)
    
    if not history:
        return {
            'player': player_name,
            'matches': 0,
            'current_rating': ratings.initial_mu,
            'current_uncertainty': ratings.initial_sigma
        }
    
    mu_change, sigma_change = get_player_rating_change(ratings, player_name)
    
    current_mu, current_sigma = history[-1][1], history[-1][2]
    initial_mu, initial_sigma = history[0][1], history[0][2]
    
    # Find best and worst matches
    mus = [mu for _, mu, _ in history]
    best_rating = max(mus)
    worst_rating = min(mus)
    
    return {
        'player': player_name,
        'matches': len(history),
        'current_rating': current_mu,
        'current_uncertainty': current_sigma,
        'conservative_rating': current_mu - 3 * current_sigma,
        'initial_rating': initial_mu,
        'rating_change': mu_change,
        'uncertainty_change': sigma_change,
        'best_rating': best_rating,
        'worst_rating': worst_rating,
        'first_match_date': history[0][0],
        'last_match_date': history[-1][0]
    }


def print_match_summary(ratings: PlayerRatings) -> None:
    """Print summary of all matches.
    
    Args:
        ratings: PlayerRatings instance.
    """
    print(f"\nTotal matches: {len(ratings.matches)}\n")
    print(f"{'Date':<12} {'Team A':<30} {'Score':<10} {'Team B':<30} {'Winner':<6}")
    print("-" * 90)
    
    for match in sorted(ratings.matches, key=lambda m: m['date']):
        team_a_str = ", ".join(match['team_a_players'][:2])  # Show first 2 players
        team_b_str = ", ".join(match['team_b_players'][:2])
        
        if len(match['team_a_players']) > 2:
            team_a_str += f" +{len(match['team_a_players']) - 2}"
        if len(match['team_b_players']) > 2:
            team_b_str += f" +{len(match['team_b_players']) - 2}"
        
        score = f"{match['team_a_score']:.0f}-{match['team_b_score']:.0f}"
        
        print(f"{match['date'].strftime('%Y-%m-%d'):<12} {team_a_str:<30} {score:<10} {team_b_str:<30} {match['winner']:<6}")
