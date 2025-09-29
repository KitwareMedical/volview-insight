import torch
from transformers import (
    AutoProcessor,
    AutoTokenizer,
    AutoModelForImageTextToText,
    TextIteratorStreamer,
)
from PIL import Image
import itk
import numpy as np
import os
from threading import Thread

def get_model_cache_dir() -> str:
    """Get the cache directory for the MRCxr1 model, preferring volume-mounted path."""
    # The volume mount maps ./volumes/model-cache to /app/models
    # So MRCxr1 model should be at /app/models/mrcxr1
    volume_cache_dir = "/app/models/mrcxr1"
    
    print(f"Checking for MRCxr1 model at: {volume_cache_dir}")
    print(f"Directory exists: {os.path.exists(volume_cache_dir)}")
    
    if os.path.exists(volume_cache_dir):
        # List contents to verify
        try:
            contents = os.listdir(volume_cache_dir)
            print(f"MRCxr1 model directory contents: {contents[:5]}...")  # Show first 5 files
            return volume_cache_dir
        except Exception as e:
            print(f"Error listing directory contents: {e}")
    
    # Try alternative paths as fallback
    alt_paths = [
        "/models/mrcxr1",
        "/app/volumes/model-cache/mrcxr1",
        "./volumes/model-cache/mrcxr1"
    ]
    
    for path in alt_paths:
        print(f"Trying alternative path: {path}")
        if os.path.exists(path):
            print(f"Found MRCxr1 model at: {path}")
            return path
    
    print("MRCxr1 model cache directory not found in any expected locations")
    return None
def run_volview_insight_mrcxr1_inference(input_data: dict, itk_img: itk.image = None) -> str:
    """
    Runs MRCxr1 inference on the provided input data and image.
    Uses ONLY local cached model, NO HuggingFace connection.
    Does NOT use vital signs in the prompt.

    Args:
        input_data (dict): A dictionary containing the prompt.
        itk_img (itk.image, optional): An ITK image object. If provided, it will be processed
                                       and included in the analysis.

    Returns:
        str: The generated text response from the MRCxr1 model.
    """
    
    # Model configuration - ONLY use local cache
    default_prompt = "Find abnormalities and support devices."
    
    # Device and dtype setup
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    
    # Get cache directory for model storage - MUST exist locally
    cache_dir = get_model_cache_dir()
    
    if not cache_dir or not os.path.exists(cache_dir):
        raise FileNotFoundError(f"MRCxr1 model not found in local cache. Expected at /app/models/mrcxr1")
    
    model_path = cache_dir
    print(f"Loading MRCxr1 model from local cache ONLY: {model_path}")
    
    # Load model and processor from local path ONLY
    model_kwargs = {
        "device_map": "auto",
        "torch_dtype": dtype,
        "local_files_only": True,  # Force local files only
    }
    processor_kwargs = {
        "local_files_only": True,  # Force local files only
    }
    
    # Load model, processor, and tokenizer
    model = AutoModelForImageTextToText.from_pretrained(model_path, **model_kwargs).eval()
    processor = AutoProcessor.from_pretrained(model_path, **processor_kwargs)
    
    # Load tokenizer for streaming
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True, local_files_only=True)
        print(">>> MRCxr1: loaded tokenizer via AutoTokenizer", flush=True)
    except Exception as e:
        # Some processors expose .tokenizer; use that as a fallback
        tokenizer = getattr(processor, "tokenizer", None)
        if tokenizer is None:
            print("!!! MRCxr1: failed to load a tokenizer for TextIteratorStreamer", flush=True)
            print(f"    error: {e}", flush=True)
            raise

    # Question setup - NO vital signs for MRCxr1
    user_question = input_data.get('prompt', default_prompt)

    # Prepare messages for chat template - NO vital signs
    messages = []
    
    if itk_img is not None:
        # Load and process image 
        img_array = itk.array_from_image(itk_img).astype(int).squeeze()
        print('Input image array shape:', img_array.shape)
        image_uint8 = (255 * (img_array - img_array.min()) / (img_array.max() - img_array.min())).astype(np.uint8)
        image = Image.fromarray(image_uint8)

        # Simple prompt without vital signs
        prompt = f"Analyze the provided chest X-ray. {user_question}"
        content = [
            {"type": "image"},
            {"type": "text", "text": prompt}
        ]
    else:
        # Text-only prompt without vital signs
        prompt = user_question
        content = [
            {"type": "text", "text": prompt}
        ]

    print('MRCxr1 prompt:', prompt)
    messages.append({"role": "user", "content": content})

    # Apply chat template and process inputs
    chat_prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    
    if itk_img is not None:
        inputs = processor(text=chat_prompt, images=[image], return_tensors="pt")
    else:
        inputs = processor(text=chat_prompt, return_tensors="pt")
    
    inputs = inputs.to(device)

    # Generation parameters
    max_new_tokens = 1024
    temperature = 0.1
    repetition_penalty = 1.05
    do_sample = True

    # Create streamer for token streaming
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    generation_args = dict(
        inputs,
        streamer=streamer,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        repetition_penalty=repetition_penalty,
        do_sample=do_sample,
    )

    print(f">>> MRCxr1 inference: args={{'temp': {temperature}, 'rep_pen': {repetition_penalty}, 'do_sample': {do_sample}}}", flush=True)

    # Run inference in a memory-efficient context
    with torch.inference_mode():
        thread = Thread(target=model.generate, kwargs=generation_args)
        thread.start()

        # Collect generated text
        response_parts = []
        for new_text in streamer:
            response_parts.append(new_text)
        
        thread.join()
        response = "".join(response_parts)

    # --- Memory Cleanup ---
    # This is the critical step to prevent CUDA memory errors on subsequent runs.
    del inputs
    if 'image' in locals():
        del image
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

    return response
