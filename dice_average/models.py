"""Data models for dice rolling using Pydantic v2."""

from datetime import datetime
from typing import List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


class OutputFormat(str, Enum):
    """Output format options."""
    TEXT = "text"
    JSON = "json"
    TABLE = "table"


class Die(BaseModel):
    """Represents a single die with specified number of sides."""
    model_config = ConfigDict(frozen=True)
    
    sides: int = Field(gt=0, description="Number of sides on the die")
    
    @property
    def min_value(self) -> int:
        """Minimum possible value for this die."""
        return 1
    
    @property
    def max_value(self) -> int:
        """Maximum possible value for this die."""
        return self.sides
    
    @property
    def average_value(self) -> float:
        """Average value for this die."""
        return (self.min_value + self.max_value) / 2


class DiceGroup(BaseModel):
    """Represents a group of identical dice (e.g., 3d6)."""
    model_config = ConfigDict(frozen=True)
    
    count: int = Field(gt=0, description="Number of dice in the group")
    die: Die = Field(description="The type of die in this group")
    
    @property
    def min_value(self) -> int:
        """Minimum possible value for this dice group."""
        return self.count * self.die.min_value
    
    @property
    def max_value(self) -> int:
        """Maximum possible value for this dice group."""
        return self.count * self.die.max_value
    
    @property
    def average_value(self) -> float:
        """Average value for this dice group."""
        return self.count * self.die.average_value


class DiceExpression(BaseModel):
    """Represents a complete dice expression (e.g., 2d6 + 1d8 + 3)."""
    model_config = ConfigDict(frozen=True)
    
    dice_groups: List[DiceGroup] = Field(description="List of dice groups")
    modifier: int = Field(default=0, description="Static modifier to add")
    
    @property
    def min_value(self) -> int:
        """Minimum possible value for this expression."""
        return sum(group.min_value for group in self.dice_groups) + self.modifier
    
    @property
    def max_value(self) -> int:
        """Maximum possible value for this expression."""
        return sum(group.max_value for group in self.dice_groups) + self.modifier
    
    @property
    def average_value(self) -> float:
        """Average value for this expression."""
        return sum(group.average_value for group in self.dice_groups) + self.modifier
    
    def __str__(self) -> str:
        """String representation of the dice expression."""
        parts = []
        for group in self.dice_groups:
            parts.append(f"{group.count}d{group.die.sides}")
        
        result = " + ".join(parts)
        if self.modifier > 0:
            result += f" + {self.modifier}"
        elif self.modifier < 0:
            result += f" - {abs(self.modifier)}"
        
        return result


class RollResult(BaseModel):
    """Result of a single dice roll."""
    model_config = ConfigDict()
    
    expression: DiceExpression = Field(description="The dice expression that was rolled")
    individual_rolls: List[List[int]] = Field(description="Individual die results for each group")
    modifier: int = Field(description="Static modifier applied")
    total: int = Field(description="Final total value")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @property
    def group_totals(self) -> List[int]:
        """Total for each dice group."""
        return [sum(rolls) for rolls in self.individual_rolls]




class AppConfig(BaseModel):
    """Application configuration."""
    model_config = ConfigDict()
    
    default_iterations: int = Field(default=1, gt=0, description="Default number of iterations")
    default_seed: Optional[int] = Field(default=None, description="Default random seed")
    output_format: OutputFormat = Field(default=OutputFormat.TEXT, description="Default output format")
    verbose: bool = Field(default=False, description="Enable verbose output by default")
    show_stats: bool = Field(default=False, description="Show statistics by default")
    history_limit: int = Field(default=100, gt=0, description="Maximum number of sessions to keep in history")
    
    @field_validator('default_seed')
    @classmethod
    def validate_seed(cls, v):
        if v is not None and (v < 0 or v > 2**32 - 1):
            raise ValueError('Seed must be between 0 and 2^32 - 1')
        return v