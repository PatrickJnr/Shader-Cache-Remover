"""
Restore dialog for selecting and restoring backups.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path


class RestoreDialog:
    """Dialog for restoring shader cache backups."""

    def __init__(self, parent, backup_service, config_manager, colors):
        """Initialize the restore dialog."""
        self.parent = parent
        self.backup_service = backup_service
        self.config_manager = config_manager
        self.colors = colors
        self.selected_backup = None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Restore Backup")
        self.window.geometry("600x400")
        self.window.minsize(500, 300)
        self.window.configure(bg=colors["bg_primary"])
        self.window.transient(parent)
        self.window.grab_set()
        
        self._create_ui()
        self._load_backups()
        
        # Center on parent
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.window.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")

    def _create_ui(self):
        """Create the dialog UI."""
        # Title
        title = tk.Label(
            self.window,
            text="Restore Backup",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_primary"],
        )
        title.pack(pady=(15, 5))

        # Description
        desc = tk.Label(
            self.window,
            text="Select a backup to restore shader cache files",
            font=("Segoe UI", 10),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_primary"],
        )
        desc.pack(pady=(0, 15))

        # Listbox frame
        list_frame = tk.Frame(self.window, bg=self.colors["bg_secondary"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # Backup listbox
        self.backup_list = tk.Listbox(
            list_frame,
            font=("Segoe UI", 10),
            bg=self.colors["bg_input"],
            fg=self.colors["text_primary"],
            selectbackground=self.colors["accent"],
            selectforeground="#ffffff",
            highlightthickness=0,
            bd=0,
        )
        self.backup_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.backup_list.bind("<<ListboxSelect>>", self._on_select)

        # Info label
        self.info_label = tk.Label(
            self.window,
            text="No backup selected",
            font=("Segoe UI", 9),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_primary"],
        )
        self.info_label.pack(pady=(0, 10))

        # Button frame
        button_frame = tk.Frame(self.window, bg=self.colors["bg_primary"])
        button_frame.pack(pady=(0, 15))

        # Restore button
        self.restore_btn = tk.Button(
            button_frame,
            text="Restore Selected",
            command=self._restore_backup,
            bg=self.colors["success"],
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            state="disabled",
        )
        self.restore_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            font=("Segoe UI", 10),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def _load_backups(self):
        """Load available backups into the listbox."""
        backup_location = self.config_manager.get_backup_location()
        self.backups = self.backup_service.list_backups(backup_location)
        
        self.backup_list.delete(0, tk.END)
        
        if not self.backups:
            self.backup_list.insert(tk.END, "No backups found")
            self.backup_list.config(state="disabled")
        else:
            for backup in self.backups:
                size_mb = backup["size"] / (1024 * 1024)
                self.backup_list.insert(
                    tk.END,
                    f"{backup['date']}  |  {size_mb:.1f} MB  |  {backup['file_count']} files"
                )

    def _on_select(self, event):
        """Handle backup selection."""
        selection = self.backup_list.curselection()
        if selection and self.backups:
            idx = selection[0]
            if idx < len(self.backups):
                self.selected_backup = self.backups[idx]
                size_mb = self.selected_backup["size"] / (1024 * 1024)
                self.info_label.config(
                    text=f"Selected: {self.selected_backup['name']} ({size_mb:.1f} MB)"
                )
                self.restore_btn.config(state="normal")

    def _restore_backup(self):
        """Restore the selected backup."""
        if not self.selected_backup:
            return
        
        if not messagebox.askyesno(
            "Confirm Restore",
            f"Restore backup from {self.selected_backup['date']}?\n\n"
            f"This will restore {self.selected_backup['file_count']} files.",
            parent=self.window
        ):
            return
        
        try:
            self.restore_btn.config(state="disabled", text="Restoring...")
            self.window.update()
            
            stats = self.backup_service.restore_backup(self.selected_backup["path"])
            
            if stats["errors"] == 0:
                messagebox.showinfo(
                    "Restore Complete",
                    f"Successfully restored {stats['files_restored']} files.",
                    parent=self.window
                )
            else:
                messagebox.showwarning(
                    "Restore Complete with Errors",
                    f"Restored {stats['files_restored']} files with {stats['errors']} errors.",
                    parent=self.window
                )
            
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror(
                "Restore Failed",
                f"Failed to restore backup: {e}",
                parent=self.window
            )
            self.restore_btn.config(state="normal", text="Restore Selected")
