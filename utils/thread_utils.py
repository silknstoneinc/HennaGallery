"""
Thread utility functions for Henna Gallery Editor.
Complete thread-safe implementation with all original features.
"""

import threading
import queue
import time
import traceback
from typing import Callable, Any, Optional, Tuple
from functools import wraps
from tkinter import messagebox

class TaskError:
    """Container for exception information from failed tasks."""
    def __init__(self, exc: Exception, traceback_str: str):
        self.exception = exc
        self.traceback = traceback_str

# Global callback queue with thread safety
_callback_queue = queue.Queue()
_queue_lock = threading.Lock()

def synchronized_queue(func):
    """Decorator for thread-safe queue operations."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with _queue_lock:
            return func(*args, **kwargs)
    return wrapper

@synchronized_queue
def schedule_callback(callback: Callable, *args: Any) -> None:
    """Schedule a callback to run in the main thread with thread safety."""
    _callback_queue.put((callback, args))

@synchronized_queue
def process_pending_callbacks() -> None:
    """Process all pending callbacks in the queue with thread safety."""
    while not _callback_queue.empty():
        try:
            callback, args = _callback_queue.get_nowait()
            callback(*args)
        except queue.Empty:
            break
        except Exception as e:
            default_error_handler(e, traceback.format_exc())

def default_error_handler(exc: Exception, traceback_str: str) -> None:
    """Default handler for uncaught background exceptions."""
    error_msg = f"Background task failed: {str(exc)}\n\n{traceback_str}"
    messagebox.showerror("Task Error", error_msg)

def run_in_thread(
    task_func: Callable[[], Any],
    callback: Optional[Callable[[Any], None]] = None,
    error_callback: Optional[Callable[[TaskError], None]] = None,
    daemon: bool = True
) -> threading.Thread:
    """
    Run a function in a background thread with GUI-safe callbacks.
    
    Args:
        task_func: The function to run in background
        callback: Function to call with result when task completes
        error_callback: Function to call if task raises an exception
        daemon: Whether thread should be daemonized
        
    Returns:
        The created Thread object
    """
    def wrapped():
        try:
            result = task_func()
            if callback:
                schedule_callback(callback, result)
        except Exception as e:
            if error_callback:
                error = TaskError(e, traceback.format_exc())
                schedule_callback(error_callback, error)
            else:
                schedule_callback(
                    lambda: default_error_handler(e, traceback.format_exc())
                )
    
    thread = threading.Thread(target=wrapped, daemon=daemon)
    thread.start()
    return thread

class ThreadPool:
    """
    Thread-safe thread pool for managing concurrent tasks.
    
    Args:
        max_workers: Maximum number of concurrent threads
    """
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.active_threads = 0
        self.pending_tasks = queue.Queue()
        self.lock = threading.Lock()
        
    def submit(
        self,
        task_func: Callable[[], Any],
        callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[TaskError], None]] = None
    ) -> None:
        """Submit a task to the thread pool with thread safety."""
        self.pending_tasks.put((task_func, callback, error_callback))
        self._start_next_task()
        
    def _start_next_task(self) -> None:
        """Start the next pending task if workers are available."""
        with self.lock:
            if self.active_threads >= self.max_workers:
                return
                
            if not self.pending_tasks.empty():
                task_func, callback, error_callback = self.pending_tasks.get()
                self.active_threads += 1
                
                def wrapped():
                    try:
                        result = task_func()
                        if callback:
                            schedule_callback(callback, result)
                    except Exception as e:
                        if error_callback:
                            error = TaskError(e, traceback.format_exc())
                            schedule_callback(error_callback, error)
                        else:
                            schedule_callback(
                                lambda: default_error_handler(e, traceback.format_exc())
                            )
                    finally:
                        with self.lock:
                            self.active_threads -= 1
                        self._start_next_task()
                
                thread = threading.Thread(target=wrapped, daemon=True)
                thread.start()

    def wait_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all tasks to complete with thread safety.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if all tasks completed, False if timeout
        """
        start_time = time.time()
        while True:
            with self.lock:
                if self.active_threads == 0 and self.pending_tasks.empty():
                    return True
                    
            if timeout is not None and (time.time() - start_time) > timeout:
                return False
                
            time.sleep(0.1)

class CancellableTask:
    """
    Thread-safe cancellable task wrapper.
    
    Args:
        task_func: The function to execute
        progress_callback: Optional progress reporting callback
    """
    def __init__(
        self,
        task_func: Callable[[Callable[[float], None]], Any],
        progress_callback: Optional[Callable[[float], None]] = None
    ):
        self.task_func = task_func
        self.progress_callback = progress_callback
        self._cancelled = False
        self._thread = None
        self._lock = threading.Lock()
        
    def start(self) -> None:
        """Start the task in a background thread with thread safety."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
                
            self._cancelled = False
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            
    def _run(self) -> None:
        """Internal task runner that handles cancellation."""
        try:
            result = self.task_func(self._report_progress)
            if not self._cancelled and self.progress_callback:
                schedule_callback(self.progress_callback, 1.0)  # 100%
        except Exception as e:
            if not self._cancelled:
                schedule_callback(
                    lambda: default_error_handler(e, traceback.format_exc())
                )
                
    def _report_progress(self, progress: float) -> bool:
        """
        Report progress and check for cancellation with thread safety.
        
        Args:
            progress: Progress value between 0 and 1
            
        Returns:
            bool: True if task should continue, False if cancelled
        """
        with self._lock:
            if self._cancelled:
                return False
                
            if self.progress_callback:
                schedule_callback(self.progress_callback, progress)
                
            return not self._cancelled
            
    def cancel(self) -> None:
        """Request cancellation of the task with thread safety."""
        with self._lock:
            self._cancelled = True
            
    def is_running(self) -> bool:
        """Check if the task is currently running with thread safety."""
        with self._lock:
            return self._thread is not None and self._thread.is_alive()