"""Data models for dice rolling using Pydantic v2."""

from datetime import datetime
from typing import List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, ConfigDict


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


class RollSession(BaseModel):
    """A session of multiple rolls with the same expression."""
    model_config = ConfigDict()
    
    expression: DiceExpression = Field(description="The dice expression used")
    rolls: List[RollResult] = Field(description="All rolls in this session")
    seed: Optional[int] = Field(default=None, description="Random seed used")
    
    @property
    def total_rolls(self) -> int:
        """Total number of rolls in this session."""
        return len(self.rolls)
    
    @property
    def roll_totals(self) -> List[int]:
        """List of all roll totals."""
        return [roll.total for roll in self.rolls]
    
    @property
    def average_total(self) -> float:
        """Average of all roll totals."""
        if not self.rolls:
            return 0.0
        return sum(self.roll_totals) / len(self.roll_totals)
    
    @property
    def min_total(self) -> int:
        """Minimum roll total."""
        return min(self.roll_totals) if self.rolls else 0
    
    @property
    def max_total(self) -> int:
        """Maximum roll total."""
        return max(self.roll_totals) if self.rolls else 0


class StatisticsResult(BaseModel):
    """Statistical analysis of a dice expression."""
    model_config = ConfigDict()
    
    expression: DiceExpression = Field(description="The analyzed expression")
    theoretical_min: int = Field(description="Theoretical minimum value")
    theoretical_max: int = Field(description="Theoretical maximum value")
    theoretical_average: float = Field(description="Theoretical average value")
    probability_distribution: dict[int, float] = Field(description="Probability for each possible value")
    
    @property
    def most_likely_value(self) -> int:
        """The most likely value to be rolled."""
        if not self.probability_distribution:
            return 0
        return max(self.probability_distribution.items(), key=lambda x: x[1])[0]
    
    @property
    def median_value(self) -> float:
        """Median value of the distribution."""
        if not self.probability_distribution:
            return 0.0
        
        sorted_values = sorted(self.probability_distribution.keys())
        cumulative_prob = 0.0
        
        for value in sorted_values:
            cumulative_prob += self.probability_distribution[value]
            if cumulative_prob >= 0.5:
                return float(value)
        
        return float(sorted_values[-1])


class RollHistory(BaseModel):
    """History of all roll sessions."""
    model_config = ConfigDict()
    
    sessions: List[RollSession] = Field(default_factory=list, description="All roll sessions")
    
    def add_session(self, session: RollSession) -> None:
        """Add a new session to the history."""
        self.sessions.append(session)
    
    def get_recent_sessions(self, limit: int = 10) -> List[RollSession]:
        """Get the most recent sessions."""
        return self.sessions[-limit:]
    
    def clear_history(self) -> None:
        """Clear all history."""
        self.sessions.clear()


class AppConfig(BaseModel):
    """Application configuration."""
    model_config = ConfigDict()
    
    default_iterations: int = Field(default=1, gt=0, description="Default number of iterations")
    default_seed: Optional[int] = Field(default=None, description="Default random seed")
    output_format: OutputFormat = Field(default=OutputFormat.TEXT, description="Default output format")
    verbose: bool = Field(default=False, description="Enable verbose output by default")
    show_stats: bool = Field(default=False, description="Show statistics by default")
    history_limit: int = Field(default=100, gt=0, description="Maximum number of sessions to keep in history")
    
    @validator('default_seed')
    def validate_seed(cls, v):
        if v is not None and (v < 0 or v > 2**32 - 1):
            raise ValueError('Seed must be between 0 and 2^32 - 1')
        return v