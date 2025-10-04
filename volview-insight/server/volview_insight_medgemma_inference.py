import torch
from transformers import AutoModelForImageTextToText, AutoProcessor
from PIL import Image
import itk
import numpy as np
import os
from huggingface_hub import login

# Import debug utilities
try:
    from debug_utils import timing_decorator, timing_context, conditional_log, MemoryMonitor
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False
    # Dummy implementations for when debug utils aren't available
    def timing_decorator(name, level=1):
        def decorator(func):
            return func
        return decorator
    def timing_context(name, level=1):
        from contextlib import nullcontext
        return nullcontext()
    def conditional_log(msg, level=1):
        pass
    class MemoryMonitor:
        def log_memory_usage(self, label, level=1):
            pass

# Initialize memory monitor
memory_monitor = MemoryMonitor() if DEBUG_AVAILABLE else MemoryMonitor()

def setup_huggingface_auth():
    """Setup Hugging Face authentication using HF_TOKEN environment variable."""
    hf_token = os.getenv('HF_TOKEN')
    if not hf_token:
        raise ValueError(
            "HF_TOKEN environment variable is required for MedGemma. "
            "Please set it in your .env file with your Hugging Face API token."
        )
    
    try:
        login(token=hf_token)
        print("✅ Successfully authenticated with Hugging Face")
    except Exception as e:
        raise RuntimeError(f"Failed to authenticate with Hugging Face: {e}")

def get_model_cache_dir(model_id: str) -> str:
    """Get the cache directory for the model, preferring volume-mounted path."""
    # Try volume-mounted path first
    volume_cache_dir = "/app/models/medgemma"
    if os.path.exists(volume_cache_dir):
        return volume_cache_dir
    
    # Fallback to default cache directory
    return None

def generate_vital_sign_summary_prompt(vital_signs_data: dict) -> str:
    """
    Parses a dictionary of vital sign measurements and generates a natural language
    summary prompt, focusing on the most recent measurement for each vital sign.

    Args:
        vital_signs_data (dict): A dictionary containing vital sign measurements.
                                 Expected keys include 'heart_rate', 'respiratory_rate',
                                 'spo2', 'systolic_bp', 'diastolic_bp' and
                                 'mean_arterial_pressure'. Each vital sign value is expected to be a list,
                                 with the most recent measurement as the last element.

    Returns:
        str: A natural language string summarizing the most recent vital signs
    """
    summary_parts = []

    # Define a mapping from dictionary keys to human-readable names and units
    vital_sign_map = {
        "heart_rate": {"name": "Heart Rate", "unit": "bpm"},
        "respiratory_rate": {"name": "Respiratory Rate", "unit": "breaths/min"},
        "spo2": {"name": "SpO2", "unit": "%"},
        "systolic_bp": {"name": "Systolic Blood Pressure", "unit": "mmHg"},
        "diastolic_bp": {"name": "Diastolic Blood Pressure", "unit": "mmHg"},
        "mean_arterial_pressure": {"name": "Mean Arterial Pressure", "unit": "mmHg"},
    }

    # Extract the most recent measurement for each vital sign
    for key, info in vital_sign_map.items():
        if key in vital_signs_data and vital_signs_data[key]:
            # The most recent measurement is the last element in the list
            most_recent_value = vital_signs_data[key][-1]
            summary_parts.append(f"{info['name']}: {most_recent_value} {info['unit']}")
        else:
            summary_parts.append(f"{info['name']}: Not available")

    # Combine the vital sign summaries
    vital_signs_summary = ", ".join(summary_parts)

    return vital_signs_summary

@timing_decorator("MEDGEMMA_INFERENCE_TOTAL", level=0)
def run_volview_insight_medgemma_inference(input_data: dict, itk_img: itk.image = None) -> str:
    """
    Runs inference using the MedGemma 27B - Multimodal model. It can process either text-only prompts (not preferred)
    or prompts combined with an ITK image and vital signs data.

    Args:
        input_data (dict): A dictionary containing input data.
                           Expected to have a 'prompt' key with the user's question (str).
                           If an image is provided, we also check the input data for vital signs
                           data: ('heart_rate', 'respiratory_rate', 'spo2', 'systolic_bp',
                           'diastolic_bp', 'mean_arterial_pressure'), each with a list
                           of measurements ordered chronologically.
        itk_img (itk.image, optional): An ITK image object. If provided, the image
                                       will be processed along with the vital signs data
                                       and the prompt. Defaults to None.

    Returns:
        str: The generated text response from the MedGemma model.
    """

    # Setup Hugging Face authentication
    with timing_context("MEDGEMMA_AUTH_SETUP", level=1):
        setup_huggingface_auth()
        conditional_log("MEDGEMMA_AUTH: Hugging Face authentication completed", level=2)
        memory_monitor.log_memory_usage("MEDGEMMA_AUTH_COMPLETE", level=2)

    model_variant = "4b-it"  # @param ["4b-it", "27b-it", "27b-text-it"]
    model_id = f"google/medgemma-{model_variant}"
    is_thinking = False
    conditional_log(f"MEDGEMMA_CONFIG: Using model variant {model_variant}", level=2)

    role_instruction = "You are an expert radiologist."
    # Max new tokens controls the length of the output response - how many tokens the LLM can generate. 
    if "27b" in model_variant and is_thinking:
        system_instruction = f"SYSTEM INSTRUCTION: think silently if needed. Please speak as an intelligent, concise physician short of time. {role_instruction}"
        max_new_tokens = 1300
    else:
        system_instruction = "Please speak as an intelligent, concise physician short of time." + role_instruction
        max_new_tokens = 300

    # Question
    user_question = input_data['prompt']
    vital_signs_summary = generate_vital_sign_summary_prompt(input_data)

    if itk_img is not None:
        with timing_context("MEDGEMMA_IMAGE_PREPROCESSING", level=1):
            # Load image 
            img_array = itk.array_from_image(itk_img).astype(int).squeeze()
            conditional_log(f"MEDGEMMA_ARRAY: Shape={img_array.shape}, dtype={img_array.dtype}", level=2)
            print('Input image array shape:', img_array.shape)
            
            image_uint8 = (255 * (img_array - img_array.min()) / (img_array.max() - img_array.min())).astype(np.uint8)
            image = Image.fromarray(image_uint8)
            conditional_log(f"MEDGEMMA_PIL_IMAGE: Size={image.size}, Mode={image.mode}", level=2)
            memory_monitor.log_memory_usage("MEDGEMMA_IMAGE_PREPROCESSED", level=2)

        prompt = f"Analyze the provided chest X-ray and the patient's most recent vital signs: {vital_signs_summary}. Based on this data, answer the following question: {user_question}"  
        content = [
                    {"type": "text", "text": prompt},
                    {"type": "image", "image": image}
                ]
    
    else:
        prompt = f"Analyze the patient's most recent vital signs: {vital_signs_summary}. Based on this data, answer the following question: {user_question}"  
        content = [
            {"type": "text", "text": prompt}
            ]

    print('MedGemma prompt:', prompt)
    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": system_instruction}]
        },
        {
            "role": "user",
            "content": content
        }
    ]

    model_id = f"google/medgemma-{model_variant}"
    
    # Get cache directory for model storage
    cache_dir = get_model_cache_dir(model_id)
    
    with timing_context("MEDGEMMA_MODEL_LOADING", level=1):
        conditional_log(f"MEDGEMMA_LOADING: Starting model load for {model_id}", level=1)
        print(f"Loading MedGemma model: {model_id}")
        if cache_dir:
            print(f"Using cache directory: {cache_dir}")
            conditional_log(f"MEDGEMMA_CACHE: Using cache directory {cache_dir}", level=2)
        
        memory_monitor.log_memory_usage("MEDGEMMA_PRE_LOAD", level=2)
        
        # Load model and processor with caching
        model_kwargs = {
            "device_map": "auto",
            "torch_dtype": torch.bfloat16,
        }
        processor_kwargs = {}
        
        if cache_dir:
            model_kwargs["cache_dir"] = cache_dir
            processor_kwargs["cache_dir"] = cache_dir
        
        model = AutoModelForImageTextToText.from_pretrained(model_id, **model_kwargs)
        processor = AutoProcessor.from_pretrained(model_id, **processor_kwargs)
        
        conditional_log("MEDGEMMA_LOADING: Model and processor loaded successfully", level=2)
        memory_monitor.log_memory_usage("MEDGEMMA_POST_LOAD", level=2)

    # --- Start of per-request logic ---
    with timing_context("MEDGEMMA_INPUT_PROCESSING", level=1):
        conditional_log("MEDGEMMA_PROCESSING: Starting input processing", level=2)
        
        # Process inputs for the model
        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device, dtype=torch.bfloat16)

        input_len = inputs["input_ids"].shape[-1]
        conditional_log(f"MEDGEMMA_INPUTS: Input length={input_len}", level=2)
        memory_monitor.log_memory_usage("MEDGEMMA_INPUTS_PROCESSED", level=2)

    # Run inference in a memory-efficient context
    with timing_context("MEDGEMMA_MODEL_INFERENCE", level=1):
        conditional_log(f"MEDGEMMA_INFERENCE: Starting generation with max_new_tokens={max_new_tokens}", level=1)
        memory_monitor.log_memory_usage("MEDGEMMA_PRE_INFERENCE", level=2)
        
        with torch.inference_mode():
            generation = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
            generation = generation[0][input_len:]
        
        conditional_log(f"MEDGEMMA_OUTPUT: Generated {len(generation)} tokens", level=2)
        memory_monitor.log_memory_usage("MEDGEMMA_POST_INFERENCE", level=2)

    # Decode the generated tokens into a string response
    with timing_context("MEDGEMMA_OUTPUT_PROCESSING", level=1):
        response = processor.decode(generation, skip_special_tokens=True)
        conditional_log(f"MEDGEMMA_DECODE: Response length={len(response)}", level=2)
        memory_monitor.log_memory_usage("MEDGEMMA_OUTPUT_PROCESSED", level=2)

    # --- Memory Cleanup ---
    with timing_context("MEDGEMMA_MEMORY_CLEANUP", level=1):
        conditional_log("MEDGEMMA_CLEANUP: Starting memory cleanup", level=2)
        memory_monitor.log_memory_usage("MEDGEMMA_PRE_CLEANUP", level=2)
        
        # This is the critical step to prevent CUDA memory errors on subsequent runs.
        # It explicitly deletes the large tensors from GPU memory.
        del inputs
        del generation
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            conditional_log("MEDGEMMA_CLEANUP: CUDA cache emptied", level=2)
        
        memory_monitor.log_memory_usage("MEDGEMMA_POST_CLEANUP", level=2)
        conditional_log("MEDGEMMA_CLEANUP: Memory cleanup completed", level=2)

    conditional_log(f"MEDGEMMA_COMPLETE: Analysis finished, response length={len(response)}", level=1)
    return response
