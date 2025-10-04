"""
GPU Optimization Module
Provides intelligent device selection based on model characteristics and performance analysis.
"""

import torch
import os
from typing import Literal

def get_optimal_device(model_type: Literal["segmentation", "medgemma", "mrcxr1", "large_llm", "small_model"]) -> torch.device:
    """
    Determine the optimal device (CPU/GPU) based on model characteristics and performance analysis.
    
    Based on empirical performance testing:
    - Large language models (4B+ params): 7-9x faster on GPU
    - Small segmentation models (~50M params): 2x faster on CPU due to overhead
    
    Args:
        model_type: Type of model for device selection
        
    Returns:
        torch.device: Optimal device for the given model type
    """
    
    # Check if GPU is available
    if not torch.cuda.is_available():
        return torch.device('cpu')
    
    # Check for environment override
    force_device = os.environ.get('VOLVIEW_FORCE_DEVICE', '').lower()
    if force_device in ['cpu', 'cuda', 'gpu']:
        device_name = 'cuda' if force_device == 'gpu' else force_device
        return torch.device(device_name)
    
    # Optimal device selection based on performance analysis
    optimal_devices = {
        # Small models: CPU is faster due to GPU overhead
        "segmentation": "cpu",    # MONAI UNETR: 2.3s CPU vs 4.9s GPU (2.1x faster on CPU)
        "small_model": "cpu",
        
        # Large language models: GPU is much faster
        "medgemma": "cuda",       # MedGemma 4B-IT: 15.6s GPU vs 115.8s CPU (7.4x faster on GPU)  
        "mrcxr1": "cuda",         # MRCxr1 3.7B: 22.3s GPU vs 203.0s CPU (9.1x faster on GPU)
        "large_llm": "cuda",
    }
    
    device_name = optimal_devices.get(model_type, "cuda")  # Default to GPU for unknown types
    return torch.device(device_name)

def log_device_selection(model_type: str, device: torch.device, logger_func=print):
    """
    Log the device selection decision with reasoning.
    
    Args:
        model_type: Type of model
        device: Selected device
        logger_func: Function to use for logging (default: print)
    """
    
    reasoning = {
        "cpu": {
            "segmentation": "Small segmentation model: CPU is 2.1x faster due to lower GPU overhead",
            "small_model": "Small model: CPU is more efficient due to GPU initialization overhead"
        },
        "cuda": {
            "medgemma": "Large language model (4B params): GPU is 7.4x faster for transformer operations",
            "mrcxr1": "Large language model (3.7B params): GPU is 9.1x faster for attention mechanisms", 
            "large_llm": "Large language model: GPU provides massive parallel acceleration"
        }
    }
    
    device_str = str(device)
    reason = reasoning.get(device_str, {}).get(model_type, f"Using {device_str} device")
    logger_func(f"DEVICE_OPTIMIZATION: {model_type} -> {device} ({reason})")

# Performance thresholds for dynamic selection
MODEL_SIZE_THRESHOLDS = {
    "small_model_max_params": 100_000_000,    # 100M parameters
    "large_model_min_params": 1_000_000_000,  # 1B parameters
    "gpu_memory_threshold_mb": 500,           # 500MB GPU memory usage
}

def get_device_by_model_size(estimated_params: int, estimated_gpu_memory_mb: float = None) -> torch.device:
    """
    Select device based on estimated model size.
    
    Args:
        estimated_params: Estimated number of model parameters
        estimated_gpu_memory_mb: Estimated GPU memory usage in MB
        
    Returns:
        torch.device: Optimal device based on size heuristics
    """
    
    if not torch.cuda.is_available():
        return torch.device('cpu')
    
    # Use GPU memory estimate if available
    if estimated_gpu_memory_mb is not None:
        if estimated_gpu_memory_mb < MODEL_SIZE_THRESHOLDS["gpu_memory_threshold_mb"]:
            return torch.device('cpu')  # Small model, CPU is likely faster
        else:
            return torch.device('cuda')  # Large model, GPU is likely faster
    
    # Use parameter count estimate
    if estimated_params < MODEL_SIZE_THRESHOLDS["small_model_max_params"]:
        return torch.device('cpu')   # Small model
    elif estimated_params > MODEL_SIZE_THRESHOLDS["large_model_min_params"]:
        return torch.device('cuda')  # Large model
    else:
        return torch.device('cuda')  # Medium model, default to GPU