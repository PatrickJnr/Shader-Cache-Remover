import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import webbrowser
import datetime
from pathlib import Path
from typing import Optional

from shader_cache_remover.core.detection_service import DetectionService
from shader_cache_remover.core.cleanup_service import CleanupService, CleanupStats
from shader_cache_remover.core.backup_service import BackupService
from shader_cache_remover.infrastructure.config_manager import ConfigManager
from shader_cache_remover.infrastructure.logging_config import LoggingConfig


class MainWindow:
    """Main application window for Shader Cache Remover."""

    def __init__(self, root: tk.Tk):
        """Initialize the main window."""
        self.root = root
        self.root.title("Shader Cache Remover")
        self.root.geometry("1580x850")
        self.root.minsize(1200, 650)
        self.root.resizable(True, True)

        # Initialize services
        self.config_manager = ConfigManager()
        self.logging_config = LoggingConfig(
            log_level=(
                "DEBUG" if self.config_manager.is_detailed_logging_enabled() else "INFO"
            ),
            detailed=self.config_manager.is_detailed_logging_enabled(),
        )
        self.logging_config.setup_logging()

        # Initialize core services
        self.detection_service = DetectionService(
            self.config_manager.get_custom_paths()
        )
        self.backup_service = BackupService()
        self.cleanup_service = CleanupService(self.backup_service)

        # Application state
        self.cleanup_thread: Optional[threading.Thread] = None
        self.is_cleaning = False
        self.log_queue = queue.Queue()

        # Set up Catppuccin theme colors
        self.colors = self._get_catppuccin_colors()

        # Create GUI
        self._setup_gui()
        self._setup_logging()
        self._apply_theme()

        # Load and apply saved configuration
        self._apply_config()

    def _get_version(self) -> str:
        """Get the application version from version.txt file.

        Returns:
            Version string
        """
        try:
            version_file = Path(__file__).parent.parent / "version.txt"
            if version_file.exists():
                return version_file.read_text().strip()
        except Exception:
            pass
        return "1.5.0"  # Fallback version

    def _get_catppuccin_colors(self) -> dict:
        """Get official Catppuccin Mocha theme colors.

        Returns:
            Dictionary of official Catppuccin Mocha color values
        """
        return {
            "rosewater": "#f5e0dc",
            "flamingo": "#f2cdcd",
            "pink": "#f5c2e7",
            "mauve": "#cba6f7",
            "red": "#f38ba8",
            "maroon": "#eba0ac",
            "peach": "#fab387",
            "yellow": "#f9e2af",
            "green": "#a6e3a1",
            "teal": "#94e2d5",
            "sky": "#89dceb",
            "sapphire": "#74c7ec",
            "blue": "#89b4fa",
            "lavender": "#b4befe",
            "text": "#cdd6f4",
            "subtext1": "#bac2de",
            "subtext0": "#a6adc8",
            "overlay2": "#9399b2",
            "overlay1": "#7f849c",
            "overlay0": "#6c7086",
            "surface2": "#585b70",
            "surface1": "#45475a",
            "surface0": "#313244",
            "base": "#1e1e2e",
            "mantle": "#181825",
            "crust": "#11111b",
        }

    def _setup_gui(self):
        """Set up the main GUI components."""
        self.root.configure(bg=self.colors["base"])

        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self._create_title_section()

        self._create_separator()

        self._create_progress_section()

        self._create_button_section()

        self._create_separator()

        self._create_log_section()

        self._create_status_section()

    def _create_title_section(self):
        """Create the title section with version and settings button."""
        title_frame = tk.Frame(
            self.main_frame,
            bg=self.colors["surface2"],
            highlightbackground=self.colors["overlay0"],
            highlightthickness=1,
            padx=15,
            pady=10,
        )
        title_frame.pack(fill=tk.X, pady=(0, 10), ipady=5)

        self.version_label = tk.Label(
            title_frame,
            text="Shader Cache Remover",
            font=("Segoe UI", 16, "bold"),
            foreground=self.colors["text"],
            background=self.colors["surface2"],
        )
        self.version_label.pack(side=tk.LEFT)

        self.settings_button = tk.Button(
            title_frame,
            text="⚙️ Settings",
            command=self._open_settings,
            bg=self.colors["overlay0"],
            fg=self.colors["text"],
            activebackground=self.colors["overlay1"],
            activeforeground=self.colors["text"],
            font=("Segoe UI", 10, "bold"),
            relief="raised",
            borderwidth=3,
            padx=25,
            pady=10,
            cursor="hand2",
        )
        self.settings_button.pack(side=tk.RIGHT)

        def on_settings_enter(e):
            self.settings_button.config(
                bg=self.colors["mauve"], relief="solid", borderwidth=4
            )

        def on_settings_leave(e):
            self.settings_button.config(
                bg=self.colors["overlay0"], relief="raised", borderwidth=3
            )

        self.settings_button.bind("<Enter>", on_settings_enter)
        self.settings_button.bind("<Leave>", on_settings_leave)

    def _create_separator(self):
        """Create a visual separator between sections."""
        separator_frame = tk.Frame(
            self.main_frame, bg=self.colors["surface2"], height=3
        )
        separator_frame.pack(fill=tk.X, pady=(20, 20))

        gradient_canvas = tk.Canvas(
            separator_frame,
            width=200,
            height=3,
            bg=self.colors["surface2"],
            highlightthickness=0,
        )
        gradient_canvas.pack(fill=tk.X)

        for i in range(3):
            color_intensity = 0.7 + (i * 0.1)
            gradient_color = f"#{int(50*color_intensity):02x}{int(50*color_intensity):02x}{int(82*color_intensity):02x}"
            gradient_canvas.create_line(0, i, 1000, i, fill=gradient_color, width=1)

    def _create_progress_section(self):
        """Create the progress bar and status label with enhanced styling."""
        progress_container = tk.Frame(self.main_frame, bg=self.colors["surface1"])
        progress_container.pack(pady=(0, 10), fill=tk.X)

        self.progress_var = tk.DoubleVar()

        self.progress_frame = tk.Frame(
            progress_container, bg=self.colors["surface0"], height=25
        )
        if self.config_manager.should_show_progress():
            self.progress_frame.pack(pady=(10, 5), padx=15, fill=tk.X, expand=True)

        self.progress_canvas = tk.Canvas(
            self.progress_frame,
            bg=self.colors["surface0"],
            height=20,
            highlightthickness=0,
        )
        self.progress_canvas.pack(fill=tk.BOTH, expand=True, pady=0, padx=0)

        self._draw_custom_progress_bar(0)

        self.progress_bar_rect = None

        self.progress_percentage_var = tk.StringVar(value="0%")
        self.progress_percentage_label = tk.Label(
            progress_container,
            textvariable=self.progress_percentage_var,
            font=("Segoe UI", 9, "bold"),
            foreground=self.colors["pink"],
            background=self.colors["surface1"],
        )
        self.progress_percentage_label.pack(pady=(0, 10))

        self.status_var = tk.StringVar(value="✨ Ready to clean shader caches")
        status_frame = tk.Frame(self.main_frame, bg=self.colors["base"])
        status_frame.pack(pady=(0, 10), fill=tk.X)

        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 12, "italic"),
            foreground=self.colors["subtext1"],
            background=self.colors["base"],
            anchor=tk.W,
            padx=15,
        )
        self.status_label.pack(fill=tk.X)

    def _create_button_section(self):
        """Create the main action buttons with enhanced styling."""
        button_container = tk.Frame(
            self.main_frame, bg=self.colors["surface1"], padx=15, pady=15
        )
        button_container.pack(pady=10)

        accent_border = tk.Frame(button_container, bg=self.colors["overlay1"], height=2)
        accent_border.pack(fill=tk.X, pady=(0, 10))

        button_style = {
            "font": ("Segoe UI", 11, "bold"),
            "relief": "raised",
            "borderwidth": 2,
            "cursor": "hand2",
            "padx": 25,
            "pady": 12,
        }

        start_frame = tk.Frame(button_container, bg=self.colors["surface1"])
        start_frame.pack(side=tk.LEFT, padx=(0, 8))
        self.start_button = tk.Button(
            start_frame,
            text="▶ Start Cleanup",
            command=self._start_cleanup,
            bg=self.colors["green"],
            fg=self.colors["base"],
            activebackground=self.colors["teal"],
            activeforeground=self.colors["base"],
            **button_style,
        )
        self.start_button.pack()

        dry_run_frame = tk.Frame(button_container, bg=self.colors["surface1"])
        dry_run_frame.pack(side=tk.LEFT, padx=8)
        self.dry_run_button = tk.Button(
            dry_run_frame,
            text="🔍 Dry Run",
            command=self._start_dry_run,
            bg=self.colors["sapphire"],
            fg=self.colors["base"],
            activebackground=self.colors["sky"],
            activeforeground=self.colors["base"],
            **button_style,
        )
        self.dry_run_button.pack()

        backup_frame = tk.Frame(button_container, bg=self.colors["surface1"])
        backup_frame.pack(side=tk.LEFT, padx=8)
        self.backup_button = tk.Button(
            backup_frame,
            text="💾 Backup Shaders",
            command=self._start_backup,
            bg=self.colors["yellow"],
            fg=self.colors["base"],
            activebackground=self.colors["peach"],
            activeforeground=self.colors["base"],
            **button_style,
        )
        self.backup_button.pack()

        stop_frame = tk.Frame(button_container, bg=self.colors["surface1"])
        stop_frame.pack(side=tk.LEFT, padx=8)
        self.stop_button = tk.Button(
            stop_frame,
            text="⏹ Stop",
            command=self._stop_cleanup,
            bg=self.colors["red"],
            fg=self.colors["base"],
            activebackground=self.colors["maroon"],
            activeforeground=self.colors["base"],
            **button_style,
            state="disabled",
        )
        self.stop_button.pack()

    def _create_log_section(self):
        """Create the log output section with enhanced styling."""
        log_container = tk.Frame(
            self.main_frame, bg=self.colors["surface2"], padx=10, pady=10
        )
        log_container.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        log_header = tk.Label(
            log_container,
            text="📋 Activity Log",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["surface2"],
            fg=self.colors["text"],
        )
        log_header.pack(anchor=tk.W, pady=(0, 5))

        self.log_output = scrolledtext.ScrolledText(
            log_container,
            width=70,
            height=15,
            wrap=tk.WORD,
            state="disabled",
            bg=self.colors["surface0"],
            fg=self.colors["text"],
            font=("Consolas", 9),
            selectbackground=self.colors["surface1"],
            selectforeground=self.colors["text"],
            insertbackground=self.colors["blue"],
            relief="sunken",
            borderwidth=2,
        )
        self.log_output.pack(fill=tk.BOTH, expand=True)

    def _create_status_section(self):
        """Create the bottom status section with stats and links."""
        bottom_container = tk.Frame(
            self.main_frame, bg=self.colors["surface1"], padx=15, pady=10
        )
        bottom_container.pack(fill=tk.X, pady=(10, 0))

        stats_frame = tk.Frame(bottom_container, bg=self.colors["surface1"])
        stats_frame.pack(side=tk.LEFT)

        stats_title = tk.Label(
            stats_frame,
            text="📊 Statistics:",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["surface1"],
            fg=self.colors["text"],
        )
        stats_title.pack(side=tk.LEFT, padx=(0, 8))

        self.stats_var = tk.StringVar(value="Ready")
        self.stats_label = tk.Label(
            stats_frame,
            textvariable=self.stats_var,
            font=("Segoe UI", 9),
            foreground=self.colors["subtext1"],
            background=self.colors["surface1"],
        )
        self.stats_label.pack(side=tk.LEFT)

        links_frame = tk.Frame(bottom_container, bg=self.colors["surface1"])
        links_frame.pack(side=tk.RIGHT)

        version_text = f"v{self._get_version()}"
        version_label = tk.Label(
            links_frame,
            text=version_text,
            font=("Segoe UI", 8, "italic"),
            bg=self.colors["surface1"],
            fg=self.colors["subtext0"],
        )
        version_label.pack(side=tk.RIGHT, padx=(15, 0))

        self.repo_label = tk.Label(
            links_frame,
            text="🔗 GitHub Repository",
            foreground=self.colors["blue"],
            cursor="hand2",
            font=("Segoe UI", 9, "underline"),
            bg=self.colors["surface1"],
        )
        self.repo_label.pack(side=tk.RIGHT, padx=(15, 0))
        self.repo_label.bind("<Button-1>", lambda e: self._open_repo_link())

    def _setup_logging(self):
        """Set up logging for both console and GUI output."""
        self.logging_config.setup_logging(log_to_file=False)
        logger = self.logging_config.get_logger("shader_cache_remover")
        logger.setLevel(self.logging_config.log_level)

        queue_handler = self.logging_config.create_queue_handler(self.log_queue)
        logger.addHandler(queue_handler)

        log_thread = threading.Thread(target=self._process_log_queue, daemon=True)
        log_thread.start()

    def _process_log_queue(self):
        """Process log messages from the queue and update the GUI."""
        while True:
            try:
                log_record = self.log_queue.get()
                if log_record is None:
                    break
                self._write_log(log_record)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing log queue: {e}")

    def _write_log(self, log_record):
        """Write log message to the GUI text box."""

        def update_gui():
            self.log_output.config(state="normal")
            message = log_record.getMessage()
            timestamp = datetime.datetime.fromtimestamp(log_record.created).strftime(
                "%H:%M:%S"
            )

            level_colors = {
                "INFO": self.colors["blue"],
                "WARNING": self.colors["yellow"],
                "ERROR": self.colors["red"],
                "DEBUG": self.colors["subtext0"],
            }

            level_color = level_colors.get(log_record.levelname, self.colors["text"])

            self.log_output.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.log_output.insert(
                tk.END, f"{log_record.levelname}: ", ("level", log_record.levelname)
            )
            self.log_output.insert(tk.END, f"{message}\n", "message")

            self.log_output.tag_configure(
                "timestamp", foreground=self.colors["subtext0"]
            )
            self.log_output.tag_configure("level", foreground=self.colors["text"])
            for level, color in level_colors.items():
                self.log_output.tag_configure(level, foreground=color)

            self.log_output.see(tk.END)
            self.log_output.config(state="disabled")

        self.root.after(0, update_gui)

    def _apply_theme(self):
        """Apply Catppuccin theme to ttk widgets."""
        style = ttk.Style()

        style.configure("TFrame", background=self.colors["base"])
        style.configure(
            "TLabel",
            background=self.colors["base"],
            foreground=self.colors["text"],
            font=("Segoe UI", 10),
        )

        style.configure(
            "TButton",
            background=self.colors["surface0"],
            foreground=self.colors["text"],
            borderwidth=1,
            focuscolor="none",
            padding=(10, 6),
        )
        style.map(
            "TButton",
            background=[
                ("active", self.colors["surface1"]),
                ("pressed", self.colors["surface2"]),
            ],
        )

        style.configure(
            "TProgressbar",
            background=self.colors["lavender"],
            troughcolor=self.colors["surface0"],
            borderwidth=0,
            lightcolor=self.colors["lavender"],
            darkcolor=self.colors["lavender"],
        )

    def _draw_custom_progress_bar(self, percentage: float):
        """Draw custom progress bar on canvas with enhanced Catppuccin styling."""
        try:
            self.progress_canvas.delete("all")

            canvas_width = self.progress_canvas.winfo_width() or 500
            canvas_height = self.progress_canvas.winfo_height() or 20
            progress_width = (percentage / 100) * canvas_width

            # Background with subtle gradient effect
            self.progress_canvas.create_rectangle(
                0,
                0,
                canvas_width,
                canvas_height,
                fill=self.colors["surface0"],
                outline=self.colors["overlay0"],
                width=1,
                tags="background",
            )

            # Progress fill with Catppuccin colors
            if percentage > 0:
                fill_width = max(progress_width, 2)
                if percentage >= 100:
                    fill_width = canvas_width

                # Use different colors based on progress stage
                if percentage < 30:
                    progress_color = self.colors["blue"]  # Early stage
                elif percentage < 70:
                    progress_color = self.colors["lavender"]  # Mid stage
                elif percentage < 100:
                    progress_color = self.colors["sapphire"]  # Late stage
                else:
                    progress_color = self.colors["green"]  # Complete

                self.progress_bar_rect = self.progress_canvas.create_rectangle(
                    0,
                    0,
                    fill_width,
                    canvas_height,
                    fill=progress_color,
                    outline=self.colors["overlay1"],
                    width=1,
                    tags="progress",
                )

                # Add subtle shine effect
                if percentage > 10:
                    shine_height = max(2, canvas_height // 4)
                    self.progress_canvas.create_rectangle(
                        0,
                        0,
                        fill_width,
                        shine_height,
                        fill=self._lighten_color(progress_color, 0.3),
                        outline="",
                        width=0,
                        tags="shine",
                    )

                # Completion border effect
                if percentage >= 100:
                    self.progress_canvas.create_rectangle(
                        0,
                        0,
                        canvas_width,
                        canvas_height,
                        outline=self.colors["mauve"],
                        width=2,
                        tags="border",
                    )
                    # Add sparkle effect for completion
                    self._add_completion_sparkles(canvas_width, canvas_height)

        except Exception as e:
            print(f"Error drawing custom progress bar: {e}")

    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """Lighten a hex color by a given factor.

        Args:
            hex_color: Hex color string (e.g., "#89b4fa")
            factor: Lightening factor (0.0 = no change, 1.0 = white)

        Returns:
            Lightened hex color string
        """
        try:
            # Remove the # if present
            hex_color = hex_color.lstrip("#")

            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            # Lighten each component
            r = int(r + (255 - r) * factor)
            g = int(g + (255 - g) * factor)
            b = int(b + (255 - b) * factor)

            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return hex_color

    def _add_completion_sparkles(self, width: int, height: int):
        """Add sparkle effects when progress is complete.

        Args:
            width: Canvas width
            height: Canvas height
        """
        try:
            # Add small sparkle dots at random positions
            import random

            for _ in range(8):
                x = random.randint(0, width)
                y = random.randint(0, height)
                sparkle_color = random.choice(
                    [
                        self.colors["yellow"],
                        self.colors["pink"],
                        self.colors["mauve"],
                        self.colors["blue"],
                    ]
                )

                # Draw small sparkle (2x2 pixel)
                self.progress_canvas.create_rectangle(
                    x,
                    y,
                    x + 2,
                    y + 2,
                    fill=sparkle_color,
                    outline=sparkle_color,
                    width=0,
                    tags="sparkle",
                )

                # Add subtle glow effect
                self.progress_canvas.create_oval(
                    x - 1,
                    y - 1,
                    x + 3,
                    y + 3,
                    fill="",
                    outline=self._lighten_color(sparkle_color, 0.5),
                    width=1,
                    tags="glow",
                )
        except Exception as e:
            print(f"Error adding completion sparkles: {e}")

    def _force_progress_bar_color(self):
        """Force override system progress bar styling with direct widget manipulation."""
        try:
            style = ttk.Style()

            current_style = self.progress_bar.cget("style")
            if current_style:
                style.configure(
                    current_style,
                    background=self.colors["pink"],
                    troughcolor=self.colors["surface0"],
                    borderwidth=2,
                    lightcolor=self.colors["pink"],
                    darkcolor=self.colors["pink"],
                )

            self.root.after(100, lambda: self._direct_progress_bar_override())

        except Exception as e:
            print(f"Error in force_progress_bar_color: {e}")

    def _direct_progress_bar_override(self):
        """Direct widget manipulation to override progress bar colors."""
        try:
            if self.progress_bar.winfo_exists():
                children = self.progress_bar.winfo_children()
                for child in children:
                    if child.winfo_class() == "Canvas":
                        try:
                            child.configure(background=self.colors["pink"])
                        except:
                            pass
        except Exception as e:
            print(f"Error in direct_progress_bar_override: {e}")

    def _apply_config(self):
        """Apply loaded configuration to the GUI."""
        if not self.config_manager.should_show_progress():
            if self.progress_bar.winfo_exists():
                self.progress_bar.pack_forget()

    def _update_status(self, message: str):
        """Update the status label."""
        self.root.after(0, lambda: self.status_var.set(message))

    def _update_progress(self, value: float):
        """Update the progress bar and percentage label."""

        def update_gui():
            self.progress_var.set(value)
            self.progress_percentage_var.set(f"{value:.1f}%")

            self._draw_custom_progress_bar(value)

        self.root.after(0, update_gui)

    def _update_stats(self, stats: CleanupStats):
        """Update statistics display."""
        if stats.start_time:
            elapsed = datetime.datetime.now() - stats.start_time
            stats_text = (
                f"Files: {stats.files_deleted} | "
                f"Dirs: {stats.directories_deleted} | "
                f"Freed: {self._format_bytes(stats.bytes_freed)} | "
                f"Errors: {stats.errors} | "
                f"Time: {elapsed.seconds}s"
            )
            self.root.after(0, lambda: self.stats_var.set(stats_text))

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable format."""
        if bytes_value < 1024:
            return f"{bytes_value} B"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    def _start_cleanup(self):
        """Start the shader cache cleanup process."""
        if self.is_cleaning:
            self.logging_config.get_logger(__name__).warning(
                "Cleanup already in progress."
            )
            return

        if self.config_manager.is_auto_backup_enabled():
            backup_path = (
                self.config_manager.get_backup_location()
                / f"ShaderCacheBackup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.backup_service.set_backup_root(backup_path)
            self.logging_config.get_logger(__name__).info(
                f"Auto-backup enabled. Backup directory: {backup_path}"
            )

        self._start_cleanup_thread(dry_run=False)

    def _start_dry_run(self):
        """Start a dry run cleanup process."""
        if self.is_cleaning:
            self.logging_config.get_logger(__name__).warning(
                "Cleanup already in progress."
            )
            return

        self.logging_config.get_logger(__name__).info(
            "Starting dry run - no files will be deleted."
        )
        self.backup_service.set_backup_root(None)
        self._start_cleanup_thread(dry_run=True)

    def _start_backup(self):
        """Start a backup-only operation using configured backup location."""
        if self.is_cleaning:
            self.logging_config.get_logger(__name__).warning(
                "Operation already in progress."
            )
            return

        # Use the configured backup location
        backup_base_path = self.config_manager.get_backup_location()
        backup_path = (
            backup_base_path
            / f"ShaderCacheBackup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        try:
            # Ensure backup directory exists
            backup_path.mkdir(parents=True, exist_ok=True)
            self.backup_service.set_backup_root(backup_path)
            self.logging_config.get_logger(__name__).info(
                f"Backup directory: {backup_path}"
            )

            # Start backup-only thread (not cleanup)
            self._start_backup_thread()
        except Exception as e:
            self.logging_config.get_logger(__name__).error(
                f"Failed to create backup directory: {e}"
            )
            self._update_status("Failed to create backup directory. Check permissions.")

    def _start_backup_thread(self):
        """Start the backup-only thread."""
        self.is_cleaning = True

        # Disable buttons during backup
        self.start_button.config(state="disabled")
        self.dry_run_button.config(state="disabled")
        self.backup_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self._update_status("Starting backup...")
        self._update_progress(0)

        self.cleanup_thread = threading.Thread(
            target=self._run_backup_only, daemon=True
        )
        self.cleanup_thread.start()

    def _run_backup_only(self):
        """Run backup-only operation without cleanup."""
        try:
            directories = self.detection_service.get_all_shader_cache_directories()

            if not directories:
                self.logging_config.get_logger(__name__).warning(
                    "No shader cache directories found."
                )
                self._update_status("No shader cache directories found.")
                return

            self.logging_config.get_logger(__name__).info(
                f"Found {len(directories)} shader cache directories to backup."
            )

            def progress_callback(progress: float):
                self._update_progress(progress)

            # Only backup, don't cleanup
            stats = self.backup_service.backup_directories(
                directories, progress_callback=progress_callback
            )

            self._update_stats_backup(stats)

        except Exception as e:
            self.logging_config.get_logger(__name__).error(
                f"Backup failed: {e}", exc_info=True
            )
            self._update_status("Backup failed due to an error.")
        finally:
            self.root.after(0, self._backup_finished)

    def _backup_finished(self):
        """Reset UI after backup completion."""
        self.is_cleaning = False

        self.start_button.config(state="normal")
        self.dry_run_button.config(state="normal")
        self.backup_button.config(state="normal")
        self.stop_button.config(state="disabled")

        self._update_progress(100)
        self._update_status("Backup completed successfully!")

    def _update_stats_backup(self, stats):
        """Update statistics display for backup operation."""
        if stats.start_time and stats.end_time:
            elapsed = stats.end_time - stats.start_time
            stats_text = (
                f"Files: {stats.files_backed_up} | "
                f"Dirs: {stats.directories_backed_up} | "
                f"Backed up: {self._format_bytes(stats.bytes_backed_up)} | "
                f"Errors: {stats.errors} | "
                f"Time: {elapsed:.1f}s"
            )
            self.root.after(0, lambda: self.stats_var.set(stats_text))

    def _start_cleanup_thread(self, dry_run: bool):
        """Start the cleanup thread."""
        self.is_cleaning = True

        self.start_button.config(state="disabled")
        self.dry_run_button.config(state="disabled")
        self.backup_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self._update_status("Initializing cleanup...")
        self._update_progress(0)

        self.cleanup_thread = threading.Thread(
            target=self._run_cleanup, args=(dry_run,), daemon=True
        )
        self.cleanup_thread.start()

    def _run_cleanup(self, dry_run: bool):
        """Run the cleanup process in the background."""
        try:
            directories = self.detection_service.get_all_shader_cache_directories()

            if not directories:
                self.logging_config.get_logger(__name__).warning(
                    "No shader cache directories found."
                )
                self._update_status("No shader cache directories found.")
                return

            self.logging_config.get_logger(__name__).info(
                f"Found {len(directories)} shader cache directories to process."
            )

            def progress_callback(progress: float):
                self._update_progress(progress)

            stats = self.cleanup_service.cleanup_directories(
                directories, dry_run=dry_run, progress_callback=progress_callback
            )

            self._update_stats(stats)

        except Exception as e:
            self.logging_config.get_logger(__name__).error(
                f"Cleanup failed: {e}", exc_info=True
            )
            self._update_status("Cleanup failed due to a fatal error.")
        finally:
            self.root.after(0, self._cleanup_finished)

    def _cleanup_finished(self):
        """Reset UI after cleanup completion."""
        self.is_cleaning = False

        self.start_button.config(state="normal")
        self.dry_run_button.config(state="normal")
        self.backup_button.config(state="normal")
        self.stop_button.config(state="disabled")

        if not self.cleanup_service.stats.bytes_freed:
            self._update_progress(0)
        else:
            self._update_progress(100)

        self._update_stats(self.cleanup_service.stats)

    def _stop_cleanup(self):
        """Stop the cleanup process."""
        if not self.is_cleaning:
            return
        self.is_cleaning = False
        self.cleanup_service.stop_cleanup()
        self._update_status("Stopping cleanup...")

    def _open_settings(self):
        """Open the settings dialog."""
        from .settings_dialog import SettingsDialog

        settings_dialog = SettingsDialog(self.root, self.config_manager, self.colors)
        self.root.wait_window(settings_dialog.window)

        self._apply_config()

    def _open_repo_link(self):
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
                    self.cleanup_thread.join(timeout=0.5)
                self.root.destroy()
        else:
            self.root.destroy()
