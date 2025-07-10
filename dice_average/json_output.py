"""JSON output formatting utilities."""

from typing import Dict, Any, Optional

from .models import RollSession
from .statistics import SessionAnalyzer


def format_roll_json(session: RollSession, iterations: int, seed: Optional[int], 
                    stats: bool = False) -> Dict[str, Any]:
    """Format roll results as JSON."""
    output_data = {
        "expression": str(session.expression),
        "iterations": iterations,
        "seed": seed,
        "results": [roll.total for roll in session.rolls],
        "average": session.average_total,
        "min": session.min_total,
        "max": session.max_total,
        "theoretical_average": session.expression.average_value,
    }
    
    if stats:
        analysis = SessionAnalyzer.analyze_session(session)
        output_data["statistics"] = analysis
    
    return output_data


def format_analyze_json(dice_expr, stats_result, extended_stats=None) -> Dict[str, Any]:
    """Format analysis results as JSON."""
    output_data = {
        "expression": str(dice_expr),
        "min_value": stats_result.theoretical_min,
        "max_value": stats_result.theoretical_max,
        "average": stats_result.theoretical_average,
        "most_likely": stats_result.most_likely_value,
        "median": stats_result.median_value,
        "probability_distribution": stats_result.probability_distribution,
    }
    
    if extended_stats:
        output_data["extended_statistics"] = extended_stats
    
    return output_data


def format_history_json(history_data, limit: int) -> Dict[str, Any]:
    """Format history data as JSON."""
    recent_sessions = history_data.get_recent_sessions(limit)
    return {
        "total_sessions": len(history_data.sessions),
        "recent_sessions": [
            {
                "expression": str(session.expression),
                "rolls": len(session.rolls),
                "average": session.average_total,
                "min": session.min_total,
                "max": session.max_total,
                "seed": session.seed,
            }
            for session in recent_sessions
        ],
    }