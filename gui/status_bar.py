"""
Status bar module for Henna Gallery Editor.
Enhanced version with better progress tracking and resource monitoring.
Now with alert message support.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Tuple
import psutil
import time
from datetime import datetime

from config import get_color

class StatusBar(tk.Frame):
    """
    Enhanced status bar with:
    - Operation progress tracking
    - System resource monitoring
    - Timestamped messages
    - Multi-part status display
    - Alert message support
    """
    
    def __init__(self, parent: tk.Widget, update_interval: int = 3, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(
            bg=get_color("dark", "#5A5A5A"),
            height=28,  # Slightly taller for better visibility
            relief="sunken",
            borderwidth=1,
            padx=8,
            pady=3
        )
        self.pack_propagate(False)
        
        # Configuration
        self.update_interval = update_interval
        self.last_update = 0
        self.current_operation = ""
        
        # Message styling
        self.normal_fg = "white"
        self.alert_fg = get_color("error", "#F44336")
        self.warning_fg = get_color("warning", "#FFC107")
        self.success_fg = get_color("success", "#4CAF50")
        
        # Progress tracking
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_label_var = tk.StringVar(value="")
        
        # System resources
        self.cpu_history = []
        self.mem_history = []
        self.max_history = 10
        
        self.create_widgets()
        self.update_resources()

    def create_widgets(self) -> None:
        """Initialize all UI components with enhanced layout."""
        # Main status frame (left-aligned)
        status_frame = tk.Frame(self, bg=get_color("dark", "#5A5A5A"))
        status_frame.pack(side="left", fill="x", expand=True)
        
        # Operation label (shows current activity)
        self.operation_label = tk.Label(
            status_frame,
            textvariable=self.progress_label_var,
            font=("Georgia", 10),
            fg=get_color("highlight", "#F1D1A1"),
            bg=get_color("dark", "#5A5A5A"),
            anchor="w",
            width=25
        )
        self.operation_label.pack(side="left", padx=(0, 10))
        
        # Status message label
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            font=("Georgia", 10),
            fg=self.normal_fg,
            bg=get_color("dark", "#5A5A5A"),
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)
        
        # Progress bar with percentage
        progress_container = tk.Frame(self, bg=get_color("dark", "#5A5A5A"))
        progress_container.pack(side="left", padx=10)
        
        self.progress_bar = ttk.Progressbar(
            progress_container,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            length=180,
            style="Gallery.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(side="top", fill="x")
        
        self.progress_text = tk.Label(
            progress_container,
            textvariable=self.progress_label_var,
            font=("Georgia", 10),
            fg="white",
            bg=get_color("dark", "#5A5A5A")
        )
        self.progress_text.pack(side="top")
        
        # System resources frame (right-aligned)
        resource_frame = tk.Frame(self, bg=get_color("dark", "#5A5A5A"))
        resource_frame.pack(side="right")
        
        # CPU/Memory indicators
        self.resource_label = tk.Label(
            resource_frame,
            text="Loading system info...",
            font=("Georgia", 10),
            fg="white",
            bg=get_color("dark", "#5A5A5A"),
            anchor="e"
        )
        self.resource_label.pack()

        # Configure ttk style for progress bar
        self.style = ttk.Style()
        self.style.configure(
            "Gallery.Horizontal.TProgressbar",
            background=get_color("primary", "#A8D5BA"),
            troughcolor=get_color("secondary", "#D8C6B8")
        )

    def update_status(
        self,
        message: str,
        progress: Optional[float] = None,
        operation: Optional[str] = None,
        alert: bool = False,
        temporary: bool = False
    ) -> None:
        """
        Enhanced status update with progress tracking and alert support.
        
        Args:
            message: Detailed status message
            progress: Current progress (0-100)
            operation: Current operation name
            alert: Whether to show as alert/error message
            temporary: If True, message will clear after 5 seconds
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_label.config(text=f"[{timestamp}] {message}")
        
        # Set message color based on alert status
        if alert:
            self.status_label.config(fg=self.alert_fg)
        else:
            self.status_label.config(fg=self.normal_fg)
        
        if operation:
            self.current_operation = operation
            self.progress_label_var.set(f"{operation}:")
        
        if progress is not None:
            self.progress_var.set(progress)
            self.progress_label_var.set(
                f"{self.current_operation}: {int(progress)}%"
            )
            self.progress_bar.update()
        
        if temporary:
            self.after(5000, self.clear_status)
        
        self.update_idletasks()

    def update_resources(self) -> None:
        """Enhanced system resource monitoring with history tracking."""
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            try:
                # Get current stats
                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory().percent
                
                # Update history
                self.cpu_history.append(cpu)
                self.mem_history.append(memory)
                if len(self.cpu_history) > self.max_history:
                    self.cpu_history.pop(0)
                    self.mem_history.pop(0)
                
                # Calculate averages
                avg_cpu = sum(self.cpu_history) / len(self.cpu_history)
                avg_mem = sum(self.mem_history) / len(self.mem_history)
                
                self.resource_label.config(
                    text=f"CPU: {avg_cpu:.1f}% | Mem: {avg_mem:.1f}%"
                )
                self.last_update = current_time
                
                # Change color if resources are stressed
                if avg_cpu > 80 or avg_mem > 80:
                    self.resource_label.config(fg=self.warning_fg)
                else:
                    self.resource_label.config(fg="white")
                    
            except Exception as e:
                self.resource_label.config(
                    text="Resource stats unavailable",
                    fg=self.alert_fg
                )
        
        self.after(1000, self.update_resources)

    def start_operation(self, operation_name: str) -> None:
        """
        Start tracking a new operation.
        
        Args:
            operation_name: Name of the operation to display
        """
        self.current_operation = operation_name
        self.progress_label_var.set(f"{operation_name}: 0%")
        self.progress_var.set(0)
        self.show_progress(True)

    def end_operation(self) -> None:
        """Complete the current operation."""
        self.progress_label_var.set("")
        self.progress_var.set(0)
        self.current_operation = ""
        self.show_progress(False)

    def show_progress(self, show: bool = True) -> None:
        """Show or hide the progress bar section."""
        if show:
            self.progress_bar.pack(side="top", fill="x")
            self.progress_text.pack(side="top")
        else:
            self.progress_bar.pack_forget()
            self.progress_text.pack_forget()
        self.update_idletasks()

    def clear_status(self) -> None:
        """Clear the status display and reset to normal state."""
        self.status_label.config(text="Ready", fg=self.normal_fg)
        self.progress_var.set(0)
        self.progress_label_var.set("")
        self.current_operation = ""
        self.show_progress(False)

    def clear(self) -> None:
        """Alias for clear_status for backward compatibility."""
        self.clear_status()