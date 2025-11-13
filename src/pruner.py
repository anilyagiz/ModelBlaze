"""
Pruner - Prune model weights to reduce size and computation
Supports: Weight pruning, channel pruning, sensitivity-based pruning
"""

import os
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
import numpy as np


class Pruner:
    """
    Universal pruner for neural network models
    """

    def __init__(self):
        self.pruning_methods = ["magnitude", "structured", "sensitivity"]

    def prune(
        self,
        model_data: Dict[str, Any],
        sparsity: float = 0.5,
        method: str = "magnitude",
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Prune a model

        Args:
            model_data: Model data from ModelLoader
            sparsity: Target sparsity (0.0 to 1.0)
            method: Pruning method ('magnitude', 'structured', 'sensitivity')
            output_path: Output path for pruned model

        Returns:
            Dictionary with pruned model and metadata
        """
        if not 0.0 <= sparsity <= 1.0:
            raise ValueError(f"Sparsity must be between 0.0 and 1.0, got {sparsity}")

        if method not in self.pruning_methods:
            raise ValueError(f"Unsupported pruning method: {method}. Supported: {self.pruning_methods}")

        framework = model_data["framework"]

        if framework == "tensorflow" or framework == "tensorflow_lite":
            return self._prune_tensorflow(model_data, sparsity, method, output_path)
        elif framework == "pytorch":
            return self._prune_pytorch(model_data, sparsity, method, output_path)
        elif framework == "onnx":
            return self._prune_onnx(model_data, sparsity, method, output_path)
        else:
            raise ValueError(f"Unsupported framework for pruning: {framework}")

    def _prune_tensorflow(
        self,
        model_data: Dict[str, Any],
        sparsity: float,
        method: str,
        output_path: Optional[str],
    ) -> Dict[str, Any]:
        """Prune TensorFlow model"""
        try:
            import tensorflow as tf
            import tensorflow_model_optimization as tfmot
        except ImportError:
            raise ImportError("TensorFlow Model Optimization not installed. Install with: pip install tensorflow-model-optimization")

        model = model_data["model"]

        if model_data["format"] != "keras":
            raise ValueError("TensorFlow pruning currently only supports Keras models")

        if output_path is None:
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, "pruned_model.h5")

        try:
            # Define pruning parameters
            if method == "magnitude":
                pruning_params = {
                    'pruning_schedule': tfmot.sparsity.keras.ConstantSparsity(
                        target_sparsity=sparsity,
                        begin_step=0,
                    )
                }
            else:
                # Use default for other methods
                pruning_params = {
                    'pruning_schedule': tfmot.sparsity.keras.PolynomialDecay(
                        initial_sparsity=0.0,
                        final_sparsity=sparsity,
                        begin_step=0,
                        end_step=1000,
                    )
                }

            # Apply pruning
            pruned_model = tfmot.sparsity.keras.prune_low_magnitude(model, **pruning_params)

            # Compile model (required after pruning)
            pruned_model.compile(
                optimizer='adam',
                loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                metrics=['accuracy']
            )

            # Strip pruning wrappers for inference
            pruned_model = tfmot.sparsity.keras.strip_pruning(pruned_model)

            # Save pruned model
            pruned_model.save(output_path)

            return {
                "model": pruned_model,
                "framework": "tensorflow",
                "format": "keras",
                "path": output_path,
                "pruning_method": method,
                "sparsity": sparsity,
                "size_mb": os.path.getsize(output_path) / (1024 * 1024),
                "total_params": pruned_model.count_params(),
            }

        except Exception as e:
            raise RuntimeError(f"TensorFlow pruning failed: {str(e)}")

    def _prune_pytorch(
        self,
        model_data: Dict[str, Any],
        sparsity: float,
        method: str,
        output_path: Optional[str],
    ) -> Dict[str, Any]:
        """Prune PyTorch model"""
        try:
            import torch
            import torch.nn.utils.prune as prune
        except ImportError:
            raise ImportError("PyTorch not installed")

        model = model_data["model"]

        if output_path is None:
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, "pruned_model.pth")

        try:
            # Check if model has modules (is an nn.Module)
            if not hasattr(model, "modules"):
                print("Warning: Cannot prune PyTorch state_dict directly. Need model architecture.")
                # Just copy the model
                torch.save(model, output_path)
                return {
                    "model": model,
                    "framework": "pytorch",
                    "format": "pth",
                    "path": output_path,
                    "pruning_method": "none",
                    "sparsity": 0.0,
                    "size_mb": os.path.getsize(output_path) / (1024 * 1024),
                }

            # Apply pruning to all conv and linear layers
            parameters_to_prune = []
            for name, module in model.named_modules():
                if isinstance(module, (torch.nn.Conv2d, torch.nn.Linear)):
                    parameters_to_prune.append((module, "weight"))

            if method == "magnitude":
                # Global magnitude pruning
                prune.global_unstructured(
                    parameters_to_prune,
                    pruning_method=prune.L1Unstructured,
                    amount=sparsity,
                )
            elif method == "structured":
                # Structured pruning (per-channel)
                for module, param_name in parameters_to_prune:
                    prune.ln_structured(
                        module,
                        name=param_name,
                        amount=sparsity,
                        n=2,
                        dim=0,
                    )
            else:
                # Default to magnitude
                prune.global_unstructured(
                    parameters_to_prune,
                    pruning_method=prune.L1Unstructured,
                    amount=sparsity,
                )

            # Make pruning permanent
            for module, param_name in parameters_to_prune:
                prune.remove(module, param_name)

            # Save pruned model
            torch.save(model.state_dict(), output_path)

            # Count remaining parameters
            total_params = sum(p.numel() for p in model.parameters())
            nonzero_params = sum((p != 0).sum().item() for p in model.parameters())
            actual_sparsity = 1.0 - (nonzero_params / total_params) if total_params > 0 else 0.0

            return {
                "model": model,
                "framework": "pytorch",
                "format": "pth",
                "path": output_path,
                "pruning_method": method,
                "target_sparsity": sparsity,
                "actual_sparsity": actual_sparsity,
                "size_mb": os.path.getsize(output_path) / (1024 * 1024),
                "total_params": total_params,
                "nonzero_params": nonzero_params,
            }

        except Exception as e:
            raise RuntimeError(f"PyTorch pruning failed: {str(e)}")

    def _prune_onnx(
        self,
        model_data: Dict[str, Any],
        sparsity: float,
        method: str,
        output_path: Optional[str],
    ) -> Dict[str, Any]:
        """Prune ONNX model"""
        # ONNX pruning is more complex and typically done before converting to ONNX
        # For now, we'll return the model as-is with a warning

        if output_path is None:
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, "pruned_model.onnx")

        # Copy the model
        import shutil
        shutil.copy(model_data["path"], output_path)

        print("Warning: ONNX pruning not fully implemented. Returning original model.")
        print("Tip: Prune the model in PyTorch or TensorFlow before converting to ONNX.")

        return {
            "model": model_data["model"],
            "framework": "onnx",
            "format": "onnx",
            "path": output_path,
            "pruning_method": "none",
            "sparsity": 0.0,
            "size_mb": os.path.getsize(output_path) / (1024 * 1024),
        }

    def sensitivity_analysis(self, model_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Analyze layer sensitivity to pruning

        Args:
            model_data: Model data from ModelLoader

        Returns:
            Dictionary mapping layer names to sensitivity scores
        """
        framework = model_data["framework"]

        if framework == "tensorflow":
            return self._sensitivity_tensorflow(model_data)
        elif framework == "pytorch":
            return self._sensitivity_pytorch(model_data)
        else:
            return {}

    def _sensitivity_tensorflow(self, model_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze TensorFlow model layer sensitivity"""
        model = model_data["model"]

        if not hasattr(model, "layers"):
            return {}

        sensitivity = {}
        for layer in model.layers:
            if hasattr(layer, "weights") and len(layer.weights) > 0:
                weights = layer.weights[0].numpy()
                # Simple sensitivity: std deviation of weights
                sensitivity[layer.name] = float(np.std(weights))

        return sensitivity

    def _sensitivity_pytorch(self, model_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze PyTorch model layer sensitivity"""
        model = model_data["model"]

        if not hasattr(model, "named_parameters"):
            return {}

        sensitivity = {}
        for name, param in model.named_parameters():
            if "weight" in name:
                weights = param.detach().cpu().numpy()
                # Simple sensitivity: std deviation of weights
                sensitivity[name] = float(np.std(weights))

        return sensitivity

    def prune_channels(
        self,
        model_data: Dict[str, Any],
        pruning_ratio: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Prune entire channels from convolutional layers

        Args:
            model_data: Model data from ModelLoader
            pruning_ratio: Ratio of channels to prune (0.0 to 1.0)

        Returns:
            Dictionary with pruned model and metadata
        """
        # This is a placeholder for channel pruning
        # Full implementation requires careful handling of layer connections
        print("Warning: Channel pruning not fully implemented yet.")
        return model_data
