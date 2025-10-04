import itk
import lightning as L
from monai.networks.nets.unetr import UNETR
from monai.transforms.compose import Compose
from monai.transforms.intensity.dictionary import NormalizeIntensityd
from monai.transforms.post.dictionary import Invertd
from monai.transforms.spatial.dictionary import Resized
from monai.transforms.utility.dictionary import EnsureChannelFirstd
from monai.transforms.utility.dictionary import ToTensord
import numpy as np
import torch

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

class NetInference(L.LightningModule):
    def __init__(self, input_size, num_classes):
        super().__init__()

        self.model = UNETR(in_channels = 1, out_channels = num_classes, img_size = input_size, spatial_dims=2)

    def forward(self,x):
        x = self.model(x)
        return x
    
@timing_decorator("SEGMENTATION_INFERENCE_TOTAL", level=0)
def run_volview_insight_seg_inference(itk_img: itk.image, model_checkpoint: str) -> itk.image:
    with timing_context("SEG_IMAGE_PREPROCESSING", level=1):
        input_img = itk.array_from_image(itk_img).astype(int).squeeze()
        conditional_log(f"SEG_ARRAY: Shape={input_img.shape}, dtype={input_img.dtype}", level=2)
        memory_monitor.log_memory_usage("SEG_IMAGE_PREPROCESSED", level=2)
    
    with timing_context("SEG_MODEL_LOADING", level=1):
        input_size = [512,512]
        num_classes = 2
        
        # Use optimal device selection: CPU is 2.1x faster for segmentation
        device = get_optimal_device("segmentation")
        log_device_selection("segmentation", device, conditional_log)
        conditional_log(f"SEG_DEVICE: Using optimal device {device}", level=2)
        
        memory_monitor.log_memory_usage("SEG_PRE_MODEL_LOAD", level=2)
        # Load on CPU first to avoid CUDA subprocess issues, then move to target device
        model = NetInference.load_from_checkpoint(
            model_checkpoint, 
            input_size=input_size, 
            num_classes=num_classes, 
            strict=False, 
            map_location='cpu'  # Always load on CPU first for subprocess compatibility
        )
        model = model.to(device)  # Move to optimal device
        model.eval() # Evaluation mode
        conditional_log(f"SEG_MODEL: Model loaded on CPU and moved to {device}, set to evaluation mode", level=2)
        memory_monitor.log_memory_usage("SEG_POST_MODEL_LOAD", level=2)

    assert len(input_img.shape) == 2, f"Expected input image of dimension 2, got: {len(input_img.shape)}"

    with timing_context("SEG_INPUT_PREPARATION", level=1):
        pre_transforms = Compose([EnsureChannelFirstd(keys = ["image"], channel_dim = 'no_channel'),
                                ToTensord(keys = ["image"]),
                                Resized(keys=['image'], spatial_size = (512,512), mode=("bilinear")),
                                NormalizeIntensityd(keys=['image'])])

        input_dict = {}
        input_dict["image"] = input_img
        conditional_log(f"SEG_INPUT: Prepared input dictionary", level=2)

        # Apply preprocessing
        transform_dict = pre_transforms(input_dict)
        conditional_log("SEG_TRANSFORMS: Preprocessing transforms applied", level=2)
        memory_monitor.log_memory_usage("SEG_INPUT_PREPARED", level=2)

    # Run inference
    with timing_context("SEG_MODEL_INFERENCE", level=1):
        # Move input to the same optimal device as model
        transform_img = transform_dict["image"][None].to(device)  # Add batch dimension and move to optimal device
        conditional_log(f"SEG_INFERENCE: Using optimal device {device} for inference", level=2)
        
        memory_monitor.log_memory_usage("SEG_PRE_INFERENCE", level=2)
        pred = model(transform_img)
        conditional_log(f"SEG_OUTPUT: Prediction shape={pred.shape}", level=2)
        memory_monitor.log_memory_usage("SEG_POST_INFERENCE", level=2)

    # Output segmentation
    with timing_context("SEG_OUTPUT_PROCESSING", level=1):
        pred.softmax(dim = 1) # Convert to probability map
        pred = torch.argmax(pred, dim=1)
        transform_dict["infer"] = pred
        conditional_log("SEG_POSTPROCESS: Softmax and argmax applied", level=2)

        # Invert resize
        post_trans = Invertd(keys = "infer", transform = pre_transforms, orig_keys = "image", nearest_interp = True)
        output_dict = post_trans(transform_dict)
        conditional_log("SEG_POSTPROCESS: Resize inversion applied", level=2)

        # Output segmentation
        seg = output_dict["infer"].cpu().numpy()
        seg = seg.astype(np.ushort)
        conditional_log(f"SEG_FINAL: Final segmentation shape={seg.shape}, dtype={seg.dtype}", level=2)
        
        PixelType = itk.ctype("unsigned short")
        Dimension = 3
        ImageType = itk.Image[PixelType, Dimension]
        result = itk.image_from_array(seg, ttype=ImageType)
        result.SetOrigin(itk_img.GetOrigin())
        result.SetSpacing(itk_img.GetSpacing())
        
        conditional_log("SEG_COMPLETE: ITK image created with proper spacing and origin", level=2)
        memory_monitor.log_memory_usage("SEG_OUTPUT_PROCESSED", level=2)
    
    conditional_log("SEG_COMPLETE: Segmentation inference finished successfully", level=1)
    return result
