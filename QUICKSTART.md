# 🚀 ModelBlaze Quick Start

Welcome to ModelBlaze! This guide will get you up and running in 5 minutes.

## ⚡ Installation

```bash
cd ModelBlaze
pip install -r requirements.txt
pip install -e .
```

## ✅ Verify Installation

```bash
modelblaze --version
```

You should see: `ModelBlaze, version 0.1.0`

## 🎯 Your First Optimization

### Option 1: Command Line (Easiest)

```bash
# Create a simple test model
python examples/create_simple_model.py

# Optimize it for mobile
modelblaze optimize examples/models/simple_cnn.onnx --target mobile --report html
```

### Option 2: Python API

```python
from src.optimizer import ModelBlaze

# Initialize
optimizer = ModelBlaze()

# Optimize
results = optimizer.quick_optimize(
    model_path="examples/models/simple_cnn.onnx",
    target_device="mobile"
)

print(f"✅ Size reduced by: {results['comparison']['improvements']['size_reduction_str']}")
```

## 📊 What You Get

After optimization, you'll see:

```
🎉 OPTIMIZATION COMPLETE!
============================================================
📉 Size: 150.00 MB → 18.00 MB (88.0% reduction)
⚡ Latency: 600.00 ms → 40.00 ms (15.0x faster)
💾 Memory: 512.00 MB → 64.00 MB (87.5% reduction)
⏱️  Time: 2.34s
✅ Output: optimized_model.onnx
============================================================
```

## 🎨 CLI Commands

```bash
# Get model info
modelblaze info model.onnx

# Benchmark a model
modelblaze benchmark model.onnx

# List supported devices
modelblaze devices

# Show examples
modelblaze examples
```

## 🔥 Real-World Example

Optimize ResNet50 for iPhone:

```bash
python examples/optimize_resnet.py
```

This will:
1. Download ResNet50 from Keras
2. Optimize it for mobile deployment
3. Generate a beautiful HTML report
4. Show before/after comparison

## 📖 Next Steps

- Read the [Full Documentation](docs/USAGE.md)
- Check out [More Examples](examples/)
- Join our [Community](https://github.com/anilyagiz/ModelBlaze/discussions)

## 🐛 Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt --upgrade
```

### "Command not found: modelblaze"
```bash
pip install -e .
```

### Out of memory
```bash
modelblaze optimize model.onnx --no-benchmark
```

## 💬 Get Help

- 📚 [Documentation](docs/)
- 🐛 [Issues](https://github.com/anilyagiz/ModelBlaze/issues)
- 💬 [Discussions](https://github.com/anilyagiz/ModelBlaze/discussions)

---

**Happy Optimizing! 🔥**
