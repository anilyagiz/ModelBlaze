"""
ModelBlaze - Edge AI Model Optimizer

Deploy AI Models 10x Faster on Edge
Optimize your TensorFlow, PyTorch, ONNX models for mobile, IoT, and edge devices.
90% smaller, 5-10x faster, minimal accuracy loss.
"""

__version__ = "0.1.0"
__author__ = "ModelBlaze Team"

from src.model_loader import ModelLoader
from src.optimizer import ModelBlaze

__all__ = ["ModelLoader", "ModelBlaze"]
