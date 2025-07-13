import shutil
import logging
import os
import platform
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import queue
import webbrowser
import logging.handlers
from pathlib import Path
import datetime
import json
import time
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from dataclasses import dataclass

try:
    import winreg  # For reading the registry on Windows
except ImportError:
    winreg = None


@dataclass
class CleanupStats:
    """Statistics for cleanup operation."""

    files_deleted: int = 0
    directories_deleted: int = 0
    bytes_freed: int = 0
    errors: int = 0
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None


class ShaderCacheRemoverApp:
    """Main application class for the Shader Cache Remover."""

    def __init__(self, root):
        self.root = root
        self.root.title("Shader Cache Remover")
        self.root.geometry("1250x600")
        self.root.resizable(True, True)

        # Application state
        self.cleanup_thread: Optional[threading.Thread] = None
        self.dry_run_mode: bool = False
        self.backup_dir: Optional[Path] = None
        self.is_cleaning: bool = False
        self.cleanup_stats = CleanupStats()
        self.config = self.load_config()

        # Set up Catppuccin theme
        self.setup_catppuccin_theme()

        # Create GUI
        self.create_gui()

        # Queue for logging messages from other threads
        self.log_queue = queue.Queue()

        # Set up the logger
        self.setup_logger()

        # Load and apply saved configuration
        self.apply_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        config_path = Path.home() / ".shader_cache_remover_config.json"
        default_config = {
            "auto_backup": False,
            "backup_location": str(Path.home() / "ShaderCacheBackups"),
            "show_progress": True,
            "detailed_logging": True,
            "custom_paths": [],
        }

        try:
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_config.items():
                        config.setdefault(key, value)
                    return config
        except Exception as e:
            logging.warning(f"Could not load config: {e}")

        return default_config

    def save_config(self):
        """Save configuration to file."""
        config_path = Path.home() / ".shader_cache_remover_config.json"
        try:
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.warning(f"Could not save config: {e}")

    def setup_catppuccin_theme(self):
        """Apply Catppuccin Mocha theme to the app."""
        # Catppuccin Mocha colors
        colors = {
            "base": "#1e1e2e",  # Main background
            "surface0": "#313244",  # Secondary background
            "surface1": "#45475a",  # Tertiary background
            "surface2": "#585b70",  # Quaternary background
            "overlay0": "#6c7086",  # Overlays
            "overlay1": "#7f849c",  # Overlays
            "overlay2": "#9399b2",  # Overlays
            "text": "#cdd6f4",  # Main text
            "subtext0": "#a6adc8",  # Secondary text
            "subtext1": "#bac2de",  # Tertiary text
            "lavender": "#b4befe",  # Accent
            "blue": "#89b4fa",  # Primary
            "sapphire": "#74c7ec",  # Info
            "sky": "#89dceb",  # Info alt
            "teal": "#94e2d5",  # Success
            "green": "#a6e3a1",  # Success alt
            "yellow": "#f9e2af",  # Warning
            "peach": "#fab387",  # Warning alt
            "maroon": "#eba0ac",  # Error
            "red": "#f38ba8",  # Error alt
            "mauve": "#cba6f7",  # Accent alt
            "pink": "#f5c2e7",  # Accent alt 2
            "flamingo": "#f2cdcd",  # Accent alt 3
            "rosewater": "#f5e0dc",  # Accent alt 4
        }

        # Set main window background
        self.root.configure(bg=colors["base"])

        # Configure ttk styles
        style = ttk.Style()

        # Configure general styles
        style.configure("TFrame", background=colors["base"])
        style.configure(
            "TLabel",
            background=colors["base"],
            foreground=colors["text"],
            font=("Segoe UI", 10),
        )

        # Configure buttons
        style.configure(
            "TButton",
            background=colors["surface0"],
            foreground=colors["text"],
            borderwidth=1,
            focuscolor="none",
            padding=(10, 6),
        )
        style.map(
            "TButton",
            background=[
                ("active", colors["surface1"]),
                ("pressed", colors["surface2"]),
            ],
        )

        # Configure checkbuttons
        style.configure(
            "TCheckbutton",
            background=colors["base"],
            foreground=colors["text"],
            focuscolor="none",
        )
        style.map("TCheckbutton", background=[("active", colors["surface0"])])

        # Configure entry widgets
        style.configure(
            "TEntry",
            fieldbackground=colors["surface0"],
            foreground=colors["text"],
            borderwidth=1,
            insertcolor=colors["text"],
        )
        style.map("TEntry", focuscolor=[("focus", colors["blue"])])

        # Configure progressbar
        style.configure(
            "TProgressbar",
            background=colors["blue"],
            troughcolor=colors["surface0"],
            borderwidth=0,
            lightcolor=colors["blue"],
            darkcolor=colors["blue"],
        )

        # Configure notebook (tabs)
        style.configure("TNotebook", background=colors["base"], tabmargins=[2, 5, 2, 0])
        style.configure(
            "TNotebook.Tab",
            background=colors["surface0"],
            foreground=colors["subtext0"],
            padding=[12, 6],
            borderwidth=1,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", colors["surface1"])],
            foreground=[("selected", colors["text"])],
        )

        # Store colors for use in other widgets
        self.colors = colors

    def create_gui(self):
        """Create the main GUI."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title and version
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        self.version_label = ttk.Label(
            title_frame,
            text="Shader Cache Remover - Version 1.4.0",
            font=("Segoe UI", 12, "bold"),
            foreground=self.colors["text"],
        )
        self.version_label.pack(side=tk.LEFT)

        # Settings button
        self.settings_button = tk.Button(
            title_frame,
            text="Settings",
            command=self.open_settings,
            bg=self.colors["surface0"],
            fg=self.colors["text"],
            activebackground=self.colors["surface1"],
            activeforeground=self.colors["text"],
            font=("Segoe UI", 10),
            relief="flat",
            borderwidth=1,
            padx=15,
            pady=5,
        )
        self.settings_button.pack(side=tk.RIGHT)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame, variable=self.progress_var, maximum=100, length=400
        )
        self.progress_bar.pack(pady=(0, 10), fill=tk.X)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            foreground=self.colors["subtext1"],
        )
        self.status_label.pack(pady=(0, 10))

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        # Buttons with Catppuccin colors
        self.start_button = tk.Button(
            button_frame,
            text="Start Cleanup",
            command=self.start_cleanup,
            bg=self.colors["green"],
            fg=self.colors["base"],
            activebackground=self.colors["teal"],
            activeforeground=self.colors["base"],
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=8,
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.dry_run_button = tk.Button(
            button_frame,
            text="Dry Run",
            command=self.start_dry_run,
            bg=self.colors["sapphire"],
            fg=self.colors["base"],
            activebackground=self.colors["sky"],
            activeforeground=self.colors["base"],
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=8,
        )
        self.dry_run_button.pack(side=tk.LEFT, padx=5)

        self.backup_button = tk.Button(
            button_frame,
            text="Backup Shaders",
            command=self.start_backup_shaders,
            bg=self.colors["yellow"],
            fg=self.colors["base"],
            activebackground=self.colors["peach"],
            activeforeground=self.colors["base"],
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=8,
        )
        self.backup_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(
            button_frame,
            text="Stop",
            command=self.stop_cleanup,
            bg=self.colors["red"],
            fg=self.colors["base"],
            activebackground=self.colors["maroon"],
            activeforeground=self.colors["base"],
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=8,
            state="disabled",
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Log output frame
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Log output with Catppuccin colors
        self.log_output = scrolledtext.ScrolledText(
            log_frame,
            width=70,
            height=15,
            wrap=tk.WORD,
            state="disabled",
            bg=self.colors["surface0"],
            fg=self.colors["text"],
            font=("Consolas", 10),
            selectbackground=self.colors["surface1"],
            selectforeground=self.colors["text"],
            insertbackground=self.colors["text"],
        )
        self.log_output.pack(fill=tk.BOTH, expand=True)

        # Bottom frame
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        # Statistics label
        self.stats_var = tk.StringVar(value="")
        self.stats_label = ttk.Label(
            bottom_frame,
            textvariable=self.stats_var,
            font=("Segoe UI", 9),
            foreground=self.colors["subtext1"],
        )
        self.stats_label.pack(side=tk.LEFT)

        # Repository link
        self.repo_label = ttk.Label(
            bottom_frame,
            text="Visit GitHub Repository",
            foreground=self.colors["blue"],
            cursor="hand2",
            font=("Segoe UI", 9, "underline"),
        )
        self.repo_label.pack(side=tk.RIGHT)
        self.repo_label.bind("<Button-1>", lambda e: self.open_repo_link())

    def apply_config(self):
        """Apply loaded configuration."""
        if self.config["show_progress"]:
            if not self.progress_bar.winfo_exists():
                self.progress_bar.pack(pady=(0, 10), fill=tk.X)
        else:
            if self.progress_bar.winfo_exists():
                self.progress_bar.pack_forget()

    def open_settings(self):
        """Open settings window."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x600")
        settings_window.resizable(True, True)
        settings_window.configure(bg=self.colors["base"])
        settings_window.transient(self.root)
        settings_window.grab_set()

        # Create notebook for tabs
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # General settings tab
        general_frame = ttk.Frame(notebook, padding="10")
        notebook.add(general_frame, text="General")

        # Auto backup option
        auto_backup_var = tk.BooleanVar(value=self.config["auto_backup"])
        auto_backup_check = ttk.Checkbutton(
            general_frame, text="Auto-backup before cleanup", variable=auto_backup_var
        )
        auto_backup_check.pack(anchor=tk.W, pady=5)

        # Detailed logging option
        detailed_logging_var = tk.BooleanVar(value=self.config["detailed_logging"])
        detailed_logging_check = ttk.Checkbutton(
            general_frame, text="Detailed logging", variable=detailed_logging_var
        )
        detailed_logging_check.pack(anchor=tk.W, pady=5)

        # Show progress option
        show_progress_var = tk.BooleanVar(value=self.config["show_progress"])
        show_progress_check = ttk.Checkbutton(
            general_frame, text="Show progress bar", variable=show_progress_var
        )
        show_progress_check.pack(anchor=tk.W, pady=5)

        # Backup location
        ttk.Label(general_frame, text="Backup Location:").pack(
            anchor=tk.W, pady=(10, 0)
        )
        backup_location_var = tk.StringVar(value=self.config["backup_location"])
        backup_entry = ttk.Entry(
            general_frame, textvariable=backup_location_var, width=60
        )
        backup_entry.pack(anchor=tk.W, pady=5, fill=tk.X)

        def browse_backup_location():
            folder = filedialog.askdirectory(initialdir=backup_location_var.get())
            if folder:
                backup_location_var.set(folder)

        browse_button = tk.Button(
            general_frame,
            text="Browse",
            command=browse_backup_location,
            bg=self.colors["surface0"],
            fg=self.colors["text"],
            activebackground=self.colors["surface1"],
            activeforeground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=5,
        )
        browse_button.pack(anchor=tk.W, pady=5)

        # Custom paths tab
        custom_frame = ttk.Frame(notebook, padding="10")
        notebook.add(custom_frame, text="Custom Paths")

        # Instructions
        instructions = ttk.Label(
            custom_frame,
            text="Add custom shader cache directories to scan during cleanup:",
            font=("Segoe UI", 10, "bold"),
            foreground=self.colors["text"],
        )
        instructions.pack(anchor=tk.W, pady=(0, 10))

        # Frame for custom paths list and buttons
        paths_frame = ttk.Frame(custom_frame)
        paths_frame.pack(fill=tk.BOTH, expand=True)

        # Custom paths listbox with scrollbar
        listbox_frame = ttk.Frame(paths_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        custom_paths_listbox = tk.Listbox(
            listbox_frame,
            height=12,
            bg=self.colors["surface0"],
            fg=self.colors["text"],
            selectbackground=self.colors["surface1"],
            selectforeground=self.colors["text"],
            font=("Segoe UI", 10),
            activestyle="none",
            borderwidth=0,
            highlightthickness=0,
        )
        custom_paths_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(
            listbox_frame, orient=tk.VERTICAL, command=custom_paths_listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        custom_paths_listbox.config(yscrollcommand=scrollbar.set)

        # Populate listbox with current custom paths
        for path in self.config["custom_paths"]:
            custom_paths_listbox.insert(tk.END, path)

        # Buttons frame
        buttons_frame = ttk.Frame(paths_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))

        def add_custom_path():
            """Add a new custom path."""
            path = filedialog.askdirectory(
                title="Select Custom Shader Cache Directory", parent=settings_window
            )
            if path:
                # Check if path already exists
                if path not in [
                    custom_paths_listbox.get(i)
                    for i in range(custom_paths_listbox.size())
                ]:
                    custom_paths_listbox.insert(tk.END, path)
                    logging.info(f"Added custom path: {path}")
                else:
                    messagebox.showwarning(
                        "Duplicate Path",
                        "This path is already in the list.",
                        parent=settings_window,
                    )

        def remove_custom_path():
            """Remove selected custom path."""
            selection = custom_paths_listbox.curselection()
            if selection:
                path = custom_paths_listbox.get(selection[0])
                custom_paths_listbox.delete(selection[0])
                logging.info(f"Removed custom path: {path}")
            else:
                messagebox.showwarning(
                    "No Selection",
                    "Please select a path to remove.",
                    parent=settings_window,
                )

        def edit_custom_path():
            """Edit selected custom path."""
            selection = custom_paths_listbox.curselection()
            if selection:
                current_path = custom_paths_listbox.get(selection[0])
                new_path = filedialog.askdirectory(
                    title="Edit Custom Shader Cache Directory",
                    initialdir=current_path,
                    parent=settings_window,
                )
                if new_path and new_path != current_path:
                    # Check if new path already exists
                    existing_paths = [
                        custom_paths_listbox.get(i)
                        for i in range(custom_paths_listbox.size())
                        if i != selection[0]
                    ]
                    if new_path not in existing.paths:
                        custom_paths_listbox.delete(selection[0])
                        custom_paths_listbox.insert(selection[0], new_path)
                        logging.info(
                            f"Updated custom path: {current_path} -> {new_path}"
                        )
                    else:
                        messagebox.showwarning(
                            "Duplicate Path",
                            "This path is already in the list.",
                            parent=settings_window,
                        )
            else:
                messagebox.showwarning(
                    "No Selection",
                    "Please select a path to edit.",
                    parent=settings_window,
                )

        def validate_custom_path():
            """Validate selected custom path."""
            selection = custom_paths_listbox.curselection()
            if selection:
                path = custom_paths_listbox.get(selection[0])
                path_obj = Path(path)
                if path_obj.exists():
                    if path_obj.is_dir():
                        messagebox.showinfo(
                            "Path Valid",
                            f"✓ Path exists and is a directory:\n{path}",
                            parent=settings_window,
                        )
                    else:
                        messagebox.showwarning(
                            "Path Invalid",
                            f"✗ Path exists but is not a directory:\n{path}",
                            parent=settings_window,
                        )
                else:
                    messagebox.showwarning(
                        "Path Invalid",
                        f"✗ Path does not exist:\n{path}",
                        parent=settings_window,
                    )
            else:
                messagebox.showwarning(
                    "No Selection",
                    "Please select a path to validate.",
                    parent=settings_window,
                )

        # Add buttons with Catppuccin styling
        button_style = {
            "bg": self.colors["surface0"],
            "fg": self.colors["text"],
            "activebackground": self.colors["surface1"],
            "activeforeground": self.colors["text"],
            "relief": "flat",
            "borderwidth": 0,
            "padx": 15,
            "pady": 5,
        }

        add_button = tk.Button(
            buttons_frame, text="Add Path", command=add_custom_path, **button_style
        )
        add_button.pack(side=tk.LEFT, padx=(0, 5))

        remove_button = tk.Button(
            buttons_frame,
            text="Remove Path",
            command=remove_custom_path,
            **button_style,
        )
        remove_button.pack(side=tk.LEFT, padx=(0, 5))

        edit_button = tk.Button(
            buttons_frame, text="Edit Path", command=edit_custom_path, **button_style
        )
        edit_button.pack(side=tk.LEFT, padx=(0, 5))

        validate_button = tk.Button(
            buttons_frame,
            text="Validate Path",
            command=validate_custom_path,
            **button_style,
        )
        validate_button.pack(side=tk.LEFT, padx=(0, 5))

        # Info label
        info_label = ttk.Label(
            custom_frame,
            text="Custom paths will be scanned for shader cache files during cleanup.\n"
            "Only add directories that contain shader cache files.",
            font=("Segoe UI", 9),
            foreground=self.colors["subtext0"],
        )
        info_label.pack(anchor=tk.W, pady=(10, 0))

        # Save button (at bottom of settings window)
        save_frame = ttk.Frame(settings_window)
        save_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        def save_settings():
            # Get custom paths from listbox
            custom_paths = [
                custom_paths_listbox.get(i) for i in range(custom_paths_listbox.size())
            ]

            # Update configuration
            self.config["auto_backup"] = auto_backup_var.get()
            self.config["detailed_logging"] = detailed_logging_var.get()
            self.config["show_progress"] = show_progress_var.get()
            self.config["backup_location"] = backup_location_var.get()
            self.config["custom_paths"] = custom_paths

            self.save_config()
            self.apply_config()
            settings_window.destroy()
            messagebox.showinfo("Settings", "Settings saved successfully!")
            logging.info(f"Settings saved with {len(custom_paths)} custom paths")

        save_button = tk.Button(
            save_frame,
            text="Save Settings",
            command=save_settings,
            bg=self.colors["green"],
            fg=self.colors["base"],
            activebackground=self.colors["teal"],
            activeforeground=self.colors["base"],
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=8,
        )
        save_button.pack(side=tk.RIGHT)

        self.root.wait_window(settings_window)

    def setup_logger(self):
        """Set up logging configuration."""
        # Create a handler that sends log messages to the queue
        queue_handler = logging.handlers.QueueHandler(self.log_queue)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        queue_handler.setFormatter(formatter)

        # Get the logger
        logger = logging.getLogger()
        logger.setLevel(
            logging.DEBUG if self.config["detailed_logging"] else logging.INFO
        )
        logger.addHandler(queue_handler)

        # Start the log processing thread
        log_thread = threading.Thread(target=self.process_log_queue, daemon=True)
        log_thread.start()

    def process_log_queue(self):
        """Process log messages from the queue and update the GUI."""
        while True:
            try:
                log_record = self.log_queue.get()
                if log_record is None:
                    break
                self.write_log(log_record)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing log queue: {e}")

    def write_log(self, log_record):
        """Write log message to the GUI text box."""

        def update_gui():
            self.log_output.config(state="normal")
            message = log_record.getMessage()
            timestamp = datetime.datetime.fromtimestamp(log_record.created).strftime(
                "%H:%M:%S"
            )

            # Color code log levels
            level_colors = {
                "INFO": self.colors["blue"],
                "WARNING": self.colors["yellow"],
                "ERROR": self.colors["red"],
                "DEBUG": self.colors["subtext0"],
            }

            level_color = level_colors.get(log_record.levelname, self.colors["text"])

            # Insert timestamp
            self.log_output.insert(tk.END, f"[{timestamp}] ", "timestamp")
            # Insert level with color
            self.log_output.insert(
                tk.END, f"{log_record.levelname}: ", ("level", log_record.levelname)
            )
            # Insert message
            self.log_output.insert(tk.END, f"{message}\n", "message")

            # Configure tags with colors
            self.log_output.tag_configure(
                "timestamp", foreground=self.colors["subtext0"]
            )
            self.log_output.tag_configure("level", foreground=self.colors["text"])
            for level, color in level_colors.items():
                self.log_output.tag_configure(level, foreground=color)

            self.log_output.see(tk.END)
            self.log_output.config(state="disabled")

        self.root.after(0, update_gui)

    def update_status(self, message: str):
        """Update the status label."""
        self.root.after(0, lambda: self.status_var.set(message))

    def update_progress(self, value: float):
        """Update the progress bar."""
        self.root.after(0, lambda: self.progress_var.set(value))

    def update_stats(self):
        """Update statistics display."""
        if self.cleanup_stats.start_time:
            now = datetime.datetime.now()
            elapsed = now - self.cleanup_stats.start_time
            stats_text = (
                f"Files: {self.cleanup_stats.files_deleted} | "
                f"Dirs: {self.cleanup_stats.directories_deleted} | "
                f"Freed: {self.format_bytes(self.cleanup_stats.bytes_freed)} | "
                f"Errors: {self.cleanup_stats.errors} | "
                f"Time: {elapsed.seconds}s"
            )
            self.root.after(0, lambda: self.stats_var.set(stats_text))

    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable format."""
        if bytes_value < 1024:
            return f"{bytes_value} B"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    def start_cleanup(self):
        """Start the shader cache cleanup process."""
        if self.is_cleaning:
            logging.warning("Cleanup already in progress.")
            return

        if self.config["auto_backup"]:
            self.backup_dir = (
                Path(self.config["backup_location"])
                / f"ShaderCacheBackup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            try:
                self.backup_dir.mkdir(parents=True, exist_ok=True)
                logging.info(
                    f"Auto-backup enabled. Backup directory: {self.backup_dir}"
                )
            except Exception as e:
                logging.error(f"Failed to create backup directory: {e}")
                messagebox.showerror("Error", f"Failed to create backup directory: {e}")
                return

        self.dry_run_mode = False
        self._start_cleanup_thread()

    def start_dry_run(self):
        """Simulate the cleanup process without deleting any files."""
        if self.is_cleaning:
            logging.warning("Cleanup already in progress.")
            return

        logging.info("Starting dry run - no files will be deleted.")
        self.dry_run_mode = True
        self.backup_dir = None
        self._start_cleanup_thread()

    def start_backup_shaders(self):
        """Backup the shader cache files before deleting them."""
        if self.is_cleaning:
            logging.warning("Cleanup already in progress.")
            return

        backup_path = filedialog.askdirectory(title="Select Backup Directory")
        if not backup_path:
            logging.warning("Backup cancelled. No directory selected.")
            return

        self.backup_dir = (
            Path(backup_path)
            / f"ShaderCacheBackup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Backup directory created: {self.backup_dir}")
        except Exception as e:
            logging.error(f"Failed to create backup directory: {e}")
            messagebox.showerror("Error", f"Failed to create backup directory: {e}")
            return

        self.dry_run_mode = False
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start the cleanup thread."""
        self.is_cleaning = True
        self.cleanup_stats = CleanupStats(start_time=datetime.datetime.now())

        # Update button states
        self.start_button.config(state="disabled")
        self.dry_run_button.config(state="disabled")
        self.backup_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self.update_status("Initializing cleanup...")
        self.update_progress(0)
        self.update_stats()

        self.cleanup_thread = threading.Thread(target=self.run_cleanup, daemon=True)
        self.cleanup_thread.start()

    def stop_cleanup(self):
        """Stop the cleanup process."""
        if not self.is_cleaning:
            return
        self.is_cleaning = False
        self.update_status("Stopping cleanup...")
        logging.info("Cleanup stopped by user.")

    def get_steam_shader_cache_path(self) -> Optional[Path]:
        """Retrieve Steam installation path from the registry and construct shader cache path."""
        if not winreg or platform.system() != "Windows":
            return None

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"
            ) as reg_key:
                steam_path, _ = winreg.QueryValueEx(reg_key, "SteamPath")

            shader_cache_path = Path(steam_path) / "steamapps" / "shadercache"
            if shader_cache_path.exists():
                logging.info(f"Steam shader cache found at: {shader_cache_path}")
                return shader_cache_path
            else:
                logging.warning("Steam shader cache directory not found.")
                return None
        except FileNotFoundError:
            logging.warning("Steam registry key not found.")
            return None
        except Exception as e:
            logging.error(f"Error reading Steam registry path: {e}")
            return None

    def get_all_drives(self) -> List[Path]:
        """Detect all available drives on the system."""
        drives = []
        if platform.system() == "Windows":
            import string

            for drive_letter in string.ascii_uppercase:
                drive_path = Path(f"{drive_letter}:\\")
                if drive_path.is_dir():
                    drives.append(drive_path)
        else:  # For Unix-like systems
            drives.append(Path("/"))
        return drives

    def get_shader_cache_directories(self) -> List[Path]:
        """Get all shader cache directories to clean."""
        directories = set()

        # Common shader cache directories
        if platform.system() == "Windows":
            common_dirs = [
                Path.home() / "AppData" / "Local" / "NVIDIA" / "DXCache",
                Path.home() / "AppData" / "Local" / "NVIDIA" / "GLCache",
                Path.home() / "AppData" / "Local" / "AMD" / "DxCache",
                Path.home() / "AppData" / "Local" / "AMD" / "GLCache",
                Path.home() / "AppData" / "Local" / "UnrealEngine" / "ShaderCache",
                Path.home() / "AppData" / "LocalLow" / "Unity" / "Caches",
                Path.home()
                / "AppData"
                / "Local"
                / "Temp"
                / "NVIDIA Corporation"
                / "NV_Cache",
                Path.home() / "AppData" / "Local" / "Temp" / "DXCache",
                Path.home() / "AppData" / "Local" / "Temp" / "D3DSCache",
                Path.home() / "AppData" / "Local" / "Temp" / "OpenGLCache",
                Path.home() / "AppData" / "Local" / "Intel" / "ShaderCache",
            ]
            for directory in common_dirs:
                if directory.exists():
                    directories.add(directory)

            # Add Steam shader cache from registry
            steam_cache = self.get_steam_shader_cache_path()
            if steam_cache:
                directories.add(steam_cache)

        # Check all drives for additional Steam installations
        for drive in self.get_all_drives():
            for steam_path_part in [
                "Program Files (x86)/Steam",
                "Program Files/Steam",
                "Steam",
            ]:
                potential_path = drive / steam_path_part / "steamapps" / "shadercache"
                if potential_path.exists():
                    directories.add(potential_path)

        # Add custom paths from config
        for custom_path in self.config.get("custom_paths", []):
            try:
                path = Path(custom_path)
                if path.is_dir():
                    directories.add(path)
                    logging.info(f"Added custom shader cache directory: {path}")
                else:
                    logging.warning(
                        f"Custom path does not exist or is not a directory: {path}"
                    )
            except Exception as e:
                logging.error(f"Error processing custom path '{custom_path}': {e}")

        return sorted(list(directories))

    def calculate_directory_size(self, directory: Path) -> int:
        """Calculate the total size of a directory."""
        total_size = 0
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except FileNotFoundError:
                        continue  # File might have been deleted by another process
        except Exception as e:
            logging.error(f"Error calculating size for {directory}: {e}")
        return total_size

    def backup_directory(self, source: Path, backup_root: Path) -> bool:
        """Backup a directory to the backup location."""
        try:
            # Create a relative path to maintain directory structure in the backup
            relative_path = source.relative_to(Path(source.anchor))
            backup_path = backup_root / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            if source.is_file():
                shutil.copy2(source, backup_path)
            elif source.is_dir():
                shutil.copytree(source, backup_path, dirs_exist_ok=True)

            logging.info(f"Backed up: {source} -> {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to backup {source}: {e}")
            self.cleanup_stats.errors += 1
            return False

    def remove_files_in_directory(self, directory: Path):
        """Delete all files and subdirectories in the specified directory."""
        if not self.is_cleaning:
            return

        try:
            items = list(directory.iterdir())
            total_items = len(items)
            for i, item in enumerate(items):
                if not self.is_cleaning:
                    self.update_status("Cleanup stopped.")
                    break

                try:
                    item_size = 0
                    if item.is_file():
                        item_size = item.stat().st_size
                    elif item.is_dir():
                        item_size = self.calculate_directory_size(item)

                    if self.backup_dir and not self.dry_run_mode:
                        self.backup_directory(item, self.backup_dir)

                    if self.dry_run_mode:
                        logging.info(f"Would delete: {item}")
                    else:
                        if item.is_file():
                            item.unlink()
                            self.cleanup_stats.files_deleted += 1
                        elif item.is_dir():
                            shutil.rmtree(item)
                            self.cleanup_stats.directories_deleted += 1
                        logging.info(
                            f"Deleted: {item} ({self.format_bytes(item_size)})"
                        )

                    self.cleanup_stats.bytes_freed += item_size

                    # Update progress and stats
                    progress = (i + 1) / total_items * 100
                    self.update_progress(progress)
                    self.update_stats()

                except FileNotFoundError:
                    logging.warning(
                        f"File not found during deletion (already removed?): {item}"
                    )
                    continue
                except Exception as e:
                    logging.error(f"Error removing {item}: {e}")
                    self.cleanup_stats.errors += 1

        except Exception as e:
            logging.error(f"Error accessing directory {directory}: {e}")
            self.cleanup_stats.errors += 1

    def run_cleanup(self):
        """Perform the cleanup process in the background."""
        try:
            self.update_status("Scanning for shader cache directories...")
            directories = self.get_shader_cache_directories()

            if not directories:
                logging.warning("No shader cache directories found.")
                self.update_status("No shader cache directories found.")
                return

            logging.info(
                f"Found {len(directories)} shader cache directories to process."
            )

            total_dirs = len(directories)
            for i, cache_dir in enumerate(directories):
                if not self.is_cleaning:
                    break

                self.update_status(f"Processing: {cache_dir.name}")
                logging.info(f"Processing shader cache in: {cache_dir}")

                self.remove_files_in_directory(cache_dir)

                # Update overall progress
                overall_progress = (i + 1) / total_dirs * 100
                self.update_progress(overall_progress)

            if not self.is_cleaning:
                self.update_status("Cleanup stopped.")
                return

            self.cleanup_stats.end_time = datetime.datetime.now()
            elapsed_time = self.cleanup_stats.end_time - self.cleanup_stats.start_time

            if self.dry_run_mode:
                final_message = "Dry run completed."
            else:
                final_message = "Cleanup completed."

            self.update_status(final_message)
            logging.info(f"{final_message} in {elapsed_time.seconds} seconds.")
            logging.info(
                f"Summary: {self.cleanup_stats.files_deleted} files, "
                f"{self.cleanup_stats.directories_deleted} directories deleted. "
                f"Total space freed: {self.format_bytes(self.cleanup_stats.bytes_freed)}. "
                f"Errors: {self.cleanup_stats.errors}"
            )

        except Exception as e:
            logging.error(f"A fatal error occurred during cleanup: {e}", exc_info=True)
            self.update_status("Cleanup failed due to a fatal error.")
        finally:
            self.root.after(0, self.cleanup_finished)

    def cleanup_finished(self):
        """Reset UI after cleanup completion."""
        self.is_cleaning = False

        # Reset button states
        self.start_button.config(state="normal")
        self.dry_run_button.config(state="normal")
        self.backup_button.config(state="normal")
        self.stop_button.config(state="disabled")

        if self.dry_run_mode or self.cleanup_stats.bytes_freed > 0:
            self.update_progress(100)
        else:
            self.update_progress(0)

        self.update_stats()

    def open_repo_link(self):
        """Open the GitHub repository link in the default browser."""
        webbrowser.open("https://github.com/PatrickJnr/Shader-Cache-Remover")

    def on_closing(self):
        """Handle application closing."""
        if self.is_cleaning:
            if messagebox.askokcancel(
                "Quit", "A cleanup is in progress. Are you sure you want to quit?"
            ):
                self.is_cleaning = False
                if self.cleanup_thread and self.cleanup_thread.is_alive():
                    # Give the thread a moment to stop gracefully
                    self.cleanup_thread.join(timeout=0.5)
                self.root.destroy()
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ShaderCacheRemoverApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
