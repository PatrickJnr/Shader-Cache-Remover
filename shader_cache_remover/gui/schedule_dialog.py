import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from shader_cache_remover.infrastructure.scheduler import SchedulerService

class ScheduleDialog:
    """Dialog for managing scheduled cleanups."""

    WINDOW_TITLE = "Schedule Cleanup"
    WINDOW_SIZE = "500x450"
    FONT_FAMILY = "Segoe UI"

    def __init__(self, parent: tk.Tk, scheduler_service: SchedulerService, colors: Dict[str, str]):
        """Initialize the schedule dialog."""
        self.parent = parent
        self.scheduler = scheduler_service
        self.colors = colors

        self.window = tk.Toplevel(parent)
        self.window.title(self.WINDOW_TITLE)
        self.window.geometry(self.WINDOW_SIZE)
        self.window.resizable(False, False)
        self.window.configure(bg=colors["bg_primary"])
        self.window.transient(parent)
        self.window.grab_set()

        # Center window
        self._center_window()

        # UI Variables
        self.frequency_var = tk.StringVar(value="WEEKLY")
        self.day_var = tk.StringVar(value="SUN")
        self.hour_var = tk.StringVar(value="03")
        self.minute_var = tk.StringVar(value="00")
        self.status_var = tk.StringVar(value="Checked scheduled tasks...")

        # Create UI
        self._create_header()
        self._create_current_status()
        self._create_settings_form()
        self._create_buttons()

        # Load current state
        self._load_current_schedule()

    def _center_window(self):
        """Center the window on the parent."""
        self.window.update_idletasks()
        try:
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            window_width = self.window.winfo_width()
            window_height = self.window.winfo_height()
            x = parent_x + (parent_width - window_width) // 2
            y = parent_y + (parent_height - window_height) // 2
            self.window.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _create_header(self):
        """Create header section."""
        frame = tk.Frame(self.window, bg=self.colors["bg_primary"], padx=20, pady=20)
        frame.pack(fill=tk.X)

        tk.Label(
            frame,
            text="Automated Cleanup",
            font=(self.FONT_FAMILY, 16, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_primary"],
        ).pack(anchor=tk.W)

        tk.Label(
            frame,
            text="Configure Windows Task Scheduler to run cleanup automatically in the background.",
            font=(self.FONT_FAMILY, 9),
            fg=self.colors["text_secondary"],
            bg=self.colors["bg_primary"],
            wraplength=450,
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(5, 0))

    def _create_current_status(self):
        """Create status section."""
        frame = tk.Frame(self.window, bg=self.colors["bg_secondary"], padx=20, pady=15)
        frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        tk.Label(
            frame,
            text="Current Status",
            font=(self.FONT_FAMILY, 10, "bold"),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_secondary"],
        ).pack(anchor=tk.W)

        self.status_label = tk.Label(
            frame,
            textvariable=self.status_var,
            font=(self.FONT_FAMILY, 9),
            fg=self.colors["accent"],
            bg=self.colors["bg_secondary"],
        )
        self.status_label.pack(anchor=tk.W, pady=(5, 0))

    def _create_settings_form(self):
        """Create the settings form."""
        frame = tk.Frame(self.window, bg=self.colors["bg_primary"], padx=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Grid config
        frame.columnconfigure(1, weight=1)

        # Frequency
        self._create_label(frame, "Frequency:", 0)
        freq_cb = ttk.Combobox(
            frame, 
            textvariable=self.frequency_var,
            values=["DAILY", "WEEKLY", "MONTHLY"],
            state="readonly",
            width=15
        )
        freq_cb.grid(row=0, column=1, sticky=tk.W, pady=10)
        freq_cb.bind("<<ComboboxSelected>>", self._on_freq_change)

        # Day (only for Weekly)
        self.day_label = self._create_label(frame, "Day of Week:", 1)
        self.day_cb = ttk.Combobox(
            frame,
            textvariable=self.day_var,
            values=["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
            state="readonly",
            width=15
        )
        self.day_cb.grid(row=1, column=1, sticky=tk.W, pady=10)

        # Time
        self._create_label(frame, "Time (24h):", 2)
        time_frame = tk.Frame(frame, bg=self.colors["bg_primary"])
        time_frame.grid(row=2, column=1, sticky=tk.W, pady=10)

        hours = [f"{i:02d}" for i in range(24)]
        minutes = [f"{i:02d}" for i in range(0, 60, 5)]

        ttk.Combobox(time_frame, textvariable=self.hour_var, values=hours, state="readonly", width=5).pack(side=tk.LEFT)
        tk.Label(time_frame, text=":", bg=self.colors["bg_primary"], fg=self.colors["text_primary"]).pack(side=tk.LEFT, padx=5)
        ttk.Combobox(time_frame, textvariable=self.minute_var, values=minutes, state="readonly", width=5).pack(side=tk.LEFT)

    def _create_label(self, parent, text, row):
        """Helper to create form labels."""
        lbl = tk.Label(
            parent,
            text=text,
            font=(self.FONT_FAMILY, 10),
            fg=self.colors["text_primary"],
            bg=self.colors["bg_primary"],
        )
        lbl.grid(row=row, column=0, sticky=tk.W, pady=10, padx=(0, 20))
        return lbl

    def _create_buttons(self):
        """Create action buttons."""
        frame = tk.Frame(self.window, bg=self.colors["bg_primary"], padx=20, pady=20)
        frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Save Button
        tk.Button(
            frame,
            text="Save Schedule",
            command=self._save_schedule,
            bg=self.colors["success"],
            fg="#ffffff",
            activebackground=self.colors["success_light"],
            activeforeground="#ffffff",
            relief="flat",
            font=(self.FONT_FAMILY, 10, "bold"),
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.RIGHT)

        # Cancel Button
        tk.Button(
            frame,
            text="Close",
            command=self.window.destroy,
            bg=self.colors["bg_tertiary"],
            fg=self.colors["text_primary"],
            activebackground=self.colors["border"],
            activeforeground=self.colors["text_primary"],
            relief="flat",
            font=(self.FONT_FAMILY, 10),
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=10)

        # Disable Button
        tk.Button(
            frame,
            text="Disable Schedule",
            command=self._disable_schedule,
            bg=self.colors["error"],
            fg="#ffffff",
            activebackground="#e74c3c",
            activeforeground="#ffffff",
            relief="flat",
            font=(self.FONT_FAMILY, 10),
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT)

    def _on_freq_change(self, event=None):
        """Handle frequency change."""
        if self.frequency_var.get() == "WEEKLY":
            self.day_cb.grid()
            self.day_label.grid()
        else:
            self.day_cb.grid_remove()
            self.day_label.grid_remove()

    def _load_current_schedule(self):
        """Load current schedule info."""
        info = self.scheduler.get_schedule_info()
        if info:
            self.status_var.set(f"Active: {info.get('Schedule Type', 'Unknown')} at {info.get('Start Time', 'Unknown')}\nNext Run: {info.get('Next Run Time', 'Unknown')}")
            self.status_label.config(fg=self.colors["success"])
        else:
            self.status_var.set("No cleanup schedule is currently active.")
            self.status_label.config(fg=self.colors["text_secondary"])

    def _save_schedule(self):
        """Save the schedule."""
        freq = self.frequency_var.get()
        day = self.day_var.get()
        time = f"{self.hour_var.get()}:{self.minute_var.get()}"

        if self.scheduler.schedule_cleanup(frequency=freq, day=day, time=time):
            messagebox.showinfo("Success", "Cleanup schedule updated successfully!", parent=self.window)
            self._load_current_schedule()
        else:
            messagebox.showerror("Error", "Failed to update schedule.\nTry running as Administrator.", parent=self.window)

    def _disable_schedule(self):
        """Disable the schedule."""
        if self.scheduler.unschedule_cleanup():
            messagebox.showinfo("Success", "Cleanup schedule disabled.", parent=self.window)
            self._load_current_schedule()
        else:
            messagebox.showerror("Error", "Failed to disable schedule.", parent=self.window)
