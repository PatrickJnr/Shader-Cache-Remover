"""
Setup configuration for the Shader Cache Remover package.

This file configures the shader_cache_remover package for installation
and distribution.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# Read version from __init__.py
init_file = Path(__file__).parent / "shader_cache_remover" / "__init__.py"
version = "1.4.0"  # Default version
if init_file.exists():
    content = init_file.read_text(encoding="utf-8")
    for line in content.splitlines():
        if line.startswith('__version__ = "'):
            version = line.split('"')[1]
            break

setup(
    name="shader-cache-remover",
    version=version,
    description="A modular application for cleaning shader cache files from various applications and game engines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="PatrickJnr",
    author_email="patrick@example.com",  # Update with actual email
    url="https://github.com/PatrickJnr/Shader-Cache-Remover",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies
        "tkinter",  # Usually included with Python
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "shader-cache-remover=shader_cache_remover.main:main",
        ],
        "gui_scripts": [
            "shader-cache-remover-gui=shader_cache_remover.main:main",
        ],
    },
    package_data={
        "shader_cache_remover": [
            "README.md",
            "LICENSE",
            "CHANGELOG.md",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
