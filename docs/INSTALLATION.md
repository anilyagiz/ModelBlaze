# Installation Guide

## Requirements

- Python 3.8 or higher
- pip package manager

## Basic Installation

### From Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/anilyagiz/ModelBlaze.git
cd ModelBlaze

# Install dependencies
pip install -r requirements.txt

# Install ModelBlaze in development mode
pip install -e .
```

### Using pip (Coming Soon)

```bash
pip install modelblaze
```

## Framework-Specific Installation

### For TensorFlow Models

```bash
pip install tensorflow>=2.13.0
pip install tensorflow-model-optimization>=0.7.5
```

### For PyTorch Models

```bash
pip install torch>=2.0.0
```

### For ONNX Models

```bash
pip install onnx>=1.14.0
pip install onnxruntime>=1.15.0
```

### Full Installation (All Frameworks)

```bash
pip install -r requirements.txt
```

## Verification

Verify the installation:

```bash
modelblaze --version
```

You should see:
```
ModelBlaze, version 0.1.0
```

## Troubleshooting

### Import Errors

If you encounter import errors, ensure all dependencies are installed:

```bash
pip install -r requirements.txt --upgrade
```

### Permission Errors

On Linux/Mac, you may need to use `pip install --user`:

```bash
pip install --user -e .
```

### Virtual Environment (Recommended)

We recommend using a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install ModelBlaze
pip install -r requirements.txt
pip install -e .
```

## Platform-Specific Notes

### macOS

```bash
# Install using Homebrew Python
brew install python@3.11
pip3.11 install -r requirements.txt
```

### Windows

```bash
# Use Windows Terminal or PowerShell
python -m pip install -r requirements.txt
python -m pip install -e .
```

### Linux

```bash
# Install Python development headers
sudo apt-get install python3-dev

# Install ModelBlaze
pip install -r requirements.txt
pip install -e .
```

## Next Steps

After installation, check out:
- [Quick Start Guide](../README.md#quick-start)
- [Examples](../examples/)
- [CLI Documentation](USAGE.md)
