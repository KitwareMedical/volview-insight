# MONAI Reasoning Integration

This document describes the integration of MONAI reasoning as an alternative backend model to medGemma in the VolView Insight application.

## Overview

The application now supports two AI models for medical reasoning:
1. **MedGemma** - The original Google MedGemma model for medical text and image analysis
2. **MONAI Reasoning** - A new alternative using MONAI-based medical reasoning via Hugging Face API

## Features

### Frontend Changes

- **Model Selection Switch**: Added a dropdown in the chat panel to switch between "MedGemma" and "MONAI Reasoning"
- **Dynamic RPC Calls**: The frontend automatically calls the appropriate backend method based on the selected model
- **State Management**: Model selection is persisted in the medgemma store

### Backend Changes

- **New RPC Method**: Added `monaiReasoningAnalysis` RPC method
- **MONAI Inference Module**: Created `volview_insight_monai_reasoning_inference.py` for MONAI reasoning logic
- **Hugging Face Integration**: Uses Hugging Face Inference API for medical text generation

## Files Modified

### Frontend
- `src/components/ChatModule.vue` - Added model selection UI and dynamic RPC calls
- `src/store/medgemma-store.ts` - Added model selection state management

### Backend
- `server/volview_insight_methods.py` - Added MONAI reasoning RPC method
- `server/volview_insight_monai_reasoning_inference.py` - New MONAI reasoning implementation
- `server/pyproject.toml` - Added requests dependency

## Configuration

### Hugging Face API Token

To use the MONAI reasoning model, you need to set your Hugging Face API token:

```bash
export HF_TOKEN="your_huggingface_token_here"
```

Or set it in your environment before running the server.

### Model Selection

The model selection is stored in the frontend store and persists during the session. Users can switch between models using the dropdown in the chat panel.

## Usage

1. **Start the application** with both frontend and backend running
2. **Select a patient** in the application
3. **Choose the AI model** using the dropdown in the chat panel
4. **Type your question** and send it
5. **The appropriate model** will process your request based on the selection

## Testing

A test script is provided to verify the integration:

```bash
cd volview-insight/server
python test_monai_integration.py
```

This will test both text-only and image-based MONAI reasoning functionality.

## Technical Details

### MONAI Reasoning Implementation

The MONAI reasoning implementation:
- Uses Hugging Face Inference API for medical text generation
- Supports both text-only and image-based analysis
- Includes fallback responses for API failures
- Processes vital signs data similar to MedGemma
- Uses medical text generation models from Hugging Face

### Model Selection Logic

The frontend determines which RPC method to call based on the selected model:
- `medgemma` → calls `medgemmaAnalysis`
- `monai-reasoning` → calls `monaiReasoningAnalysis`

Both methods use the same store for input/output, ensuring compatibility.

## Future Enhancements

Potential improvements for the MONAI reasoning integration:
1. **Better Model Selection**: Use more sophisticated MONAI models
2. **Image Processing**: Improve image analysis capabilities
3. **Caching**: Add response caching for better performance
4. **Error Handling**: Enhanced error handling and user feedback
5. **Model Configuration**: Allow users to configure model parameters

## Troubleshooting

### Common Issues

1. **API Token Not Set**: Ensure `HF_TOKEN` environment variable is set
2. **Network Issues**: Check internet connectivity for Hugging Face API calls
3. **Model Loading**: Some models may take time to load on first use
4. **Memory Issues**: Large models may require significant memory

### Debug Mode

Enable debug logging by setting the log level in your application configuration.

## Dependencies

The MONAI reasoning integration requires:
- `requests` - For Hugging Face API calls
- `transformers` - For model loading (already included)
- `PIL` - For image processing (already included)
- `itk` - For medical image processing (already included)
