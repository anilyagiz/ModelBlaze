"""
ModelBlaze CLI - Command Line Interface
"""

import click
import sys
from pathlib import Path
import numpy as np

from src.optimizer import ModelBlaze
from src.report_generator import ReportGenerator
from src.model_loader import ModelLoader


@click.group()
@click.version_option(version="0.1.0", prog_name="ModelBlaze")
def cli():
    """
    🔥 ModelBlaze - Deploy AI Models 10x Faster on Edge

    Optimize your TensorFlow, PyTorch, ONNX models for mobile, IoT, and edge devices.
    90% smaller, 5-10x faster, minimal accuracy loss.
    """
    pass


@cli.command()
@click.argument("model_path", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output path for optimized model"
)
@click.option(
    "--target", "-t",
    type=click.Choice(["mobile", "iphone", "android", "raspberry_pi", "jetson", "web", "iot"]),
    default="mobile",
    help="Target device (default: mobile)"
)
@click.option(
    "--level", "-l",
    type=click.Choice(["low", "medium", "high", "max"]),
    default="high",
    help="Optimization level (default: high)"
)
@click.option(
    "--quantization", "-q",
    type=click.Choice(["int8", "fp16", "dynamic", "none"]),
    default="int8",
    help="Quantization mode (default: int8)"
)
@click.option(
    "--pruning", "-p",
    type=float,
    default=0.3,
    help="Pruning sparsity 0.0-1.0 (default: 0.3)"
)
@click.option(
    "--report", "-r",
    type=click.Choice(["text", "html", "json", "markdown"]),
    default="text",
    help="Report format (default: text)"
)
@click.option(
    "--report-path",
    type=click.Path(),
    help="Path to save report file"
)
@click.option(
    "--no-benchmark",
    is_flag=True,
    help="Skip benchmarking"
)
def optimize(model_path, output, target, level, quantization, pruning, report, report_path, no_benchmark):
    """
    Optimize a model for edge deployment

    Example:
        modelblaze optimize model.onnx --target iphone --level high
    """
    try:
        # Initialize optimizer
        optimizer = ModelBlaze()

        # Generate test input
        test_input = None
        if not no_benchmark:
            click.echo("📊 Generating test input for benchmarking...")
            test_input = optimizer._generate_dummy_input(model_path)

        # Run optimization
        results = optimizer.optimize(
            model_path=model_path,
            output_path=output,
            target_device=target,
            optimization_level=level,
            quantization_mode=quantization if quantization != "none" else "int8",
            pruning_sparsity=pruning,
            test_input=test_input,
            benchmark=not no_benchmark,
        )

        # Generate report
        if report != "text" or report_path:
            click.echo(f"\n📄 Generating {report} report...")
            generator = ReportGenerator()

            # Determine report path
            if report_path is None and report != "text":
                model_name = Path(model_path).stem
                report_ext = "html" if report == "html" else "md" if report == "markdown" else "json"
                report_path = f"modelblaze_report_{model_name}.{report_ext}"

            generator.generate(results, report_path, format=report)

        click.echo("\n✅ Optimization complete!")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("model_path", type=click.Path(exists=True))
def info(model_path):
    """
    Display model information

    Example:
        modelblaze info model.onnx
    """
    try:
        loader = ModelLoader()

        click.echo(f"📦 Loading model: {model_path}")
        model_data = loader.load(model_path)
        model_info = loader.get_model_info(model_data)

        click.echo("\n" + "="*60)
        click.echo("MODEL INFORMATION")
        click.echo("="*60)
        click.echo(f"Framework:  {model_info['framework']}")
        click.echo(f"Format:     {model_info['format']}")
        click.echo(f"Size:       {model_info['size_str']}")

        if "params_str" in model_info:
            click.echo(f"Parameters: {model_info['params_str']}")

        if "layers" in model_info:
            click.echo(f"Layers:     {model_info['layers']}")

        if "input_shape" in model_info:
            click.echo(f"Input:      {model_info['input_shape']}")

        if "output_shape" in model_info:
            click.echo(f"Output:     {model_info['output_shape']}")

        click.echo("="*60)

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("model_path", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output path for benchmarked model"
)
@click.option(
    "--runs", "-n",
    type=int,
    default=50,
    help="Number of benchmark runs (default: 50)"
)
def benchmark(model_path, output, runs):
    """
    Benchmark a model's performance

    Example:
        modelblaze benchmark model.onnx --runs 100
    """
    try:
        from src.benchmarker import Benchmarker

        loader = ModelLoader()
        benchmarker = Benchmarker()

        # Override benchmark runs
        benchmarker.num_benchmark_runs = runs

        click.echo(f"⚡ Benchmarking model: {model_path}")
        model_data = loader.load(model_path)

        # Generate test input
        optimizer = ModelBlaze()
        test_input = optimizer._generate_dummy_input(model_path)

        # Run benchmark
        results = benchmarker.benchmark(model_data, test_input)

        click.echo("\n" + "="*60)
        click.echo("BENCHMARK RESULTS")
        click.echo("="*60)
        click.echo(f"Size:           {results['size_mb']:.2f} MB")

        if "mean_latency_ms" in results:
            click.echo(f"Mean Latency:   {results['mean_latency_ms']:.2f} ms")
            click.echo(f"Median Latency: {results['median_latency_ms']:.2f} ms")
            click.echo(f"Min Latency:    {results['min_latency_ms']:.2f} ms")
            click.echo(f"Max Latency:    {results['max_latency_ms']:.2f} ms")
            click.echo(f"P95 Latency:    {results['p95_latency_ms']:.2f} ms")
            click.echo(f"P99 Latency:    {results['p99_latency_ms']:.2f} ms")

        if "peak_memory_mb" in results:
            click.echo(f"Peak Memory:    {results['peak_memory_mb']:.2f} MB")
            click.echo(f"Memory Increase: {results.get('memory_increase_mb', 0):.2f} MB")

        if "battery_impact" in results:
            click.echo(f"Battery Impact: {results['battery_impact']}")

        click.echo("="*60)

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def devices():
    """
    List supported target devices

    Example:
        modelblaze devices
    """
    optimizer = ModelBlaze()
    devices_list = optimizer.list_target_devices()

    click.echo("\n" + "="*60)
    click.echo("SUPPORTED TARGET DEVICES")
    click.echo("="*60)

    for device in devices_list:
        config = optimizer.get_device_config(device)
        click.echo(f"  {device:15} - {config.get('optimization_level', 'default')} optimization")

    click.echo("="*60)
    click.echo("\nUsage: modelblaze optimize model.onnx --target <device>")


@cli.command()
def examples():
    """
    Show usage examples
    """
    examples_text = """
🔥 ModelBlaze Usage Examples

1. Basic optimization for mobile:
   $ modelblaze optimize model.onnx --target mobile

2. Optimize for iPhone with CoreML:
   $ modelblaze optimize model.h5 --target iphone --level high

3. Optimize for Android with custom output:
   $ modelblaze optimize model.pth --target android -o optimized.tflite

4. Maximum optimization for IoT:
   $ modelblaze optimize model.onnx --target iot --level max

5. Custom quantization and pruning:
   $ modelblaze optimize model.h5 --quantization fp16 --pruning 0.5

6. Generate HTML report:
   $ modelblaze optimize model.onnx --report html --report-path report.html

7. Get model information:
   $ modelblaze info model.onnx

8. Benchmark a model:
   $ modelblaze benchmark model.onnx --runs 100

9. List supported devices:
   $ modelblaze devices

For more information, visit: https://github.com/anilyagiz/ModelBlaze
"""
    click.echo(examples_text)


if __name__ == "__main__":
    cli()
