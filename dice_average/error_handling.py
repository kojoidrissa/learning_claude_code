"""Error handling utilities for the CLI."""

import typer
from rich.console import Console

from .parser import DiceParseError
from .display import handle_parse_error, print_error

console = Console()


def handle_cli_error(func):
    """Decorator to handle common CLI errors."""
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DiceParseError as e:
            # Extract expression from args if available
            expression = args[0] if args else "unknown"
            handle_parse_error(expression, e)
            raise typer.Exit(1)
        except ValueError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            raise typer.Exit(1)
    return wrapper


def safe_int_conversion(value: str, field_name: str) -> int:
    """Safely convert string to int with descriptive error."""
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Invalid {field_name}: '{value}' must be a number")


def safe_bool_conversion(value: str) -> bool:
    """Safely convert string to boolean."""
    return value.lower() in ("true", "1", "yes")