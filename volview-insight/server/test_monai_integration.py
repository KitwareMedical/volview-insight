#!/usr/bin/env python3
"""
Simple test script to verify MONAI reasoning integration.
This script tests the MONAI reasoning inference function without requiring a full server setup.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from volview_insight_monai_reasoning_inference import run_volview_insight_monai_reasoning_inference

def test_monai_reasoning_text_only():
    """Test MONAI reasoning with text-only input (no image)."""
    print("Testing MONAI reasoning with text-only input...")
    
    # Test data
    input_data = {
        'prompt': 'What do these vital signs indicate about the patient\'s condition?',
        'heart_rate': [85, 90, 88],
        'respiratory_rate': [16, 18, 17],
        'spo2': [98, 97, 99],
        'systolic_bp': [120, 125, 122],
        'diastolic_bp': [80, 82, 81]
    }
    
    try:
        result = run_volview_insight_monai_reasoning_inference(input_data, itk_img=None)
        print("✅ Text-only test passed!")
        print(f"Response: {result[:200]}...")  # Show first 200 characters
        return True
    except Exception as e:
        print(f"❌ Text-only test failed: {e}")
        return False

def test_monai_reasoning_with_image():
    """Test MONAI reasoning with image input."""
    print("\nTesting MONAI reasoning with image input...")
    
    # Create a simple test image
    import numpy as np
    import itk
    
    # Create a simple 2D test image
    test_array = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
    test_image = itk.image_from_array(test_array)
    
    # Test data
    input_data = {
        'prompt': 'Analyze this medical image and provide insights.',
        'heart_rate': [75],
        'respiratory_rate': [14],
        'spo2': [99]
    }
    
    try:
        result = run_volview_insight_monai_reasoning_inference(input_data, itk_img=test_image)
        print("✅ Image test passed!")
        print(f"Response: {result[:200]}...")  # Show first 200 characters
        return True
    except Exception as e:
        print(f"❌ Image test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing MONAI Reasoning Integration")
    print("=" * 50)
    
    # Set a dummy HF token for testing (the function will use fallback if API fails)
    os.environ['HF_TOKEN'] = 'dummy_token_for_testing'
    
    tests_passed = 0
    total_tests = 2
    
    if test_monai_reasoning_text_only():
        tests_passed += 1
    
    if test_monai_reasoning_with_image():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! MONAI reasoning integration is working.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
