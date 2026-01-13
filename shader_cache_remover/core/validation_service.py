"""
Validation service for pre-flight checks before cleanup operations.

This module provides validation of cleanup operations before they proceed,
catching potential issues early and preventing destructive mistakes.
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional

from .interfaces import CacheLocation


class ValidationSeverity(Enum):
    """Severity levels for validation results."""
    INFO = auto()       # Informational, does not block
    WARNING = auto()    # Concerning, but allows continue
    ERROR = auto()      # Blocks operation
    CRITICAL = auto()   # Blocks with strong warning


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    passed: bool
    message: str
    severity: ValidationSeverity
    path: Optional[Path] = None
    check_name: str = ""


@dataclass
class ValidationReport:
    """Complete validation report for a cleanup operation."""
    results: List[ValidationResult] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        """Check if validation passed (no ERROR or CRITICAL)."""
        return not any(
            r.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
            and not r.passed
            for r in self.results
        )
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return any(
            r.severity == ValidationSeverity.WARNING and not r.passed
            for r in self.results
        )
    
    def get_errors(self) -> List[ValidationResult]:
        """Get all error results."""
        return [r for r in self.results 
                if r.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
                and not r.passed]
    
    def get_warnings(self) -> List[ValidationResult]:
        """Get all warning results."""
        return [r for r in self.results
                if r.severity == ValidationSeverity.WARNING and not r.passed]


class ValidationService:
    """
    Pre-flight validation before cleanup operations.
    
    Runs a series of safety checks to ensure cleanup operations
    are safe to proceed.
    """
    
    # Protected system path prefixes (case-insensitive on Windows)
    PROTECTED_PREFIXES = [
        Path("C:/Windows"),
        Path("C:/Program Files"),
        Path("C:/Program Files (x86)"),
        Path("C:/ProgramData/Microsoft"),
    ]
    
    # Minimum required free space after cleanup (in bytes) - 1GB
    MIN_FREE_SPACE = 1 * 1024 * 1024 * 1024
    
    def __init__(self):
        """Initialize the validation service."""
        self.logger = logging.getLogger(__name__)
    
    def validate_cleanup(self, locations: List[CacheLocation]) -> ValidationReport:
        """
        Run all validations before cleanup.
        
        Args:
            locations: List of cache locations to validate
        
        Returns:
            ValidationReport with all check results
        """
        report = ValidationReport()
        
        # Check each location
        for location in locations:
            if location.enabled:
                report.results.extend(self._validate_location(location))
        
        # Check system requirements
        report.results.extend(self._check_system_requirements())
        
        return report
    
    def _validate_location(self, location: CacheLocation) -> List[ValidationResult]:
        """Validate a single cache location."""
        results = []
        path = location.path
        
        # Check path exists
        if not path.exists():
            results.append(ValidationResult(
                passed=True,  # Not an error, just skip
                message=f"Path does not exist (will be skipped): {path}",
                severity=ValidationSeverity.INFO,
                path=path,
                check_name="path_exists"
            ))
            return results
        
        # Check not in protected paths
        results.append(self._check_not_protected(path))
        
        # Check read/write permissions
        results.append(self._check_permissions(path))
        
        # Check path is a directory
        if not path.is_dir():
            results.append(ValidationResult(
                passed=False,
                message=f"Path is not a directory: {path}",
                severity=ValidationSeverity.ERROR,
                path=path,
                check_name="is_directory"
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                message=f"Path is a valid directory: {path}",
                severity=ValidationSeverity.INFO,
                path=path,
                check_name="is_directory"
            ))
        
        return results
    
    def _check_not_protected(self, path: Path) -> ValidationResult:
        """Check if path is not in a protected location."""
        resolved = path.resolve()
        path_str = str(resolved).lower()
        
        for protected in self.PROTECTED_PREFIXES:
            protected_str = str(protected).lower()
            if path_str.startswith(protected_str):
                return ValidationResult(
                    passed=False,
                    message=f"Path is inside protected system directory: {protected}",
                    severity=ValidationSeverity.CRITICAL,
                    path=path,
                    check_name="not_protected"
                )
        
        return ValidationResult(
            passed=True,
            message=f"Path is not in protected location: {path}",
            severity=ValidationSeverity.INFO,
            path=path,
            check_name="not_protected"
        )
    
    def _check_permissions(self, path: Path) -> ValidationResult:
        """Check if we have read/write permissions on the path."""
        try:
            # Check if we can list directory contents
            list(path.iterdir())
            
            # Check write permission using os.access
            if os.access(path, os.W_OK):
                return ValidationResult(
                    passed=True,
                    message=f"Have read/write access to: {path}",
                    severity=ValidationSeverity.INFO,
                    path=path,
                    check_name="permissions"
                )
            else:
                return ValidationResult(
                    passed=False,
                    message=f"No write permission for: {path}",
                    severity=ValidationSeverity.ERROR,
                    path=path,
                    check_name="permissions"
                )
        except PermissionError:
            return ValidationResult(
                passed=False,
                message=f"Permission denied accessing: {path}",
                severity=ValidationSeverity.ERROR,
                path=path,
                check_name="permissions"
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Error checking permissions for {path}: {e}",
                severity=ValidationSeverity.WARNING,
                path=path,
                check_name="permissions"
            )
    
    def _check_system_requirements(self) -> List[ValidationResult]:
        """Check system-level requirements."""
        results = []
        
        # Check available disk space on system drive
        import shutil
        try:
            total, used, free = shutil.disk_usage(Path.home())
            if free < self.MIN_FREE_SPACE:
                results.append(ValidationResult(
                    passed=False,
                    message=f"Low disk space: {free / (1024**3):.1f} GB free",
                    severity=ValidationSeverity.WARNING,
                    check_name="disk_space"
                ))
            else:
                results.append(ValidationResult(
                    passed=True,
                    message=f"Adequate disk space: {free / (1024**3):.1f} GB free",
                    severity=ValidationSeverity.INFO,
                    check_name="disk_space"
                ))
        except Exception as e:
            results.append(ValidationResult(
                passed=True,  # Don't block on this
                message=f"Could not check disk space: {e}",
                severity=ValidationSeverity.WARNING,
                check_name="disk_space"
            ))
        
        return results
