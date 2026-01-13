"""
Settings dialog for the Shader Cache Remover application.

A clean, modern dialog using Windows Fluent-inspired design.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Dict, Any, List

from shader_cache_remover.infrastructure.config_manager import ConfigManager
from shader_cache_remover.core.update_service import UpdateService
import threading


class SettingsDialog:
    """Settings dialog window for application configuration."""

    WINDOW_TITLE = "Settings"
    WINDOW_SIZE = "600x650"
    FONT_FAMILY = "Segoe UI"

    def __init__(self, parent: tk.Tk, config_manager: ConfigManager, colors: Dict[str, str]):
        """Initialize the settings dialog."""
        self.parent = parent
        self.config_manager = config_manager
        self.colors = colors

        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title(self.WINDOW_TITLE)
        self.window.geometry(self.WINDOW_SIZE)
        self.window.resizable(True, True)
        self.window.configure(bg=colors["bg_primary"])
        self.window.transient(parent)
        self.window.grab_set()

        # Keyboard shortcuts
        self.window.bind("<Control-s>", lambda e: self._save_settings())
        self.window.bind("<Escape>", lambda e: self.window.destroy())

        # Create notebook for tabs
        self._apply_notebook_style()
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Create tabs
        self._create_general_tab()
        self._create_custom_paths_tab()

        # Save button
        self._create_save_button()

        # Center window
        self._center_window()

    def _apply_notebook_style(self):
        """Apply modern style to notebook."""
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TNotebook", background=self.colors["bg_primary"])
        style.configure("TNotebook.Tab",
            background=self.colors["bg_secondary"],
            foreground=self.colors["text_primary"],
            padding=[15, 8],
            font=(self.FONT_FAMILY, 10)
        )
        style.map("TNotebook.Tab",
            background=[("selected", self.colors["accent"])],
            foreground=[("selected", "#ffffff")]
        )

    def _create_general_tab(self):
        """Create the general settings tab."""
        general_frame = tk.Frame(self.notebook, bg=self.colors["bg_primary"], padx=15, pady=15)
        self.notebook.add(general_frame, text="General")

        # Options section
        self._create_section_header(general_frame, "Options")
        
        options_frame = tk.Frame(general_frame, bg=self.colors["bg_secondary"], padx=15, pady=15)
        options_frame.pack(fill=tk.X, pady=(0, 15))

        # Auto-backup checkbox
        self.auto_backup_var = tk.BooleanVar(value=self.config_manager.is_auto_backup_enabled())
        self._create_checkbox(options_frame, self.auto_backup_var, 
            "Auto-backup before cleanup",
            "Create backups before removing cache files")

        # Detailed logging checkbox
        self.detailed_logging_var = tk.BooleanVar(value=self.config_manager.is_detailed_logging_enabled())
        self._create_checkbox(options_frame, self.detailed_logging_var,
            "Detailed logging",
            "Enable verbose logging for troubleshooting")

        # Show progress checkbox
        self.show_progress_var = tk.BooleanVar(value=self.config_manager.should_show_progress())
        self._create_checkbox(options_frame, self.show_progress_var,
            "Show progress bar",
            "Display progress during cleanup")

        # Updates section
        self._create_section_header(general_frame, "Updates")
        
        update_frame = tk.Frame(general_frame, bg=self.colors["bg_secondary"], padx=15, pady=15)
        update_frame.pack(fill=tk.X, pady=(0, 15))

        # Startup check checkbox
        self.check_on_startup_var = tk.BooleanVar(value=self.config_manager.get_config_value("check_updates_on_startup", True))
        self._create_checkbox(update_frame, self.check_on_startup_var,
            "Check for updates on launch",
            "Automatically check for new versions when the app starts")
            
        tk.Label(update_frame, text="", bg=self.colors["bg_secondary"], height=1).pack() # Spacer

        tk.Label(
            update_frame, 
            text=f"Current Version: {UpdateService.get_current_version()}",
            font=(self.FONT_FAMILY, 10),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_primary"]
        ).pack(side=tk.LEFT)

        self.check_update_btn = tk.Button(
            update_frame,
            text="Check for Updates",
            command=self._start_update_check,
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["accent"],
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        )
        self.check_update_btn.pack(side=tk.RIGHT)

        # Backup location section
        self._create_section_header(general_frame, "Backup Location")
        
        backup_frame = tk.Frame(general_frame, bg=self.colors["bg_secondary"], padx=15, pady=15)
        backup_frame.pack(fill=tk.X)

        self.backup_location_var = tk.StringVar(value=str(self.config_manager.get_backup_location()))

        entry_container = tk.Frame(backup_frame, bg=self.colors["bg_secondary"])
        entry_container.pack(fill=tk.X, pady=(0, 10))

        backup_entry = tk.Entry(
            entry_container,
            textvariable=self.backup_location_var,
            font=(self.FONT_FAMILY, 10),
            bg=self.colors["bg_input"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["text_primary"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["accent"],
        )
        backup_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)

        browse_button = tk.Button(
            entry_container,
            text="Browse",
            command=self._browse_backup_location,
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["accent"],
            activeforeground="#ffffff",
            relief="flat",
            padx=15,
            pady=6,
            cursor="hand2",
        )
        browse_button.pack(side=tk.LEFT, padx=(10, 0))

        # Validation label
        self.backup_validation_label = tk.Label(
            backup_frame,
            text="",
            font=(self.FONT_FAMILY, 9),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_secondary"],
        )
        self.backup_validation_label.pack(anchor=tk.W)

        backup_entry.bind("<KeyRelease>", lambda e: self._validate_backup_location())
        self._validate_backup_location()

    def _create_custom_paths_tab(self):
        """Create the custom paths tab."""
        custom_frame = tk.Frame(self.notebook, bg=self.colors["bg_primary"], padx=15, pady=15)
        self.notebook.add(custom_frame, text="Custom Paths")

        # Instructions
        instructions = tk.Label(
            custom_frame,
            text="Add custom shader cache directories to scan during cleanup:",
            font=(self.FONT_FAMILY, 10),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_primary"],
        )
        instructions.pack(anchor=tk.W, pady=(0, 10))

        # Listbox frame
        listbox_frame = tk.Frame(custom_frame, bg=self.colors["bg_secondary"])
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.custom_paths_listbox = tk.Listbox(
            listbox_frame,
            height=12,
            bg=self.colors["bg_input"],
            fg=self.colors["text_primary"],
            selectbackground=self.colors["accent"],
            selectforeground="#ffffff",
            font=(self.FONT_FAMILY, 10),
            activestyle="none",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
        )
        self.custom_paths_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.custom_paths_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.custom_paths_listbox.config(yscrollcommand=scrollbar.set)

        # Load existing paths
        for path in self.config_manager.get_custom_paths():
            self.custom_paths_listbox.insert(tk.END, path)

        # Buttons
        buttons_frame = tk.Frame(custom_frame, bg=self.colors["bg_primary"])
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        button_style = {
            "bg": self.colors["bg_tertiary"],
            "fg": self.colors["text_primary"],
            "activebackground": self.colors["accent"],
            "activeforeground": "#ffffff",
            "relief": "flat",
            "padx": 12,
            "pady": 6,
            "cursor": "hand2",
        }

        tk.Button(buttons_frame, text="Add", command=self._add_custom_path, **button_style).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(buttons_frame, text="Remove", command=self._remove_custom_path, **button_style).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_frame, text="Validate All", command=self._validate_all_paths_ui, **button_style).pack(side=tk.LEFT, padx=5)

    def _create_save_button(self):
        """Create the save button."""
        save_frame = tk.Frame(self.window, bg=self.colors["bg_primary"])
        save_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        save_button = tk.Button(
            save_frame,
            text="Save Settings",
            command=self._save_settings,
            bg=self.colors["success"],
            fg="#ffffff",
            activebackground=self.colors["success_light"],
            activeforeground="#ffffff",
            font=(self.FONT_FAMILY, 10, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
        )
        save_button.pack(side=tk.RIGHT)

        cancel_button = tk.Button(
            save_frame,
            text="Cancel",
            command=self.window.destroy,
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["border"],
            activeforeground=self.colors["text_primary"],
            font=(self.FONT_FAMILY, 10),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
        )
        cancel_button.pack(side=tk.RIGHT, padx=(0, 10))

    def _create_section_header(self, parent, text: str):
        """Create a section header."""
        label = tk.Label(
            parent,
            text=text,
            font=(self.FONT_FAMILY, 11, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_primary"],
        )
        label.pack(anchor=tk.W, pady=(0, 8))

    def _create_checkbox(self, parent, var: tk.BooleanVar, text: str, description: str):
        """Create a styled checkbox with description."""
        container = tk.Frame(parent, bg=self.colors["bg_secondary"])
        container.pack(fill=tk.X, pady=(0, 10))

        checkbox = tk.Checkbutton(
            container,
            text=text,
            variable=var,
            font=(self.FONT_FAMILY, 10),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["bg_secondary"],
            activeforeground=self.colors["text_primary"],
            selectcolor=self.colors["bg_input"],
            cursor="hand2",
        )
        checkbox.pack(anchor=tk.W)

        desc_label = tk.Label(
            container,
            text=description,
            font=(self.FONT_FAMILY, 9),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_secondary"],
        )
        desc_label.pack(anchor=tk.W, padx=(24, 0))

    def _center_window(self):
        """Center the window on the parent."""
        self.window.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        self.window.geometry(f"+{x}+{y}")

    def _browse_backup_location(self):
        """Browse for backup location."""
        current = self.backup_location_var.get()
        initial = current if Path(current).exists() else str(Path.home())
        
        folder = filedialog.askdirectory(
            title="Select Backup Directory",
            initialdir=initial,
            parent=self.window,
        )
        if folder:
            self.backup_location_var.set(folder)
            self._validate_backup_location()

    def _validate_backup_location(self):
        """Validate backup location."""
        path_str = self.backup_location_var.get().strip()
        if not path_str:
            self.backup_validation_label.config(text="⚠ Location cannot be empty", fg=self.colors["warning"])
            return False
        
        path = Path(path_str)
        if path.exists() and path.is_dir():
            self.backup_validation_label.config(text="✓ Valid location", fg=self.colors["success"])
            return True
        else:
            self.backup_validation_label.config(text="⚠ Directory does not exist", fg=self.colors["warning"])
            return False

    def _add_custom_path(self):
        """Add a custom path."""
        path = filedialog.askdirectory(title="Select Shader Cache Directory", parent=self.window)
        if path:
            existing = [self.custom_paths_listbox.get(i) for i in range(self.custom_paths_listbox.size())]
            if path not in existing:
                self.custom_paths_listbox.insert(tk.END, path)
            else:
                messagebox.showwarning("Duplicate", "This path is already in the list.", parent=self.window)

    def _remove_custom_path(self):
        """Remove selected custom path."""
        selection = self.custom_paths_listbox.curselection()
        if selection:
            self.custom_paths_listbox.delete(selection[0])
        else:
            messagebox.showwarning("No Selection", "Please select a path to remove.", parent=self.window)

    def _validate_all_paths(self) -> List[str]:
        """Validate all paths and return invalid ones."""
        invalid = []
        for i in range(self.custom_paths_listbox.size()):
            path = Path(self.custom_paths_listbox.get(i))
            if not path.exists():
                invalid.append(f"Does not exist: {path}")
            elif not path.is_dir():
                invalid.append(f"Not a directory: {path}")
        return invalid

    def _validate_all_paths_ui(self):
        """Show validation results."""
        invalid = self._validate_all_paths()
        if not invalid:
            messagebox.showinfo("Validation", "✓ All paths are valid!", parent=self.window)
        else:
            messagebox.showerror("Invalid Paths", "\n".join(invalid), parent=self.window)

    def _save_settings(self):
        """Save settings and close."""
        try:
            if not self._validate_backup_location():
                messagebox.showerror("Error", "Please set a valid backup location.", parent=self.window)
                return

            invalid = self._validate_all_paths()
            if invalid:
                messagebox.showerror("Invalid Paths", "\n".join(invalid), parent=self.window)
                return

            custom_paths = [self.custom_paths_listbox.get(i) for i in range(self.custom_paths_listbox.size())]

            config_updates = {
                "auto_backup": self.auto_backup_var.get(),
                "detailed_logging": self.detailed_logging_var.get(),
                "show_progress": self.show_progress_var.get(),
                "backup_location": self.backup_location_var.get(),
                "custom_paths": custom_paths,
                "check_updates_on_startup": self.check_on_startup_var.get(),
            }

            self.config_manager.update_config(config_updates)
            self.window.destroy()
            messagebox.showinfo("Settings", "Settings saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}", parent=self.window)

    def _start_update_check(self):
        """Start update check in background thread."""
        self.check_update_btn.config(state="disabled", text="Checking...")
        threading.Thread(target=self._check_for_updates, daemon=True).start()

    def _check_for_updates(self):
        """Perform the actual update check."""
        try:
            available, version, url, notes = UpdateService.check_for_updates()
            
            # Schedule UI update on main thread
            self.window.after(0, lambda: self._handle_update_result(available, version, url, notes))
        except Exception as e:
            self.window.after(0, lambda: self._handle_update_error(str(e)))

    def _handle_update_result(self, available, version, url, notes):
        """Handle the result of the update check in the UI thread."""
        self.check_update_btn.config(state="normal", text="Check for Updates")
        
        if available:
            if messagebox.askyesno(
                "Update Available", 
                f"Version {version} is available!\n\nRelease Notes:\n{notes}\n\nDo you want to view the release page?",
                parent=self.window
            ):
                UpdateService.open_download_page(url)
        else:
            messagebox.showinfo("Up to Date", "You are running the latest version.", parent=self.window)

    def _handle_update_error(self, error_msg):
        """Handle update check error."""
        self.check_update_btn.config(state="normal", text="Check for Updates")
        messagebox.showerror("Update Check Failed", f"Could not check for updates:\n{error_msg}", parent=self.window)
