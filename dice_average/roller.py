"""Dice rolling logic and utilities."""

import random
from typing import List, Optional, Tuple

from .models import DiceExpression, RollResult


class DiceRoller:
    """Handles dice rolling operations."""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the dice roller.
        
        Args:
            seed: Random seed for reproducible results
        """
        self.seed = seed
        self.random = random.Random(seed)
    
    def roll_single(self, expression: DiceExpression) -> RollResult:
        """
        Roll a dice expression once.
        
        Args:
            expression: The dice expression to roll
            
        Returns:
            RollResult with the outcome
        """
        individual_rolls = []
        
        for group in expression.dice_groups:
            group_rolls = []
            for _ in range(group.count):
                roll = self.random.randint(1, group.die.sides)
                group_rolls.append(roll)
            individual_rolls.append(group_rolls)
        
        # Calculate total
        total = sum(sum(rolls) for rolls in individual_rolls) + expression.modifier
        
        return RollResult(
            expression=expression,
            individual_rolls=individual_rolls,
            modifier=expression.modifier,
            total=total
        )
    
    def roll_multiple(self, expression: DiceExpression, iterations: int) -> List[RollResult]:
        """
        Roll a dice expression multiple times.
        
        Args:
            expression: The dice expression to roll
            iterations: Number of times to roll
            
        Returns:
            List of RollResult objects
        """
        if iterations <= 0:
            raise ValueError("Iterations must be positive")
        
        rolls = []
        for _ in range(iterations):
            roll = self.roll_single(expression)
            rolls.append(roll)
        
        return rolls
    
    def roll_with_target(self, expression: DiceExpression, target: int, 
                        max_attempts: int = 10000) -> Tuple[RollResult, int]:
        """
        Roll until a target value is reached.
        
        Args:
            expression: The dice expression to roll
            target: Target value to reach
            max_attempts: Maximum number of attempts
            
        Returns:
            Tuple of (RollResult, attempts_count)
            
        Raises:
            ValueError: If target is impossible or max attempts exceeded
        """
        if target < expression.min_value or target > expression.max_value:
            raise ValueError(f"Target {target} is impossible for expression {expression}")
        
        for attempt in range(1, max_attempts + 1):
            roll = self.roll_single(expression)
            if roll.total == target:
                return roll, attempt
        
        raise ValueError(f"Could not reach target {target} in {max_attempts} attempts")
    
    def set_seed(self, seed: Optional[int]) -> None:
        """Set a new random seed."""
        self.seed = seed
        self.random = random.Random(seed)


def roll_dice(expression: DiceExpression, iterations: int = 1, 
              seed: Optional[int] = None) -> List[RollResult]:
    """
    Convenience function to roll dice.
    
    Args:
        expression: The dice expression to roll
        iterations: Number of times to roll
        seed: Random seed for reproducible results
        
    Returns:
        List of RollResult objects
    """
    roller = DiceRoller(seed=seed)
    return roller.roll_multiple(expression, iterations)


def roll_dice_once(expression: DiceExpression, 
                   seed: Optional[int] = None) -> RollResult:
    """
    Convenience function to roll dice once.
    
    Args:
        expression: The dice expression to roll
        seed: Random seed for reproducible results
        
    Returns:
        RollResult with the outcome
    """
    roller = DiceRoller(seed=seed)
    return roller.roll_single(expression)


class DiceSimulator:
    """Advanced dice simulation utilities."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the simulator."""
        self.roller = DiceRoller(seed=seed)
    
    def simulate_outcomes(self, expression: DiceExpression, 
                         iterations: int = 10000) -> dict[int, int]:
        """
        Simulate many rolls and count outcomes.
        
        Args:
            expression: The dice expression to simulate
            iterations: Number of simulations to run
            
        Returns:
            Dictionary mapping outcomes to their counts
        """
        outcomes = {}
        
        for _ in range(iterations):
            roll = self.roller.roll_single(expression)
            outcomes[roll.total] = outcomes.get(roll.total, 0) + 1
        
        return outcomes
    
    def find_probability_empirical(self, expression: DiceExpression, 
                                  target: int, iterations: int = 10000) -> float:
        """
        Find empirical probability of rolling a specific value.
        
        Args:
            expression: The dice expression to test
            target: Target value
            iterations: Number of simulations
            
        Returns:
            Empirical probability (0.0 to 1.0)
        """
        if target < expression.min_value or target > expression.max_value:
            return 0.0
        
        hits = 0
        for _ in range(iterations):
            roll = self.roller.roll_single(expression)
            if roll.total == target:
                hits += 1
        
        return hits / iterations
    
    def compare_expressions(self, expr1: DiceExpression, expr2: DiceExpression,
                           iterations: int = 10000) -> dict:
        """
        Compare two dice expressions by simulation.
        
        Args:
            expr1: First expression
            expr2: Second expression
            iterations: Number of simulations
            
        Returns:
            Dictionary with comparison results
        """
        rolls1 = self.roller.roll_multiple(expr1, iterations)
        rolls2 = self.roller.roll_multiple(expr2, iterations)
        
        expr1_wins = sum(1 for r1, r2 in zip(rolls1, rolls2) 
                        if r1.total > r2.total)
        expr2_wins = sum(1 for r1, r2 in zip(rolls1, rolls2) 
                        if r2.total > r1.total)
        ties = iterations - expr1_wins - expr2_wins
        
        return {
            "expression1": str(expr1),
            "expression2": str(expr2),
            "iterations": iterations,
            "expr1_wins": expr1_wins,
            "expr2_wins": expr2_wins,
            "ties": ties,
            "expr1_win_rate": expr1_wins / iterations,
            "expr2_win_rate": expr2_wins / iterations,
            "tie_rate": ties / iterations,
            "expr1_avg": sum(r.total for r in rolls1) / len(rolls1),
            "expr2_avg": sum(r.total for r in rolls2) / len(rolls2),
        }