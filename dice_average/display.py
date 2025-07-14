"""Display and formatting utilities for the dice average calculator."""

import json
from typing import Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .models import RollResult, DiceExpression
from .parser import DiceParseError

console = Console()


def handle_parse_error(expression: str, error: DiceParseError) -> None:
    """Handle dice parsing errors with helpful messages."""
    console.print(f"[red]Error parsing dice expression:[/red] {expression}")
    console.print(f"[red]{error}[/red]")
    console.print("\n[yellow]Supported formats:[/yellow]")
    
    examples = [
        "d6", "3d6", "2d20+5", "1d8+2d6", "4d6-2", "d20 + 3"
    ]
    
    for example in examples:
        console.print(f"  • {example}")


def format_roll_result(roll: RollResult, expression: DiceExpression, verbose: bool = False, 
                      show_stats: bool = True) -> None:
    """Format and display roll results."""
    _format_single_roll(roll, expression, verbose)


def _format_single_roll(roll: RollResult, expression: DiceExpression, verbose: bool) -> None:
    """Format output for a single roll."""
    console.print(f"\n[bold green]Rolling {expression}[/bold green]")
    
    if verbose:
        _show_roll_breakdown(roll, expression)
    
    console.print(f"[bold blue]Result: {roll.total}[/bold blue]")
    console.print(f"[dim]Theoretical Average: {expression.average_value:.2f}[/dim]")




def _show_roll_breakdown(roll, expression: DiceExpression) -> None:
    """Show detailed breakdown of individual dice rolls."""
    for i, group_rolls in enumerate(roll.individual_rolls):
        group = expression.dice_groups[i]
        rolls_str = " + ".join(str(r) for r in group_rolls)
        console.print(f"  {group.count}d{group.die.sides}: [{rolls_str}] = {sum(group_rolls)}")
    
    if roll.modifier != 0:
        console.print(f"  Modifier: {roll.modifier:+d}")














def format_expression_info(expression: str, info_data: Dict[str, Any]) -> None:
    """Format and display expression information."""
    console.print(f"\n[bold green]Expression Info: {expression}[/bold green]")
    
    info_table = Table()
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="magenta")
    
    info_table.add_row("Parsed Expression", info_data["expression"])
    info_table.add_row("Dice Groups", str(info_data["dice_groups"]))
    info_table.add_row("Total Dice", str(info_data["total_dice"]))
    info_table.add_row("Modifier", str(info_data["modifier"]))
    info_table.add_row("Min Value", str(info_data["min_value"]))
    info_table.add_row("Max Value", str(info_data["max_value"]))
    info_table.add_row("Average Value", f"{info_data['average_value']:.2f}")
    
    console.print(info_table)
    
    if info_data["dice_types"]:
        _show_dice_breakdown(info_data["dice_types"])


def _show_dice_breakdown(dice_types) -> None:
    """Display dice breakdown table."""
    dice_table = Table(title="Dice Breakdown")
    dice_table.add_column("Count", style="cyan")
    dice_table.add_column("Sides", style="magenta")
    dice_table.add_column("Min", style="yellow")
    dice_table.add_column("Max", style="green")
    dice_table.add_column("Average", style="blue")
    
    for dice_type in dice_types:
        dice_table.add_row(
            str(dice_type["count"]),
            str(dice_type["sides"]),
            str(dice_type["min"]),
            str(dice_type["max"]),
            f"{dice_type['average']:.2f}",
        )
    
    console.print(dice_table)


def format_config_display(current_config, config_info) -> None:
    """Format and display configuration information."""
    console.print("[bold green]Current Configuration[/bold green]")
    
    config_table = Table()
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="magenta")
    
    config_table.add_row("Default Iterations", str(current_config.default_iterations))
    config_table.add_row("Default Seed", str(current_config.default_seed))
    config_table.add_row("Output Format", current_config.output_format.value)
    config_table.add_row("Verbose", str(current_config.verbose))
    config_table.add_row("Show Stats", str(current_config.show_stats))
    config_table.add_row("History Limit", str(current_config.history_limit))
    
    console.print(config_table)
    
    console.print(f"\n[bold blue]Configuration Files[/bold blue]")
    console.print(f"Config Dir: {config_info['config_dir']}")
    console.print(f"Config File: {config_info['config_file']} ({'exists' if config_info['config_exists'] else 'missing'})")
    console.print(f"History File: {config_info['history_file']} ({'exists' if config_info['history_exists'] else 'missing'})")




def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_json(data: Dict[str, Any]) -> None:
    """Print JSON data with proper formatting."""
    console.print(json.dumps(data, indent=2))