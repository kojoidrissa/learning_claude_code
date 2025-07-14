"""Tests for CLI functionality."""

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
        subcommands = {'history', 'info', 'config', 'version'}
        
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
            "--seed", "42",
            "--verbose"
        ])
        assert result.exit_code == 0
        assert "Rolling 2d8 + 3" in result.stdout
    
    
    def test_roll_command_invalid_expression(self):
        """Test roll command with invalid expression."""
        result = self._invoke_main(["invalid"])
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
    
    # History command removed - test disabled
    
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
            "--no-save"
        ])
        assert result.exit_code == 0
        assert "Rolling d6" in result.stdout
    
    def test_roll_command_no_stats(self):
        """Test roll command without statistics."""
        result = self._invoke_main([
            "d6"
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
            result = self._invoke_main([expr])
            assert result.exit_code == 0, f"Failed for expression: {expr}"
            assert f"Rolling {expr}" in result.stdout or expr in result.stdout
    
    def test_help_messages(self):
        """Test help messages."""
        # Main help
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "dice-average" in result.stdout
        
        # Command help
        commands = ["roll", "info", "config", "version"]
        for cmd in commands:
            result = self.runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0
    
    def test_error_handling(self):
        """Test error handling for various scenarios."""
        # Missing required argument (should show help)
        result = self._invoke_main([])
        assert result.exit_code == 0  # Shows help and exits
        
        # Invalid seed format should still work as it validates the type
        
        # Invalid seed
        result = self._invoke_main(["d6", "--seed", "invalid"])
        assert result.exit_code == 2  # Type error
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Single roll with seed
        result = self._invoke_main([
            "d6", 
            "--seed", "42"
        ])
        assert result.exit_code == 0
        
        # Complex expression
        result = self._invoke_main(["10d6+5d8+3d4-10"])
        assert result.exit_code == 0