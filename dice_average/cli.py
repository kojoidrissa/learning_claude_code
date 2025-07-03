"""Command-line interface for the dice average calculator."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import get_config_manager, load_config_with_env
from .models import OutputFormat, RollSession
from .parser import parse_dice_expression, DiceParseError, get_expression_info
from .roller import roll_dice, DiceSimulator
from .statistics import DiceStatistics, SessionAnalyzer

app = typer.Typer(
    name="dice-average",
    help="A Python command-line dice rolling average calculator",
    add_completion=False,
)

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


def format_roll_result(session: RollSession, verbose: bool = False, 
                      show_stats: bool = True) -> None:
    """Format and display roll results."""
    if len(session.rolls) == 1:
        # Single roll
        roll = session.rolls[0]
        console.print(f"\n[bold green]Rolling {session.expression}[/bold green]")
        
        if verbose:
            for i, group_rolls in enumerate(roll.individual_rolls):
                group = session.expression.dice_groups[i]
                rolls_str = " + ".join(str(r) for r in group_rolls)
                console.print(f"  {group.count}d{group.die.sides}: [{rolls_str}] = {sum(group_rolls)}")
            
            if roll.modifier != 0:
                console.print(f"  Modifier: {roll.modifier:+d}")
        
        console.print(f"[bold blue]Result: {roll.total}[/bold blue]")
    
    else:
        # Multiple rolls
        console.print(f"\n[bold green]Rolling {session.expression} × {len(session.rolls)}[/bold green]")
        
        if verbose and len(session.rolls) <= 20:
            for i, roll in enumerate(session.rolls, 1):
                console.print(f"  Roll {i}: {roll.total}")
        elif verbose:
            console.print(f"  Results: {', '.join(str(r.total) for r in session.rolls[:10])}...")
        
        if show_stats:
            stats = SessionAnalyzer.analyze_session(session)
            
            table = Table(title="Roll Statistics")
            table.add_column("Statistic", style="cyan")
            table.add_column("Value", style="magenta")
            
            table.add_row("Total Rolls", str(stats["total_rolls"]))
            table.add_row("Average", f"{stats['mean']:.2f}")
            table.add_row("Median", f"{stats['median']:.2f}")
            table.add_row("Min", str(stats["min_value"]))
            table.add_row("Max", str(stats["max_value"]))
            table.add_row("Std Dev", f"{stats['standard_deviation']:.2f}")
            table.add_row("Theoretical Avg", f"{stats['theoretical_mean']:.2f}")
            
            console.print(table)


def format_statistics(expression, stats_result) -> None:
    """Format and display statistical analysis."""
    console.print(f"\n[bold green]Statistical Analysis: {expression}[/bold green]")
    
    # Basic info table
    basic_table = Table(title="Basic Statistics")
    basic_table.add_column("Property", style="cyan")
    basic_table.add_column("Value", style="magenta")
    
    basic_table.add_row("Min Value", str(stats_result.theoretical_min))
    basic_table.add_row("Max Value", str(stats_result.theoretical_max))
    basic_table.add_row("Average", f"{stats_result.theoretical_average:.2f}")
    basic_table.add_row("Most Likely", str(stats_result.most_likely_value))
    basic_table.add_row("Median", f"{stats_result.median_value:.2f}")
    
    console.print(basic_table)
    
    # Probability distribution (top 10 most likely)
    sorted_probs = sorted(stats_result.probability_distribution.items(), 
                         key=lambda x: x[1], reverse=True)[:10]
    
    if sorted_probs:
        prob_table = Table(title="Top 10 Most Likely Values")
        prob_table.add_column("Value", style="cyan")
        prob_table.add_column("Probability", style="magenta")
        prob_table.add_column("Percentage", style="yellow")
        
        for value, prob in sorted_probs:
            prob_table.add_row(
                str(value), 
                f"{prob:.4f}", 
                f"{prob * 100:.2f}%"
            )
        
        console.print(prob_table)


def format_history(history, limit: int = 10) -> None:
    """Format and display roll history."""
    if not history.sessions:
        console.print("[yellow]No roll history found.[/yellow]")
        return
    
    recent_sessions = history.get_recent_sessions(limit)
    
    console.print(f"\n[bold green]Recent Roll History[/bold green] (last {len(recent_sessions)} sessions)")
    
    history_table = Table()
    history_table.add_column("Expression", style="cyan")
    history_table.add_column("Rolls", style="magenta")
    history_table.add_column("Average", style="yellow")
    history_table.add_column("Range", style="green")
    
    for session in recent_sessions:
        if session.rolls:
            min_val = min(r.total for r in session.rolls)
            max_val = max(r.total for r in session.rolls)
            range_str = f"{min_val}-{max_val}"
        else:
            range_str = "N/A"
        
        history_table.add_row(
            str(session.expression),
            str(len(session.rolls)),
            f"{session.average_total:.2f}",
            range_str
        )
    
    console.print(history_table)


@app.command()
def roll(
    expression: str = typer.Argument(..., help="Dice expression (e.g., '3d6', '2d20+5')"),
    iterations: int = typer.Option(None, "--iterations", "-i", help="Number of rolls"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Random seed"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    stats: bool = typer.Option(None, "--stats/--no-stats", help="Show statistics"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save to history"),
) -> None:
    """Roll dice and calculate averages."""
    try:
        # Load configuration
        config = load_config_with_env()
        config_manager = get_config_manager()
        
        # Apply defaults
        if iterations is None:
            iterations = config.default_iterations
        if seed is None:
            seed = config.default_seed
        if stats is None:
            stats = config.show_stats
        
        # Parse expression
        dice_expr = parse_dice_expression(expression)
        
        # Roll dice
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Rolling {expression}...", total=None)
            session = roll_dice(dice_expr, iterations, seed)
            progress.update(task, completed=True)
        
        # Save to history
        if save:
            history = config_manager.load_history()
            history.add_session(session)
            config_manager.save_history(history)
        
        # Output results
        if json_output:
            output_data = {
                "expression": str(dice_expr),
                "iterations": iterations,
                "seed": seed,
                "results": [roll.total for roll in session.rolls],
                "average": session.average_total,
                "min": session.min_total,
                "max": session.max_total,
            }
            
            if stats:
                analysis = SessionAnalyzer.analyze_session(session)
                output_data["statistics"] = analysis
            
            console.print(json.dumps(output_data, indent=2))
        else:
            format_roll_result(session, verbose, stats)
    
    except DiceParseError as e:
        handle_parse_error(expression, e)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def analyze(
    expression: str = typer.Argument(..., help="Dice expression to analyze"),
    extended: bool = typer.Option(False, "--extended", "-e", help="Show extended statistics"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Analyze dice expressions and show probability distributions."""
    try:
        dice_expr = parse_dice_expression(expression)
        stats_result = DiceStatistics.calculate_statistics(dice_expr)
        
        if json_output:
            output_data = {
                "expression": str(dice_expr),
                "min_value": stats_result.theoretical_min,
                "max_value": stats_result.theoretical_max,
                "average": stats_result.theoretical_average,
                "most_likely": stats_result.most_likely_value,
                "median": stats_result.median_value,
                "probability_distribution": stats_result.probability_distribution,
            }
            
            if extended:
                extended_stats = DiceStatistics.get_extended_statistics(dice_expr)
                output_data["extended_statistics"] = extended_stats
            
            console.print(json.dumps(output_data, indent=2))
        else:
            format_statistics(dice_expr, stats_result)
            
            if extended:
                extended_stats = DiceStatistics.get_extended_statistics(dice_expr)
                
                ext_table = Table(title="Extended Statistics")
                ext_table.add_column("Statistic", style="cyan")
                ext_table.add_column("Value", style="magenta")
                
                ext_table.add_row("Variance", f"{extended_stats['variance']:.4f}")
                ext_table.add_row("Std Deviation", f"{extended_stats['standard_deviation']:.4f}")
                ext_table.add_row("Skewness", f"{extended_stats['skewness']:.4f}")
                ext_table.add_row("Kurtosis", f"{extended_stats['kurtosis']:.4f}")
                ext_table.add_row("CV", f"{extended_stats['coefficient_of_variation']:.4f}")
                
                console.print(ext_table)
    
    except DiceParseError as e:
        handle_parse_error(expression, e)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recent sessions to show"),
    clear: bool = typer.Option(False, "--clear", "-c", help="Clear all history"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show or manage roll history."""
    try:
        config_manager = get_config_manager()
        history_data = config_manager.load_history()
        
        if clear:
            if typer.confirm("Are you sure you want to clear all history?"):
                config_manager.clear_history()
                console.print("[green]History cleared.[/green]")
            return
        
        if json_output:
            recent_sessions = history_data.get_recent_sessions(limit)
            output_data = {
                "total_sessions": len(history_data.sessions),
                "recent_sessions": [
                    {
                        "expression": str(session.expression),
                        "rolls": len(session.rolls),
                        "average": session.average_total,
                        "min": session.min_total,
                        "max": session.max_total,
                        "seed": session.seed,
                    }
                    for session in recent_sessions
                ],
            }
            console.print(json.dumps(output_data, indent=2))
        else:
            format_history(history_data, limit)
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def info(
    expression: str = typer.Argument(..., help="Dice expression to analyze"),
) -> None:
    """Show detailed information about a dice expression."""
    try:
        info_data = get_expression_info(expression)
        
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
        
        # Show dice types
        if info_data["dice_types"]:
            dice_table = Table(title="Dice Breakdown")
            dice_table.add_column("Count", style="cyan")
            dice_table.add_column("Sides", style="magenta")
            dice_table.add_column("Min", style="yellow")
            dice_table.add_column("Max", style="green")
            dice_table.add_column("Average", style="blue")
            
            for dice_type in info_data["dice_types"]:
                dice_table.add_row(
                    str(dice_type["count"]),
                    str(dice_type["sides"]),
                    str(dice_type["min"]),
                    str(dice_type["max"]),
                    f"{dice_type['average']:.2f}",
                )
            
            console.print(dice_table)
    
    except DiceParseError as e:
        handle_parse_error(expression, e)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    reset: bool = typer.Option(False, "--reset", "-r", help="Reset to default configuration"),
    set_key: Optional[str] = typer.Option(None, "--set", help="Set configuration key"),
    value: Optional[str] = typer.Option(None, "--value", help="Value to set"),
) -> None:
    """Manage application configuration."""
    try:
        config_manager = get_config_manager()
        
        if reset:
            if typer.confirm("Are you sure you want to reset configuration to defaults?"):
                config_manager.reset_config()
                console.print("[green]Configuration reset to defaults.[/green]")
            return
        
        if set_key and value:
            # Simple key-value setting
            valid_keys = [
                "default_iterations", "default_seed", "output_format",
                "verbose", "show_stats", "history_limit"
            ]
            
            if set_key not in valid_keys:
                console.print(f"[red]Invalid configuration key.[/red] Valid keys: {', '.join(valid_keys)}")
                raise typer.Exit(1)
            
            # Convert value to appropriate type
            if set_key in ["default_iterations", "history_limit"]:
                value = int(value)
            elif set_key == "default_seed":
                value = int(value) if value != "null" else None
            elif set_key in ["verbose", "show_stats"]:
                value = value.lower() in ("true", "1", "yes")
            elif set_key == "output_format":
                value = OutputFormat(value)
            
            config_manager.update_config(**{set_key: value})
            console.print(f"[green]Configuration updated:[/green] {set_key} = {value}")
            return
        
        if show or (not set_key and not value):
            current_config = config_manager.load_config()
            config_info = config_manager.get_config_info()
            
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
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    from . import __version__
    console.print(f"dice-average version {__version__}")


if __name__ == "__main__":
    app()