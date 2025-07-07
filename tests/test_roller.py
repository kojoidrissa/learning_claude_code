"""Tests for dice rolling functionality."""

import pytest

from dice_average.roller import DiceRoller, roll_dice, roll_dice_once, DiceSimulator
from dice_average.models import Die, DiceGroup, DiceExpression, RollResult, RollSession
from dice_average.parser import parse_dice_expression


class TestDiceRoller:
    """Test dice roller functionality."""
    
    def test_roller_creation(self):
        """Test creating a dice roller."""
        roller = DiceRoller()
        assert roller.seed is None
        
        roller_with_seed = DiceRoller(seed=42)
        assert roller_with_seed.seed == 42
    
    def test_single_roll(self):
        """Test rolling a single die."""
        die = Die(sides=6)
        group = DiceGroup(count=1, die=die)
        expr = DiceExpression(dice_groups=[group])
        
        roller = DiceRoller(seed=42)
        result = roller.roll_single(expr)
        
        assert isinstance(result, RollResult)
        assert result.expression == expr
        assert len(result.individual_rolls) == 1
        assert len(result.individual_rolls[0]) == 1
        assert 1 <= result.individual_rolls[0][0] <= 6
        assert result.total == result.individual_rolls[0][0]
    
    def test_multiple_dice_single_roll(self):
        """Test rolling multiple dice once."""
        die = Die(sides=6)
        group = DiceGroup(count=3, die=die)
        expr = DiceExpression(dice_groups=[group])
        
        roller = DiceRoller(seed=42)
        result = roller.roll_single(expr)
        
        assert len(result.individual_rolls) == 1
        assert len(result.individual_rolls[0]) == 3
        assert all(1 <= roll <= 6 for roll in result.individual_rolls[0])
        assert result.total == sum(result.individual_rolls[0])
    
    def test_roll_with_modifier(self):
        """Test rolling with modifier."""
        die = Die(sides=6)
        group = DiceGroup(count=2, die=die)
        expr = DiceExpression(dice_groups=[group], modifier=5)
        
        roller = DiceRoller(seed=42)
        result = roller.roll_single(expr)
        
        dice_total = sum(result.individual_rolls[0])
        assert result.total == dice_total + 5
        assert result.modifier == 5
    
    def test_multiple_dice_groups(self):
        """Test rolling multiple dice groups."""
        die6 = Die(sides=6)
        die8 = Die(sides=8)
        group1 = DiceGroup(count=2, die=die6)
        group2 = DiceGroup(count=1, die=die8)
        expr = DiceExpression(dice_groups=[group1, group2])
        
        roller = DiceRoller(seed=42)
        result = roller.roll_single(expr)
        
        assert len(result.individual_rolls) == 2
        assert len(result.individual_rolls[0]) == 2  # 2d6
        assert len(result.individual_rolls[1]) == 1  # 1d8
        
        expected_total = sum(result.individual_rolls[0]) + sum(result.individual_rolls[1])
        assert result.total == expected_total
    
    def test_roll_multiple(self):
        """Test rolling multiple times."""
        die = Die(sides=6)
        group = DiceGroup(count=1, die=die)
        expr = DiceExpression(dice_groups=[group])
        
        roller = DiceRoller(seed=42)
        session = roller.roll_multiple(expr, 10)
        
        assert isinstance(session, RollSession)
        assert session.expression == expr
        assert len(session.rolls) == 10
        assert session.seed == 42
        assert all(isinstance(roll, RollResult) for roll in session.rolls)
    
    def test_roll_multiple_zero_iterations(self):
        """Test rolling with zero iterations."""
        die = Die(sides=6)
        group = DiceGroup(count=1, die=die)
        expr = DiceExpression(dice_groups=[group])
        
        roller = DiceRoller()
        with pytest.raises(ValueError):
            roller.roll_multiple(expr, 0)
    
    def test_roll_with_target(self):
        """Test rolling until target is reached."""
        die = Die(sides=6)
        group = DiceGroup(count=1, die=die)
        expr = DiceExpression(dice_groups=[group])
        
        roller = DiceRoller(seed=42)
        result, attempts = roller.roll_with_target(expr, 3)
        
        assert result.total == 3
        assert attempts >= 1
        assert attempts <= 10000  # Should find it within max attempts
    
    def test_roll_with_impossible_target(self):
        """Test rolling with impossible target."""
        die = Die(sides=6)
        group = DiceGroup(count=1, die=die)
        expr = DiceExpression(dice_groups=[group])
        
        roller = DiceRoller()
        
        # Too low
        with pytest.raises(ValueError):
            roller.roll_with_target(expr, 0)
        
        # Too high
        with pytest.raises(ValueError):
            roller.roll_with_target(expr, 7)
    
    def test_set_seed(self):
        """Test setting seed."""
        roller = DiceRoller()
        roller.set_seed(123)
        assert roller.seed == 123
    
    def test_reproducible_results(self):
        """Test that same seed produces same results."""
        die = Die(sides=6)
        group = DiceGroup(count=1, die=die)
        expr = DiceExpression(dice_groups=[group])
        
        roller1 = DiceRoller(seed=42)
        roller2 = DiceRoller(seed=42)
        
        result1 = roller1.roll_single(expr)
        result2 = roller2.roll_single(expr)
        
        assert result1.total == result2.total
        assert result1.individual_rolls == result2.individual_rolls


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_roll_dice(self):
        """Test roll_dice convenience function."""
        expr = parse_dice_expression("3d6")
        session = roll_dice(expr, 5, seed=42)
        
        assert isinstance(session, RollSession)
        assert len(session.rolls) == 5
        assert session.seed == 42
    
    def test_roll_dice_once(self):
        """Test roll_dice_once convenience function."""
        expr = parse_dice_expression("2d8+3")
        result = roll_dice_once(expr, seed=42)
        
        assert isinstance(result, RollResult)
        assert result.expression == expr
        assert result.modifier == 3


class TestDiceSimulator:
    """Test dice simulator functionality."""
    
    def test_simulator_creation(self):
        """Test creating a dice simulator."""
        simulator = DiceSimulator()
        assert simulator.roller is not None
        
        simulator_with_seed = DiceSimulator(seed=42)
        assert simulator_with_seed.roller.seed == 42
    
    def test_simulate_outcomes(self):
        """Test simulating many outcomes."""
        expr = parse_dice_expression("d6")
        simulator = DiceSimulator(seed=42)
        
        outcomes = simulator.simulate_outcomes(expr, 1000)
        
        assert isinstance(outcomes, dict)
        assert all(1 <= value <= 6 for value in outcomes.keys())
        assert sum(outcomes.values()) == 1000
        
        # Each outcome should appear roughly equally
        for value in range(1, 7):
            assert value in outcomes
            assert 100 <= outcomes[value] <= 300  # Rough bounds
    
    def test_find_probability_empirical(self):
        """Test finding empirical probability."""
        expr = parse_dice_expression("d6")
        simulator = DiceSimulator(seed=42)
        
        # Test valid target
        prob = simulator.find_probability_empirical(expr, 3, 1000)
        assert 0.0 <= prob <= 1.0
        assert 0.1 <= prob <= 0.25  # Should be around 1/6
        
        # Test impossible target
        prob_impossible = simulator.find_probability_empirical(expr, 10, 1000)
        assert prob_impossible == 0.0
    
    def test_compare_expressions(self):
        """Test comparing two expressions."""
        expr1 = parse_dice_expression("d6")
        expr2 = parse_dice_expression("d8")
        simulator = DiceSimulator(seed=42)
        
        comparison = simulator.compare_expressions(expr1, expr2, 1000)
        
        assert comparison["expression1"] == "1d6"
        assert comparison["expression2"] == "1d8"
        assert comparison["iterations"] == 1000
        assert comparison["expr1_wins"] + comparison["expr2_wins"] + comparison["ties"] == 1000
        assert 0.0 <= comparison["expr1_win_rate"] <= 1.0
        assert 0.0 <= comparison["expr2_win_rate"] <= 1.0
        assert 0.0 <= comparison["tie_rate"] <= 1.0
        
        # d8 should win more often than d6
        assert comparison["expr2_win_rate"] > comparison["expr1_win_rate"]
        assert comparison["expr2_avg"] > comparison["expr1_avg"]
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Test with very small number of iterations
        expr = parse_dice_expression("d6")
        simulator = DiceSimulator(seed=42)
        
        outcomes = simulator.simulate_outcomes(expr, 1)
        assert sum(outcomes.values()) == 1
        
        # Test with expression that always gives same result
        expr = parse_dice_expression("d1")  # Always rolls 1
        outcomes = simulator.simulate_outcomes(expr, 100)
        assert outcomes == {1: 100}