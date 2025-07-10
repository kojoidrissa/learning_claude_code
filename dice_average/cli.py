"""Command-line interface for the dice average calculator."""

from typing import Optional, Any

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import get_config_manager, load_config_with_env
from .display import (
    format_roll_result, format_statistics, format_history,
    format_expression_info, format_config_display, format_extended_statistics,
    print_success
)
from .error_handling import handle_cli_error, safe_int_conversion, safe_bool_conversion
from .models import OutputFormat
from .parser import parse_dice_expression, get_expression_info
from .roller import roll_dice
from .statistics import DiceStatistics

app = typer.Typer(
    name="dice-average",
    help="A Python command-line dice rolling average calculator",
    add_completion=False,
)

console = Console()


@app.command()
@handle_cli_error
def roll(
    expression: str = typer.Argument(..., help="Dice expression (e.g., '3d6', '2d20+5')"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Random seed"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save to history"),
) -> None:
    """Roll dice once and show result."""
    config = load_config_with_env()
    config_manager = get_config_manager()
    
    # Apply configuration defaults
    iterations = 1  # Always single roll
    seed = seed if seed is not None else config.default_seed
    
    # Validate iterations
    if iterations <= 0:
        raise ValueError("Iterations must be a positive number")
    
    # Parse and roll dice
    dice_expr = parse_dice_expression(expression)
    session = _execute_roll(dice_expr, iterations, seed, expression)
    
    # Save to history
    if save:
        _save_session_to_history(config_manager, session)
    
    # Output results
    format_roll_result(session, verbose, False)


def _execute_roll(dice_expr: Any, iterations: int, seed: Optional[int], 
                 expression: str) -> Any:
    """Execute the dice roll with optional progress display."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Rolling {expression}...", total=None)
        session = roll_dice(dice_expr, iterations, seed)
        progress.update(task, completed=True)
        return session


def _save_session_to_history(config_manager: Any, session: Any) -> None:
    """Save session to history."""
    history = config_manager.load_history()
    history.add_session(session)
    config_manager.save_history(history)


@app.command()
@handle_cli_error
def analyze(
    expression: str = typer.Argument(..., help="Dice expression to analyze"),
    extended: bool = typer.Option(False, "--extended", "-e", help="Show extended statistics"),
) -> None:
    """Analyze dice expressions and show probability distributions."""
    dice_expr = parse_dice_expression(expression)
    stats_result = DiceStatistics.calculate_statistics(dice_expr)
    
    extended_stats = None
    if extended:
        extended_stats = DiceStatistics.get_extended_statistics(dice_expr)
    
    format_statistics(dice_expr, stats_result)
    if extended:
        format_extended_statistics(extended_stats)


@app.command()
@handle_cli_error
def history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recent sessions to show"),
    clear: bool = typer.Option(False, "--clear", "-c", help="Clear all history"),
) -> None:
    """Show or manage roll history."""
    config_manager = get_config_manager()
    history_data = config_manager.load_history()
    
    if clear:
        if typer.confirm("Are you sure you want to clear all history?"):
            config_manager.clear_history()
            print_success("History cleared.")
        return
    
    format_history(history_data, limit)


@app.command()
@handle_cli_error
def info(
    expression: str = typer.Argument(..., help="Dice expression to analyze"),
) -> None:
    """Show detailed information about a dice expression."""
    info_data = get_expression_info(expression)
    format_expression_info(expression, info_data)


@app.command()
@handle_cli_error
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    reset: bool = typer.Option(False, "--reset", "-r", help="Reset to default configuration"),
    set_key: Optional[str] = typer.Option(None, "--set", help="Set configuration key"),
    value: Optional[str] = typer.Option(None, "--value", help="Value to set"),
) -> None:
    """Manage application configuration."""
    config_manager = get_config_manager()
    
    if reset:
        if typer.confirm("Are you sure you want to reset configuration to defaults?"):
            config_manager.reset_config()
            print_success("Configuration reset to defaults.")
        return
    
    if set_key and value:
        _update_config_value(config_manager, set_key, value)
        return
    
    if show or (not set_key and not value):
        _show_current_config(config_manager)


def _update_config_value(config_manager: Any, set_key: str, value: str) -> None:
    """Update a configuration value."""
    valid_keys = [
        "default_iterations", "default_seed", "output_format",
        "verbose", "show_stats", "history_limit"
    ]
    
    if set_key not in valid_keys:
        raise ValueError(f"Invalid configuration key. Valid keys: {', '.join(valid_keys)}")
    
    # Convert value to appropriate type
    converted_value = _convert_config_value(set_key, value)
    
    config_manager.update_config(**{set_key: converted_value})
    print_success(f"Configuration updated: {set_key} = {converted_value}")


def _convert_config_value(set_key: str, value: str) -> Any:
    """Convert string value to appropriate type for configuration."""
    if set_key in ["default_iterations", "history_limit"]:
        return safe_int_conversion(value, set_key)
    elif set_key == "default_seed":
        return safe_int_conversion(value, set_key) if value != "null" else None
    elif set_key in ["verbose", "show_stats"]:
        return safe_bool_conversion(value)
    elif set_key == "output_format":
        return OutputFormat(value)
    return value


def _show_current_config(config_manager: Any) -> None:
    """Display current configuration."""
    current_config = config_manager.load_config()
    config_info = config_manager.get_config_info()
    format_config_display(current_config, config_info)


@app.command()
def version() -> None:
    """Show version information."""
    from . import __version__
    console.print(f"dice-average version {__version__}")


def main():
    """Main entry point that handles dice expressions without requiring 'roll' command."""
    import sys
    
    # If no arguments, show help for the full app
    if len(sys.argv) == 1:
        app()
        return
    
    # Check if first argument is a known subcommand
    first_arg = sys.argv[1]
    subcommands = {"analyze", "history", "info", "config", "version"}
    
    if first_arg in subcommands or first_arg.startswith('-'):
        # Run as multi-command app
        app()
    else:
        # Prepend 'roll' to the arguments and run
        sys.argv.insert(1, 'roll')
        app()


if __name__ == "__main__":
    main()