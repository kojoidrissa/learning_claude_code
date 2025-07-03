"""Tests for statistics and probability calculations."""

import pytest
from collections import Counter

from dice_average.statistics import DiceStatistics, SessionAnalyzer
from dice_average.models import Die, DiceGroup, DiceExpression, RollResult, RollSession
from dice_average.parser import parse_dice_expression


class TestDiceStatistics:
    """Test dice statistics calculations."""
    
    def test_single_die_distribution(self):
        """Test distribution for single die."""
        distribution = DiceStatistics._single_die_distribution(6)
        
        assert len(distribution) == 6
        assert all(1 <= value <= 6 for value in distribution.keys())
        assert all(prob == 1/6 for prob in distribution.values())
        assert sum(distribution.values()) == pytest.approx(1.0)
    
    def test_convolve_distributions(self):
        """Test convolving two distributions."""
        dist1 = {1: 0.5, 2: 0.5}  # d2
        dist2 = {1: 0.5, 2: 0.5}  # d2
        
        result = DiceStatistics._convolve_distributions(dist1, dist2)
        
        expected = {
            2: 0.25,  # 1+1
            3: 0.5,   # 1+2, 2+1
            4: 0.25,  # 2+2
        }
        
        assert result == expected
        assert sum(result.values()) == pytest.approx(1.0)
    
    def test_dice_group_distribution(self):
        """Test distribution for dice group."""
        die = Die(sides=6)
        group = DiceGroup(count=2, die=die)
        
        distribution = DiceStatistics._dice_group_distribution(group)
        
        assert min(distribution.keys()) == 2  # 1+1
        assert max(distribution.keys()) == 12  # 6+6
        assert sum(distribution.values()) == pytest.approx(1.0)
        
        # 7 should be the most likely (most ways to make it)
        assert distribution[7] == max(distribution.values())
    
    def test_calculate_distribution_simple(self):
        """Test calculating distribution for simple expression."""
        expr = parse_dice_expression("d6")
        distribution = DiceStatistics.calculate_distribution(expr)
        
        assert len(distribution) == 6
        assert all(1 <= value <= 6 for value in distribution.keys())
        assert all(prob == 1/6 for prob in distribution.values())
        assert sum(distribution.values()) == pytest.approx(1.0)
    
    def test_calculate_distribution_with_modifier(self):
        """Test calculating distribution with modifier."""
        expr = parse_dice_expression("d6+2")
        distribution = DiceStatistics.calculate_distribution(expr)
        
        assert len(distribution) == 6
        assert all(3 <= value <= 8 for value in distribution.keys())
        assert all(prob == 1/6 for prob in distribution.values())
        assert sum(distribution.values()) == pytest.approx(1.0)
    
    def test_calculate_distribution_multiple_dice(self):
        """Test calculating distribution for multiple dice."""
        expr = parse_dice_expression("2d6")
        distribution = DiceStatistics.calculate_distribution(expr)
        
        assert min(distribution.keys()) == 2
        assert max(distribution.keys()) == 12
        assert sum(distribution.values()) == pytest.approx(1.0)
        
        # 7 should be most likely
        assert distribution[7] == max(distribution.values())
        
        # 2 and 12 should be least likely
        assert distribution[2] == distribution[12] == min(distribution.values())
    
    def test_calculate_distribution_complex(self):
        """Test calculating distribution for complex expression."""
        expr = parse_dice_expression("2d6+1d4-1")
        distribution = DiceStatistics.calculate_distribution(expr)
        
        # Min: 2*1 + 1*1 - 1 = 2
        # Max: 2*6 + 1*4 - 1 = 15
        assert min(distribution.keys()) == 2
        assert max(distribution.keys()) == 15
        assert sum(distribution.values()) == pytest.approx(1.0)
    
    def test_calculate_statistics(self):
        """Test calculating comprehensive statistics."""
        expr = parse_dice_expression("3d6")
        stats = DiceStatistics.calculate_statistics(expr)
        
        assert stats.expression == expr
        assert stats.theoretical_min == 3
        assert stats.theoretical_max == 18
        assert stats.theoretical_average == 10.5
        assert stats.most_likely_value in [10, 11]  # Around the middle
        assert 10 <= stats.median_value <= 11
        
        # Check distribution
        assert len(stats.probability_distribution) == 16  # 3 to 18
        assert sum(stats.probability_distribution.values()) == pytest.approx(1.0)
    
    def test_calculate_percentiles(self):
        """Test calculating percentiles."""
        # Simple uniform distribution
        distribution = {1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25}
        percentiles = [0.25, 0.5, 0.75]
        
        result = DiceStatistics.calculate_percentiles(distribution, percentiles)
        
        assert 0.25 in result
        assert 0.5 in result
        assert 0.75 in result
        assert all(1 <= value <= 4 for value in result.values())
    
    def test_variance_and_std_dev(self):
        """Test variance and standard deviation calculations."""
        # Simple distribution
        distribution = {1: 0.5, 3: 0.5}  # Mean = 2
        mean = 2.0
        
        variance = DiceStatistics.calculate_variance(distribution, mean)
        std_dev = DiceStatistics.calculate_standard_deviation(distribution, mean)
        
        assert variance == 1.0  # (1-2)^2 * 0.5 + (3-2)^2 * 0.5 = 1
        assert std_dev == 1.0  # sqrt(1) = 1
    
    def test_skewness_and_kurtosis(self):
        """Test skewness and kurtosis calculations."""
        # Symmetric distribution
        distribution = {1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25}
        mean = 2.5
        std_dev = DiceStatistics.calculate_standard_deviation(distribution, mean)
        
        skewness = DiceStatistics.calculate_skewness(distribution, mean, std_dev)
        kurtosis = DiceStatistics.calculate_kurtosis(distribution, mean, std_dev)
        
        # Symmetric distribution should have skewness near 0
        assert abs(skewness) < 0.1
        
        # Uniform distribution should have negative excess kurtosis
        assert kurtosis < 0
    
    def test_get_extended_statistics(self):
        """Test getting extended statistics."""
        expr = parse_dice_expression("2d6")
        extended = DiceStatistics.get_extended_statistics(expr)
        
        required_keys = [
            "mean", "median", "mode", "variance", "standard_deviation",
            "skewness", "kurtosis", "percentiles", "min_value", "max_value",
            "range", "coefficient_of_variation"
        ]
        
        assert all(key in extended for key in required_keys)
        assert extended["mean"] == 7.0
        assert extended["min_value"] == 2
        assert extended["max_value"] == 12
        assert extended["range"] == 10
        assert extended["mode"] == 7  # Most likely value
        assert 0.05 in extended["percentiles"]
        assert 0.95 in extended["percentiles"]


class TestSessionAnalyzer:
    """Test session analysis functionality."""
    
    def test_analyze_empty_session(self):
        """Test analyzing empty session."""
        expr = parse_dice_expression("d6")
        session = RollSession(expression=expr, rolls=[])
        
        analysis = SessionAnalyzer.analyze_session(session)
        assert analysis == {}
    
    def test_analyze_session_basic(self):
        """Test basic session analysis."""
        expr = parse_dice_expression("d6")
        
        # Create some rolls
        rolls = [
            RollResult(expression=expr, individual_rolls=[[1]], modifier=0, total=1),
            RollResult(expression=expr, individual_rolls=[[3]], modifier=0, total=3),
            RollResult(expression=expr, individual_rolls=[[6]], modifier=0, total=6),
            RollResult(expression=expr, individual_rolls=[[3]], modifier=0, total=3),
            RollResult(expression=expr, individual_rolls=[[5]], modifier=0, total=5),
        ]
        
        session = RollSession(expression=expr, rolls=rolls)
        analysis = SessionAnalyzer.analyze_session(session)
        
        assert analysis["total_rolls"] == 5
        assert analysis["mean"] == 3.6  # (1+3+6+3+5)/5
        assert analysis["median"] == 3.0
        assert analysis["modes"] == [3]  # 3 appears twice
        assert analysis["min_value"] == 1
        assert analysis["max_value"] == 6
        assert analysis["range"] == 5
        assert analysis["theoretical_mean"] == 3.5
        assert abs(analysis["mean_deviation"] - 0.1) < 0.01  # |3.6 - 3.5|
    
    def test_analyze_session_percentiles(self):
        """Test session analysis percentiles."""
        expr = parse_dice_expression("d6")
        
        # Create 10 rolls with known values
        rolls = []
        for i in range(1, 11):  # Values 1-10, but d6 only goes to 6
            value = min(i, 6)
            rolls.append(RollResult(expression=expr, individual_rolls=[[value]], modifier=0, total=value))
        
        session = RollSession(expression=expr, rolls=rolls)
        analysis = SessionAnalyzer.analyze_session(session)
        
        assert "percentiles" in analysis
        assert 0.05 in analysis["percentiles"]
        assert 0.95 in analysis["percentiles"]
        assert analysis["percentiles"][0.05] <= analysis["percentiles"][0.95]
    
    def test_analyze_session_distribution(self):
        """Test session analysis distribution."""
        expr = parse_dice_expression("d6")
        
        # Create rolls with known distribution
        rolls = []
        for value in [1, 2, 2, 3, 3, 3]:
            rolls.append(RollResult(expression=expr, individual_rolls=[[value]], modifier=0, total=value))
        
        session = RollSession(expression=expr, rolls=rolls)
        analysis = SessionAnalyzer.analyze_session(session)
        
        expected_distribution = {1: 1, 2: 2, 3: 3}
        assert analysis["distribution"] == expected_distribution
    
    def test_compare_to_theoretical(self):
        """Test comparing session to theoretical expectations."""
        expr = parse_dice_expression("d6")
        
        # Create a session with known results
        rolls = []
        for value in [1, 2, 3, 4, 5, 6] * 10:  # 10 of each value
            rolls.append(RollResult(expression=expr, individual_rolls=[[value]], modifier=0, total=value))
        
        session = RollSession(expression=expr, rolls=rolls)
        comparison = SessionAnalyzer.compare_to_theoretical(session)
        
        assert "theoretical_distribution" in comparison
        assert "actual_distribution" in comparison
        assert "chi_square" in comparison
        assert "total_rolls" in comparison
        assert "theoretical_mean" in comparison
        assert "actual_mean" in comparison
        assert "mean_difference" in comparison
        assert "values_with_zero_probability" in comparison
        
        # Perfect uniform distribution should have low chi-square
        assert comparison["chi_square"] < 1.0
        
        # Mean should be close to theoretical
        assert abs(comparison["actual_mean"] - comparison["theoretical_mean"]) < 0.1
        
        # No impossible values
        assert comparison["values_with_zero_probability"] == []
    
    def test_compare_with_impossible_values(self):
        """Test comparison with impossible values."""
        expr = parse_dice_expression("d6")
        
        # Create rolls including impossible values (manually constructed)
        rolls = [
            RollResult(expression=expr, individual_rolls=[[3]], modifier=0, total=3),
            RollResult(expression=expr, individual_rolls=[[7]], modifier=0, total=7),  # Impossible!
        ]
        
        session = RollSession(expression=expr, rolls=rolls)
        comparison = SessionAnalyzer.compare_to_theoretical(session)
        
        # Should detect impossible value
        assert 7 in comparison["values_with_zero_probability"]
    
    def test_edge_cases(self):
        """Test edge cases in session analysis."""
        expr = parse_dice_expression("d6")
        
        # Single roll
        single_roll = [RollResult(expression=expr, individual_rolls=[[4]], modifier=0, total=4)]
        session = RollSession(expression=expr, rolls=single_roll)
        
        analysis = SessionAnalyzer.analyze_session(session)
        assert analysis["total_rolls"] == 1
        assert analysis["mean"] == 4.0
        assert analysis["median"] == 4.0
        assert analysis["variance"] == 0.0
        assert analysis["standard_deviation"] == 0.0
        
        # All same value
        same_rolls = [RollResult(expression=expr, individual_rolls=[[3]], modifier=0, total=3) for _ in range(5)]
        session = RollSession(expression=expr, rolls=same_rolls)
        
        analysis = SessionAnalyzer.analyze_session(session)
        assert analysis["mean"] == 3.0
        assert analysis["variance"] == 0.0
        assert analysis["standard_deviation"] == 0.0
        assert analysis["modes"] == [3]