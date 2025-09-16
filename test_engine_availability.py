#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, '.')

import torch

def test_engine_availability():
    print("Testing engine availability detection and fallback behavior...")

    try:
        from audiblez.settings import Settings

        # Create a settings instance
        settings = Settings()

        print("✅ Settings module imported successfully")

        # Test engine availability detection
        print("\n🔍 Engine Availability Detection:")
        available_engines = settings.get_available_engines()
        for engine, available in available_engines.items():
            status = "✅ Available" if available else "❌ Not Available"
            print(f"  {engine.upper()}: {status}")

        # Test best available engine
        best_engine = settings.get_best_available_engine()
        print(f"\n🏆 Best Available Engine: {best_engine}")

        # Test engine validation/fallback logic
        print("\n🔧 Engine Validation Tests:")

        test_cases = [
            ('cpu', 'Should always work'),
            ('cuda', 'Should work if CUDA available, otherwise fall back'),
            ('apple', 'Should work if MPS available, otherwise fall back'),
            ('invalid', 'Should fall back to best available')
        ]

        for test_engine, description in test_cases:
            validated = settings._validate_engine(test_engine)
            print(f"  Request: '{test_engine}' → Result: '{validated}' ({description})")

        # Test settings loading with different saved engines
        print("\n💾 Settings Loading Tests:")

        # Temporarily save different engine settings and test loading
        test_scenarios = [
            ('cpu', 'User prefers CPU'),
            ('cuda', 'User saved CUDA (may fall back)'),
            ('apple', 'User saved Apple Silicon (may fall back)')
        ]

        for test_engine, description in test_scenarios:
            # Set the engine
            settings.set_engine(test_engine)
            actual_engine = settings.get_engine()
            print(f"  Set: '{test_engine}' → Loaded: '{actual_engine}' ({description})")

        # Test what happens on this system specifically
        print(f"\n🖥️  Current System Configuration:")
        print(f"  PyTorch version: {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        print(f"  MPS available: {torch.backends.mps.is_available()}")
        print(f"  Current default device: {torch.get_default_device()}")

        # Demonstrate the fallback behavior expected on this Mac
        print(f"\n🍎 Expected Mac Behavior:")
        print(f"  - CPU saved → Use CPU (preserve preference)")
        print(f"  - CUDA saved → Fall back to Apple Silicon (best available)")
        print(f"  - Apple saved → Use Apple Silicon")
        print(f"  - UI should show: CPU ✅, CUDA ❌ (disabled), Apple Silicon ✅")

        print(f"\n📂 Settings file location: {settings.settings_file}")

    except Exception as e:
        print(f"❌ Error testing engine availability: {e}")
        import traceback
        traceback.print_exc()


def test_ui_import():
    """Test that the UI can still be imported with the new engine logic"""
    print("\n🖼️  Testing UI Import with Engine Detection:")
    try:
        from audiblez.ui import MainWindow
        print("✅ UI module imports successfully with engine detection")

        # We can't actually create the UI in a headless environment,
        # but we can at least verify the import works

    except Exception as e:
        print(f"❌ Error importing UI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_engine_availability()
    test_ui_import()
    print("\n🎉 Engine availability testing completed!")