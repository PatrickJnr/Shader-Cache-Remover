"""
Settings dialog for the Shader Cache Remover application.

This module contains the settings dialog window that allows users to
configure application preferences and custom shader cache paths.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable

from shader_cache_remover.infrastructure.config_manager import ConfigManager


class SettingsDialog:
    """Settings dialog window for application configuration."""

    # Constants
    WINDOW_TITLE = "Settings"
    WINDOW_SIZE = "700x800"
    FONT_FAMILY = "Segoe UI"
    BUTTON_PADDING = {"padx": 15, "pady": 5}
    ENTRY_WIDTH = 60
    LISTBOX_HEIGHT = 12

    # Visual styling constants
    CORNER_RADIUS = 8
    SHADOW_DEPTH = 2
    SECTION_PADDING = 20
    ELEMENT_SPACING = 8
    GROUP_SPACING = 16

    def __init__(
        self, parent: tk.Tk, config_manager: ConfigManager, colors: Dict[str, str]
    ):
        """Initialize the settings dialog.

        Args:
            parent: Parent tkinter window
            config_manager: Configuration manager instance
            colors: Color scheme dictionary
        """
        self.parent = parent
        self.config_manager = config_manager
        self.colors = colors

        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title(self.WINDOW_TITLE)
        self.window.geometry(self.WINDOW_SIZE)
        self.window.resizable(True, True)
        self.window.configure(bg=colors["base"])
        self.window.transient(parent)
        self.window.grab_set()

        # Add keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self._create_general_tab()
        self._create_custom_paths_tab()

        # Save button
        self._create_save_button()

        # Center the window
        self._center_window()

    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for the settings dialog."""
        self.window.bind("<Control-s>", lambda e: self._save_settings())
        self.window.bind("<Control-w>", lambda e: self.window.destroy())
        self.window.bind("<Escape>", lambda e: self.window.destroy())
        self.window.bind("<F1>", lambda e: self._show_help())

    def _show_help(self):
        """Show help information for the settings dialog."""
        help_text = (
            "Settings Help:\n\n"
            "General Tab:\n"
            "- Enable auto-backup to create backups before cleanup\n"
            "- Enable detailed logging for more verbose output\n"
            "- Show progress bar during cleanup operations\n"
            "- Set custom backup location for storing backups\n\n"
            "Custom Paths Tab:\n"
            "- Add directories containing shader cache files\n"
            "- Remove or edit existing custom paths\n"
            "- Validate paths to ensure they exist\n\n"
            "Keyboard Shortcuts:\n"
            "- Ctrl+S: Save settings\n"
            "- Ctrl+W: Close dialog\n"
            "- Escape: Close dialog\n"
            "- F1: Show this help"
        )
        messagebox.showinfo("Settings Help", help_text, parent=self.window)

    def _create_general_tab(self):
        """Create the general settings tab with improved styling."""
        general_frame = tk.Frame(
            self.notebook,
            bg=self.colors["base"],
            padx=self.SECTION_PADDING,
            pady=self.SECTION_PADDING,
        )
        self.notebook.add(general_frame, text="General")

        self._create_settings_section(
            general_frame,
            "General Options",
            [
                (
                    "auto_backup",
                    "Auto-backup before cleanup",
                    "Create backups before cleanup operations",
                ),
                (
                    "detailed_logging",
                    "Detailed logging",
                    "Enable verbose logging for troubleshooting",
                ),
                (
                    "show_progress",
                    "Show progress bar",
                    "Display progress during cleanup operations",
                ),
            ],
            self.colors["surface2"],
        )

        self._create_backup_location_section(general_frame, self.colors["surface1"])

    def _create_custom_paths_tab(self):
        """Create the custom paths tab."""
        custom_frame = tk.Frame(self.notebook, bg=self.colors["base"], padx=10, pady=10)
        self.notebook.add(custom_frame, text="Custom Paths")

        instructions_frame = tk.Frame(
            custom_frame, bg=self.colors["surface2"], padx=10, pady=5
        )
        instructions_frame.pack(fill=tk.X, pady=(0, 10))

        instructions = tk.Label(
            instructions_frame,
            text="Add custom shader cache directories to scan during cleanup:",
            font=(self.FONT_FAMILY, 10, "bold"),
            foreground=self.colors["text"],
            background=self.colors["surface2"],
        )
        instructions.pack(anchor=tk.W)

        search_frame = tk.Frame(custom_frame, bg=self.colors["surface1"])
        search_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            search_frame,
            text="Search:",
            foreground=self.colors["text"],
            background=self.colors["surface1"],
        ).pack(anchor=tk.W)
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=search_var,
            width=40,
            background=self.colors["surface0"],
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            font=(self.FONT_FAMILY, 10),
            relief="flat",
            borderwidth=0,
        )
        search_entry.pack(anchor=tk.W, pady=(2, 0), fill=tk.X)

        def filter_paths(*args):
            """Filter paths based on search term."""
            search_term = search_var.get().lower()
            self.custom_paths_listbox.delete(0, tk.END)

            all_paths = []
            if hasattr(self, "_original_paths"):
                all_paths = self._original_paths
            else:
                for i in range(self.custom_paths_listbox.size()):
                    all_paths.append(self.custom_paths_listbox.get(i))
                self._original_paths = all_paths

            filtered_paths = [path for path in all_paths if search_term in path.lower()]
            for path in filtered_paths:
                self.custom_paths_listbox.insert(tk.END, path)

        def clear_search():
            """Clear search and show all paths."""
            search_var.set("")
            filter_paths()

        search_var.trace_add("write", filter_paths)

        ttk.Button(search_frame, text="Clear", command=clear_search).pack(
            anchor=tk.W, pady=(5, 0)
        )

        paths_frame = tk.Frame(custom_frame, bg=self.colors["surface2"])
        paths_frame.pack(fill=tk.BOTH, expand=True)

        listbox_frame = tk.Frame(paths_frame, bg=self.colors["surface2"])
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.custom_paths_listbox = tk.Listbox(
            listbox_frame,
            height=self.LISTBOX_HEIGHT,
            bg=self.colors["surface0"],
            fg=self.colors["text"],
            selectbackground=self.colors["surface1"],
            selectforeground=self.colors["text"],
            font=(self.FONT_FAMILY, 10),
            activestyle="none",
            borderwidth=0,
            highlightthickness=0,
        )
        self.custom_paths_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            listbox_frame, orient=tk.VERTICAL, command=self.custom_paths_listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.custom_paths_listbox.config(yscrollcommand=scrollbar.set)

        for path in self.config_manager.get_custom_paths():
            self.custom_paths_listbox.insert(tk.END, path)

        buttons_frame = tk.Frame(paths_frame, bg=self.colors["surface2"])
        buttons_frame.pack(fill=tk.X, pady=(0, 10))

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
            buttons_frame,
            text="Add Path",
            command=self._add_custom_path,
            **button_style,
        )
        add_button.pack(side=tk.LEFT, padx=(0, 5))

        remove_button = tk.Button(
            buttons_frame,
            text="Remove Path",
            command=self._remove_custom_path,
            **button_style,
        )
        remove_button.pack(side=tk.LEFT, padx=(0, 5))

        edit_button = tk.Button(
            buttons_frame,
            text="Edit Path",
            command=self._edit_custom_path,
            **button_style,
        )
        edit_button.pack(side=tk.LEFT, padx=(0, 5))

        validate_button = tk.Button(
            buttons_frame,
            text="Validate Path",
            command=self._validate_custom_path,
            **button_style,
        )
        validate_button.pack(side=tk.LEFT, padx=(0, 5))

        validate_all_button = tk.Button(
            buttons_frame,
            text="Validate All",
            command=self._validate_all_paths_ui,
            **button_style,
        )
        validate_all_button.pack(side=tk.LEFT, padx=(0, 5))

        import_export_frame = tk.Frame(paths_frame, bg=self.colors["surface2"])
        import_export_frame.pack(fill=tk.X, pady=(5, 0))

        import_button = tk.Button(
            import_export_frame,
            text="Import Settings",
            command=self._import_settings,
            bg=self.colors["blue"],
            fg=self.colors["base"],
            activebackground=self.colors["surface1"],
            activeforeground=self.colors["base"],
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=3,
        )
        import_button.pack(side=tk.LEFT, padx=(0, 5))

        export_button = tk.Button(
            import_export_frame,
            text="Export Settings",
            command=self._export_settings,
            bg=self.colors["blue"],
            fg=self.colors["base"],
            activebackground=self.colors["surface1"],
            activeforeground=self.colors["base"],
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=3,
        )
        export_button.pack(side=tk.LEFT, padx=(0, 5))

        reset_button = tk.Button(
            import_export_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults,
            bg=self.colors["red"],
            fg=self.colors["base"],
            activebackground=self.colors["surface1"],
            activeforeground=self.colors["base"],
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=3,
        )
        reset_button.pack(side=tk.LEFT, padx=(0, 5))

        info_frame = tk.Frame(custom_frame, bg=self.colors["surface1"], padx=10, pady=5)
        info_frame.pack(anchor=tk.W, pady=(10, 0))

        info_label = tk.Label(
            info_frame,
            text="Custom paths will be scanned for shader cache files during cleanup.\n"
            "Only add directories that contain shader cache files.",
            font=("Segoe UI", 9),
            foreground=self.colors["subtext0"],
            background=self.colors["surface1"],
        )
        info_label.pack(anchor=tk.W)

    def _create_save_button(self):
        """Create the save button at the bottom."""
        save_frame = tk.Frame(self.window, bg=self.colors["base"])
        save_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        save_button = tk.Button(
            save_frame,
            text="Save Settings",
            command=self._save_settings,
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

    def _center_window(self):
        """Center the settings window on the screen."""
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

    def _add_custom_path(self):
        """Add a new custom path."""
        path = filedialog.askdirectory(
            title="Select Custom Shader Cache Directory", parent=self.window
        )
        if path:
            if path not in [
                self.custom_paths_listbox.get(i)
                for i in range(self.custom_paths_listbox.size())
            ]:
                self.custom_paths_listbox.insert(tk.END, path)
            else:
                messagebox.showwarning(
                    "Duplicate Path",
                    "This path is already in the list.",
                    parent=self.window,
                )

    def _remove_custom_path(self):
        """Remove selected custom path."""
        selection = self.custom_paths_listbox.curselection()
        if selection:
            self.custom_paths_listbox.delete(selection[0])
        else:
            messagebox.showwarning(
                "No Selection",
                "Please select a path to remove.",
                parent=self.window,
            )

    def _edit_custom_path(self):
        """Edit selected custom path."""
        selection = self.custom_paths_listbox.curselection()
        if selection:
            current_path = self.custom_paths_listbox.get(selection[0])
            new_path = filedialog.askdirectory(
                title="Edit Custom Shader Cache Directory",
                initialdir=current_path,
                parent=self.window,
            )
            if new_path and new_path != current_path:
                existing_paths = [
                    self.custom_paths_listbox.get(i)
                    for i in range(self.custom_paths_listbox.size())
                    if i != selection[0]
                ]
                if new_path not in existing_paths:
                    self.custom_paths_listbox.delete(selection[0])
                    self.custom_paths_listbox.insert(selection[0], new_path)
                else:
                    messagebox.showwarning(
                        "Duplicate Path",
                        "This path is already in the list.",
                        parent=self.window,
                    )
        else:
            messagebox.showwarning(
                "No Selection",
                "Please select a path to edit.",
                parent=self.window,
            )

    def _validate_custom_path(self):
        """Validate selected custom path."""
        selection = self.custom_paths_listbox.curselection()
        if selection:
            path = self.custom_paths_listbox.get(selection[0])
            path_obj = Path(path)
            if path_obj.exists():
                if path_obj.is_dir():
                    messagebox.showinfo(
                        "Path Valid",
                        f"✓ Path exists and is a directory:\n{path}",
                        parent=self.window,
                    )
                else:
                    messagebox.showwarning(
                        "Path Invalid",
                        f"✗ Path exists but is not a directory:\n{path}",
                        parent=self.window,
                    )
            else:
                messagebox.showwarning(
                    "Path Invalid",
                    f"✗ Path does not exist:\n{path}",
                    parent=self.window,
                )
        else:
            messagebox.showwarning(
                "No Selection",
                "Please select a path to validate.",
                parent=self.window,
            )

    def _validate_all_paths(self) -> List[str]:
        """Validate all custom paths and return list of invalid paths."""
        invalid_paths = []
        for i in range(self.custom_paths_listbox.size()):
            path_str = self.custom_paths_listbox.get(i)
            path = Path(path_str)
            if not path.exists():
                invalid_paths.append(f"Does not exist: {path_str}")
            elif not path.is_dir():
                invalid_paths.append(f"Not a directory: {path_str}")
        return invalid_paths

    def _validate_backup_location(self) -> bool:
        """Validate backup location and return True if valid."""
        path_str = self.backup_location_var.get().strip()
        if not path_str:
            return False
        path = Path(path_str)
        return path.exists() and path.is_dir()

    def _save_settings(self):
        """Save the settings and close the dialog with comprehensive validation."""
        try:
            if not self._validate_backup_location():
                messagebox.showerror(
                    "Invalid Backup Location",
                    "Please select a valid backup directory.",
                    parent=self.window,
                )
                return

            invalid_paths = self._validate_all_paths()
            if invalid_paths:
                error_msg = "The following custom paths are invalid:\n\n" + "\n".join(
                    invalid_paths
                )
                messagebox.showerror(
                    "Invalid Custom Paths", error_msg, parent=self.window
                )
                return

            custom_paths = [
                self.custom_paths_listbox.get(i)
                for i in range(self.custom_paths_listbox.size())
            ]

            # Batch all config changes and save only once
            config_updates = {
                "auto_backup": self.auto_backup_var.get(),
                "detailed_logging": self.detailed_logging_var.get(),
                "show_progress": self.show_progress_var.get(),
                "backup_location": str(Path(self.backup_location_var.get())),
                "custom_paths": custom_paths,
            }

            # Apply all changes at once
            self.config_manager.update_config(config_updates)

            self.window.destroy()
            messagebox.showinfo("Settings", "Settings saved successfully!")

        except PermissionError:
            messagebox.showerror(
                "Permission Error",
                "Permission denied while saving settings. Please check file permissions.",
                parent=self.window,
            )
        except OSError as e:
            messagebox.showerror(
                "File System Error",
                f"File system error while saving settings: {e}",
                parent=self.window,
            )
        except Exception as e:
            messagebox.showerror(
                "Unexpected Error",
                f"An unexpected error occurred while saving settings: {e}",
                parent=self.window,
            )

    def _validate_all_paths_ui(self):
        """Validate all custom paths and show results in a dialog."""
        invalid_paths = self._validate_all_paths()

        if not invalid_paths:
            messagebox.showinfo(
                "Validation Results",
                "✓ All custom paths are valid!",
                parent=self.window,
            )
        else:
            error_msg = "The following custom paths are invalid:\n\n" + "\n".join(
                invalid_paths
            )
            messagebox.showerror("Validation Results", error_msg, parent=self.window)

    def _export_settings(self):
        """Export current settings to a JSON file."""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Settings",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=self.window,
            )

            if not filename:
                return

            # Get current settings
            settings = {
                "auto_backup": self.auto_backup_var.get(),
                "detailed_logging": self.detailed_logging_var.get(),
                "show_progress": self.show_progress_var.get(),
                "backup_location": self.backup_location_var.get(),
                "custom_paths": [
                    self.custom_paths_listbox.get(i)
                    for i in range(self.custom_paths_listbox.size())
                ],
            }

            import json

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            messagebox.showinfo(
                "Export Successful",
                f"Settings exported successfully to:\n{filename}",
                parent=self.window,
            )

        except Exception as e:
            messagebox.showerror(
                "Export Error", f"Failed to export settings: {e}", parent=self.window
            )

    def _import_settings(self):
        """Import settings from a JSON file."""
        try:
            filename = filedialog.askopenfilename(
                title="Import Settings",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=self.window,
            )

            if not filename:
                return

            import json

            with open(filename, "r", encoding="utf-8") as f:
                settings = json.load(f)

            # Confirm import
            if not messagebox.askyesno(
                "Import Settings",
                "This will overwrite your current settings. Continue?",
                parent=self.window,
            ):
                return

            # Apply imported settings
            self.auto_backup_var.set(settings.get("auto_backup", False))
            self.detailed_logging_var.set(settings.get("detailed_logging", False))
            self.show_progress_var.set(settings.get("show_progress", True))
            self.backup_location_var.set(settings.get("backup_location", ""))

            # Clear and repopulate custom paths
            self.custom_paths_listbox.delete(0, tk.END)
            for path in settings.get("custom_paths", []):
                self.custom_paths_listbox.insert(tk.END, path)

            # Clear search filter if active
            if hasattr(self, "_original_paths"):
                delattr(self, "_original_paths")

            messagebox.showinfo(
                "Import Successful",
                "Settings imported successfully!",
                parent=self.window,
            )

        except json.JSONDecodeError:
            messagebox.showerror(
                "Import Error", "Invalid JSON file format.", parent=self.window
            )
        except FileNotFoundError:
            messagebox.showerror("Import Error", "File not found.", parent=self.window)
        except Exception as e:
            messagebox.showerror(
                "Import Error", f"Failed to import settings: {e}", parent=self.window
            )

    def _reset_to_defaults(self):
        """Reset all settings to their default values."""
        if not messagebox.askyesno(
            "Reset to Defaults",
            "This will reset all settings to their default values. Continue?",
            parent=self.window,
        ):
            return

        try:
            # Reset to default values
            self.auto_backup_var.set(False)
            self.detailed_logging_var.set(False)
            self.show_progress_var.set(True)
            self.backup_location_var.set(str(Path.home() / "ShaderCacheBackups"))

            # Clear custom paths
            self.custom_paths_listbox.delete(0, tk.END)

            # Clear search filter if active
            if hasattr(self, "_original_paths"):
                delattr(self, "_original_paths")

            # Update validation label
            self.backup_validation_label.config(
                text="✓ Valid backup location", foreground=self.colors["green"]
            )

            messagebox.showinfo(
                "Reset Complete",
                "All settings have been reset to defaults.",
                parent=self.window,
            )

        except Exception as e:
            messagebox.showerror(
                "Reset Error", f"Failed to reset settings: {e}", parent=self.window
            )

    def _create_settings_section(
        self, parent, title: str, options: List[tuple], accent_color: str
    ):
        """Create a settings section with checkboxes and descriptions."""
        # Section frame with subtle background using accent color
        section_frame = tk.Frame(
            parent,
            bg=accent_color,
            padx=self.ELEMENT_SPACING,
            pady=self.ELEMENT_SPACING,
        )
        section_frame.pack(fill=tk.X, pady=(0, self.GROUP_SPACING))

        # Section title
        title_label = tk.Label(
            section_frame,
            text=title,
            font=(self.FONT_FAMILY, 12, "bold"),
            foreground=self.colors["text"],
            background=accent_color,
        )
        title_label.pack(anchor=tk.W, pady=(0, self.ELEMENT_SPACING))

        # Create options with descriptions
        for var_name, label_text, description in options:
            option_frame = tk.Frame(section_frame, bg=accent_color)
            option_frame.pack(fill=tk.X, pady=(0, self.ELEMENT_SPACING))

            # Checkbox with variable - get current value properly
            if var_name == "auto_backup":
                current_value = self.config_manager.is_auto_backup_enabled()
            elif var_name == "detailed_logging":
                current_value = self.config_manager.is_detailed_logging_enabled()
            elif var_name == "show_progress":
                current_value = self.config_manager.should_show_progress()
            else:
                current_value = False

            var = tk.BooleanVar(value=current_value)
            checkbox = tk.Checkbutton(
                option_frame,
                text=label_text,
                variable=var,
                bg=accent_color,
                fg=self.colors["text"],
                activebackground=accent_color,
                activeforeground=self.colors["text"],
                selectcolor=self.colors["surface0"],
            )
            checkbox.pack(anchor=tk.W)

            # Description label
            desc_label = tk.Label(
                option_frame,
                text=description,
                font=(self.FONT_FAMILY, 9),
                foreground=self.colors["subtext0"],
                background=accent_color,
            )
            desc_label.pack(anchor=tk.W, padx=(25, 0))

            # Store variable reference
            setattr(self, f"{var_name}_var", var)

    def _create_backup_location_section(self, parent, accent_color: str):
        """Create the backup location section with enhanced styling."""
        section_frame = tk.Frame(
            parent,
            bg=accent_color,
            padx=self.SECTION_PADDING,
            pady=self.SECTION_PADDING,
        )
        section_frame.pack(fill=tk.X, pady=(self.GROUP_SPACING, 0))

        title_frame = tk.Frame(section_frame, bg=accent_color)
        title_frame.pack(fill=tk.X, pady=(0, self.ELEMENT_SPACING))

        title_label = tk.Label(
            title_frame,
            text="Backup Configuration",
            font=(self.FONT_FAMILY, 11, "bold"),
            foreground=self.colors["text"],
            background=accent_color,
        )
        title_label.pack(anchor=tk.W)

        separator = tk.Frame(title_frame, bg=self.colors["overlay0"], height=1)
        separator.pack(fill=tk.X, pady=(2, 0))

        input_frame = tk.Frame(
            section_frame,
            bg=accent_color,
            padx=self.ELEMENT_SPACING,
            pady=self.ELEMENT_SPACING,
        )
        input_frame.pack(fill=tk.X)

        tk.Label(
            input_frame,
            text="📁 Backup Location:",
            font=(self.FONT_FAMILY, 10),
            foreground=self.colors["text"],
            background=accent_color,
        ).pack(anchor=tk.W, pady=(0, self.ELEMENT_SPACING))

        backup_location_var = tk.StringVar(
            value=str(self.config_manager.get_backup_location())
        )

        entry_frame = tk.Frame(
            input_frame,
            background=self.colors["surface0"],
            highlightthickness=1,
            highlightcolor=self.colors["overlay0"],
            highlightbackground=self.colors["overlay0"],
        )
        entry_frame.pack(anchor=tk.W, pady=(0, self.ELEMENT_SPACING), fill=tk.X)

        backup_entry = tk.Entry(
            entry_frame,
            textvariable=backup_location_var,
            width=self.ENTRY_WIDTH,
            font=(self.FONT_FAMILY, 10),
            background=self.colors["surface0"],
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            borderwidth=0,
        )
        backup_entry.pack(fill=tk.X, padx=1, pady=1)
        self.backup_location_var = backup_location_var

        validation_frame = tk.Frame(input_frame, background=accent_color)
        validation_frame.pack(anchor=tk.W, fill=tk.X)

        self.backup_validation_label = tk.Label(
            validation_frame,
            text="",
            font=(self.FONT_FAMILY, 9),
            foreground=self.colors["subtext0"],
            background=accent_color,
        )
        self.backup_validation_label.pack(anchor=tk.W)

        def validate_backup_location():
            """Validate the backup location path with enhanced feedback."""
            path_str = backup_location_var.get().strip()
            if not path_str:
                self.backup_validation_label.config(
                    text="⚠️  Backup location cannot be empty",
                    foreground=self.colors.get("yellow", "#FFA500"),
                )
                return False

            path = Path(path_str)
            if path.exists() and path.is_dir():
                self.backup_validation_label.config(
                    text="✅ Valid backup location",
                    foreground=self.colors.get("green", "#28A745"),
                )
                return True
            else:
                self.backup_validation_label.config(
                    text="⚠️  Directory does not exist",
                    foreground=self.colors.get("yellow", "#FFA500"),
                )
                return False

        def browse_backup_location():
            """Browse for backup location with enhanced styling."""
            current_path = backup_location_var.get()
            if current_path and Path(current_path).exists():
                initial_dir = current_path
            else:
                initial_dir = str(Path.home())

            folder = filedialog.askdirectory(
                title="Select Backup Directory",
                initialdir=initial_dir,
                parent=self.window,
            )
            if folder:
                backup_location_var.set(folder)
                validate_backup_location()

        backup_entry.bind("<KeyRelease>", lambda e: validate_backup_location())
        backup_entry.bind("<FocusOut>", lambda e: validate_backup_location())

        validate_backup_location()

        browse_button = tk.Button(
            input_frame,
            text="📂 Browse",
            command=browse_backup_location,
            bg=self.colors.get("surface1", "#45475A"),
            fg=self.colors.get("text", "#CDD6F4"),
            activebackground=self.colors.get("surface2", "#585B70"),
            activeforeground=self.colors.get("text", "#CDD6F4"),
            relief="flat",
            borderwidth=0,
            font=(self.FONT_FAMILY, 9, "bold"),
            padx=16,
            pady=8,
            cursor="hand2",
        )
        browse_button.pack(anchor=tk.W, pady=(self.ELEMENT_SPACING, 0))
