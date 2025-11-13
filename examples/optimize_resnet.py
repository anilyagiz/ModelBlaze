"""
Example: Optimize ResNet50 for Mobile Deployment
"""

import numpy as np
from src.optimizer import ModelBlaze
from src.report_generator import ReportGenerator


def optimize_resnet():
    """
    Download and optimize ResNet50 model
    """
    print("="*60)
    print("ResNet50 Optimization Example")
    print("="*60)

    try:
        import tensorflow as tf

        # Download ResNet50
        print("\n📦 Downloading ResNet50...")
        model = tf.keras.applications.ResNet50(
            weights='imagenet',
            input_shape=(224, 224, 3)
        )

        # Save model
        model_path = "examples/models/resnet50.h5"
        model.save(model_path)
        print(f"✓ Model saved: {model_path}")

        # Initialize optimizer
        optimizer = ModelBlaze()

        # Create test input
        test_input = np.random.randn(1, 224, 224, 3).astype(np.float32)

        # Optimize for mobile
        print("\n🔥 Optimizing for mobile deployment...")
        results = optimizer.optimize(
            model_path=model_path,
            output_path="examples/models/resnet50_optimized.tflite",
            target_device="mobile",
            optimization_level="high",
            quantization_mode="int8",
            pruning_sparsity=0.3,
            test_input=test_input,
            benchmark=True,
        )

        # Generate HTML report
        print("\n📄 Generating report...")
        report_gen = ReportGenerator()
        report_gen.generate(
            results=results,
            output_path="examples/resnet50_optimization_report.html",
            format="html",
        )

        print("\n✅ Optimization complete!")
        print(f"   Optimized model: examples/models/resnet50_optimized.tflite")
        print(f"   Report: examples/resnet50_optimization_report.html")

    except ImportError:
        print("⚠ TensorFlow not installed. Install with: pip install tensorflow")
        print("\nAlternatively, you can optimize any existing model:")
        print("  modelblaze optimize your_model.h5 --target mobile")


if __name__ == "__main__":
    optimize_resnet()
