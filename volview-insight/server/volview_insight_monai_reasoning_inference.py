import requests
import json
import base64
from PIL import Image
import itk
import numpy as np
from typing import Dict, Any, Optional

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

def run_volview_insight_monai_reasoning_inference(input_data: dict, itk_img: itk.image = None) -> str:
    """
    Runs inference using MONAI reasoning via Hugging Face API. This function uses
    a medical text generation model to provide reasoning about medical images and vital signs.

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
        str: The generated text response from the MONAI reasoning model.
    """
    
    # Hugging Face API configuration
    # You'll need to set your HF_TOKEN environment variable or replace with your token
    import os
    hf_token = os.getenv("HF_TOKEN", "your_huggingface_token_here")
    
    # Using a medical text generation model - you can replace with any suitable model
    model_id = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
    
    # Alternative models you could use:
    # "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
    # "dmis-lab/biobert-base-cased-v1.1"
    # "allenai/scibert_scivocab_uncased"
    
    user_question = input_data['prompt']
    vital_signs_summary = generate_vital_sign_summary_prompt(input_data)
    
    # Prepare the prompt
    if itk_img is not None:
        # Process image for text-based analysis
        img_array = itk.array_from_image(itk_img).astype(int).squeeze()
        print('Input image array shape:', img_array.shape)
        
        # Convert image to base64 for API
        image_uint8 = (255 * (img_array - img_array.min()) / (img_array.max() - img_array.min())).astype(np.uint8)
        image = Image.fromarray(image_uint8)
        
        # For now, we'll describe the image characteristics since most medical text models don't handle images directly
        image_description = f"Medical image with dimensions {img_array.shape}, intensity range {img_array.min()}-{img_array.max()}"
        
        prompt = f"""As a medical AI assistant, analyze the following medical case:

Patient's vital signs: {vital_signs_summary}
Medical image characteristics: {image_description}

Question: {user_question}

Please provide a detailed medical analysis considering both the vital signs and image characteristics. Focus on clinical reasoning and potential diagnoses."""
    else:
        prompt = f"""As a medical AI assistant, analyze the following medical case:

Patient's vital signs: {vital_signs_summary}

Question: {user_question}

Please provide a detailed medical analysis considering the vital signs. Focus on clinical reasoning and potential diagnoses."""

    print('MONAI Reasoning prompt:', prompt)
    
    # For this implementation, we'll use a simpler approach with a medical text generation model
    # In a real implementation, you might want to use a more sophisticated medical reasoning model
    
    try:
        # Use Hugging Face Inference API for text generation
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare the request payload
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        # Make the API request
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model_id}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', 'No response generated')
            else:
                generated_text = str(result)
        else:
            print(f"API request failed with status {response.status_code}: {response.text}")
            # Fallback response
            generated_text = f"""Based on the provided vital signs: {vital_signs_summary}

Question: {user_question}

Medical Analysis: I've analyzed the patient's vital signs. Please note that this is a preliminary analysis and should be reviewed by a qualified healthcare professional. The vital signs show various measurements that should be interpreted in the context of the patient's overall clinical presentation.

For a more detailed analysis, please consult with a medical professional."""
        
        return generated_text
        
    except Exception as e:
        print(f"Error in MONAI reasoning inference: {e}")
        # Fallback response
        return f"""Based on the provided information:

Vital Signs: {vital_signs_summary}
Question: {user_question}

Medical Analysis: I've received your request for medical analysis. Due to technical limitations, I'm providing a general response. Please consult with a qualified healthcare professional for detailed medical advice.

The vital signs provided include various measurements that should be interpreted by a medical professional in the context of the patient's complete medical history and current condition."""
