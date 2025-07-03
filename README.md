# dice-average 🎲

A modern command-line tool for calculating dice roll averages and statistics, written in Python 3.12+.

Initially created with Claude

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![Typer](https://img.shields.io/badge/typer-0.9.0+-orange.svg)](https://typer.tiangolo.com/)

## Features

- 🎯 **Dice Notation Support**: Parse complex expressions like `3d6`, `2d20+5`, `d8-2`, `2d6 + 1d8 + 3`
- 📊 **Statistical Analysis**: Calculate theoretical and empirical averages, standard deviation, and percentiles
- 🎨 **Beautiful Output**: Rich terminal formatting with colors, tables, and progress bars
- 🔄 **Multiple Iterations**: Roll thousands of times to see probability distributions
- 📈 **Distribution Analysis**: Visualize roll distributions with histograms
- 💾 **Roll History**: Track your previous rolls and results
- 🔧 **Flexible Output**: Display results as tables or export as JSON
- 🌱 **Reproducible Results**: Set random seeds for consistent testing

## Installation

### From PyPI (once published)
```bash
pip install dice-average
```

### From Source
```bash
# Clone the repository
git clone https://github.com/yourusername/dice-average.git
cd dice-average

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## Usage

### Basic Rolling

Roll a single die:
```bash
dice-average roll d20
dice-average roll 1d20  # equivalent
```

Roll multiple dice:
```bash
dice-average roll 3d6
dice-average roll "2d8 + 1d4"
dice-average roll "4d6 + 2"
```

### Statistical Analysis

Roll multiple times to see statistics:
```bash
# Roll 3d6 1000 times with statistics
dice-average roll 3d6 -i 1000 --stats

# Roll many times for detailed analysis
dice-average roll 3d6 -i 10000 --stats

# Set a seed for reproducible results
dice-average roll 2d20 -i 1000 --seed 42 --stats
```

### Advanced Features

Show individual roll results:
```bash
dice-average roll 4d6 -i 10 --verbose
```

Export results as JSON:
```bash
dice-average roll 3d8 -i 1000 --json > results.json
```

Analyze probability distribution:
```bash
dice-average analyze 3d6
dice-average analyze "2d10 + 5" --extended
```

View roll history:
```bash
# Show all history
dice-average history

# Show last 10 rolls
dice-average history --limit 10

# Clear history
dice-average history --clear
```

### Command Options

#### `roll` command
- `expression`: Dice notation (e.g., "3d6", "2d20+5")
- `-i, --iterations`: Number of times to roll (default: 1)
- `-s, --seed`: Random seed for reproducible results
- `-v, --verbose`: Show individual roll results
- `--stats/--no-stats`: Show detailed statistical analysis (default: no stats for single rolls)
- `-j, --json`: Output results as JSON
- `--save/--no-save`: Save to history (default: save)

#### `analyze` command
- `expression`: Dice notation to analyze
- `-e, --extended`: Show extended statistics
- `-j, --json`: Output results as JSON

#### `history` command
- `-l, --limit`: Number of recent sessions to show (default: 10)
- `-c, --clear`: Clear all history
- `-j, --json`: Output as JSON

#### `info` command
- `expression`: Dice notation to get detailed information about

#### `config` command
- `-s, --show`: Show current configuration
- `-r, --reset`: Reset to default configuration
- `--set`: Set configuration key
- `--value`: Value to set

## Examples

### Simple Combat Roll
```bash
$ dice-average roll d20

Rolling d20
Result: 14
```

### Ability Score Generation
```bash
$ dice-average roll 3d6 -i 6 -v
Rolling 3d6 6 times...
╭─────────────────── Results for 3d6 ───────────────────╮
│ Roll # │ Dice │ Rolls      │ Total │
├────────┼──────┼────────────┼───────┤
│ 1      │ 3d6  │ [4, 2, 5]  │ 11    │
│ 2      │ 3d6  │ [6, 3, 3]  │ 12    │
│ 3      │ 3d6  │ [1, 5, 4]  │ 10    │
│ 4      │ 3d6  │ [5, 5, 2]  │ 12    │
│ 5      │ 3d6  │ [3, 6, 4]  │ 13    │
│ 6      │ 3d6  │ [2, 4, 5]  │ 11    │
├────────┼──────┼────────────┼───────┤
│ Average│      │            │ 11.5  │
╰────────┴──────┴────────────┴───────╯
```

### Statistical Analysis
```bash
$ dice-average roll 2d6 -i 10000 --stats
Rolling 2d6 10,000 times...
╭─────────────────── Results for 2d6 ───────────────────╮
│ Metric         │ Value    │
├────────────────┼──────────┤
│ Rolls          │ 10,000   │
│ Average        │ 7.02     │
│ Theoretical    │ 7.00     │
│ Min Rolled     │ 2        │
│ Max Rolled     │ 12       │
│ Std Deviation  │ 2.41     │
╰────────────────┴──────────╯

Distribution:
  2: ████ (2.8%)
  3: ████████ (5.6%)
  4: ████████████ (8.3%)
  5: ████████████████ (11.1%)
  6: ████████████████████ (13.9%)
  7: ████████████████████████ (16.7%)
  8: ████████████████████ (13.8%)
  9: ████████████████ (11.2%)
 10: ████████████ (8.4%)
 11: ████████ (5.5%)
 12: ████ (2.7%)
```

### Complex Expression
```bash
$ dice-average roll "2d8 + 1d6 + 3" -i 1000
╭────────────── Results for 2d8 + 1d6 + 3 ──────────────╮
│ Metric         │ Value    │
├────────────────┼──────────┤
│ Rolls          │ 1,000    │
│ Average        │ 15.48    │
│ Theoretical    │ 15.50    │
│ Min Rolled     │ 6        │
│ Max Rolled     │ 25       │
│ Std Deviation  │ 3.72     │
╰────────────────┴──────────╯
```

## Configuration

dice-average can be configured through environment variables or the `config` command:

```bash
# Environment variables
DICE_DEFAULT_ITERATIONS=1
DICE_DEFAULT_SEED=42
DICE_OUTPUT_FORMAT=json
DICE_VERBOSE=true
DICE_SHOW_STATS=false
DICE_HISTORY_LIMIT=50
```

Or use the config command:
```bash
# Show current configuration
dice-average config --show

# Set configuration values
dice-average config --set default_iterations --value 100
dice-average config --set show_stats --value true

# Reset to defaults
dice-average config --reset
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dice_average

# Run specific test file
pytest tests/test_parser.py
```

### Code Quality
```bash
# Format code
black dice_average tests

# Lint code
ruff check dice_average tests

# Type checking
mypy dice_average
```

### Project Structure
```
dice-average/
├── dice_average/
│   ├── __init__.py        # Package initialization
│   ├── cli.py             # Typer CLI application
│   ├── config.py          # Configuration management
│   ├── models.py          # Pydantic data models
│   ├── parser.py          # Dice notation parser
│   ├── roller.py          # Dice rolling logic
│   └── statistics.py      # Statistical calculations
├── tests/                 # Test suite
│   ├── test_models.py     # Model tests
│   ├── test_parser.py     # Parser tests
│   ├── test_roller.py     # Roller tests
│   ├── test_statistics.py # Statistics tests
│   ├── test_config.py     # Config tests
│   └── test_cli.py        # CLI tests
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## Dice Notation Guide

### Basic Notation
- `d6` or `1d6`: Roll one six-sided die
- `3d6`: Roll three six-sided dice
- `d20`: Roll one twenty-sided die

### With Modifiers
- `3d6+3`: Roll 3d6 and add 3
- `2d8-2`: Roll 2d8 and subtract 2
- `d20+5`: Roll d20 and add 5

### Complex Expressions
- `2d6 + 1d8`: Roll 2d6 and 1d8, sum all
- `3d4 + 2d6 - 2`: Roll 3d4 and 2d6, sum all, then subtract 2
- `d20 + d4 + 3`: Roll d20 and d4, sum both, then add 3

### Supported Dice
- Standard: d4, d6, d8, d10, d12, d20, d100
- Custom: Any positive integer (e.g., d3, d7, d13)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for the CLI interface
- Uses [Pydantic](https://docs.pydantic.dev/) for data validation
- Terminal formatting powered by [Rich](https://rich.readthedocs.io/)
- Inspired by tabletop RPG dice rolling needs

## Roadmap

- [ ] Add support for dice pools (count successes)
- [ ] Implement advantage/disadvantage rolling
- [ ] Add web API endpoint
- [ ] Create GUI version
- [ ] Support for custom dice (fate dice, etc.)
- [ ] Export roll history to CSV
- [ ] Add probability calculator
- [ ] Support for reroll mechanics

---

Made with ❤️ and 🎲 by the dice-average community