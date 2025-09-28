"""
Shader Cache Remover - Main Entry Point

A modular application for detecting and removing shader cache files
from various applications and game engines.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))


def main():
    """Main entry point for the application."""
    try:
        # Import GUI components directly
        from shader_cache_remover.gui.main_window import MainWindow
        import tkinter as tk

        # Create the root window and application
        root = tk.Tk()
        app = MainWindow(root)

        # Set up the window close handler
        root.protocol("WM_DELETE_WINDOW", app.on_closing)

        # Start the main event loop
        root.mainloop()

    except ImportError as e:
        print(f"Error: Could not import required components: {e}")
        print("Please ensure tkinter is installed: pip install tk")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting Shader Cache Remover: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
