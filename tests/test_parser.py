"""Tests for dice notation parser."""

import pytest

from dice_average.parser import (
    DiceParser, DiceParseError, parse_dice_expression,
    validate_dice_expression, get_expression_info
)
from dice_average.models import Die, DiceGroup, DiceExpression


class TestDiceParser:
    """Test dice notation parser."""
    
    def test_simple_die(self):
        """Test parsing simple die notation."""
        expr = DiceParser.parse("d6")
        assert len(expr.dice_groups) == 1
        assert expr.dice_groups[0].count == 1
        assert expr.dice_groups[0].die.sides == 6
        assert expr.modifier == 0
    
    def test_multiple_dice(self):
        """Test parsing multiple dice notation."""
        expr = DiceParser.parse("3d6")
        assert len(expr.dice_groups) == 1
        assert expr.dice_groups[0].count == 3
        assert expr.dice_groups[0].die.sides == 6
        assert expr.modifier == 0
    
    def test_with_positive_modifier(self):
        """Test parsing with positive modifier."""
        expr = DiceParser.parse("2d8+5")
        assert len(expr.dice_groups) == 1
        assert expr.dice_groups[0].count == 2
        assert expr.dice_groups[0].die.sides == 8
        assert expr.modifier == 5
    
    def test_with_negative_modifier(self):
        """Test parsing with negative modifier."""
        expr = DiceParser.parse("1d20-3")
        assert len(expr.dice_groups) == 1
        assert expr.dice_groups[0].count == 1
        assert expr.dice_groups[0].die.sides == 20
        assert expr.modifier == -3
    
    def test_multiple_dice_groups(self):
        """Test parsing multiple dice groups."""
        expr = DiceParser.parse("2d6+1d8")
        assert len(expr.dice_groups) == 2
        
        # First group
        assert expr.dice_groups[0].count == 2
        assert expr.dice_groups[0].die.sides == 6
        
        # Second group
        assert expr.dice_groups[1].count == 1
        assert expr.dice_groups[1].die.sides == 8
        
        assert expr.modifier == 0
    
    def test_complex_expression(self):
        """Test parsing complex expression."""
        expr = DiceParser.parse("3d6 + 2d8 + 1d4 - 2")
        assert len(expr.dice_groups) == 3
        
        # First group: 3d6
        assert expr.dice_groups[0].count == 3
        assert expr.dice_groups[0].die.sides == 6
        
        # Second group: 2d8
        assert expr.dice_groups[1].count == 2
        assert expr.dice_groups[1].die.sides == 8
        
        # Third group: 1d4
        assert expr.dice_groups[2].count == 1
        assert expr.dice_groups[2].die.sides == 4
        
        assert expr.modifier == -2
    
    def test_whitespace_handling(self):
        """Test handling of whitespace."""
        expressions = [
            "3d6+5",
            "3d6 + 5",
            " 3d6 + 5 ",
            "3d6+  5",
            "3d6 +5",
        ]
        
        for expr_str in expressions:
            expr = DiceParser.parse(expr_str)
            assert len(expr.dice_groups) == 1
            assert expr.dice_groups[0].count == 3
            assert expr.dice_groups[0].die.sides == 6
            assert expr.modifier == 5
    
    def test_case_insensitive(self):
        """Test case insensitive parsing."""
        expressions = ["3d6", "3D6", "3d6", "3D6"]
        
        for expr_str in expressions:
            expr = DiceParser.parse(expr_str)
            assert len(expr.dice_groups) == 1
            assert expr.dice_groups[0].count == 3
            assert expr.dice_groups[0].die.sides == 6
    
    def test_multiple_modifiers(self):
        """Test parsing with multiple modifiers."""
        expr = DiceParser.parse("2d6+3-1+2")
        assert len(expr.dice_groups) == 1
        assert expr.dice_groups[0].count == 2
        assert expr.dice_groups[0].die.sides == 6
        assert expr.modifier == 4  # +3 -1 +2 = +4
    
    def test_invalid_expressions(self):
        """Test parsing invalid expressions."""
        invalid_expressions = [
            "",
            "   ",
            "3x6",  # Wrong separator
            "0d6",  # Zero count
            "3d0",  # Zero sides
            "-1d6",  # Negative count
            "3d-6",  # Negative sides
            "abc",  # No dice notation
            "3d6 + abc",  # Invalid modifier
        ]
        
        for expr_str in invalid_expressions:
            with pytest.raises(DiceParseError):
                DiceParser.parse(expr_str)
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Large numbers
        expr = DiceParser.parse("100d100+1000")
        assert expr.dice_groups[0].count == 100
        assert expr.dice_groups[0].die.sides == 100
        assert expr.modifier == 1000
        
        # Single die with modifier
        expr = DiceParser.parse("d20+10")
        assert expr.dice_groups[0].count == 1
        assert expr.dice_groups[0].die.sides == 20
        assert expr.modifier == 10
    
    def test_validation_function(self):
        """Test validation function."""
        assert DiceParser.validate_expression("3d6") is True
        assert DiceParser.validate_expression("2d8+5") is True
        assert DiceParser.validate_expression("invalid") is False
        assert DiceParser.validate_expression("") is False
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = DiceParser.get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert all(isinstance(f, str) for f in formats)


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_parse_dice_expression(self):
        """Test parse_dice_expression convenience function."""
        expr = parse_dice_expression("3d6+2")
        assert isinstance(expr, DiceExpression)
        assert len(expr.dice_groups) == 1
        assert expr.modifier == 2
    
    def test_validate_dice_expression(self):
        """Test validate_dice_expression convenience function."""
        assert validate_dice_expression("3d6") is True
        assert validate_dice_expression("invalid") is False
    
    def test_get_expression_info(self):
        """Test get_expression_info convenience function."""
        info = get_expression_info("3d6+2")
        
        assert info["expression"] == "3d6 + 2"
        assert info["dice_groups"] == 1
        assert info["total_dice"] == 3
        assert info["modifier"] == 2
        assert info["min_value"] == 5  # 3*1 + 2
        assert info["max_value"] == 20  # 3*6 + 2
        assert info["average_value"] == 12.5  # 3*3.5 + 2
        
        assert len(info["dice_types"]) == 1
        dice_type = info["dice_types"][0]
        assert dice_type["count"] == 3
        assert dice_type["sides"] == 6
        assert dice_type["min"] == 3
        assert dice_type["max"] == 18
        assert dice_type["average"] == 10.5
    
    def test_get_expression_info_complex(self):
        """Test get_expression_info with complex expression."""
        info = get_expression_info("2d6+1d8-1")
        
        assert info["dice_groups"] == 2
        assert info["total_dice"] == 3
        assert info["modifier"] == -1
        assert info["min_value"] == 2  # 2*1 + 1*1 - 1
        assert info["max_value"] == 19  # 2*6 + 1*8 - 1
        assert info["average_value"] == 10.5  # 2*3.5 + 1*4.5 - 1
        
        assert len(info["dice_types"]) == 2
        
        # First dice type (2d6)
        dice_type1 = info["dice_types"][0]
        assert dice_type1["count"] == 2
        assert dice_type1["sides"] == 6
        
        # Second dice type (1d8)
        dice_type2 = info["dice_types"][1]
        assert dice_type2["count"] == 1
        assert dice_type2["sides"] == 8