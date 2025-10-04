"""
Performance middleware for request/response timing and monitoring.
Provides comprehensive request lifecycle tracking and payload analysis.
"""

import time
import sys
from typing import Dict, Any, Callable
from debug_utils import RequestTracker, conditional_log, format_bytes, get_debug_level

class RequestPerformanceMiddleware:
    """Middleware to track request performance metrics."""
    
    def __init__(self):
        self.active_requests = {}
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap request processing functions."""
        def wrapper(*args, **kwargs):
            # Create request tracker
            tracker = RequestTracker("REQUEST")
            tracker.start()
            
            # Log request start with basic info
            self._log_request_start(args, kwargs, tracker)
            
            try:
                # Execute the wrapped function
                result = func(*args, **kwargs)
                
                # Log successful completion
                self._log_request_success(result, tracker)
                
                return result
                
            except Exception as e:
                # Log error
                self._log_request_error(e, tracker)
                raise
            finally:
                # Always end tracking
                tracker.end()
        
        return wrapper
    
    def _log_request_start(self, args, kwargs, tracker: RequestTracker):
        """Log request start information."""
        if get_debug_level() < 1:
            return
            
        # Try to estimate payload size from arguments
        payload_size = self._estimate_payload_size(args, kwargs)
        tracker.log_step("PAYLOAD_SIZE", payload_size, level=1)
        
        # Log request parameters if debug level is high enough
        if get_debug_level() >= 3:
            self._log_detailed_request_info(args, kwargs, tracker)
    
    def _log_request_success(self, result, tracker: RequestTracker):
        """Log successful request completion."""
        if get_debug_level() < 1:
            return
            
        # Estimate response size
        response_size = self._estimate_response_size(result)
        tracker.log_step("RESPONSE_SIZE", response_size, level=1)
    
    def _log_request_error(self, error: Exception, tracker: RequestTracker):
        """Log request error."""
        conditional_log(f"REQUEST_ERROR: {type(error).__name__}: {str(error)}", level=1)
    
    def _estimate_payload_size(self, args, kwargs) -> int:
        """Estimate payload size from function arguments."""
        total_size = 0
        
        # Check for common image-related arguments
        for arg in args:
            if hasattr(arg, '__sizeof__'):
                total_size += sys.getsizeof(arg)
            elif isinstance(arg, dict):
                total_size += self._estimate_dict_size(arg)
        
        for key, value in kwargs.items():
            if hasattr(value, '__sizeof__'):
                total_size += sys.getsizeof(value)
            elif isinstance(value, dict):
                total_size += self._estimate_dict_size(value)
        
        return total_size
    
    def _estimate_response_size(self, result) -> int:
        """Estimate response size."""
        if isinstance(result, str):
            return len(result.encode('utf-8'))
        elif isinstance(result, dict):
            return self._estimate_dict_size(result)
        elif hasattr(result, '__sizeof__'):
            return sys.getsizeof(result)
        return 0
    
    def _estimate_dict_size(self, d: dict) -> int:
        """Estimate size of a dictionary."""
        try:
            return sys.getsizeof(str(d))
        except:
            return 0
    
    def _log_detailed_request_info(self, args, kwargs, tracker: RequestTracker):
        """Log detailed request information for debugging."""
        # Log argument types and basic info
        arg_info = []
        for i, arg in enumerate(args):
            arg_type = type(arg).__name__
            if hasattr(arg, 'shape'):
                arg_info.append(f"arg{i}: {arg_type}(shape={arg.shape})")
            elif isinstance(arg, (str, int, float, bool)):
                arg_info.append(f"arg{i}: {arg_type}({arg})")
            else:
                arg_info.append(f"arg{i}: {arg_type}")
        
        if arg_info:
            conditional_log(f"REQUEST_ARGS: {', '.join(arg_info)}", level=3)
        
        # Log keyword arguments
        if kwargs:
            kwarg_info = []
            for key, value in kwargs.items():
                value_type = type(value).__name__
                if hasattr(value, 'shape'):
                    kwarg_info.append(f"{key}: {value_type}(shape={value.shape})")
                elif isinstance(value, (str, int, float, bool)):
                    kwarg_info.append(f"{key}: {value_type}({value})")
                else:
                    kwarg_info.append(f"{key}: {value_type}")
            
            if kwarg_info:
                conditional_log(f"REQUEST_KWARGS: {', '.join(kwarg_info)}", level=3)

class MRCxr1PerformanceWrapper:
    """Specialized performance wrapper for MRCxr1 inference operations."""
    
    def __init__(self, operation_name: str = "MRCXR1_INFERENCE"):
        self.operation_name = operation_name
        self.middleware = RequestPerformanceMiddleware()
    
    def __call__(self, func: Callable) -> Callable:
        """Wrap MRCxr1 inference function with performance monitoring."""
        def wrapper(*args, **kwargs):
            # Create specialized tracker for MRCxr1
            tracker = RequestTracker(self.operation_name)
            tracker.start()
            
            # Log MRCxr1 specific start information
            self._log_mrcxr1_start(args, kwargs, tracker)
            
            try:
                result = func(*args, **kwargs)
                self._log_mrcxr1_success(result, tracker)
                return result
                
            except Exception as e:
                self._log_mrcxr1_error(e, tracker)
                raise
            finally:
                tracker.end()
        
        return wrapper
    
    def _log_mrcxr1_start(self, args, kwargs, tracker: RequestTracker):
        """Log MRCxr1 specific start information."""
        if get_debug_level() >= 2:
            # Log input data information
            for i, arg in enumerate(args):
                if hasattr(arg, 'get') and callable(arg.get):  # Dict-like input_data
                    prompt = arg.get('prompt', 'No prompt')
                    conditional_log(f"MRCXR1_PROMPT: {prompt[:100]}{'...' if len(prompt) > 100 else ''}", level=2)
                
                # Check for ITK image
                elif hasattr(arg, 'GetLargestPossibleRegion'):  # ITK image
                    region = arg.GetLargestPossibleRegion()
                    size = region.GetSize()
                    conditional_log(f"MRCXR1_IMAGE: ITK Image {size[0]}x{size[1]} (dims: {len(size)})", level=2)
    
    def _log_mrcxr1_success(self, result, tracker: RequestTracker):
        """Log MRCxr1 successful completion."""
        if isinstance(result, str) and get_debug_level() >= 2:
            response_length = len(result)
            response_preview = result[:200] + "..." if len(result) > 200 else result
            conditional_log(f"MRCXR1_RESPONSE: {response_length} chars", level=2)
            if get_debug_level() >= 3:
                conditional_log(f"MRCXR1_RESPONSE_PREVIEW: {response_preview}", level=3)
    
    def _log_mrcxr1_error(self, error: Exception, tracker: RequestTracker):
        """Log MRCxr1 specific errors."""
        conditional_log(f"MRCXR1_ERROR: {type(error).__name__}: {str(error)}", level=1)

# Create middleware instances for easy import
request_performance_middleware = RequestPerformanceMiddleware()
mrcxr1_performance_wrapper = MRCxr1PerformanceWrapper()

def log_image_info(itk_img, label: str = "IMAGE"):
    """Helper function to log ITK image information."""
    if get_debug_level() < 2 or itk_img is None:
        return
    
    try:
        region = itk_img.GetLargestPossibleRegion()
        size = region.GetSize()
        spacing = itk_img.GetSpacing()
        origin = itk_img.GetOrigin()
        
        size_str = "x".join(map(str, size))
        spacing_str = "x".join(f"{s:.2f}" for s in spacing)
        
        conditional_log(f"{label}_INFO: Size={size_str}, Spacing=({spacing_str}), Origin=({origin[0]:.1f},{origin[1]:.1f})", level=2)
        
    except Exception as e:
        conditional_log(f"{label}_INFO: Failed to extract info - {str(e)}", level=2)

def log_model_info(model, label: str = "MODEL"):
    """Helper function to log model information."""
    if get_debug_level() < 2 or model is None:
        return
    
    try:
        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        conditional_log(f"{label}_INFO: Total params={total_params:,}, Trainable={trainable_params:,}", level=2)
        
        # Log device information
        if hasattr(model, 'device'):
            conditional_log(f"{label}_DEVICE: {model.device}", level=2)
        
    except Exception as e:
        conditional_log(f"{label}_INFO: Failed to extract info - {str(e)}", level=2)