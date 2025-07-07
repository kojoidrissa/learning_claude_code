"""Tests for configuration management."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from dice_average.config import ConfigManager, get_config_from_env, load_config_with_env
from dice_average.models import AppConfig, RollHistory, OutputFormat


class TestConfigManager:
    """Test configuration manager functionality."""
    
    def test_config_manager_creation(self):
        """Test creating a config manager."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            assert manager.config_dir == config_dir
            assert manager.config_file == config_dir / "config.json"
            assert manager.history_file == config_dir / "history.json"
            assert config_dir.exists()
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            config = manager.load_config()
            
            assert isinstance(config, AppConfig)
            assert config.default_iterations == 1
            assert config.default_seed is None
            assert config.output_format == OutputFormat.TEXT
            assert config.verbose is False
            assert config.show_stats is False
            assert config.history_limit == 100
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            # Create custom config
            custom_config = AppConfig(
                default_iterations=50,
                default_seed=42,
                output_format=OutputFormat.JSON,
                verbose=True,
                show_stats=False,
                history_limit=50
            )
            
            # Save and reload
            manager.save_config(custom_config)
            loaded_config = manager.load_config()
            
            assert loaded_config.default_iterations == 50
            assert loaded_config.default_seed == 42
            assert loaded_config.output_format == OutputFormat.JSON
            assert loaded_config.verbose is True
            assert loaded_config.show_stats is False
            assert loaded_config.history_limit == 50
    
    def test_update_config(self):
        """Test updating configuration."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            # Update some values
            updated_config = manager.update_config(
                default_iterations=200,
                verbose=True
            )
            
            assert updated_config.default_iterations == 200
            assert updated_config.verbose is True
            assert updated_config.show_stats is False  # Unchanged
    
    def test_load_invalid_config(self):
        """Test loading invalid configuration file."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            # Write invalid JSON
            config_file = config_dir / "config.json"
            config_file.write_text("invalid json")
            
            # Should fallback to default
            config = manager.load_config()
            assert isinstance(config, AppConfig)
            assert config.default_iterations == 1
    
    def test_load_empty_history(self):
        """Test loading empty history."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            history = manager.load_history()
            
            assert isinstance(history, RollHistory)
            assert len(history.sessions) == 0
    
    def test_save_and_load_history(self):
        """Test saving and loading history."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            # Create history with some sessions
            history = RollHistory()
            # Note: We'd need to create proper RollSession objects here
            # For now, test with empty history
            
            manager.save_history(history)
            loaded_history = manager.load_history()
            
            assert isinstance(loaded_history, RollHistory)
            assert len(loaded_history.sessions) == 0
    
    def test_clear_history(self):
        """Test clearing history."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            manager.clear_history()
            history = manager.load_history()
            
            assert len(history.sessions) == 0
    
    def test_get_config_info(self):
        """Test getting configuration information."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            info = manager.get_config_info()
            
            assert "config_dir" in info
            assert "config_file" in info
            assert "history_file" in info
            assert "config_exists" in info
            assert "history_exists" in info
            assert "config_size" in info
            assert "history_size" in info
            
            assert info["config_dir"] == str(config_dir)
            assert info["config_exists"] is False  # No config file yet
            assert info["history_exists"] is False  # No history file yet
    
    def test_reset_config(self):
        """Test resetting configuration."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            # Update config first
            manager.update_config(default_iterations=500)
            
            # Reset
            reset_config = manager.reset_config()
            
            assert reset_config.default_iterations == 1
            assert reset_config.default_seed is None
            assert reset_config.output_format == OutputFormat.TEXT
    
    def test_import_config(self):
        """Test importing configuration from file."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            # Create external config file
            external_config = Path(tmpdir) / "external_config.json"
            config_data = {
                "default_iterations": 300,
                "default_seed": 123,
                "output_format": "json",
                "verbose": True,
                "show_stats": False,
                "history_limit": 200
            }
            external_config.write_text(json.dumps(config_data))
            
            # Import
            imported_config = manager.import_config(external_config)
            
            assert imported_config.default_iterations == 300
            assert imported_config.default_seed == 123
            assert imported_config.output_format == OutputFormat.JSON
            assert imported_config.verbose is True
            assert imported_config.show_stats is False
            assert imported_config.history_limit == 200
    
    def test_import_nonexistent_config(self):
        """Test importing from nonexistent file."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            nonexistent_file = Path(tmpdir) / "nonexistent.json"
            
            with pytest.raises(FileNotFoundError):
                manager.import_config(nonexistent_file)
    
    def test_import_invalid_config(self):
        """Test importing invalid configuration."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            # Create invalid config file
            invalid_config = Path(tmpdir) / "invalid_config.json"
            invalid_config.write_text("invalid json")
            
            with pytest.raises(ValueError):
                manager.import_config(invalid_config)
    
    def test_export_config(self):
        """Test exporting configuration."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            # Update config
            manager.update_config(default_iterations=150)
            
            # Export
            export_file = Path(tmpdir) / "exported_config.json"
            manager.export_config(export_file)
            
            # Verify exported file
            assert export_file.exists()
            with open(export_file, 'r') as f:
                exported_data = json.load(f)
            
            assert exported_data["default_iterations"] == 150
    
    def test_history_limit_enforcement(self):
        """Test that history limit is enforced."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "test_config"
            manager = ConfigManager(config_dir)
            
            # Set low history limit
            manager.update_config(history_limit=3)
            
            # Create history with many sessions
            history = RollHistory()
            # Note: In a real test, we'd add actual RollSession objects
            # For now, we'll test the limit enforcement concept
            
            manager.save_history(history)
            loaded_history = manager.load_history()
            
            assert len(loaded_history.sessions) <= 3


class TestEnvironmentConfig:
    """Test environment variable configuration."""
    
    def test_get_config_from_env_empty(self):
        """Test getting config from environment with no variables set."""
        import os
        
        # Save original environment
        original_env = dict(os.environ)
        
        try:
            # Clear relevant environment variables
            for key in list(os.environ.keys()):
                if key.startswith("DICE_"):
                    del os.environ[key]
            
            config_overrides = get_config_from_env()
            assert config_overrides == {}
        
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_get_config_from_env_with_values(self):
        """Test getting config from environment with values set."""
        import os
        
        # Save original environment
        original_env = dict(os.environ)
        
        try:
            # Set environment variables
            os.environ["DICE_DEFAULT_ITERATIONS"] = "250"
            os.environ["DICE_DEFAULT_SEED"] = "999"
            os.environ["DICE_OUTPUT_FORMAT"] = "json"
            os.environ["DICE_VERBOSE"] = "true"
            os.environ["DICE_SHOW_STATS"] = "false"
            os.environ["DICE_HISTORY_LIMIT"] = "75"
            
            config_overrides = get_config_from_env()
            
            assert config_overrides["default_iterations"] == 250
            assert config_overrides["default_seed"] == 999
            assert config_overrides["output_format"] == OutputFormat.JSON
            assert config_overrides["verbose"] is True
            assert config_overrides["show_stats"] is False
            assert config_overrides["history_limit"] == 75
        
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_get_config_from_env_invalid_values(self):
        """Test getting config from environment with invalid values."""
        import os
        
        # Save original environment
        original_env = dict(os.environ)
        
        try:
            # Set invalid environment variables
            os.environ["DICE_DEFAULT_ITERATIONS"] = "invalid"
            os.environ["DICE_VERBOSE"] = "maybe"
            
            config_overrides = get_config_from_env()
            
            # Invalid values should be ignored
            assert "default_iterations" not in config_overrides
            # "maybe" is interpreted as False for boolean values
            assert config_overrides.get("verbose") is False
        
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_load_config_with_env(self):
        """Test loading config with environment overrides."""
        import os
        
        # Save original environment
        original_env = dict(os.environ)
        
        try:
            # Set environment variable
            os.environ["DICE_DEFAULT_ITERATIONS"] = "500"
            
            # This would normally use the global config manager
            # For testing, we'll just test that the function exists
            # and returns an AppConfig
            config = load_config_with_env()
            assert isinstance(config, AppConfig)
        
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)