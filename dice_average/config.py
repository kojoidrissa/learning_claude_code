"""Configuration management for the dice average application."""

import json
import os
from pathlib import Path
from typing import Optional

from .models import AppConfig, OutputFormat


class ConfigManager:
    """Manages application configuration and persistent data."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
        """
        if config_dir is None:
            config_dir = Path.home() / ".dice-average"
        
        self.config_dir = config_dir
        self.config_file = config_dir / "config.json"
        self.history_file = config_dir / "history.json"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._config: Optional[AppConfig] = None
    
    def load_config(self) -> AppConfig:
        """
        Load configuration from file or create default.
        
        Returns:
            AppConfig object
        """
        if self._config is not None:
            return self._config
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                self._config = AppConfig.model_validate(config_data)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load config file: {e}")
                self._config = AppConfig()
        else:
            self._config = AppConfig()
        
        return self._config
    
    def save_config(self, config: Optional[AppConfig] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config: AppConfig to save, uses current config if None
        """
        if config is not None:
            self._config = config
        
        if self._config is None:
            return
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config.model_dump(), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def update_config(self, **kwargs) -> AppConfig:
        """
        Update configuration with new values.
        
        Args:
            **kwargs: Configuration values to update
            
        Returns:
            Updated AppConfig
        """
        config = self.load_config()
        
        # Create new config with updated values
        config_data = config.model_dump()
        config_data.update(kwargs)
        
        self._config = AppConfig.model_validate(config_data)
        self.save_config()
        
        return self._config
    
    
    def get_config_info(self) -> dict:
        """Get information about configuration files."""
        return {
            "config_dir": str(self.config_dir),
            "config_file": str(self.config_file),
            "history_file": str(self.history_file),
            "config_exists": self.config_file.exists(),
            "history_exists": self.history_file.exists(),
            "config_size": self.config_file.stat().st_size if self.config_file.exists() else 0,
            "history_size": self.history_file.stat().st_size if self.history_file.exists() else 0,
        }
    
    def reset_config(self) -> AppConfig:
        """Reset configuration to defaults."""
        self._config = AppConfig()
        self.save_config()
        return self._config
    
    def import_config(self, config_path: Path) -> AppConfig:
        """
        Import configuration from another file.
        
        Args:
            config_path: Path to configuration file to import
            
        Returns:
            Imported AppConfig
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            config = AppConfig.model_validate(config_data)
            self._config = config
            self.save_config()
            
            return config
        except (json.JSONDecodeError, Exception) as e:
            raise ValueError(f"Invalid config file: {e}")
    
    def export_config(self, export_path: Path) -> None:
        """
        Export current configuration to a file.
        
        Args:
            export_path: Path where to export the configuration
        """
        config = self.load_config()
        
        try:
            with open(export_path, 'w') as f:
                json.dump(config.model_dump(), f, indent=2)
        except Exception as e:
            raise ValueError(f"Could not export config: {e}")


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_config() -> AppConfig:
    """Convenience function to load configuration."""
    return get_config_manager().load_config()


def save_config(config: AppConfig) -> None:
    """Convenience function to save configuration."""
    get_config_manager().save_config(config)




def get_config_from_env() -> dict:
    """Get configuration overrides from environment variables."""
    config_overrides = {}
    
    # Environment variable mappings
    env_mappings = {
        "DICE_DEFAULT_ITERATIONS": ("default_iterations", int),
        "DICE_DEFAULT_SEED": ("default_seed", int),
        "DICE_OUTPUT_FORMAT": ("output_format", OutputFormat),
        "DICE_VERBOSE": ("verbose", lambda x: x.lower() in ("true", "1", "yes")),
        "DICE_SHOW_STATS": ("show_stats", lambda x: x.lower() in ("true", "1", "yes")),
    }
    
    for env_var, (config_key, converter) in env_mappings.items():
        value = os.environ.get(env_var)
        if value is not None:
            try:
                config_overrides[config_key] = converter(value)
            except (ValueError, TypeError):
                print(f"Warning: Invalid value for {env_var}: {value}")
    
    return config_overrides


def load_config_with_env() -> AppConfig:
    """Load configuration with environment variable overrides."""
    config = load_config()
    env_overrides = get_config_from_env()
    
    if env_overrides:
        config_data = config.model_dump()
        config_data.update(env_overrides)
        config = AppConfig.model_validate(config_data)
    
    return config