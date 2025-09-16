#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Settings management for Audiblez UI"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import torch.backends.mps
import torch.cuda


class Settings:
    """Manages persistent settings for the Audiblez UI"""

    def __init__(self):
        # Default settings
        self.defaults = {
            'window': {
                'width': 800,
                'height': 600
            },
            'engine': self._get_default_engine(),
            'voice': None,  # Will be set to first available voice
            'speed': 1.0,
            'output_folder': os.path.abspath('.')
        }

        # Settings file path (in user's home directory)
        self.settings_file = Path.home() / '.audiblez' / 'settings.yaml'

        # Ensure settings directory exists
        self.settings_file.parent.mkdir(exist_ok=True)

        # Load existing settings
        self.settings = self._load_settings()

    def get_available_engines(self) -> Dict[str, bool]:
        """Get availability status for all engines"""
        return {
            'cpu': True,  # CPU is always available
            'cuda': torch.cuda.is_available(),
            'apple': torch.backends.mps.is_available()
        }

    def get_best_available_engine(self) -> str:
        """Get the best available engine based on performance hierarchy"""
        if torch.backends.mps.is_available():
            return 'apple'
        elif torch.cuda.is_available():
            return 'cuda'
        else:
            return 'cpu'

    def _get_default_engine(self) -> str:
        """Determine the default engine based on system capabilities"""
        return self.get_best_available_engine()

    def _validate_engine(self, engine: str) -> str:
        """Validate engine availability and return fallback if needed"""
        available_engines = self.get_available_engines()

        # If the requested engine is available, use it
        if engine in available_engines and available_engines[engine]:
            return engine

        # Otherwise, fall back to best available engine
        return self.get_best_available_engine()

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from YAML file, using defaults for missing values"""
        if not self.settings_file.exists():
            return self.defaults.copy()

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = yaml.safe_load(f) or {}

            # Merge with defaults (defaults take precedence for missing keys)
            settings = self.defaults.copy()
            self._deep_update(settings, loaded_settings)

            # Validate and potentially fix the engine setting
            if 'engine' in settings:
                settings['engine'] = self._validate_engine(settings['engine'])

            return settings

        except Exception as e:
            print(f"Warning: Failed to load settings from {self.settings_file}: {e}")
            return self.defaults.copy()

    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """Recursively update base_dict with values from update_dict"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def save_settings(self) -> bool:
        """Save current settings to YAML file"""
        try:
            # Ensure directory exists
            self.settings_file.parent.mkdir(exist_ok=True)

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self.settings, f, default_flow_style=False, indent=2)

            print(f"Settings saved to {self.settings_file}")
            return True

        except Exception as e:
            print(f"Error: Failed to save settings to {self.settings_file}: {e}")
            return False

    # Getter methods
    def get_window_size(self) -> tuple[int, int]:
        """Get window size as (width, height)"""
        window = self.settings.get('window', {})
        return (window.get('width', 800), window.get('height', 600))

    def get_engine(self) -> str:
        """Get selected engine ('cpu', 'cuda', or 'apple')"""
        return self.settings.get('engine', 'cpu')

    def get_voice(self) -> Optional[str]:
        """Get selected voice (with flag, e.g., '🇺🇸 Amy')"""
        return self.settings.get('voice')

    def get_speed(self) -> float:
        """Get selected speed"""
        return float(self.settings.get('speed', 1.0))

    def get_output_folder(self) -> str:
        """Get output folder path"""
        return self.settings.get('output_folder', os.path.abspath('.'))

    # Setter methods
    def set_window_size(self, width: int, height: int) -> None:
        """Set window size"""
        if 'window' not in self.settings:
            self.settings['window'] = {}
        self.settings['window']['width'] = width
        self.settings['window']['height'] = height

    def set_engine(self, engine: str) -> None:
        """Set selected engine ('cpu', 'cuda', or 'apple')"""
        if engine in ['cpu', 'cuda', 'apple']:
            # Only set the engine if it's actually available
            validated_engine = self._validate_engine(engine)
            self.settings['engine'] = validated_engine
            if validated_engine != engine:
                print(f"Warning: Engine '{engine}' not available, using '{validated_engine}' instead")

    def set_voice(self, voice: str) -> None:
        """Set selected voice (with flag, e.g., '🇺🇸 Amy')"""
        self.settings['voice'] = voice

    def set_speed(self, speed: float) -> None:
        """Set selected speed"""
        self.settings['speed'] = float(speed)

    def set_output_folder(self, folder: str) -> None:
        """Set output folder path"""
        self.settings['output_folder'] = folder


# Global settings instance
_settings_instance = None


def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance