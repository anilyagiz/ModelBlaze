"""
Basic ModelBlaze Usage Example
"""

import numpy as np
from src.optimizer import ModelBlaze

def main():
    # Initialize ModelBlaze
    optimizer = ModelBlaze()

    # Example 1: Quick optimization with default settings
    print("="*60)
    print("Example 1: Quick Optimization")
    print("="*60)

    # Note: Replace with your actual model path
    # model_path = "path/to/your/model.onnx"

    # Uncomment to run:
    # results = optimizer.quick_optimize(
    #     model_path=model_path,
    #     target_device="mobile",
    # )

    # Example 2: Custom optimization
    print("\n" + "="*60)
    print("Example 2: Custom Optimization")
    print("="*60)

    # Uncomment to run:
    # test_input = np.random.randn(1, 224, 224, 3).astype(np.float32)
    #
    # results = optimizer.optimize(
    #     model_path=model_path,
    #     output_path="optimized_model.onnx",
    #     target_device="iphone",
    #     optimization_level="high",
    #     quantization_mode="int8",
    #     pruning_sparsity=0.3,
    #     test_input=test_input,
    #     benchmark=True,
    # )

    # Example 3: Generate report
    print("\n" + "="*60)
    print("Example 3: Generate Report")
    print("="*60)

    # Uncomment to run:
    # from src.report_generator import ReportGenerator
    #
    # report_gen = ReportGenerator()
    # report_gen.generate(
    #     results=results,
    #     output_path="optimization_report.html",
    #     format="html",
    # )

    # List supported devices
    print("\n" + "="*60)
    print("Supported Target Devices:")
    print("="*60)
    for device in optimizer.list_target_devices():
        print(f"  - {device}")

if __name__ == "__main__":
    main()
