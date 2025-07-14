"""Tests for data models."""

import pytest
from datetime import datetime

from dice_average.models import (
    Die, DiceGroup, DiceExpression, RollResult, AppConfig, OutputFormat
)


class TestDie:
    """Test Die model."""
    
    def test_die_creation(self):
        """Test creating a die."""
        die = Die(sides=6)
        assert die.sides == 6
        assert die.min_value == 1
        assert die.max_value == 6
        assert die.average_value == 3.5
    
    def test_die_validation(self):
        """Test die validation."""
        with pytest.raises(ValueError):
            Die(sides=0)
        with pytest.raises(ValueError):
            Die(sides=-1)
    
    def test_die_immutable(self):
        """Test that die is immutable."""
        from pydantic_core import ValidationError
        die = Die(sides=6)
        with pytest.raises(ValidationError):
            die.sides = 8


class TestDiceGroup:
    """Test DiceGroup model."""
    
    def test_dice_group_creation(self):
        """Test creating a dice group."""
        die = Die(sides=6)
        group = DiceGroup(count=3, die=die)
        assert group.count == 3
        assert group.die.sides == 6
        assert group.min_value == 3
        assert group.max_value == 18
        assert group.average_value == 10.5
    
    def test_dice_group_validation(self):
        """Test dice group validation."""
        die = Die(sides=6)
        with pytest.raises(ValueError):
            DiceGroup(count=0, die=die)
        with pytest.raises(ValueError):
            DiceGroup(count=-1, die=die)


class TestDiceExpression:
    """Test DiceExpression model."""
    
    def test_simple_expression(self):
        """Test simple dice expression."""
        die = Die(sides=6)
        group = DiceGroup(count=3, die=die)
        expr = DiceExpression(dice_groups=[group])
        
        assert expr.min_value == 3
        assert expr.max_value == 18
        assert expr.average_value == 10.5
        assert "3d6" in str(expr)
    
    def test_expression_with_modifier(self):
        """Test expression with modifier."""
        die = Die(sides=6)
        group = DiceGroup(count=2, die=die)
        expr = DiceExpression(dice_groups=[group], modifier=5)
        
        assert expr.min_value == 7
        assert expr.max_value == 17
        assert expr.average_value == 12.0
        assert "2d6" in str(expr)
        assert "+5" in str(expr) or "+ 5" in str(expr)
    
    def test_complex_expression(self):
        """Test complex expression with multiple dice groups."""
        die6 = Die(sides=6)
        die8 = Die(sides=8)
        group1 = DiceGroup(count=2, die=die6)
        group2 = DiceGroup(count=1, die=die8)
        expr = DiceExpression(dice_groups=[group1, group2], modifier=-1)
        
        assert expr.min_value == 2  # 2 + 1 - 1
        assert expr.max_value == 19  # 12 + 8 - 1
        assert expr.average_value == 10.5  # 7 + 4.5 - 1


class TestRollResult:
    """Test RollResult model."""
    
    def test_roll_result_creation(self):
        """Test creating a roll result."""
        die = Die(sides=6)
        group = DiceGroup(count=2, die=die)
        expr = DiceExpression(dice_groups=[group])
        
        roll = RollResult(
            expression=expr,
            individual_rolls=[[3, 5]],
            modifier=0,
            total=8
        )
        
        assert roll.total == 8
        assert roll.group_totals == [8]
        assert isinstance(roll.timestamp, datetime)
    
    def test_roll_result_with_modifier(self):
        """Test roll result with modifier."""
        die = Die(sides=6)
        group = DiceGroup(count=1, die=die)
        expr = DiceExpression(dice_groups=[group], modifier=3)
        
        roll = RollResult(
            expression=expr,
            individual_rolls=[[4]],
            modifier=3,
            total=7
        )
        
        assert roll.total == 7
        assert roll.modifier == 3








class TestAppConfig:
    """Test AppConfig model."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = AppConfig()
        
        assert config.default_iterations == 1
        assert config.default_seed is None
        assert config.output_format == OutputFormat.TEXT
        assert config.verbose is False
        assert config.show_stats is False
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = AppConfig(
            default_iterations=50,
            default_seed=12345,
            output_format=OutputFormat.JSON,
            verbose=True,
            show_stats=False,
        )
        
        assert config.default_iterations == 50
        assert config.default_seed == 12345
        assert config.output_format == OutputFormat.JSON
        assert config.verbose is True
        assert config.show_stats is False
        
        # Invalid iterations
        with pytest.raises(ValueError):
            AppConfig(default_iterations=0)
        
        
        # Invalid seed
        with pytest.raises(ValueError):
            AppConfig(default_seed=-1)
        
        with pytest.raises(ValueError):
            AppConfig(default_seed=2**32)