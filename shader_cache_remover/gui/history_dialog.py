"""
History dialog for viewing past cleanup operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class HistoryDialog:
    """Dialog for viewing cleanup history."""

    def __init__(self, parent, history_service, colors):
        """Initialize the history dialog."""
        self.parent = parent
        self.history_service = history_service
        self.colors = colors
        
        self.window = tk.Toplevel(parent)
        self.window.title("Cleanup History")
        self.window.geometry("700x450")
        self.window.minsize(600, 350)
        self.window.configure(bg=colors["bg_primary"])
        self.window.transient(parent)
        self.window.grab_set()
        
        self._create_ui()
        self._load_history()
        
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
            text="Cleanup History",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_primary"],
        )
        title.pack(pady=(15, 5))

        # Stats summary
        self.stats_label = tk.Label(
            self.window,
            text="",
            font=("Segoe UI", 10),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_primary"],
        )
        self.stats_label.pack(pady=(0, 15))

        # Treeview frame
        tree_frame = tk.Frame(self.window, bg=self.colors["bg_secondary"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview
        columns = ("date", "files", "dirs", "freed", "duration", "type")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.tree.yview)

        # Configure columns
        self.tree.heading("date", text="Date")
        self.tree.heading("files", text="Files")
        self.tree.heading("dirs", text="Dirs")
        self.tree.heading("freed", text="Space Freed")
        self.tree.heading("duration", text="Duration")
        self.tree.heading("type", text="Type")

        self.tree.column("date", width=150)
        self.tree.column("files", width=60, anchor="center")
        self.tree.column("dirs", width=60, anchor="center")
        self.tree.column("freed", width=100, anchor="e")
        self.tree.column("duration", width=80, anchor="e")
        self.tree.column("type", width=80, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Button frame
        button_frame = tk.Frame(self.window, bg=self.colors["bg_primary"])
        button_frame.pack(pady=(0, 15))

        # Clear history button
        clear_btn = tk.Button(
            button_frame,
            text="Clear History",
            command=self._clear_history,
            bg=self.colors["error"],
            fg="#ffffff",
            font=("Segoe UI", 10),
            relief="flat",
            padx=15,
            pady=6,
            cursor="hand2",
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Close button
        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy,
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            font=("Segoe UI", 10),
            relief="flat",
            padx=20,
            pady=6,
            cursor="hand2",
        )
        close_btn.pack(side=tk.LEFT, padx=5)

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human readable string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"

    def _load_history(self):
        """Load history into the treeview."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load history
        history = self.history_service.get_history()
        
        for entry in history:
            # Parse timestamp
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(entry.timestamp)
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = entry.timestamp[:16]
            
            self.tree.insert("", tk.END, values=(
                date_str,
                entry.files_deleted,
                entry.directories_deleted,
                self._format_bytes(entry.bytes_freed),
                f"{entry.duration_seconds:.1f}s",
                "Dry Run" if entry.was_dry_run else "Cleanup",
            ))
        
        # Update stats summary
        stats = self.history_service.get_total_stats()
        self.stats_label.config(
            text=f"Total: {stats['total_cleanups']} cleanups  |  "
                 f"{stats['total_files_deleted']} files  |  "
                 f"{self._format_bytes(stats['total_bytes_freed'])} freed"
        )

    def _clear_history(self):
        """Clear all history."""
        if messagebox.askyesno(
            "Clear History",
            "Are you sure you want to clear all cleanup history?",
            parent=self.window
        ):
            self.history_service.clear_history()
            self._load_history()
            messagebox.showinfo(
                "History Cleared",
                "Cleanup history has been cleared.",
                parent=self.window
            )
