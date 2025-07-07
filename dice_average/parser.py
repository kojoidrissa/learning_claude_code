"""Parser for dice notation expressions."""

import re
from typing import List, Tuple

from .models import Die, DiceGroup, DiceExpression


class DiceParseError(Exception):
    """Exception raised when parsing dice notation fails."""
    pass


class DiceParser:
    """Parser for dice notation expressions like '3d6', '2d20+5', etc."""
    
    # Regex patterns for parsing dice notation
    DICE_PATTERN = re.compile(r'(\d*)d(\d+)', re.IGNORECASE)
    MODIFIER_PATTERN = re.compile(r'([+-])\s*(\d+)(?!d)', re.IGNORECASE)
    WHITESPACE_PATTERN = re.compile(r'\s+')
    
    @classmethod
    def parse(cls, expression: str) -> DiceExpression:
        """
        Parse a dice expression string into a DiceExpression object.
        
        Args:
            expression: String like '3d6', '2d20+5', '1d8 + 2d6 - 3', etc.
            
        Returns:
            DiceExpression object
            
        Raises:
            DiceParseError: If the expression cannot be parsed
        """
        if not expression or not expression.strip():
            raise DiceParseError("Empty expression")
        
        # Clean up the expression
        expression = cls.WHITESPACE_PATTERN.sub('', expression.strip())
        
        # Check for invalid characters early
        import string
        valid_chars = set(string.digits + 'dD+- ')
        if not set(expression).issubset(valid_chars):
            invalid_chars = set(expression) - valid_chars
            raise DiceParseError(f"Invalid characters in expression: {''.join(sorted(invalid_chars))}")
        
        # Check for negative dice count (leading minus before d)
        if re.search(r'-\d*[dD]\d+', expression):
            raise DiceParseError("Negative dice counts are not allowed")
        
        # Find all dice groups
        dice_groups = []
        dice_matches = cls.DICE_PATTERN.findall(expression)
        
        if not dice_matches:
            raise DiceParseError(f"No valid dice notation found in '{expression}'")
        
        for count_str, sides_str in dice_matches:
            try:
                count = int(count_str) if count_str else 1
                sides = int(sides_str)
                
                if count <= 0:
                    raise DiceParseError(f"Dice count must be positive, got {count}")
                if sides <= 0:
                    raise DiceParseError(f"Dice sides must be positive, got {sides}")
                
                die = Die(sides=sides)
                dice_group = DiceGroup(count=count, die=die)
                dice_groups.append(dice_group)
                
            except ValueError as e:
                raise DiceParseError(f"Invalid number in dice notation: {e}")
        
        # Parse modifier
        modifier = cls._parse_modifier(expression)
        
        return DiceExpression(dice_groups=dice_groups, modifier=modifier)
    
    @classmethod
    def _parse_modifier(cls, expression: str) -> int:
        """Parse the modifier part of a dice expression."""
        modifier = 0
        modifier_matches = cls.MODIFIER_PATTERN.findall(expression)
        
        for sign, value_str in modifier_matches:
            try:
                value = int(value_str)
                if sign == '+':
                    modifier += value
                elif sign == '-':
                    modifier -= value
            except ValueError:
                raise DiceParseError(f"Invalid modifier value: {value_str}")
        
        return modifier
    
    @classmethod
    def validate_expression(cls, expression: str) -> bool:
        """
        Validate if a dice expression is valid without parsing it.
        
        Args:
            expression: String to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            cls.parse(expression)
            return True
        except DiceParseError:
            return False
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """Get examples of supported dice notation formats."""
        return [
            "d6",           # Single six-sided die
            "3d6",          # Three six-sided dice
            "2d20+5",       # Two twenty-sided dice plus 5
            "1d8+2d6",      # One eight-sided die plus two six-sided dice
            "4d6-2",        # Four six-sided dice minus 2
            "d20 + 3",      # Twenty-sided die plus 3 (with spaces)
            "2d10 + 1d4 - 1",  # Complex expression
        ]


def parse_dice_expression(expression: str) -> DiceExpression:
    """
    Convenience function to parse a dice expression.
    
    Args:
        expression: Dice notation string
        
    Returns:
        DiceExpression object
        
    Raises:
        DiceParseError: If parsing fails
    """
    return DiceParser.parse(expression)


def validate_dice_expression(expression: str) -> bool:
    """
    Convenience function to validate a dice expression.
    
    Args:
        expression: Dice notation string
        
    Returns:
        True if valid, False otherwise
    """
    return DiceParser.validate_expression(expression)


def get_expression_info(expression: str) -> dict:
    """
    Get information about a dice expression without rolling.
    
    Args:
        expression: Dice notation string
        
    Returns:
        Dictionary with expression information
        
    Raises:
        DiceParseError: If parsing fails
    """
    dice_expr = parse_dice_expression(expression)
    
    return {
        "expression": str(dice_expr),
        "dice_groups": len(dice_expr.dice_groups),
        "total_dice": sum(group.count for group in dice_expr.dice_groups),
        "modifier": dice_expr.modifier,
        "min_value": dice_expr.min_value,
        "max_value": dice_expr.max_value,
        "average_value": dice_expr.average_value,
        "dice_types": [
            {
                "count": group.count,
                "sides": group.die.sides,
                "min": group.min_value,
                "max": group.max_value,
                "average": group.average_value,
            }
            for group in dice_expr.dice_groups
        ],
    }