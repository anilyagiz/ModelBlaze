"""
ModelBlaze Optimizer - Main optimization pipeline
Orchestrates model loading, optimization, and benchmarking
"""

import os
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import numpy as np

from src.model_loader import ModelLoader
from src.quantizer import Quantizer
from src.pruner import Pruner
from src.benchmarker import Benchmarker


class ModelBlaze:
    """
    Main ModelBlaze optimizer class
    """

    def __init__(self):
        self.loader = ModelLoader()
        self.quantizer = Quantizer()
        self.pruner = Pruner()
        self.benchmarker = Benchmarker()

        self.target_devices = {
            "mobile": {"optimization_level": "high", "target_size_mb": 50},
            "iphone": {"optimization_level": "high", "target_size_mb": 50, "format": "coreml"},
            "android": {"optimization_level": "high", "target_size_mb": 50, "format": "tflite"},
            "raspberry_pi": {"optimization_level": "medium", "target_size_mb": 100},
            "jetson": {"optimization_level": "medium", "target_size_mb": 200},
            "web": {"optimization_level": "high", "target_size_mb": 20, "format": "wasm"},
            "iot": {"optimization_level": "max", "target_size_mb": 10},
        }

    def optimize(
        self,
        model_path: str,
        output_path: Optional[str] = None,
        target_device: str = "mobile",
        optimization_level: str = "high",
        quantization_mode: str = "int8",
        pruning_sparsity: float = 0.3,
        test_input: Optional[np.ndarray] = None,
        benchmark: bool = True,
    ) -> Dict[str, Any]:
        """
        Optimize a model for edge deployment

        Args:
            model_path: Path to input model
            output_path: Path to save optimized model
            target_device: Target device ('mobile', 'iphone', 'android', 'raspberry_pi', 'jetson', 'web', 'iot')
            optimization_level: Optimization level ('low', 'medium', 'high', 'max')
            quantization_mode: Quantization mode ('int8', 'fp16', 'dynamic')
            pruning_sparsity: Pruning sparsity (0.0 to 1.0)
            test_input: Optional test input for benchmarking
            benchmark: Whether to benchmark the models

        Returns:
            Dictionary with optimization results
        """
        start_time = time.time()

        print(f"🔥 ModelBlaze - Optimizing {model_path}")
        print(f"   Target: {target_device} | Level: {optimization_level}")

        # Load device config
        device_config = self.target_devices.get(target_device, {})

        # Override optimization level if specified in device config
        if "optimization_level" in device_config:
            optimization_level = device_config["optimization_level"]

        # Step 1: Load model
        print("\n📦 Step 1/5: Loading model...")
        original_model_data = self.loader.load(model_path)
        model_info = self.loader.get_model_info(original_model_data)

        print(f"   ✓ Loaded {model_info['framework']} model")
        print(f"   ✓ Size: {model_info['size_str']}")
        if "total_params" in model_info:
            print(f"   ✓ Parameters: {model_info['params_str']}")

        # Step 2: Benchmark original model
        original_benchmark = None
        if benchmark and test_input is not None:
            print("\n⚡ Step 2/5: Benchmarking original model...")
            original_benchmark = self.benchmarker.benchmark(original_model_data, test_input)
            print(f"   ✓ Size: {original_benchmark['size_mb']:.2f} MB")
            if "mean_latency_ms" in original_benchmark:
                print(f"   ✓ Latency: {original_benchmark['mean_latency_ms']:.2f} ms")
        else:
            print("\n⚡ Step 2/5: Skipping benchmark (no test input)")

        # Step 3: Apply optimizations based on level
        print(f"\n🔧 Step 3/5: Applying optimizations (level: {optimization_level})...")

        optimized_model_data = original_model_data

        # Determine which optimizations to apply
        apply_quantization = optimization_level in ["medium", "high", "max"]
        apply_pruning = optimization_level in ["high", "max"]

        # Apply pruning first (if enabled)
        if apply_pruning and pruning_sparsity > 0:
            try:
                print(f"   → Pruning (sparsity: {pruning_sparsity})...")
                optimized_model_data = self.pruner.prune(
                    optimized_model_data,
                    sparsity=pruning_sparsity,
                    method="magnitude",
                )
                print(f"   ✓ Pruning complete")
            except Exception as e:
                print(f"   ⚠ Pruning failed: {str(e)}")
                print(f"   → Continuing without pruning...")

        # Apply quantization (if enabled)
        if apply_quantization:
            try:
                print(f"   → Quantizing ({quantization_mode})...")
                optimized_model_data = self.quantizer.quantize(
                    optimized_model_data,
                    mode=quantization_mode,
                    output_path=output_path,
                )
                print(f"   ✓ Quantization complete")
            except Exception as e:
                print(f"   ⚠ Quantization failed: {str(e)}")
                print(f"   → Continuing with unquantized model...")

        # Step 4: Save optimized model
        print("\n💾 Step 4/5: Saving optimized model...")
        if output_path is None:
            # Generate output path
            input_path = Path(model_path)
            output_path = str(input_path.parent / f"{input_path.stem}_optimized{input_path.suffix}")

        # Copy optimized model to output path if not already there
        if optimized_model_data["path"] != output_path:
            import shutil
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            shutil.copy(optimized_model_data["path"], output_path)
            optimized_model_data["path"] = output_path

        print(f"   ✓ Saved to: {output_path}")

        # Step 5: Benchmark optimized model
        optimized_benchmark = None
        comparison = None

        if benchmark and test_input is not None and original_benchmark is not None:
            print("\n📊 Step 5/5: Benchmarking optimized model...")
            optimized_benchmark = self.benchmarker.benchmark(optimized_model_data, test_input)
            print(f"   ✓ Size: {optimized_benchmark['size_mb']:.2f} MB")
            if "mean_latency_ms" in optimized_benchmark:
                print(f"   ✓ Latency: {optimized_benchmark['mean_latency_ms']:.2f} ms")

            # Compare results
            comparison = self.benchmarker.compare(original_benchmark, optimized_benchmark)
        else:
            print("\n📊 Step 5/5: Skipping benchmark (no test input)")

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Print summary
        print("\n" + "="*60)
        print("🎉 OPTIMIZATION COMPLETE!")
        print("="*60)

        if comparison and "improvements" in comparison:
            improvements = comparison["improvements"]

            if "size_reduction_pct" in improvements:
                print(f"📉 Size: {original_benchmark['size_mb']:.2f} MB → {optimized_benchmark['size_mb']:.2f} MB "
                      f"({improvements['size_reduction_str']} reduction)")

            if "latency_speedup" in improvements:
                print(f"⚡ Latency: {original_benchmark['mean_latency_ms']:.2f} ms → {optimized_benchmark['mean_latency_ms']:.2f} ms "
                      f"({improvements['latency_speedup_str']} faster)")

            if "memory_reduction_pct" in improvements:
                print(f"💾 Memory: {original_benchmark['peak_memory_mb']:.2f} MB → {optimized_benchmark['peak_memory_mb']:.2f} MB "
                      f"({improvements['memory_reduction_pct']:.1f}% reduction)")

        print(f"⏱️  Time: {elapsed_time:.2f}s")
        print(f"✅ Output: {output_path}")
        print("="*60)

        # Return results
        return {
            "success": True,
            "original_model": model_info,
            "optimized_model": {
                "path": output_path,
                "framework": optimized_model_data["framework"],
                "format": optimized_model_data["format"],
                "size_mb": optimized_model_data.get("size_mb", 0),
            },
            "original_benchmark": original_benchmark,
            "optimized_benchmark": optimized_benchmark,
            "comparison": comparison,
            "optimization_config": {
                "target_device": target_device,
                "optimization_level": optimization_level,
                "quantization_mode": quantization_mode if apply_quantization else "none",
                "pruning_sparsity": pruning_sparsity if apply_pruning else 0.0,
            },
            "elapsed_time": elapsed_time,
        }

    def quick_optimize(
        self,
        model_path: str,
        target_device: str = "mobile",
    ) -> Dict[str, Any]:
        """
        Quick optimization with default settings

        Args:
            model_path: Path to input model
            target_device: Target device

        Returns:
            Optimization results
        """
        # Generate dummy test input
        test_input = self._generate_dummy_input(model_path)

        return self.optimize(
            model_path=model_path,
            target_device=target_device,
            test_input=test_input,
        )

    def _generate_dummy_input(self, model_path: str) -> Optional[np.ndarray]:
        """Generate dummy input for testing"""
        try:
            model_data = self.loader.load(model_path)

            # Try to infer input shape
            if "input_shape" in model_data and model_data["input_shape"] is not None:
                input_shape = model_data["input_shape"]
                # Remove batch dimension if present
                if isinstance(input_shape, tuple) and input_shape[0] is None:
                    input_shape = (1,) + input_shape[1:]
                return np.random.randn(*input_shape).astype(np.float32)

            elif "input_details" in model_data:
                input_shape = model_data["input_details"][0]["shape"]
                return np.random.randn(*input_shape).astype(np.float32)

            elif "input_info" in model_data:
                input_shape = model_data["input_info"][0][1]
                # Replace dynamic dimensions with 1
                input_shape = tuple(1 if (isinstance(d, str) or d is None or d < 0) else d for d in input_shape)
                return np.random.randn(*input_shape).astype(np.float32)

        except Exception as e:
            print(f"Warning: Could not generate test input: {str(e)}")

        # Default input
        return np.random.randn(1, 224, 224, 3).astype(np.float32)

    def list_target_devices(self) -> List[str]:
        """List all supported target devices"""
        return list(self.target_devices.keys())

    def get_device_config(self, target_device: str) -> Dict[str, Any]:
        """Get configuration for a target device"""
        return self.target_devices.get(target_device, {})
