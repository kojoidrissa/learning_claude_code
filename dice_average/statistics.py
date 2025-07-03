"""Statistical analysis and probability calculations for dice expressions."""

from collections import Counter
from functools import lru_cache
from typing import Dict, List, Tuple
import math

from .models import DiceExpression, DiceGroup, StatisticsResult, RollSession


class DiceStatistics:
    """Calculate theoretical statistics for dice expressions."""
    
    @staticmethod
    @lru_cache(maxsize=128)
    def _single_die_distribution(sides: int) -> Dict[int, float]:
        """Get probability distribution for a single die."""
        prob = 1.0 / sides
        return {i: prob for i in range(1, sides + 1)}
    
    @staticmethod
    def _convolve_distributions(dist1: Dict[int, float], 
                               dist2: Dict[int, float]) -> Dict[int, float]:
        """Convolve two probability distributions (for adding dice)."""
        result = {}
        
        for val1, prob1 in dist1.items():
            for val2, prob2 in dist2.items():
                total = val1 + val2
                result[total] = result.get(total, 0.0) + prob1 * prob2
        
        return result
    
    @classmethod
    def _dice_group_distribution(cls, group: DiceGroup) -> Dict[int, float]:
        """Get probability distribution for a group of identical dice."""
        if group.count == 1:
            return cls._single_die_distribution(group.die.sides)
        
        # Start with one die
        result = cls._single_die_distribution(group.die.sides)
        
        # Add remaining dice one by one
        for _ in range(group.count - 1):
            single_die = cls._single_die_distribution(group.die.sides)
            result = cls._convolve_distributions(result, single_die)
        
        return result
    
    @classmethod
    def calculate_distribution(cls, expression: DiceExpression) -> Dict[int, float]:
        """
        Calculate the complete probability distribution for a dice expression.
        
        Args:
            expression: The dice expression to analyze
            
        Returns:
            Dictionary mapping each possible value to its probability
        """
        if not expression.dice_groups:
            # Just a modifier
            return {expression.modifier: 1.0}
        
        # Start with the first dice group
        result = cls._dice_group_distribution(expression.dice_groups[0])
        
        # Add remaining dice groups
        for group in expression.dice_groups[1:]:
            group_dist = cls._dice_group_distribution(group)
            result = cls._convolve_distributions(result, group_dist)
        
        # Apply modifier
        if expression.modifier != 0:
            modified_result = {}
            for value, prob in result.items():
                modified_result[value + expression.modifier] = prob
            result = modified_result
        
        return result
    
    @classmethod
    def calculate_statistics(cls, expression: DiceExpression) -> StatisticsResult:
        """
        Calculate comprehensive statistics for a dice expression.
        
        Args:
            expression: The dice expression to analyze
            
        Returns:
            StatisticsResult with all calculated statistics
        """
        distribution = cls.calculate_distribution(expression)
        
        return StatisticsResult(
            expression=expression,
            theoretical_min=expression.min_value,
            theoretical_max=expression.max_value,
            theoretical_average=expression.average_value,
            probability_distribution=distribution
        )
    
    @staticmethod
    def calculate_percentiles(distribution: Dict[int, float], 
                            percentiles: List[float]) -> Dict[float, int]:
        """
        Calculate percentiles for a probability distribution.
        
        Args:
            distribution: Probability distribution
            percentiles: List of percentiles to calculate (0.0 to 1.0)
            
        Returns:
            Dictionary mapping percentiles to values
        """
        if not distribution:
            return {}
        
        # Sort values and calculate cumulative distribution
        sorted_values = sorted(distribution.keys())
        cumulative = 0.0
        cumulative_dist = []
        
        for value in sorted_values:
            cumulative += distribution[value]
            cumulative_dist.append((value, cumulative))
        
        # Find percentile values
        result = {}
        for percentile in percentiles:
            if percentile < 0.0 or percentile > 1.0:
                continue
            
            for value, cumulative_prob in cumulative_dist:
                if cumulative_prob >= percentile:
                    result[percentile] = value
                    break
        
        return result
    
    @staticmethod
    def calculate_variance(distribution: Dict[int, float], mean: float) -> float:
        """Calculate variance of a probability distribution."""
        variance = 0.0
        for value, prob in distribution.items():
            variance += prob * (value - mean) ** 2
        return variance
    
    @staticmethod
    def calculate_standard_deviation(distribution: Dict[int, float], 
                                   mean: float) -> float:
        """Calculate standard deviation of a probability distribution."""
        variance = DiceStatistics.calculate_variance(distribution, mean)
        return math.sqrt(variance)
    
    @staticmethod
    def calculate_skewness(distribution: Dict[int, float], 
                          mean: float, std_dev: float) -> float:
        """Calculate skewness of a probability distribution."""
        if std_dev == 0:
            return 0.0
        
        skewness = 0.0
        for value, prob in distribution.items():
            skewness += prob * ((value - mean) / std_dev) ** 3
        return skewness
    
    @staticmethod
    def calculate_kurtosis(distribution: Dict[int, float], 
                          mean: float, std_dev: float) -> float:
        """Calculate kurtosis of a probability distribution."""
        if std_dev == 0:
            return 0.0
        
        kurtosis = 0.0
        for value, prob in distribution.items():
            kurtosis += prob * ((value - mean) / std_dev) ** 4
        return kurtosis - 3.0  # Excess kurtosis
    
    @classmethod
    def get_extended_statistics(cls, expression: DiceExpression) -> Dict:
        """
        Get extended statistical information for a dice expression.
        
        Args:
            expression: The dice expression to analyze
            
        Returns:
            Dictionary with extended statistics
        """
        distribution = cls.calculate_distribution(expression)
        mean = expression.average_value
        std_dev = cls.calculate_standard_deviation(distribution, mean)
        
        percentiles = cls.calculate_percentiles(distribution, 
                                               [0.05, 0.25, 0.5, 0.75, 0.95])
        
        return {
            "mean": mean,
            "median": percentiles.get(0.5, mean),
            "mode": max(distribution.items(), key=lambda x: x[1])[0],
            "variance": cls.calculate_variance(distribution, mean),
            "standard_deviation": std_dev,
            "skewness": cls.calculate_skewness(distribution, mean, std_dev),
            "kurtosis": cls.calculate_kurtosis(distribution, mean, std_dev),
            "percentiles": percentiles,
            "min_value": expression.min_value,
            "max_value": expression.max_value,
            "range": expression.max_value - expression.min_value,
            "coefficient_of_variation": std_dev / mean if mean != 0 else 0.0,
        }


class SessionAnalyzer:
    """Analyze actual roll sessions."""
    
    @staticmethod
    def analyze_session(session: RollSession) -> Dict:
        """
        Analyze a roll session and provide statistics.
        
        Args:
            session: The roll session to analyze
            
        Returns:
            Dictionary with session analysis
        """
        if not session.rolls:
            return {}
        
        totals = session.roll_totals
        
        # Basic statistics
        total_count = len(totals)
        mean = sum(totals) / total_count
        sorted_totals = sorted(totals)
        
        # Median
        if total_count % 2 == 0:
            median = (sorted_totals[total_count // 2 - 1] + 
                     sorted_totals[total_count // 2]) / 2
        else:
            median = sorted_totals[total_count // 2]
        
        # Mode
        counter = Counter(totals)
        mode_count = max(counter.values())
        modes = [value for value, count in counter.items() if count == mode_count]
        
        # Variance and standard deviation
        variance = sum((x - mean) ** 2 for x in totals) / total_count
        std_dev = math.sqrt(variance)
        
        # Percentiles
        percentiles = {}
        for p in [0.05, 0.25, 0.5, 0.75, 0.95]:
            index = int(p * (total_count - 1))
            percentiles[p] = sorted_totals[index]
        
        return {
            "total_rolls": total_count,
            "mean": mean,
            "median": median,
            "modes": modes,
            "variance": variance,
            "standard_deviation": std_dev,
            "min_value": min(totals),
            "max_value": max(totals),
            "range": max(totals) - min(totals),
            "percentiles": percentiles,
            "distribution": dict(counter),
            "theoretical_mean": session.expression.average_value,
            "mean_deviation": abs(mean - session.expression.average_value),
        }
    
    @staticmethod
    def compare_to_theoretical(session: RollSession) -> Dict:
        """
        Compare a session's results to theoretical expectations.
        
        Args:
            session: The roll session to compare
            
        Returns:
            Dictionary with comparison results
        """
        if not session.rolls:
            return {}
        
        # Get theoretical distribution
        theoretical = DiceStatistics.calculate_distribution(session.expression)
        
        # Get actual distribution
        actual_counts = Counter(session.roll_totals)
        total_rolls = len(session.rolls)
        actual_probs = {value: count / total_rolls 
                       for value, count in actual_counts.items()}
        
        # Chi-square test preparation
        chi_square = 0.0
        for value in theoretical:
            expected = theoretical[value] * total_rolls
            observed = actual_counts.get(value, 0)
            if expected > 0:
                chi_square += (observed - expected) ** 2 / expected
        
        return {
            "theoretical_distribution": theoretical,
            "actual_distribution": actual_probs,
            "chi_square": chi_square,
            "total_rolls": total_rolls,
            "theoretical_mean": session.expression.average_value,
            "actual_mean": session.average_total,
            "mean_difference": abs(session.average_total - session.expression.average_value),
            "values_with_zero_probability": [
                value for value in actual_counts 
                if value not in theoretical
            ],
        }