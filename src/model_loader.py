"""
Model Loader - Load and analyze models from different frameworks
Supports: TensorFlow, PyTorch, ONNX
"""

import os
from typing import Dict, Any, Union, Optional
from pathlib import Path
import numpy as np
import logging

from src.utils.logger import get_logger
from src.utils.error_handler import ErrorHandler, ModelLoadError

logger = get_logger(__name__)


class ModelLoader:
    """
    Universal model loader for TensorFlow, PyTorch, and ONNX models
    """

    def __init__(self):
        self.supported_formats = {
            "tensorflow": [".h5", ".pb", ".keras", ".tflite"],
            "pytorch": [".pth", ".pt", ".ckpt"],
            "onnx": [".onnx"],
        }

    def load(self, model_path: str) -> Dict[str, Any]:
        """
        Load a model and return metadata

        Args:
            model_path: Path to the model file

        Returns:
            Dictionary containing model, framework, and metadata
        """
        model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        extension = model_path.suffix.lower()

        # Detect framework
        if extension in self.supported_formats["tensorflow"]:
            return self._load_tensorflow(model_path)
        elif extension in self.supported_formats["pytorch"]:
            return self._load_pytorch(model_path)
        elif extension in self.supported_formats["onnx"]:
            return self._load_onnx(model_path)
        else:
            raise ValueError(f"Unsupported model format: {extension}")

    def _load_tensorflow(self, model_path: Path) -> Dict[str, Any]:
        """Load TensorFlow model"""
        try:
            import tensorflow as tf
        except ImportError:
            raise ImportError("TensorFlow not installed. Install with: pip install tensorflow")

        extension = model_path.suffix.lower()

        if extension == ".tflite":
            # Load TFLite model
            interpreter = tf.lite.Interpreter(model_path=str(model_path))
            interpreter.allocate_tensors()

            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()

            return {
                "model": interpreter,
                "framework": "tensorflow_lite",
                "format": "tflite",
                "path": str(model_path),
                "input_details": input_details,
                "output_details": output_details,
                "size_mb": model_path.stat().st_size / (1024 * 1024),
            }

        elif extension in [".h5", ".keras"]:
            # Load Keras model
            model = tf.keras.models.load_model(str(model_path))

            return {
                "model": model,
                "framework": "tensorflow",
                "format": "keras",
                "path": str(model_path),
                "input_shape": model.input_shape if hasattr(model, "input_shape") else None,
                "output_shape": model.output_shape if hasattr(model, "output_shape") else None,
                "total_params": model.count_params() if hasattr(model, "count_params") else 0,
                "trainable_params": sum([tf.size(w).numpy() for w in model.trainable_weights]),
                "layers": len(model.layers) if hasattr(model, "layers") else 0,
                "size_mb": model_path.stat().st_size / (1024 * 1024),
            }

        elif extension == ".pb":
            # Load SavedModel or frozen graph
            try:
                model = tf.saved_model.load(str(model_path.parent))
                logger.debug(f"Successfully loaded TensorFlow SavedModel from {model_path.parent}")
                return {
                    "model": model,
                    "framework": "tensorflow",
                    "format": "saved_model",
                    "path": str(model_path),
                    "size_mb": sum(f.stat().st_size for f in model_path.parent.rglob("*") if f.is_file()) / (1024 * 1024),
                }
            except (OSError, ValueError, ImportError) as e:
                logger.error(f"Failed to load .pb file: {e}")
                raise ModelLoadError(
                    "Could not load .pb file as SavedModel. "
                    "Please ensure it's a valid TensorFlow SavedModel directory."
                ) from e

        else:
            raise ValueError(f"Unsupported TensorFlow format: {extension}")

    def _load_pytorch(self, model_path: Path) -> Dict[str, Any]:
        """Load PyTorch model"""
        try:
            import torch
        except ImportError as e:
            logger.error(f"PyTorch import failed: {e}")
            raise ImportError("PyTorch not installed. Install with: pip install torch") from e

        # Load checkpoint with security: weights_only=True prevents arbitrary code execution
        # This is critical to prevent RCE attacks via malicious pickle files
        try:
            checkpoint = torch.load(
                str(model_path),
                map_location="cpu",
                weights_only=True  # Security: Prevent arbitrary code execution
            )
            logger.debug(f"Successfully loaded PyTorch checkpoint from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load PyTorch model with weights_only=True: {e}")
            # Try without weights_only for backwards compatibility, but warn user
            logger.warning(
                "Attempting to load model without weights_only protection. "
                "Only load models from trusted sources!"
            )
            try:
                checkpoint = torch.load(str(model_path), map_location="cpu")
            except Exception as e2:
                logger.error(f"Failed to load PyTorch model: {e2}")
                raise ModelLoadError(
                    f"Could not load PyTorch model. The file may be corrupted or "
                    f"from an incompatible PyTorch version."
                ) from e2

        # Try to extract model
        if isinstance(checkpoint, dict):
            model = checkpoint.get("model", checkpoint.get("state_dict", checkpoint))
        else:
            model = checkpoint

        # Count parameters
        total_params = 0
        if isinstance(model, dict):
            total_params = sum(p.numel() for p in model.values() if isinstance(p, torch.Tensor))
        elif hasattr(model, "parameters"):
            total_params = sum(p.numel() for p in model.parameters())

        return {
            "model": model,
            "framework": "pytorch",
            "format": model_path.suffix[1:],
            "path": str(model_path),
            "total_params": total_params,
            "size_mb": model_path.stat().st_size / (1024 * 1024),
            "checkpoint": checkpoint if isinstance(checkpoint, dict) else None,
        }

    def _load_onnx(self, model_path: Path) -> Dict[str, Any]:
        """Load ONNX model"""
        try:
            import onnx
            import onnxruntime as ort
        except ImportError:
            raise ImportError("ONNX not installed. Install with: pip install onnx onnxruntime")

        # Load ONNX model
        model = onnx.load(str(model_path))

        # Validate model
        onnx.checker.check_model(model)

        # Create inference session
        session = ort.InferenceSession(str(model_path))

        # Get input/output info
        input_info = [(i.name, i.shape, i.type) for i in session.get_inputs()]
        output_info = [(o.name, o.shape, o.type) for o in session.get_outputs()]

        # Count parameters
        total_params = sum(
            np.prod(init.dims) if init.dims else 0
            for init in model.graph.initializer
        )

        return {
            "model": model,
            "session": session,
            "framework": "onnx",
            "format": "onnx",
            "path": str(model_path),
            "input_info": input_info,
            "output_info": output_info,
            "total_params": int(total_params),
            "size_mb": model_path.stat().st_size / (1024 * 1024),
            "opset_version": model.opset_import[0].version if model.opset_import else None,
        }

    def get_model_info(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed model information

        Args:
            model_data: Model data from load()

        Returns:
            Detailed model information
        """
        info = {
            "framework": model_data["framework"],
            "format": model_data["format"],
            "path": model_data["path"],
            "size_mb": round(model_data["size_mb"], 2),
            "size_str": f"{model_data['size_mb']:.2f} MB",
        }

        # Add framework-specific info
        if "total_params" in model_data:
            info["total_params"] = model_data["total_params"]
            info["params_str"] = f"{model_data['total_params']:,}"

        if "layers" in model_data:
            info["layers"] = model_data["layers"]

        if "input_shape" in model_data:
            info["input_shape"] = model_data["input_shape"]

        if "output_shape" in model_data:
            info["output_shape"] = model_data["output_shape"]

        return info

    def list_supported_formats(self) -> Dict[str, list]:
        """Return all supported formats"""
        return self.supported_formats
