# Usage Guide

## Command Line Interface (CLI)

### Basic Usage

```bash
modelblaze optimize <model_path> --target <device>
```

### Common Commands

#### 1. Optimize a Model

```bash
# Basic optimization for mobile
modelblaze optimize model.onnx --target mobile

# Optimize for iPhone
modelblaze optimize model.h5 --target iphone --level high

# Custom optimization settings
modelblaze optimize model.pth \
  --target android \
  --level max \
  --quantization int8 \
  --pruning 0.5 \
  --output optimized_model.tflite
```

#### 2. Model Information

```bash
# Get model details
modelblaze info model.onnx
```

Output:
```
MODEL INFORMATION
============================================================
Framework:  onnx
Format:     onnx
Size:       150.00 MB
Parameters: 25,557,032
```

#### 3. Benchmark a Model

```bash
# Benchmark performance
modelblaze benchmark model.onnx --runs 100
```

#### 4. List Target Devices

```bash
# Show supported devices
modelblaze devices
```

#### 5. View Examples

```bash
# Show usage examples
modelblaze examples
```

### Command Options

#### `optimize` Command

```
Usage: modelblaze optimize [OPTIONS] MODEL_PATH

Options:
  -o, --output PATH            Output path for optimized model
  -t, --target DEVICE          Target device:
                                 - mobile (default)
                                 - iphone
                                 - android
                                 - raspberry_pi
                                 - jetson
                                 - web
                                 - iot
  -l, --level LEVEL           Optimization level:
                                 - low
                                 - medium
                                 - high (default)
                                 - max
  -q, --quantization MODE      Quantization mode:
                                 - int8 (default)
                                 - fp16
                                 - dynamic
                                 - none
  -p, --pruning FLOAT         Pruning sparsity (0.0-1.0, default: 0.3)
  -r, --report FORMAT         Report format:
                                 - text (default)
                                 - html
                                 - json
                                 - markdown
  --report-path PATH          Path to save report file
  --no-benchmark              Skip performance benchmarking
  --help                      Show this message and exit
```

## Python API

### Basic Usage

```python
from src.optimizer import ModelBlaze
import numpy as np

# Initialize
optimizer = ModelBlaze()

# Create test input
test_input = np.random.randn(1, 224, 224, 3).astype(np.float32)

# Optimize
results = optimizer.optimize(
    model_path="model.onnx",
    output_path="optimized_model.onnx",
    target_device="mobile",
    test_input=test_input,
)

# Access results
print(f"Original size: {results['original_benchmark']['size_mb']:.2f} MB")
print(f"Optimized size: {results['optimized_benchmark']['size_mb']:.2f} MB")
print(f"Size reduction: {results['comparison']['improvements']['size_reduction_str']}")
```

### Advanced Usage

```python
from src.optimizer import ModelBlaze
from src.report_generator import ReportGenerator
import numpy as np

# Initialize
optimizer = ModelBlaze()

# Custom optimization
results = optimizer.optimize(
    model_path="model.h5",
    output_path="optimized_model.tflite",
    target_device="android",
    optimization_level="max",
    quantization_mode="int8",
    pruning_sparsity=0.5,
    test_input=test_input,
    benchmark=True,
)

# Generate HTML report
report_gen = ReportGenerator()
report_gen.generate(
    results=results,
    output_path="optimization_report.html",
    format="html",
)
```

### Individual Components

#### Model Loader

```python
from src.model_loader import ModelLoader

loader = ModelLoader()

# Load model
model_data = loader.load("model.onnx")

# Get info
info = loader.get_model_info(model_data)
print(info)
```

#### Quantizer

```python
from src.model_loader import ModelLoader
from src.quantizer import Quantizer

loader = ModelLoader()
quantizer = Quantizer()

# Load model
model_data = loader.load("model.h5")

# Quantize
quantized = quantizer.quantize(
    model_data,
    mode="int8",
    output_path="quantized_model.tflite",
)
```

#### Pruner

```python
from src.model_loader import ModelLoader
from src.pruner import Pruner

loader = ModelLoader()
pruner = Pruner()

# Load model
model_data = loader.load("model.pth")

# Prune
pruned = pruner.prune(
    model_data,
    sparsity=0.5,
    method="magnitude",
)
```

#### Benchmarker

```python
from src.model_loader import ModelLoader
from src.benchmarker import Benchmarker
import numpy as np

loader = ModelLoader()
benchmarker = Benchmarker()

# Load model
model_data = loader.load("model.onnx")

# Create test input
test_input = np.random.randn(1, 224, 224, 3).astype(np.float32)

# Benchmark
results = benchmarker.benchmark(model_data, test_input)
print(f"Latency: {results['mean_latency_ms']:.2f} ms")
print(f"Memory: {results['peak_memory_mb']:.2f} MB")
```

## Examples

### Optimize ResNet50

```python
import tensorflow as tf
from src.optimizer import ModelBlaze

# Download ResNet50
model = tf.keras.applications.ResNet50(weights='imagenet')
model.save("resnet50.h5")

# Optimize
optimizer = ModelBlaze()
results = optimizer.quick_optimize(
    model_path="resnet50.h5",
    target_device="mobile",
)
```

### Optimize Custom PyTorch Model

```python
import torch
from src.optimizer import ModelBlaze

# Your model
model = YourCustomModel()
torch.save(model.state_dict(), "custom_model.pth")

# Optimize
optimizer = ModelBlaze()
results = optimizer.optimize(
    model_path="custom_model.pth",
    target_device="raspberry_pi",
    optimization_level="high",
)
```

### Batch Optimization

```python
from src.optimizer import ModelBlaze
import glob

optimizer = ModelBlaze()

# Optimize all models in a directory
for model_path in glob.glob("models/*.onnx"):
    print(f"Optimizing {model_path}...")
    results = optimizer.quick_optimize(
        model_path=model_path,
        target_device="mobile",
    )
```

## Tips and Best Practices

1. **Start with Default Settings**: Use default optimization settings first, then adjust based on results

2. **Benchmark Before and After**: Always benchmark to measure improvements

3. **Choose the Right Target Device**: Select the device that matches your deployment target

4. **Balance Size vs Accuracy**: Use lower optimization levels if accuracy is critical

5. **Test on Real Devices**: Benchmark on actual target hardware when possible

6. **Generate Reports**: Use HTML reports to visualize optimization results

7. **Iterate**: Try different settings and compare results

## Troubleshooting

### Model Loading Errors

If model loading fails:
- Ensure the model file is not corrupted
- Check that you have the required framework installed
- Verify the model format is supported

### Quantization Errors

If quantization fails:
- Some models may not support all quantization modes
- Try different quantization modes (fp16 instead of int8)
- Check that calibration data is appropriate

### Memory Errors

If you run out of memory:
- Close other applications
- Use a smaller model for testing
- Try optimization in smaller steps

### Slow Optimization

If optimization is slow:
- Disable benchmarking with `--no-benchmark`
- Reduce the number of benchmark runs
- Use a faster machine or GPU

## Next Steps

- Check out [Examples](../examples/)
- Read the [API Documentation](API.md)
- Join our [Community](https://github.com/anilyagiz/ModelBlaze/discussions)
