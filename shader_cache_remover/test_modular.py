#!/usr/bin/env python3
"""
Basic test script for the modular Shader Cache Remover.

This script tests the core functionality of the modular architecture
without requiring a GUI environment.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path to allow imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import modules for testing
try:
    from shader_cache_remover.core.detection_service import DetectionService
    from shader_cache_remover.core.cleanup_service import CleanupService, CleanupStats
    from shader_cache_remover.core.backup_service import BackupService
    from shader_cache_remover.infrastructure.config_manager import ConfigManager
    from shader_cache_remover.infrastructure.registry_utils import RegistryUtils
    from shader_cache_remover.infrastructure.logging_config import LoggingConfig

    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_SUCCESSFUL = False


def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing module imports...")

    try:
        from shader_cache_remover.core.detection_service import DetectionService
        from shader_cache_remover.core.cleanup_service import (
            CleanupService,
            CleanupStats,
        )
        from shader_cache_remover.core.backup_service import BackupService
        from shader_cache_remover.infrastructure.config_manager import ConfigManager
        from shader_cache_remover.infrastructure.registry_utils import RegistryUtils
        from shader_cache_remover.infrastructure.logging_config import LoggingConfig

        print("✓ All core modules imported successfully")
        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_services():
    """Test basic service functionality."""
    print("\nTesting service functionality...")

    try:
        # Test configuration manager
        config_manager = ConfigManager()
        print(
            f"✓ Config manager initialized (config file: {config_manager.config_path})"
        )

        # Test detection service
        detection_service = DetectionService()
        directories = detection_service.get_all_shader_cache_directories()
        print(f"✓ Detection service found {len(directories)} shader cache directories")

        # Test backup service
        backup_service = BackupService()
        backup_info = backup_service.get_backup_info()
        print(
            f"✓ Backup service initialized (enabled: {backup_info['backup_enabled']})"
        )

        # Test cleanup service
        cleanup_service = CleanupService()
        print("✓ Cleanup service initialized")

        # Test logging config
        logging_config = LoggingConfig()
        print("✓ Logging config initialized")

        return True

    except Exception as e:
        print(f"✗ Service test error: {e}")
        return False


def test_configuration():
    """Test configuration management."""
    print("\nTesting configuration management...")

    try:
        config_manager = ConfigManager()

        # Test getting values
        auto_backup = config_manager.is_auto_backup_enabled()
        detailed_logging = config_manager.is_detailed_logging_enabled()
        show_progress = config_manager.should_show_progress()

        print(
            f"✓ Configuration loaded (auto_backup: {auto_backup}, detailed_logging: {detailed_logging}, show_progress: {show_progress})"
        )

        # Test setting values
        config_manager.set_auto_backup(True)
        assert config_manager.is_auto_backup_enabled() == True
        print("✓ Auto-backup setting updated")

        # Reset to original value
        config_manager.set_auto_backup(auto_backup)

        return True

    except Exception as e:
        print(f"✗ Configuration test error: {e}")
        return False


def test_directory_detection():
    """Test shader cache directory detection."""
    print("\nTesting directory detection...")

    try:
        detection_service = DetectionService()

        # Test common directories detection
        common_dirs = detection_service.get_common_shader_cache_directories()
        print(f"✓ Found {len(common_dirs)} common shader cache directories")

        # Test drive detection
        drives = detection_service.get_all_drives()
        print(f"✓ Found {len(drives)} drives/partitions")

        # Test all directories detection
        all_dirs = detection_service.get_all_shader_cache_directories()
        print(f"✓ Total shader cache directories found: {len(all_dirs)}")

        # Show some examples
        for i, directory in enumerate(all_dirs[:3]):  # Show first 3
            print(f"  {i+1}. {directory}")

        if len(all_dirs) > 3:
            print(f"  ... and {len(all_dirs) - 3} more")

        return True

    except Exception as e:
        print(f"✗ Directory detection test error: {e}")
        return False


def main():
    """Run all tests."""
    print("Shader Cache Remover - Modular Architecture Test")
    print("=" * 50)

    tests = [
        test_imports,
        test_services,
        test_configuration,
        test_directory_detection,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The modular architecture is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
