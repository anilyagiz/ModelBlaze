"""
Create Simple Test Models for ModelBlaze
This script creates simple models for testing optimization
"""

import os
import numpy as np


def create_tensorflow_model():
    """Create a simple TensorFlow model"""
    try:
        import tensorflow as tf

        print("Creating TensorFlow model...")

        # Create a simple CNN model
        model = tf.keras.Sequential([
            tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3)),
            tf.keras.layers.MaxPooling2D((2, 2)),
            tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
            tf.keras.layers.MaxPooling2D((2, 2)),
            tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(10, activation='softmax')
        ])

        # Compile model
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        # Save model
        os.makedirs("examples/models", exist_ok=True)
        model.save("examples/models/simple_cnn.h5")

        print(f"✓ TensorFlow model saved: examples/models/simple_cnn.h5")
        print(f"  Size: {os.path.getsize('examples/models/simple_cnn.h5') / (1024*1024):.2f} MB")
        print(f"  Parameters: {model.count_params():,}")

        return model

    except ImportError:
        print("⚠ TensorFlow not installed, skipping TensorFlow model creation")
        return None


def create_pytorch_model():
    """Create a simple PyTorch model"""
    try:
        import torch
        import torch.nn as nn

        print("\nCreating PyTorch model...")

        # Create a simple CNN model
        class SimpleCNN(nn.Module):
            def __init__(self):
                super(SimpleCNN, self).__init__()
                self.conv1 = nn.Conv2d(3, 32, kernel_size=3)
                self.pool = nn.MaxPool2d(2, 2)
                self.conv2 = nn.Conv2d(32, 64, kernel_size=3)
                self.conv3 = nn.Conv2d(64, 64, kernel_size=3)
                self.fc1 = nn.Linear(64 * 26 * 26, 64)
                self.fc2 = nn.Linear(64, 10)
                self.relu = nn.ReLU()

            def forward(self, x):
                x = self.pool(self.relu(self.conv1(x)))
                x = self.pool(self.relu(self.conv2(x)))
                x = self.relu(self.conv3(x))
                x = x.view(-1, 64 * 26 * 26)
                x = self.relu(self.fc1(x))
                x = self.fc2(x)
                return x

        model = SimpleCNN()

        # Save model
        os.makedirs("examples/models", exist_ok=True)
        torch.save(model.state_dict(), "examples/models/simple_cnn.pth")

        print(f"✓ PyTorch model saved: examples/models/simple_cnn.pth")
        print(f"  Size: {os.path.getsize('examples/models/simple_cnn.pth') / (1024*1024):.2f} MB")

        total_params = sum(p.numel() for p in model.parameters())
        print(f"  Parameters: {total_params:,}")

        return model

    except ImportError:
        print("⚠ PyTorch not installed, skipping PyTorch model creation")
        return None


def create_onnx_model_from_pytorch():
    """Create ONNX model from PyTorch"""
    try:
        import torch
        import torch.nn as nn

        print("\nCreating ONNX model from PyTorch...")

        # Create model
        class SimpleCNN(nn.Module):
            def __init__(self):
                super(SimpleCNN, self).__init__()
                self.conv1 = nn.Conv2d(3, 32, kernel_size=3)
                self.pool = nn.MaxPool2d(2, 2)
                self.conv2 = nn.Conv2d(32, 64, kernel_size=3)
                self.conv3 = nn.Conv2d(64, 64, kernel_size=3)
                self.fc1 = nn.Linear(64 * 26 * 26, 64)
                self.fc2 = nn.Linear(64, 10)
                self.relu = nn.ReLU()

            def forward(self, x):
                x = self.pool(self.relu(self.conv1(x)))
                x = self.pool(self.relu(self.conv2(x)))
                x = self.relu(self.conv3(x))
                x = x.view(-1, 64 * 26 * 26)
                x = self.relu(self.fc1(x))
                x = self.fc2(x)
                return x

        model = SimpleCNN()
        model.eval()

        # Create dummy input
        dummy_input = torch.randn(1, 3, 224, 224)

        # Export to ONNX
        os.makedirs("examples/models", exist_ok=True)
        torch.onnx.export(
            model,
            dummy_input,
            "examples/models/simple_cnn.onnx",
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )

        print(f"✓ ONNX model saved: examples/models/simple_cnn.onnx")
        print(f"  Size: {os.path.getsize('examples/models/simple_cnn.onnx') / (1024*1024):.2f} MB")

    except ImportError:
        print("⚠ PyTorch/ONNX not installed, skipping ONNX model creation")


def main():
    print("="*60)
    print("Creating Test Models for ModelBlaze")
    print("="*60)

    # Create models
    create_tensorflow_model()
    create_pytorch_model()
    create_onnx_model_from_pytorch()

    print("\n" + "="*60)
    print("✅ Model creation complete!")
    print("="*60)
    print("\nYou can now optimize these models using:")
    print("  modelblaze optimize examples/models/simple_cnn.h5 --target mobile")
    print("  modelblaze optimize examples/models/simple_cnn.pth --target mobile")
    print("  modelblaze optimize examples/models/simple_cnn.onnx --target mobile")


if __name__ == "__main__":
    main()
