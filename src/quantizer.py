"""
Quantizer - Quantize models to reduce size and improve performance
Supports: INT8, FP16, dynamic quantization
"""

import os
import tempfile
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import numpy as np


class Quantizer:
    """
    Universal quantizer for TensorFlow, PyTorch, and ONNX models
    """

    def __init__(self):
        self.quantization_modes = ["int8", "fp16", "dynamic"]

    def quantize(
        self,
        model_data: Dict[str, Any],
        mode: str = "int8",
        calibration_data: Optional[np.ndarray] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Quantize a model

        Args:
            model_data: Model data from ModelLoader
            mode: Quantization mode ('int8', 'fp16', 'dynamic')
            calibration_data: Optional calibration data for INT8 quantization
            output_path: Output path for quantized model

        Returns:
            Dictionary with quantized model and metadata
        """
        if mode not in self.quantization_modes:
            raise ValueError(f"Unsupported quantization mode: {mode}. Supported: {self.quantization_modes}")

        framework = model_data["framework"]

        if framework == "tensorflow" or framework == "tensorflow_lite":
            return self._quantize_tensorflow(model_data, mode, calibration_data, output_path)
        elif framework == "pytorch":
            return self._quantize_pytorch(model_data, mode, calibration_data, output_path)
        elif framework == "onnx":
            return self._quantize_onnx(model_data, mode, calibration_data, output_path)
        else:
            raise ValueError(f"Unsupported framework for quantization: {framework}")

    def _quantize_tensorflow(
        self,
        model_data: Dict[str, Any],
        mode: str,
        calibration_data: Optional[np.ndarray],
        output_path: Optional[str],
    ) -> Dict[str, Any]:
        """Quantize TensorFlow model"""
        try:
            import tensorflow as tf
        except ImportError:
            raise ImportError("TensorFlow not installed")

        model = model_data["model"]

        # Create output path
        if output_path is None:
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, f"quantized_{mode}.tflite")

        # Convert to TFLite with quantization
        if model_data["format"] == "keras":
            converter = tf.lite.TFLiteConverter.from_keras_model(model)
        elif model_data["format"] == "saved_model":
            converter = tf.lite.TFLiteConverter.from_saved_model(model_data["path"])
        elif model_data["format"] == "tflite":
            # Already TFLite, re-quantize
            converter = tf.lite.TFLiteConverter.from_saved_model(model_data["path"])
        else:
            raise ValueError(f"Cannot convert {model_data['format']} to TFLite")

        # Set quantization options
        if mode == "int8":
            converter.optimizations = [tf.lite.Optimize.DEFAULT]

            if calibration_data is not None:
                # Full integer quantization with calibration
                def representative_dataset():
                    for data in calibration_data:
                        yield [np.array([data], dtype=np.float32)]

                converter.representative_dataset = representative_dataset
                converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
                converter.inference_input_type = tf.int8
                converter.inference_output_type = tf.int8
            else:
                # Dynamic range quantization
                pass

        elif mode == "fp16":
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.float16]

        elif mode == "dynamic":
            converter.optimizations = [tf.lite.Optimize.DEFAULT]

        # Convert
        try:
            quantized_model = converter.convert()

            # Save to file
            with open(output_path, "wb") as f:
                f.write(quantized_model)

            # Load quantized model to get info
            interpreter = tf.lite.Interpreter(model_path=output_path)
            interpreter.allocate_tensors()

            return {
                "model": interpreter,
                "framework": "tensorflow_lite",
                "format": "tflite",
                "path": output_path,
                "quantization_mode": mode,
                "size_mb": os.path.getsize(output_path) / (1024 * 1024),
                "input_details": interpreter.get_input_details(),
                "output_details": interpreter.get_output_details(),
            }

        except Exception as e:
            raise RuntimeError(f"TensorFlow quantization failed: {str(e)}")

    def _quantize_pytorch(
        self,
        model_data: Dict[str, Any],
        mode: str,
        calibration_data: Optional[np.ndarray],
        output_path: Optional[str],
    ) -> Dict[str, Any]:
        """Quantize PyTorch model"""
        try:
            import torch
            from torch.quantization import quantize_dynamic, quantize_qat, get_default_qconfig
        except ImportError:
            raise ImportError("PyTorch not installed")

        model = model_data["model"]

        # Ensure model is in eval mode
        if hasattr(model, "eval"):
            model.eval()

        if output_path is None:
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, f"quantized_{mode}.pth")

        try:
            if mode == "int8" or mode == "dynamic":
                # Dynamic quantization
                if hasattr(model, "modules"):
                    quantized_model = quantize_dynamic(
                        model,
                        {torch.nn.Linear, torch.nn.Conv2d, torch.nn.LSTM},
                        dtype=torch.qint8,
                    )
                else:
                    # If model is state_dict, we can't quantize it directly
                    quantized_model = model
                    print("Warning: Cannot quantize PyTorch state_dict directly. Need model architecture.")

            elif mode == "fp16":
                # Half precision
                if hasattr(model, "half"):
                    quantized_model = model.half()
                else:
                    quantized_model = model

            else:
                raise ValueError(f"Unsupported PyTorch quantization mode: {mode}")

            # Save quantized model
            if hasattr(quantized_model, "state_dict"):
                torch.save(quantized_model.state_dict(), output_path)
            else:
                torch.save(quantized_model, output_path)

            return {
                "model": quantized_model,
                "framework": "pytorch",
                "format": "pth",
                "path": output_path,
                "quantization_mode": mode,
                "size_mb": os.path.getsize(output_path) / (1024 * 1024),
            }

        except Exception as e:
            raise RuntimeError(f"PyTorch quantization failed: {str(e)}")

    def _quantize_onnx(
        self,
        model_data: Dict[str, Any],
        mode: str,
        calibration_data: Optional[np.ndarray],
        output_path: Optional[str],
    ) -> Dict[str, Any]:
        """Quantize ONNX model"""
        try:
            import onnx
            from onnxruntime.quantization import quantize_dynamic, quantize_static, QuantType
        except ImportError:
            raise ImportError("ONNX quantization tools not installed")

        model_path = model_data["path"]

        if output_path is None:
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, f"quantized_{mode}.onnx")

        try:
            if mode == "int8" or mode == "dynamic":
                # Dynamic quantization
                quantize_dynamic(
                    model_path,
                    output_path,
                    weight_type=QuantType.QInt8,
                )

            elif mode == "fp16":
                # FP16 conversion
                from onnxconverter_common import float16
                model = onnx.load(model_path)
                model_fp16 = float16.convert_float_to_float16(model)
                onnx.save(model_fp16, output_path)

            else:
                raise ValueError(f"Unsupported ONNX quantization mode: {mode}")

            # Load quantized model
            quantized_model = onnx.load(output_path)

            return {
                "model": quantized_model,
                "framework": "onnx",
                "format": "onnx",
                "path": output_path,
                "quantization_mode": mode,
                "size_mb": os.path.getsize(output_path) / (1024 * 1024),
            }

        except Exception as e:
            raise RuntimeError(f"ONNX quantization failed: {str(e)}")

    def measure_accuracy_loss(
        self,
        original_model_data: Dict[str, Any],
        quantized_model_data: Dict[str, Any],
        test_data: np.ndarray,
        test_labels: np.ndarray,
    ) -> Dict[str, float]:
        """
        Measure accuracy loss after quantization

        Args:
            original_model_data: Original model data
            quantized_model_data: Quantized model data
            test_data: Test dataset
            test_labels: Test labels

        Returns:
            Dictionary with accuracy metrics
        """
        # This is a placeholder - actual implementation depends on task type
        # (classification, detection, segmentation, etc.)

        return {
            "original_accuracy": 0.0,
            "quantized_accuracy": 0.0,
            "accuracy_loss": 0.0,
            "accuracy_loss_pct": 0.0,
        }

    def get_quantization_info(self, quantized_model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about quantized model"""
        return {
            "framework": quantized_model_data["framework"],
            "format": quantized_model_data["format"],
            "quantization_mode": quantized_model_data.get("quantization_mode", "unknown"),
            "size_mb": round(quantized_model_data["size_mb"], 2),
        }
