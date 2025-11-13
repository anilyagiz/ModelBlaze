"""
Benchmarker - Measure model performance metrics
Metrics: Size, latency, memory, accuracy, battery impact
"""

import os
import time
import gc
from typing import Dict, Any, Optional, List
import numpy as np
import psutil


class Benchmarker:
    """
    Universal benchmarker for neural network models
    """

    def __init__(self):
        self.num_warmup_runs = 5
        self.num_benchmark_runs = 50

    def benchmark(
        self,
        model_data: Dict[str, Any],
        test_input: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Run comprehensive benchmark on a model

        Args:
            model_data: Model data from ModelLoader
            test_input: Optional test input for inference benchmarking

        Returns:
            Dictionary with benchmark results
        """
        results = {}

        # Measure size
        results["size_mb"] = self.measure_size(model_data)

        # Measure latency and memory if test input provided
        if test_input is not None:
            latency_results = self.measure_latency(model_data, test_input)
            results.update(latency_results)

            memory_results = self.measure_memory(model_data, test_input)
            results.update(memory_results)

            # Estimate battery impact
            results["battery_impact"] = self.estimate_battery_impact(
                latency_results["mean_latency_ms"],
                memory_results.get("peak_memory_mb", 0)
            )

        # Add model info
        results["framework"] = model_data["framework"]
        results["format"] = model_data["format"]

        return results

    def measure_size(self, model_data: Dict[str, Any]) -> float:
        """
        Measure model size in MB

        Args:
            model_data: Model data from ModelLoader

        Returns:
            Model size in MB
        """
        path = model_data.get("path")

        if path and os.path.exists(path):
            if os.path.isfile(path):
                size_bytes = os.path.getsize(path)
            else:
                # For directories (e.g., SavedModel)
                size_bytes = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(path)
                    for filename in filenames
                )

            return size_bytes / (1024 * 1024)

        return model_data.get("size_mb", 0.0)

    def measure_latency(
        self,
        model_data: Dict[str, Any],
        test_input: np.ndarray,
    ) -> Dict[str, float]:
        """
        Measure inference latency

        Args:
            model_data: Model data from ModelLoader
            test_input: Test input array

        Returns:
            Dictionary with latency statistics
        """
        framework = model_data["framework"]

        if framework == "tensorflow" or framework == "tensorflow_lite":
            latencies = self._measure_latency_tensorflow(model_data, test_input)
        elif framework == "pytorch":
            latencies = self._measure_latency_pytorch(model_data, test_input)
        elif framework == "onnx":
            latencies = self._measure_latency_onnx(model_data, test_input)
        else:
            return {"mean_latency_ms": 0.0, "std_latency_ms": 0.0}

        return {
            "mean_latency_ms": float(np.mean(latencies)),
            "median_latency_ms": float(np.median(latencies)),
            "std_latency_ms": float(np.std(latencies)),
            "min_latency_ms": float(np.min(latencies)),
            "max_latency_ms": float(np.max(latencies)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
            "p99_latency_ms": float(np.percentile(latencies, 99)),
        }

    def _measure_latency_tensorflow(
        self,
        model_data: Dict[str, Any],
        test_input: np.ndarray,
    ) -> List[float]:
        """Measure TensorFlow model latency"""
        import tensorflow as tf

        model = model_data["model"]
        latencies = []

        if model_data["format"] == "tflite":
            # TFLite interpreter
            interpreter = model
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()

            # Ensure input shape matches
            input_shape = input_details[0]['shape']
            if test_input.shape != tuple(input_shape):
                test_input = np.resize(test_input, input_shape)

            # Warmup
            for _ in range(self.num_warmup_runs):
                interpreter.set_tensor(input_details[0]['index'], test_input.astype(input_details[0]['dtype']))
                interpreter.invoke()

            # Benchmark
            for _ in range(self.num_benchmark_runs):
                start_time = time.time()
                interpreter.set_tensor(input_details[0]['index'], test_input.astype(input_details[0]['dtype']))
                interpreter.invoke()
                end_time = time.time()
                latencies.append((end_time - start_time) * 1000)  # Convert to ms

        else:
            # Keras model
            # Warmup
            for _ in range(self.num_warmup_runs):
                _ = model(test_input, training=False)

            # Benchmark
            for _ in range(self.num_benchmark_runs):
                start_time = time.time()
                _ = model(test_input, training=False)
                end_time = time.time()
                latencies.append((end_time - start_time) * 1000)

        return latencies

    def _measure_latency_pytorch(
        self,
        model_data: Dict[str, Any],
        test_input: np.ndarray,
    ) -> List[float]:
        """Measure PyTorch model latency"""
        import torch

        model = model_data["model"]
        latencies = []

        # Convert to tensor
        input_tensor = torch.from_numpy(test_input).float()

        if not hasattr(model, "eval"):
            # State dict, can't benchmark
            return [0.0] * self.num_benchmark_runs

        model.eval()

        with torch.no_grad():
            # Warmup
            for _ in range(self.num_warmup_runs):
                try:
                    _ = model(input_tensor)
                except:
                    # Skip if model can't process input
                    return [0.0] * self.num_benchmark_runs

            # Benchmark
            for _ in range(self.num_benchmark_runs):
                start_time = time.time()
                _ = model(input_tensor)
                end_time = time.time()
                latencies.append((end_time - start_time) * 1000)

        return latencies

    def _measure_latency_onnx(
        self,
        model_data: Dict[str, Any],
        test_input: np.ndarray,
    ) -> List[float]:
        """Measure ONNX model latency"""
        session = model_data.get("session")
        if session is None:
            return [0.0] * self.num_benchmark_runs

        input_name = session.get_inputs()[0].name
        latencies = []

        # Warmup
        for _ in range(self.num_warmup_runs):
            _ = session.run(None, {input_name: test_input})

        # Benchmark
        for _ in range(self.num_benchmark_runs):
            start_time = time.time()
            _ = session.run(None, {input_name: test_input})
            end_time = time.time()
            latencies.append((end_time - start_time) * 1000)

        return latencies

    def measure_memory(
        self,
        model_data: Dict[str, Any],
        test_input: np.ndarray,
    ) -> Dict[str, float]:
        """
        Measure memory usage during inference

        Args:
            model_data: Model data from ModelLoader
            test_input: Test input array

        Returns:
            Dictionary with memory statistics
        """
        # Get current process
        process = psutil.Process()

        # Force garbage collection
        gc.collect()

        # Measure baseline memory
        baseline_memory = process.memory_info().rss / (1024 * 1024)  # MB

        # Run inference and measure peak memory
        framework = model_data["framework"]

        try:
            if framework == "tensorflow" or framework == "tensorflow_lite":
                self._run_inference_tensorflow(model_data, test_input)
            elif framework == "pytorch":
                self._run_inference_pytorch(model_data, test_input)
            elif framework == "onnx":
                self._run_inference_onnx(model_data, test_input)

            # Measure peak memory
            peak_memory = process.memory_info().rss / (1024 * 1024)  # MB

        except Exception as e:
            print(f"Warning: Memory measurement failed: {str(e)}")
            peak_memory = baseline_memory

        return {
            "baseline_memory_mb": baseline_memory,
            "peak_memory_mb": peak_memory,
            "memory_increase_mb": max(0, peak_memory - baseline_memory),
        }

    def _run_inference_tensorflow(self, model_data: Dict[str, Any], test_input: np.ndarray):
        """Run TensorFlow inference"""
        import tensorflow as tf

        model = model_data["model"]

        if model_data["format"] == "tflite":
            interpreter = model
            input_details = interpreter.get_input_details()
            input_shape = input_details[0]['shape']
            if test_input.shape != tuple(input_shape):
                test_input = np.resize(test_input, input_shape)
            interpreter.set_tensor(input_details[0]['index'], test_input.astype(input_details[0]['dtype']))
            interpreter.invoke()
        else:
            _ = model(test_input, training=False)

    def _run_inference_pytorch(self, model_data: Dict[str, Any], test_input: np.ndarray):
        """Run PyTorch inference"""
        import torch

        model = model_data["model"]
        if not hasattr(model, "eval"):
            return

        input_tensor = torch.from_numpy(test_input).float()
        model.eval()
        with torch.no_grad():
            _ = model(input_tensor)

    def _run_inference_onnx(self, model_data: Dict[str, Any], test_input: np.ndarray):
        """Run ONNX inference"""
        session = model_data.get("session")
        if session is None:
            return

        input_name = session.get_inputs()[0].name
        _ = session.run(None, {input_name: test_input})

    def estimate_battery_impact(
        self,
        latency_ms: float,
        memory_mb: float,
    ) -> str:
        """
        Estimate battery impact based on latency and memory

        Args:
            latency_ms: Inference latency in milliseconds
            memory_mb: Memory usage in MB

        Returns:
            Battery impact estimate ('low', 'medium', 'high')
        """
        # Simple heuristic
        impact_score = (latency_ms / 100) + (memory_mb / 100)

        if impact_score < 2:
            return "low"
        elif impact_score < 5:
            return "medium"
        else:
            return "high"

    def compare(
        self,
        original_results: Dict[str, Any],
        optimized_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compare original and optimized model benchmarks

        Args:
            original_results: Benchmark results from original model
            optimized_results: Benchmark results from optimized model

        Returns:
            Comparison dictionary with improvements
        """
        comparison = {
            "original": original_results,
            "optimized": optimized_results,
            "improvements": {},
        }

        # Size reduction
        original_size = original_results.get("size_mb", 0)
        optimized_size = optimized_results.get("size_mb", 0)

        if original_size > 0:
            size_reduction_pct = ((original_size - optimized_size) / original_size) * 100
            comparison["improvements"]["size_reduction_mb"] = original_size - optimized_size
            comparison["improvements"]["size_reduction_pct"] = size_reduction_pct
            comparison["improvements"]["size_reduction_str"] = f"{size_reduction_pct:.1f}%"

        # Latency improvement
        original_latency = original_results.get("mean_latency_ms", 0)
        optimized_latency = optimized_results.get("mean_latency_ms", 0)

        if original_latency > 0 and optimized_latency > 0:
            latency_speedup = original_latency / optimized_latency
            latency_reduction_pct = ((original_latency - optimized_latency) / original_latency) * 100

            comparison["improvements"]["latency_speedup"] = latency_speedup
            comparison["improvements"]["latency_speedup_str"] = f"{latency_speedup:.1f}x"
            comparison["improvements"]["latency_reduction_ms"] = original_latency - optimized_latency
            comparison["improvements"]["latency_reduction_pct"] = latency_reduction_pct

        # Memory reduction
        original_memory = original_results.get("peak_memory_mb", 0)
        optimized_memory = optimized_results.get("peak_memory_mb", 0)

        if original_memory > 0:
            memory_reduction_pct = ((original_memory - optimized_memory) / original_memory) * 100
            comparison["improvements"]["memory_reduction_mb"] = original_memory - optimized_memory
            comparison["improvements"]["memory_reduction_pct"] = memory_reduction_pct

        return comparison
