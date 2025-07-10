"""Tests for CLI functionality."""

import json
import pytest
from typer.testing import CliRunner

from dice_average.cli import app


class TestCLI:
    """Test CLI functionality."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    def _invoke_main(self, args):
        """Helper to invoke the main CLI behavior."""
        if len(args) == 0:
            return self.runner.invoke(app, ['--help'])
        
        first_arg = args[0]
        subcommands = {'analyze', 'history', 'info', 'config', 'version'}
        
        if first_arg in subcommands or first_arg.startswith('-'):
            # Run as multi-command app
            return self.runner.invoke(app, args)
        else:
            # Prepend 'roll' to the arguments and run
            return self.runner.invoke(app, ['roll'] + args)
    
    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "dice-average version" in result.stdout
    
    def test_roll_command_basic(self):
        """Test basic roll command."""
        result = self._invoke_main(["3d6"])
        assert result.exit_code == 0
        assert "Rolling 3d6" in result.stdout
    
    def test_roll_command_with_options(self):
        """Test roll command with options."""
        result = self._invoke_main([
            "2d8+3", 
            "--iterations", "5",
            "--seed", "42",
            "--verbose"
        ])
        assert result.exit_code == 0
        assert "Rolling 2d8 + 3" in result.stdout
    
    def test_roll_command_json_output(self):
        """Test roll command with JSON output."""
        result = self._invoke_main([
            "d6", 
            "--iterations", "3",
            "--seed", "42",
            "--json"
        ])
        assert result.exit_code == 0
        
        # Should be valid JSON
        output_data = json.loads(result.stdout)
        assert "expression" in output_data
        assert "iterations" in output_data
        assert "results" in output_data
        assert len(output_data["results"]) == 3
    
    def test_roll_command_invalid_expression(self):
        """Test roll command with invalid expression."""
        result = self._invoke_main(["invalid"])
        assert result.exit_code == 1
        assert "Error parsing dice expression" in result.stdout
    
    def test_analyze_command_basic(self):
        """Test basic analyze command."""
        result = self.runner.invoke(app, ["analyze", "2d6"])
        assert result.exit_code == 0
        assert "Statistical Analysis" in result.stdout
        assert "Basic Statistics" in result.stdout
    
    def test_analyze_command_extended(self):
        """Test analyze command with extended statistics."""
        result = self.runner.invoke(app, ["analyze", "3d6", "--extended"])
        assert result.exit_code == 0
        assert "Statistical Analysis" in result.stdout
        assert "Extended Statistics" in result.stdout
    
    def test_analyze_command_json(self):
        """Test analyze command with JSON output."""
        result = self.runner.invoke(app, ["analyze", "d6", "--json"])
        assert result.exit_code == 0
        
        # Should be valid JSON
        output_data = json.loads(result.stdout)
        assert "expression" in output_data
        assert "min_value" in output_data
        assert "max_value" in output_data
        assert "probability_distribution" in output_data
    
    def test_analyze_command_invalid_expression(self):
        """Test analyze command with invalid expression."""
        result = self.runner.invoke(app, ["analyze", "invalid"])
        assert result.exit_code == 1
        assert "Error parsing dice expression" in result.stdout
    
    def test_info_command(self):
        """Test info command."""
        result = self.runner.invoke(app, ["info", "2d6+3"])
        assert result.exit_code == 0
        assert "Expression Info" in result.stdout
        assert "Dice Breakdown" in result.stdout
    
    def test_info_command_invalid_expression(self):
        """Test info command with invalid expression."""
        result = self.runner.invoke(app, ["info", "invalid"])
        assert result.exit_code == 1
        assert "Error parsing dice expression" in result.stdout
    
    def test_history_command_empty(self):
        """Test history command with empty history."""
        result = self.runner.invoke(app, ["history"])
        assert result.exit_code == 0
        # Should handle empty history gracefully
    
    def test_history_command_json(self):
        """Test history command with JSON output."""
        result = self.runner.invoke(app, ["history", "--json"])
        assert result.exit_code == 0
        
        # Should be valid JSON
        output_data = json.loads(result.stdout)
        assert "total_sessions" in output_data
        assert "recent_sessions" in output_data
    
    def test_config_command_show(self):
        """Test config command show."""
        result = self.runner.invoke(app, ["config", "--show"])
        assert result.exit_code == 0
        assert "Current Configuration" in result.stdout
        assert "Configuration Files" in result.stdout
    
    def test_config_command_set(self):
        """Test config command set."""
        result = self.runner.invoke(app, [
            "config", 
            "--set", "default_iterations",
            "--value", "150"
        ])
        assert result.exit_code == 0
        assert "Configuration updated" in result.stdout
    
    def test_config_command_set_invalid_key(self):
        """Test config command with invalid key."""
        result = self.runner.invoke(app, [
            "config", 
            "--set", "invalid_key",
            "--value", "100"
        ])
        assert result.exit_code == 1
        assert "Invalid configuration key" in result.stdout
    
    def test_roll_command_no_save(self):
        """Test roll command without saving to history."""
        result = self._invoke_main([
            "d6", 
            "--iterations", "1",
            "--no-save"
        ])
        assert result.exit_code == 0
        assert "Rolling d6" in result.stdout
    
    def test_roll_command_no_stats(self):
        """Test roll command without statistics."""
        result = self._invoke_main([
            "d6", 
            "--iterations", "5",
            "--no-stats"
        ])
        assert result.exit_code == 0
        assert "Rolling d6" in result.stdout
    
    def test_complex_dice_expressions(self):
        """Test various complex dice expressions."""
        expressions = [
            "d6",
            "3d6",
            "2d8+5",
            "1d20-3",
            "2d6+1d8+3",
            "4d6-2",
        ]
        
        for expr in expressions:
            result = self._invoke_main([expr, "--iterations", "1"])
            assert result.exit_code == 0, f"Failed for expression: {expr}"
            assert f"Rolling {expr}" in result.stdout or expr in result.stdout
    
    def test_analyze_various_expressions(self):
        """Test analyze command with various expressions."""
        expressions = [
            "d6",
            "2d6",
            "3d6+2",
            "1d8+1d6",
        ]
        
        for expr in expressions:
            result = self.runner.invoke(app, ["analyze", expr])
            assert result.exit_code == 0, f"Failed for expression: {expr}"
            assert "Statistical Analysis" in result.stdout
    
    def test_help_messages(self):
        """Test help messages."""
        # Main help
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "dice-average" in result.stdout
        
        # Command help
        commands = ["roll", "analyze", "history", "info", "config", "version"]
        for cmd in commands:
            result = self.runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0
    
    def test_error_handling(self):
        """Test error handling for various scenarios."""
        # Missing required argument (should show help)
        result = self._invoke_main([])
        assert result.exit_code == 0  # Shows help and exits
        
        # Invalid iterations
        result = self._invoke_main(["d6", "--iterations", "0"])
        assert result.exit_code == 1
        
        # Invalid seed
        result = self._invoke_main(["d6", "--seed", "invalid"])
        assert result.exit_code == 2  # Type error
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Large number of iterations
        result = self._invoke_main([
            "d6", 
            "--iterations", "1000",
            "--seed", "42"
        ])
        assert result.exit_code == 0
        
        # Complex expression
        result = self.runner.invoke(app, [
            "analyze", "10d6+5d8+3d4-10"
        ])
        assert result.exit_code == 0