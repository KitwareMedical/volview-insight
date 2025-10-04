"""
Debug utilities for performance monitoring and timing analysis.
Provides decorators, context managers, and monitoring tools for comprehensive debugging.
"""

import time
import os
import functools
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import threading

# Global request context storage
_request_context = threading.local()

def get_debug_level() -> int:
    """Get the current debug level from environment variable."""
    return int(os.environ.get('VOLVIEW_DEBUG_LEVEL', '0'))

def is_request_tracking_enabled() -> bool:
    """Check if request tracking is enabled."""
    return get_debug_level() > 0  # Enable request tracking when debug is on

def is_memory_monitoring_enabled() -> bool:
    """Check if memory monitoring is enabled."""
    return os.environ.get('VOLVIEW_MEMORY_MONITORING', 'false').lower() == 'true'

def get_correlation_id() -> str:
    """Get or create correlation ID for the current request."""
    if not hasattr(_request_context, 'correlation_id'):
        _request_context.correlation_id = str(uuid.uuid4())[:8]
    return _request_context.correlation_id

def set_correlation_id(correlation_id: str):
    """Set correlation ID for the current request."""
    _request_context.correlation_id = correlation_id

def format_bytes(bytes_value: int) -> str:
    """Format bytes into human readable string."""
    if bytes_value == 0:
        return "0B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}PB"

def format_time(seconds: float) -> str:
    """Format seconds into human readable string."""
    if seconds < 1:
        return f"{seconds*1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m{remaining_seconds:.1f}s"

def conditional_log(message: str, level: int = 1):
    """Log message only if debug level is sufficient."""
    if get_debug_level() >= level:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        correlation_id = get_correlation_id() if is_request_tracking_enabled() else "---"
        print(f"[{timestamp}] [REQ:{correlation_id}] {message}", flush=True)

class MemoryMonitor:
    """Monitor GPU and CPU memory usage."""
    
    def __init__(self):
        self.torch_available = False
        self.initial_gpu_memory = 0
        self.initial_cpu_memory = 0
        
        try:
            import torch
            self.torch = torch
            self.torch_available = torch.cuda.is_available()
        except ImportError:
            pass
            
        try:
            import psutil
            self.psutil = psutil
            self.process = psutil.Process()
        except ImportError:
            self.psutil = None
    
    def get_gpu_memory(self) -> int:
        """Get current GPU memory usage in bytes."""
        if self.torch_available:
            return self.torch.cuda.memory_allocated()
        return 0
    
    def get_cpu_memory(self) -> int:
        """Get current CPU memory usage in bytes."""
        if self.psutil:
            return self.process.memory_info().rss
        return 0
    
    def log_memory_usage(self, label: str, level: int = 2):
        """Log current memory usage."""
        if not is_memory_monitoring_enabled() or get_debug_level() < level:
            return
            
        gpu_memory = self.get_gpu_memory()
        cpu_memory = self.get_cpu_memory()
        
        memory_info = []
        if self.torch_available:
            memory_info.append(f"GPU: {format_bytes(gpu_memory)}")
        if self.psutil:
            memory_info.append(f"CPU: {format_bytes(cpu_memory)}")
            
        if memory_info:
            conditional_log(f"{label} - Memory: {', '.join(memory_info)}", level)

# Global memory monitor instance
memory_monitor = MemoryMonitor()

def timing_decorator(operation_name: str = None, level: int = 1):
    """Decorator to time function execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if get_debug_level() < level:
                return func(*args, **kwargs)
                
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            # Log start
            conditional_log(f"{name}: Starting", level)
            memory_monitor.log_memory_usage(f"{name}: Start", level + 1)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                elapsed = end_time - start_time
                
                # Log completion
                conditional_log(f"{name}: Completed in {format_time(elapsed)}", level)
                memory_monitor.log_memory_usage(f"{name}: End", level + 1)
                
                return result
            except Exception as e:
                end_time = time.time()
                elapsed = end_time - start_time
                conditional_log(f"{name}: Failed after {format_time(elapsed)} - {str(e)}", level)
                raise
        return wrapper
    return decorator

@contextmanager
def timing_context(operation_name: str, level: int = 1):
    """Context manager for timing code blocks."""
    if get_debug_level() < level:
        yield
        return
        
    conditional_log(f"{operation_name}: Starting", level)
    memory_monitor.log_memory_usage(f"{operation_name}: Start", level + 1)
    
    start_time = time.time()
    try:
        yield
        end_time = time.time()
        elapsed = end_time - start_time
        
        conditional_log(f"{operation_name}: Completed in {format_time(elapsed)}", level)
        memory_monitor.log_memory_usage(f"{operation_name}: End", level + 1)
        
    except Exception as e:
        end_time = time.time()
        elapsed = end_time - start_time
        conditional_log(f"{operation_name}: Failed after {format_time(elapsed)} - {str(e)}", level)
        raise

class RequestTracker:
    """Track request lifecycle and timing."""
    
    def __init__(self, operation_name: str = "REQUEST"):
        self.operation_name = operation_name
        self.start_time = None
        self.correlation_id = None
    
    @staticmethod
    def generate_correlation_id() -> str:
        """Generate a new correlation ID."""
        return str(uuid.uuid4())[:8]
    
    @staticmethod
    def set_correlation_id(correlation_id: str):
        """Set correlation ID for the current request."""
        set_correlation_id(correlation_id)
        
    def start(self, correlation_id: str = None):
        """Start tracking a request."""
        self.start_time = time.time()
        self.correlation_id = correlation_id or str(uuid.uuid4())[:8]
        set_correlation_id(self.correlation_id)
        
        if is_request_tracking_enabled():
            conditional_log(f"{self.operation_name}_START", 1)
            memory_monitor.log_memory_usage(f"{self.operation_name}_START", 2)
    
    def end(self):
        """End tracking a request."""
        if self.start_time and is_request_tracking_enabled():
            elapsed = time.time() - self.start_time
            conditional_log(f"{self.operation_name}_END: Total time {format_time(elapsed)}", 1)
            memory_monitor.log_memory_usage(f"{self.operation_name}_END", 2)
    
    def log_step(self, step_name: str, payload_size: int = None, level: int = 1):
        """Log a step in the request processing."""
        if not is_request_tracking_enabled():
            return
            
        message = f"{step_name}"
        if payload_size:
            message += f": {format_bytes(payload_size)}"
            
        conditional_log(message, level)

def log_system_info():
    """Log system information for debugging."""
    if get_debug_level() < 2:
        return
        
    conditional_log("=== SYSTEM INFO ===", 2)
    
    # Python and package versions
    import sys
    conditional_log(f"Python: {sys.version.split()[0]}", 2)
    
    # PyTorch info
    try:
        import torch
        conditional_log(f"PyTorch: {torch.__version__}", 2)
        conditional_log(f"CUDA Available: {torch.cuda.is_available()}", 2)
        if torch.cuda.is_available():
            conditional_log(f"CUDA Device: {torch.cuda.get_device_name()}", 2)
            conditional_log(f"CUDA Memory: {format_bytes(torch.cuda.get_device_properties(0).total_memory)}", 2)
    except ImportError:
        conditional_log("PyTorch: Not available", 2)
    
    # Memory info
    try:
        import psutil
        mem = psutil.virtual_memory()
        conditional_log(f"System Memory: {format_bytes(mem.total)} (Available: {format_bytes(mem.available)})", 2)
    except ImportError:
        conditional_log("psutil: Not available for memory monitoring", 2)
    
    conditional_log("=== END SYSTEM INFO ===", 2)

# Initialize system info logging
if get_debug_level() >= 2:
    log_system_info()