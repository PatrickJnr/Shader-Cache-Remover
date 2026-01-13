"""
Main application window for Shader Cache Remover.

A clean, modern GUI using a professional Windows Fluent-inspired design.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import webbrowser
import datetime
from pathlib import Path
from typing import Optional

from shader_cache_remover.core.detection_service import DetectionService
from shader_cache_remover.core.cleanup_service import CleanupService, CleanupStats
from shader_cache_remover.core.backup_service import BackupService
from shader_cache_remover.core.history_service import HistoryService
from shader_cache_remover.infrastructure.config_manager import ConfigManager
from shader_cache_remover.infrastructure.logging_config import LoggingConfig


class MainWindow:
    """Main application window for Shader Cache Remover."""

    def __init__(self, root: tk.Tk):
        """Initialize the main window."""
        self.root = root
        self.root.title("Shader Cache Remover")
        self.root.geometry("1100x700")
        self.root.minsize(900, 550)
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
            config_manager=self.config_manager,
            custom_paths=self.config_manager.get_custom_paths()
        )
        self.backup_service = BackupService()
        self.cleanup_service = CleanupService(self.backup_service)
        self.history_service = HistoryService()

        # Application state
        self.cleanup_thread: Optional[threading.Thread] = None
        self.is_cleaning = False
        self.log_queue = queue.Queue()

        # Set up modern theme colors
        self.colors = self._get_theme_colors()

        # Create GUI
        self._setup_gui()
        self._setup_logging()
        self._apply_theme()

        # Load and apply saved configuration
        self._apply_config()

    def _get_version(self) -> str:
        """Get the application version from version.txt file."""
        try:
            version_file = Path(__file__).parent.parent / "version.txt"
            if version_file.exists():
                return version_file.read_text().strip()
        except Exception:
            pass
        return "1.5.0"

    def _get_theme_colors(self) -> dict:
        """Get modern clean theme colors.
        
        A professional dark theme inspired by Windows Fluent Design.
        """
        return {
            # Background layers
            "bg_primary": "#1a1a1a",      # Main background
            "bg_secondary": "#252525",     # Card/section background
            "bg_tertiary": "#2d2d2d",      # Elevated elements
            "bg_input": "#333333",         # Input fields
            
            # Text colors
            "text_primary": "#ffffff",     # Primary text
            "text_secondary": "#b0b0b0",   # Secondary/muted text
            "text_disabled": "#666666",    # Disabled text
            
            # Accent colors
            "accent": "#0078d4",           # Windows blue accent
            "accent_hover": "#1a86db",     # Lighter accent
            "accent_pressed": "#005a9e",   # Darker accent
            
            # Semantic colors
            "success": "#107c10",          # Green - success
            "success_light": "#13a113",    # Light green
            "warning": "#ca5010",          # Orange - warning
            "error": "#d13438",            # Red - error
            "info": "#0078d4",             # Blue - info
            
            # Border and dividers
            "border": "#3d3d3d",           # Subtle border
            "border_focus": "#0078d4",     # Focus border
            "divider": "#404040",          # Section dividers
            
            # Progress bar
            "progress_bg": "#333333",
            "progress_fill": "#0078d4",
            "progress_complete": "#107c10",
        }

    def _setup_gui(self):
        """Set up the main GUI components."""
        self.root.configure(bg=self.colors["bg_primary"])

        # Main container with padding
        self.main_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        self._create_header()
        self._create_progress_section()
        self._create_button_section()
        self._create_provider_toggles()
        self._create_log_section()
        self._create_footer()

    def _create_header(self):
        """Create the header with title and settings."""
        header_frame = tk.Frame(self.main_frame, bg=self.colors["bg_primary"])
        header_frame.pack(fill=tk.X, pady=(0, 15))

        # Title
        title_label = tk.Label(
            header_frame,
            text="Shader Cache Remover",
            font=("Segoe UI", 20, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_primary"],
        )
        title_label.pack(side=tk.LEFT)

        # Settings button
        self.settings_button = tk.Button(
            header_frame,
            text="⚙ Settings",
            command=self._open_settings,
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["accent"],
            activeforeground=self.colors["text_primary"],
            font=("Segoe UI", 10),
            relief="flat",
            padx=15,
            pady=6,
            cursor="hand2",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
        )
        self.settings_button.pack(side=tk.RIGHT)
        self._add_hover_effect(self.settings_button, self.colors["bg_tertiary"], self.colors["accent"])

    def _create_progress_section(self):
        """Create the progress bar and status section."""
        # Status card
        status_card = tk.Frame(
            self.main_frame,
            bg=self.colors["bg_secondary"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        status_card.pack(fill=tk.X, pady=(0, 15))

        inner_frame = tk.Frame(status_card, bg=self.colors["bg_secondary"])
        inner_frame.pack(fill=tk.X, padx=15, pady=12)

        # Status label
        self.status_var = tk.StringVar(value="Ready to clean shader caches")
        self.status_label = tk.Label(
            inner_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 11),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_secondary"],
            anchor=tk.W,
        )
        self.status_label.pack(fill=tk.X, pady=(0, 10))

        # Progress bar container
        self.progress_var = tk.DoubleVar()
        progress_frame = tk.Frame(inner_frame, bg=self.colors["bg_secondary"])
        if self.config_manager.should_show_progress():
            progress_frame.pack(fill=tk.X)

        # Custom progress canvas
        self.progress_canvas = tk.Canvas(
            progress_frame,
            bg=self.colors["progress_bg"],
            height=8,
            highlightthickness=0,
        )
        self.progress_canvas.pack(fill=tk.X, pady=(0, 5))

        # Progress percentage
        self.progress_percentage_var = tk.StringVar(value="0%")
        self.progress_percentage_label = tk.Label(
            progress_frame,
            textvariable=self.progress_percentage_var,
            font=("Segoe UI", 9),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_secondary"],
        )
        self.progress_percentage_label.pack(anchor=tk.E)

        # Bind resize event to redraw progress bar
        self.progress_canvas.bind("<Configure>", lambda e: self._draw_progress_bar(self.progress_var.get()))

        self._draw_progress_bar(0)

    def _create_button_section(self):
        """Create the action buttons."""
        button_frame = tk.Frame(self.main_frame, bg=self.colors["bg_primary"])
        button_frame.pack(fill=tk.X, pady=(0, 15))

        button_style = {
            "font": ("Segoe UI", 10, "bold"),
            "relief": "flat",
            "cursor": "hand2",
            "padx": 20,
            "pady": 10,
            "bd": 0,
            "highlightthickness": 0,
        }

        # Start Cleanup button (primary)
        self.start_button = tk.Button(
            button_frame,
            text="▶  Start Cleanup",
            command=self._start_cleanup,
            bg=self.colors["success"],
            fg="#ffffff",
            activebackground=self.colors["success_light"],
            activeforeground="#ffffff",
            **button_style,
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 8))
        self._add_hover_effect(self.start_button, self.colors["success"], self.colors["success_light"])

        # Dry Run button
        self.dry_run_button = tk.Button(
            button_frame,
            text="🔍  Dry Run",
            command=self._start_dry_run,
            bg=self.colors["accent"],
            fg="#ffffff",
            activebackground=self.colors["accent_hover"],
            activeforeground="#ffffff",
            **button_style,
        )
        self.dry_run_button.pack(side=tk.LEFT, padx=8)
        self._add_hover_effect(self.dry_run_button, self.colors["accent"], self.colors["accent_hover"])

        # Backup button
        self.backup_button = tk.Button(
            button_frame,
            text="💾  Backup",
            command=self._start_backup,
            bg=self.colors["warning"],
            fg="#ffffff",
            activebackground="#da5812",
            activeforeground="#ffffff",
            **button_style,
        )
        self.backup_button.pack(side=tk.LEFT, padx=8)
        self._add_hover_effect(self.backup_button, self.colors["warning"], "#da5812")

        # Stop button
        self.stop_button = tk.Button(
            button_frame,
            text="⏹  Stop",
            command=self._stop_cleanup,
            bg=self.colors["error"],
            fg="#ffffff",
            activebackground="#e74c3c",
            activeforeground="#ffffff",
            state="disabled",
            **button_style,
        )
        self.stop_button.pack(side=tk.LEFT, padx=8)
        self._add_hover_effect(self.stop_button, self.colors["error"], "#e74c3c")

        # Spacer
        spacer = tk.Frame(button_frame, bg=self.colors["bg_primary"], width=20)
        spacer.pack(side=tk.LEFT)

        # Restore button
        restore_button = tk.Button(
            button_frame,
            text="🔄 Restore",
            command=self._open_restore_dialog,
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["accent"],
            activeforeground="#ffffff",
            font=("Segoe UI", 10),
            relief="flat",
            padx=15,
            pady=10,
            cursor="hand2",
        )
        restore_button.pack(side=tk.LEFT, padx=4)

        # History button
        history_button = tk.Button(
            button_frame,
            text="📊 History",
            command=self._open_history_dialog,
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["accent"],
            activeforeground="#ffffff",
            font=("Segoe UI", 10),
            relief="flat",
            padx=15,
            pady=10,
            cursor="hand2",
        )
        history_button.pack(side=tk.LEFT, padx=4)

    def _create_provider_toggles(self):
        """Create the provider toggles section."""
        # Collapsible container
        toggle_card = tk.Frame(
            self.main_frame,
            bg=self.colors["bg_secondary"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        toggle_card.pack(fill=tk.X, pady=(0, 15))

        # Header with expand/collapse
        header_frame = tk.Frame(toggle_card, bg=self.colors["bg_secondary"])
        header_frame.pack(fill=tk.X, padx=12, pady=(8, 0))

        self.toggle_expanded = tk.BooleanVar(value=False)
        self.toggle_arrow = tk.Label(
            header_frame,
            text="▶",
            font=("Segoe UI", 9),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_secondary"],
            cursor="hand2",
        )
        self.toggle_arrow.pack(side=tk.LEFT)

        header_label = tk.Label(
            header_frame,
            text="Cache Providers",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_secondary"],
            cursor="hand2",
        )
        header_label.pack(side=tk.LEFT, padx=(5, 0))

        # Provider count label
        providers = self.detection_service.get_provider_info()
        enabled_count = sum(1 for p in providers if p.is_enabled and p.is_available)
        self.provider_count_label = tk.Label(
            header_frame,
            text=f"({enabled_count}/{len(providers)} enabled)",
            font=("Segoe UI", 9),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_secondary"],
        )
        self.provider_count_label.pack(side=tk.LEFT, padx=(10, 0))

        # Collapsible content frame
        self.provider_content = tk.Frame(toggle_card, bg=self.colors["bg_secondary"])
        
        # Create checkbox variables and widgets
        self.provider_vars = {}
        
        checkbox_frame = tk.Frame(self.provider_content, bg=self.colors["bg_secondary"])
        checkbox_frame.pack(fill=tk.X, padx=12, pady=(5, 10))

        for i, provider in enumerate(providers):
            var = tk.BooleanVar(value=provider.is_enabled and provider.is_available)
            self.provider_vars[provider.name] = var

            # Create checkbox
            cb = tk.Checkbutton(
                checkbox_frame,
                text=provider.display_name,
                variable=var,
                command=lambda n=provider.name: self._on_provider_toggle(n),
                font=("Segoe UI", 9),
                bg=self.colors["bg_secondary"],
                fg=self.colors["text_primary"] if provider.is_available else self.colors["text_disabled"],
                activebackground=self.colors["bg_secondary"],
                activeforeground=self.colors["text_primary"],
                selectcolor=self.colors["bg_input"],
                state="normal" if provider.is_available else "disabled",
                cursor="hand2" if provider.is_available else "arrow",
            )
            
            # Grid layout - 4 columns
            row = i // 4
            col = i % 4
            cb.grid(row=row, column=col, sticky=tk.W, padx=(0, 20), pady=2)

        # Bind click events for expand/collapse
        def toggle_expand(e=None):
            if self.toggle_expanded.get():
                self.provider_content.pack_forget()
                self.toggle_arrow.config(text="▶")
                self.toggle_expanded.set(False)
            else:
                self.provider_content.pack(fill=tk.X)
                self.toggle_arrow.config(text="▼")
                self.toggle_expanded.set(True)

        self.toggle_arrow.bind("<Button-1>", toggle_expand)
        header_label.bind("<Button-1>", toggle_expand)

    def _on_provider_toggle(self, provider_name: str):
        """Handle provider toggle checkbox change."""
        enabled = self.provider_vars[provider_name].get()
        
        if enabled:
            self.detection_service.enable_provider(provider_name)
        else:
            self.detection_service.disable_provider(provider_name)
        
        # Update count label
        providers = self.detection_service.get_provider_info()
        enabled_count = sum(1 for p in providers if p.is_enabled and p.is_available)
        self.provider_count_label.config(text=f"({enabled_count}/{len(providers)} enabled)")

    def _create_log_section(self):
        """Create the log output section."""
        # Log card
        log_card = tk.Frame(
            self.main_frame,
            bg=self.colors["bg_secondary"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        log_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Log header
        log_header = tk.Label(
            log_card,
            text="Activity Log",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_primary"],
            anchor=tk.W,
        )
        log_header.pack(fill=tk.X, padx=12, pady=(10, 5))

        # Log output
        self.log_output = scrolledtext.ScrolledText(
            log_card,
            wrap=tk.WORD,
            state="disabled",
            bg=self.colors["bg_input"],
            fg=self.colors["text_primary"],
            font=("Consolas", 9),
            selectbackground=self.colors["accent"],
            selectforeground="#ffffff",
            insertbackground=self.colors["accent"],
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=8,
        )
        self.log_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def _create_footer(self):
        """Create the footer with stats and links."""
        footer_frame = tk.Frame(self.main_frame, bg=self.colors["bg_primary"])
        footer_frame.pack(fill=tk.X)

        # Stats label
        self.stats_var = tk.StringVar(value="Ready")
        stats_label = tk.Label(
            footer_frame,
            textvariable=self.stats_var,
            font=("Segoe UI", 9),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_primary"],
        )
        stats_label.pack(side=tk.LEFT)

        # Export Report button
        export_button = tk.Button(
            footer_frame,
            text="📄 Export",
            command=self._export_report,
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["accent"],
            activeforeground="#ffffff",
            font=("Segoe UI", 8),
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            bd=0,
        )
        export_button.pack(side=tk.LEFT, padx=(15, 0))

        # Version
        version_label = tk.Label(
            footer_frame,
            text=f"v{self._get_version()}",
            font=("Segoe UI", 9),
            fg=self.colors["text_disabled"],
            bg=self.colors["bg_primary"],
        )
        version_label.pack(side=tk.RIGHT)

        # GitHub link
        self.repo_label = tk.Label(
            footer_frame,
            text="GitHub",
            fg=self.colors["accent"],
            cursor="hand2",
            font=("Segoe UI", 9, "underline"),
            bg=self.colors["bg_primary"],
        )
        self.repo_label.pack(side=tk.RIGHT, padx=(0, 15))
        self.repo_label.bind("<Button-1>", lambda e: self._open_repo_link())

    def _add_hover_effect(self, button: tk.Button, normal_bg: str, hover_bg: str):
        """Add hover effect to a button."""
        def on_enter(e):
            if button["state"] != "disabled":
                button.config(bg=hover_bg)

        def on_leave(e):
            if button["state"] != "disabled":
                button.config(bg=normal_bg)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def _draw_progress_bar(self, percentage: float):
        """Draw the progress bar."""
        try:
            self.progress_canvas.delete("all")

            canvas_width = self.progress_canvas.winfo_width() or 500
            canvas_height = self.progress_canvas.winfo_height() or 8

            # Background (rounded rectangle effect)
            self.progress_canvas.create_rectangle(
                0, 0, canvas_width, canvas_height,
                fill=self.colors["progress_bg"],
                outline="",
            )

            # Progress fill
            if percentage > 0:
                if percentage >= 100:
                    fill_width = canvas_width  # Fill entire width at 100%
                    fill_color = self.colors["progress_complete"]
                else:
                    fill_width = max((percentage / 100) * canvas_width, 2)
                    fill_color = self.colors["progress_fill"]

                self.progress_canvas.create_rectangle(
                    0, 0, fill_width, canvas_height,
                    fill=fill_color,
                    outline="",
                )

        except Exception as e:
            print(f"Error drawing progress bar: {e}")

    def _setup_logging(self):
        """Set up logging for GUI output."""
        self.logging_config.setup_logging(log_to_file=False)
        logger = self.logging_config.get_logger("shader_cache_remover")
        logger.setLevel(self.logging_config.log_level)

        queue_handler = self.logging_config.create_queue_handler(self.log_queue)
        logger.addHandler(queue_handler)

        log_thread = threading.Thread(target=self._process_log_queue, daemon=True)
        log_thread.start()

    def _process_log_queue(self):
        """Process log messages from the queue."""
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
        """Write log message to the GUI."""
        def update_gui():
            self.log_output.config(state="normal")
            message = log_record.getMessage()
            timestamp = datetime.datetime.fromtimestamp(log_record.created).strftime("%H:%M:%S")

            level_colors = {
                "INFO": self.colors["accent"],
                "WARNING": self.colors["warning"],
                "ERROR": self.colors["error"],
                "DEBUG": self.colors["text_disabled"],
            }

            # Insert formatted log entry
            self.log_output.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.log_output.insert(tk.END, f"{log_record.levelname}: ", ("level", log_record.levelname))
            self.log_output.insert(tk.END, f"{message}\n", "message")

            # Configure tags
            self.log_output.tag_configure("timestamp", foreground=self.colors["text_disabled"])
            for level, color in level_colors.items():
                self.log_output.tag_configure(level, foreground=color)

            self.log_output.see(tk.END)
            self.log_output.config(state="disabled")

        self.root.after(0, update_gui)

    def _apply_theme(self):
        """Apply theme to ttk widgets."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=self.colors["bg_primary"])
        style.configure(
            "TLabel",
            background=self.colors["bg_primary"],
            foreground=self.colors["text_primary"],
            font=("Segoe UI", 10),
        )

    def _apply_config(self):
        """Apply loaded configuration."""
        pass  # Progress visibility handled in _create_progress_section

    def _update_status(self, message: str):
        """Update the status label."""
        self.root.after(0, lambda: self.status_var.set(message))

    def _update_progress(self, value: float):
        """Update the progress bar."""
        def update_gui():
            self.progress_var.set(value)
            self.progress_percentage_var.set(f"{value:.0f}%")
            self._draw_progress_bar(value)

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
            self.logging_config.get_logger(__name__).warning("Cleanup already in progress.")
            return

        # Show confirmation dialog
        if not self._show_cleanup_confirmation():
            return

        if self.config_manager.is_auto_backup_enabled():
            backup_path = (
                self.config_manager.get_backup_location()
                / f"ShaderCacheBackup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.backup_service.set_backup_root(backup_path)
            self.logging_config.get_logger(__name__).info(f"Auto-backup enabled. Backup directory: {backup_path}")

        self._start_cleanup_thread(dry_run=False)

    def _show_cleanup_confirmation(self) -> bool:
        """Show confirmation dialog before cleanup.
        
        Returns:
            True if user confirmed, False otherwise.
        """
        # Get cache locations and calculate size
        locations = self.detection_service.get_all_cache_locations()
        
        if not locations:
            messagebox.showinfo(
                "No Caches Found",
                "No shader cache directories were found to clean.",
                parent=self.root
            )
            return False
        
        # Calculate total estimated size
        total_size = 0
        for loc in locations:
            if loc.path.exists():
                try:
                    if loc.path.is_file():
                        total_size += loc.path.stat().st_size
                    else:
                        for f in loc.path.rglob("*"):
                            if f.is_file():
                                total_size += f.stat().st_size
                except (PermissionError, OSError):
                    pass
        
        # Build confirmation message
        providers = self.detection_service.get_provider_info()
        enabled_providers = [p.display_name for p in providers if p.is_enabled and p.is_available]
        
        message = (
            f"Ready to clean shader caches:\n\n"
            f"• Locations: {len(locations)}\n"
            f"• Estimated size: {self._format_bytes(total_size)}\n"
            f"• Providers: {', '.join(enabled_providers[:4])}"
        )
        if len(enabled_providers) > 4:
            message += f" +{len(enabled_providers) - 4} more"
        
        message += "\n\nProceed with cleanup?"
        
        return messagebox.askyesno(
            "Confirm Cleanup",
            message,
            parent=self.root
        )

    def _start_dry_run(self):
        """Start a dry run cleanup process."""
        if self.is_cleaning:
            self.logging_config.get_logger(__name__).warning("Cleanup already in progress.")
            return

        self.logging_config.get_logger(__name__).info("Starting dry run - no files will be deleted.")
        self.backup_service.set_backup_root(None)
        self._start_cleanup_thread(dry_run=True)

    def _start_backup(self):
        """Start a backup-only operation."""
        if self.is_cleaning:
            self.logging_config.get_logger(__name__).warning("Operation already in progress.")
            return

        backup_base_path = self.config_manager.get_backup_location()
        backup_path = (
            backup_base_path
            / f"ShaderCacheBackup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            self.backup_service.set_backup_root(backup_path)
            self.logging_config.get_logger(__name__).info(f"Backup directory: {backup_path}")
            self._start_backup_thread()
        except Exception as e:
            self.logging_config.get_logger(__name__).error(f"Failed to create backup directory: {e}")
            self._update_status("Failed to create backup directory.")

    def _start_backup_thread(self):
        """Start the backup-only thread."""
        self.is_cleaning = True
        self._set_buttons_state(cleaning=True)
        self._update_status("Starting backup...")
        self._update_progress(0)

        self.cleanup_thread = threading.Thread(target=self._run_backup_only, daemon=True)
        self.cleanup_thread.start()

    def _run_backup_only(self):
        """Run backup-only operation."""
        try:
            directories = self.detection_service.get_all_shader_cache_directories()

            if not directories:
                self.logging_config.get_logger(__name__).warning("No shader cache directories found.")
                self._update_status("No shader cache directories found.")
                return

            self.logging_config.get_logger(__name__).info(f"Found {len(directories)} directories to backup.")

            stats = self.backup_service.backup_directories(
                directories, progress_callback=self._update_progress
            )

            self._update_stats_backup(stats)

        except Exception as e:
            self.logging_config.get_logger(__name__).error(f"Backup failed: {e}", exc_info=True)
            self._update_status("Backup failed.")
        finally:
            self.root.after(0, self._operation_finished)

    def _update_stats_backup(self, stats):
        """Update statistics for backup operation."""
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
        self._set_buttons_state(cleaning=True)
        self._update_status("Initializing cleanup...")
        self._update_progress(0)

        self.cleanup_thread = threading.Thread(
            target=self._run_cleanup, args=(dry_run,), daemon=True
        )
        self.cleanup_thread.start()

    def _run_cleanup(self, dry_run: bool):
        """Run the cleanup process."""
        try:
            directories = self.detection_service.get_all_shader_cache_directories()

            if not directories:
                self.logging_config.get_logger(__name__).warning("No shader cache directories found.")
                self._update_status("No shader cache directories found.")
                return

            self.logging_config.get_logger(__name__).info(
                f"Found {len(directories)} shader cache directories to process."
            )

            stats = self.cleanup_service.cleanup_directories(
                directories, dry_run=dry_run, progress_callback=self._update_progress
            )

            self._update_stats(stats)

        except Exception as e:
            self.logging_config.get_logger(__name__).error(f"Cleanup failed: {e}", exc_info=True)
            self._update_status("Cleanup failed.")
        finally:
            self.root.after(0, lambda: self._operation_finished(was_dry_run=dry_run))

    def _operation_finished(self, was_dry_run: bool = False):
        """Reset UI after operation completion."""
        self.is_cleaning = False
        self._set_buttons_state(cleaning=False)

        stats = self.cleanup_service.stats
        
        # Record to history
        if stats.start_time:
            duration = 0.0
            if stats.end_time:
                duration = (stats.end_time - stats.start_time).total_seconds()
            
            providers = self.detection_service.get_provider_info()
            enabled_providers = [p.name for p in providers if p.is_enabled and p.is_available]
            
            self.history_service.record_cleanup(
                files_deleted=stats.files_deleted,
                directories_deleted=stats.directories_deleted,
                bytes_freed=stats.bytes_freed,
                errors=stats.errors,
                skipped=stats.skipped,
                duration_seconds=duration,
                was_dry_run=was_dry_run,
                providers_used=enabled_providers
            )

        if stats.bytes_freed:
            self._update_progress(100)
            self._update_status("Cleanup completed successfully!")
        else:
            self._update_progress(0)

        self._update_stats(stats)

    def _set_buttons_state(self, cleaning: bool):
        """Set button states based on operation status."""
        state = "disabled" if cleaning else "normal"
        stop_state = "normal" if cleaning else "disabled"

        self.start_button.config(state=state)
        self.dry_run_button.config(state=state)
        self.backup_button.config(state=state)
        self.stop_button.config(state=stop_state)

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
        """Open the GitHub repository."""
        webbrowser.open("https://github.com/PatrickJnr/Shader-Cache-Remover")

    def _export_report(self):
        """Export cleanup report to a file."""
        # Ask user for save location
        filename = filedialog.asksaveasfilename(
            title="Export Cleanup Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"ShaderCacheReport_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            parent=self.root,
        )
        
        if not filename:
            return
        
        try:
            stats = self.cleanup_service.stats
            providers = self.detection_service.get_provider_info()
            
            # Build report content
            report = []
            report.append("=" * 60)
            report.append("SHADER CACHE REMOVER - CLEANUP REPORT")
            report.append("=" * 60)
            report.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"Version: {self._get_version()}")
            report.append("")
            
            # Stats section
            report.append("-" * 40)
            report.append("CLEANUP STATISTICS")
            report.append("-" * 40)
            report.append(f"Files Deleted: {stats.files_deleted}")
            report.append(f"Directories Deleted: {stats.directories_deleted}")
            report.append(f"Space Freed: {self._format_bytes(stats.bytes_freed)}")
            report.append(f"Errors: {stats.errors}")
            report.append(f"Skipped: {stats.skipped}")
            if stats.start_time:
                elapsed = (stats.end_time or datetime.datetime.now()) - stats.start_time
                report.append(f"Duration: {elapsed.total_seconds():.1f} seconds")
            report.append("")
            
            # Providers section
            report.append("-" * 40)
            report.append("ENABLED PROVIDERS")
            report.append("-" * 40)
            for p in providers:
                status = "✓" if p.is_enabled and p.is_available else "✗"
                report.append(f"  {status} {p.display_name}")
            report.append("")
            
            # Log section
            report.append("-" * 40)
            report.append("ACTIVITY LOG")
            report.append("-" * 40)
            log_content = self.log_output.get("1.0", tk.END).strip()
            report.append(log_content)
            report.append("")
            report.append("=" * 60)
            report.append("END OF REPORT")
            report.append("=" * 60)
            
            # Write to file
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(report))
            
            messagebox.showinfo(
                "Export Complete",
                f"Report saved to:\n{filename}",
                parent=self.root
            )
            
        except Exception as e:
            messagebox.showerror(
                "Export Failed",
                f"Failed to export report: {e}",
                parent=self.root
            )

    def _open_restore_dialog(self):
        """Open the restore backup dialog."""
        from .restore_dialog import RestoreDialog
        RestoreDialog(self.root, self.backup_service, self.config_manager, self.colors)

    def _open_history_dialog(self):
        """Open the cleanup history dialog."""
        from .history_dialog import HistoryDialog
        HistoryDialog(self.root, self.history_service, self.colors)

    def on_closing(self):
        """Handle application closing."""
        if self.is_cleaning:
            if messagebox.askokcancel("Quit", "A cleanup is in progress. Are you sure you want to quit?"):
                self.is_cleaning = False
                if self.cleanup_thread and self.cleanup_thread.is_alive():
                    self.cleanup_thread.join(timeout=0.5)
                self.root.destroy()
        else:
            self.root.destroy()

