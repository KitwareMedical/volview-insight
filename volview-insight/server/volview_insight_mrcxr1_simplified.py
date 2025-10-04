import torch
from transformers import AutoModelForImageTextToText, AutoProcessor
from PIL import Image
import itk
import numpy as np
from typing import Dict, Any

# Import debugging utilities
from debug_utils import timing_decorator, timing_context, conditional_log, memory_monitor, format_time
from performance_middleware import mrcxr1_performance_wrapper, log_image_info, log_model_info

# Import GPU optimization
try:
    from gpu_optimization import get_optimal_device, log_device_selection
    GPU_OPTIMIZATION_AVAILABLE = True
except ImportError:
    GPU_OPTIMIZATION_AVAILABLE = False
    def get_optimal_device(model_type):
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    def log_device_selection(model_type, device, logger_func=print):
        logger_func(f"Using device {device} for {model_type}")

@mrcxr1_performance_wrapper
@timing_decorator("MRCXR1_SIMPLIFIED_INFERENCE", level=1)
def run_volview_insight_mrcxr1_simplified_inference(input_data: Dict[str, Any], itk_img: itk.Image) -> str:
    """
    Runs inference using the local MRCxr1 model on a chest X-ray.
    Simplified version following the Nvidia implementation patterns.
    This version automatically detects and uses available hardware (GPU or CPU).

    Args:
        input_data (Dict[str, Any]): A dictionary containing the user's prompt
                                     under the 'prompt' key.
        itk_img (itk.Image): An ITK image object of the chest X-ray.

    Returns:
        str: The generated text response from the model.
    """
    if itk_img is None:
        raise ValueError("MRCxr1 model requires an image for analysis.")

    # Log input information
    log_image_info(itk_img, "MRCXR1_INPUT")
    conditional_log(f"MRCXR1_PROMPT: {input_data.get('prompt', 'Default prompt')}", level=2)

    # --- 1. Define Model Path and Load ---
    model_path = "/app/models/mrcxr1"  # Use the volume-mounted path directly
    conditional_log(f"MRCXR1_MODEL_PATH: {model_path}", level=2)

    with timing_context("MRCXR1_MODEL_LOADING", level=1):
        # Log optimal device selection for MRCxr1 (large language model)
        optimal_device = get_optimal_device("mrcxr1")
        log_device_selection("mrcxr1", optimal_device, conditional_log)
        
        model = AutoModelForImageTextToText.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",  # Automatically places 3.7B param model on optimal devices (GPU)
            local_files_only=True,
        ).eval()
        memory_monitor.log_memory_usage("MRCXR1_MODEL_LOADED", level=2)
        log_model_info(model, "MRCXR1_MODEL")
        
        processor = AutoProcessor.from_pretrained(model_path, local_files_only=True)
        conditional_log("MRCXR1_PROCESSOR: Loaded successfully", level=2)

    # --- 2. Prepare Image ---
    with timing_context("MRCXR1_IMAGE_PREPROCESSING", level=1):
        img_array = itk.array_view_from_image(itk_img).squeeze()
        conditional_log(f"MRCXR1_ARRAY: Shape={img_array.shape}, dtype={img_array.dtype}", level=2)
        
        # Normalize to 8-bit integer if not already
        if img_array.dtype != np.uint8:
            numerator = img_array - img_array.min()
            denominator = img_array.max() - img_array.min()
            conditional_log(f"MRCXR1_NORMALIZE: Range [{img_array.min():.2f}, {img_array.max():.2f}]", level=3)
            
            # Handle the case of a flat image (denominator is zero)
            if denominator > 0:
                img_array = (255 * numerator / denominator).astype(np.uint8)
            else:
                img_array = np.zeros_like(img_array, dtype=np.uint8)
                conditional_log("MRCXR1_NORMALIZE: Flat image detected, using zeros", level=2)
        
        image = Image.fromarray(img_array).convert("RGB")
        conditional_log(f"MRCXR1_PIL_IMAGE: Size={image.size}, Mode={image.mode}", level=2)
        memory_monitor.log_memory_usage("MRCXR1_IMAGE_PREPROCESSED", level=2)

    # --- 3. Prepare Input Prompt ---
    with timing_context("MRCXR1_PROMPT_PREPARATION", level=1):
        user_question = input_data.get('prompt', "Find abnormalities and support devices.")
        conditional_log(f"MRCXR1_PROMPT: Length={len(user_question)}", level=2)
        messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": user_question}]}]
        memory_monitor.log_memory_usage("MRCXR1_PROMPT_PREPARED", level=2)

    # --- 4. Process Inputs for Model ---
    with timing_context("MRCXR1_INPUT_PROCESSING", level=1):
        text = processor.apply_chat_template(messages, add_generation_prompt=True)
        conditional_log(f"MRCXR1_TEMPLATE: Length={len(text)}", level=2)
        
        # The .to(model.device) ensures tensors are on the same device as the model
        inputs = processor(text=text, images=[image], return_tensors="pt").to(model.device)
        conditional_log(f"MRCXR1_INPUTS: Keys={list(inputs.keys())}", level=2)
        memory_monitor.log_memory_usage("MRCXR1_INPUTS_PROCESSED", level=2)

    # --- 5. Generate Response ---
    with timing_context("MRCXR1_MODEL_INFERENCE", level=1):
        conditional_log("MRCXR1_INFERENCE: Starting model generation", level=1)
        memory_monitor.log_memory_usage("MRCXR1_PRE_INFERENCE", level=2)
        
        with torch.inference_mode():
            generated_ids = model.generate(**inputs, max_new_tokens=1024, temperature=0.1, do_sample=True)
        
        conditional_log(f"MRCXR1_OUTPUT: Generated IDs shape={generated_ids.shape}", level=2)
        memory_monitor.log_memory_usage("MRCXR1_POST_INFERENCE", level=2)

    # --- 6. Trim and Decode Output ---
    with timing_context("MRCXR1_OUTPUT_PROCESSING", level=1):
        input_ids_len = inputs.input_ids.shape[1]
        conditional_log(f"MRCXR1_DECODE: Input IDs length={input_ids_len}", level=2)
        
        trimmed_generated_ids = generated_ids[:, input_ids_len:]
        conditional_log(f"MRCXR1_DECODE: Trimmed shape={trimmed_generated_ids.shape}", level=2)
        
        generated_text = processor.batch_decode(trimmed_generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        conditional_log(f"MRCXR1_DECODE: Output text length={len(generated_text)}", level=2)
        memory_monitor.log_memory_usage("MRCXR1_OUTPUT_PROCESSED", level=2)

    # --- 7. Clean Up Memory ---
    with timing_context("MRCXR1_MEMORY_CLEANUP", level=1):
        conditional_log("MRCXR1_CLEANUP: Starting memory cleanup", level=2)
        memory_monitor.log_memory_usage("MRCXR1_PRE_CLEANUP", level=2)
        
        del inputs, generated_ids, model, processor
        
        # Only try to empty cache if CUDA is available, preventing errors on CPU-only machines.
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            conditional_log("MRCXR1_CLEANUP: CUDA cache emptied", level=2)
        
        memory_monitor.log_memory_usage("MRCXR1_POST_CLEANUP", level=2)
        conditional_log("MRCXR1_CLEANUP: Memory cleanup completed", level=2)

    conditional_log(f"MRCXR1_COMPLETE: Analysis finished, response length={len(generated_text)}", level=1)
    print(f"Analysis with MRCxr1 (simplified) finished. Response:\n{generated_text}")
    return generated_text
