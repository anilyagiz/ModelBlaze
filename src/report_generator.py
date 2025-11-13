"""
Report Generator - Generate beautiful optimization reports
Formats: HTML, JSON, Text, Markdown
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class ReportGenerator:
    """
    Generate optimization reports in multiple formats
    """

    def __init__(self):
        self.supported_formats = ["html", "json", "text", "markdown"]

    def generate(
        self,
        results: Dict[str, Any],
        output_path: Optional[str] = None,
        format: str = "text",
    ) -> str:
        """
        Generate optimization report

        Args:
            results: Optimization results from ModelBlaze
            output_path: Output file path (optional)
            format: Report format ('html', 'json', 'text', 'markdown')

        Returns:
            Report content as string
        """
        if format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.supported_formats}")

        if format == "html":
            report = self._generate_html(results)
        elif format == "json":
            report = self._generate_json(results)
        elif format == "markdown":
            report = self._generate_markdown(results)
        else:  # text
            report = self._generate_text(results)

        # Save to file if output path provided
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"📄 Report saved to: {output_path}")

        return report

    def _generate_text(self, results: Dict[str, Any]) -> str:
        """Generate plain text report"""
        lines = []
        lines.append("=" * 80)
        lines.append("🔥 MODELBLAZE OPTIMIZATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Original model
        if "original_model" in results:
            orig = results["original_model"]
            lines.append("📦 ORIGINAL MODEL")
            lines.append("-" * 80)
            lines.append(f"  Framework: {orig.get('framework', 'N/A')}")
            lines.append(f"  Format:    {orig.get('format', 'N/A')}")
            lines.append(f"  Size:      {orig.get('size_str', 'N/A')}")
            if "params_str" in orig:
                lines.append(f"  Parameters: {orig['params_str']}")
            lines.append("")

        # Optimized model
        if "optimized_model" in results:
            opt = results["optimized_model"]
            lines.append("✨ OPTIMIZED MODEL")
            lines.append("-" * 80)
            lines.append(f"  Framework: {opt.get('framework', 'N/A')}")
            lines.append(f"  Format:    {opt.get('format', 'N/A')}")
            lines.append(f"  Size:      {opt.get('size_mb', 0):.2f} MB")
            lines.append(f"  Path:      {opt.get('path', 'N/A')}")
            lines.append("")

        # Optimization config
        if "optimization_config" in results:
            config = results["optimization_config"]
            lines.append("⚙️  OPTIMIZATION CONFIG")
            lines.append("-" * 80)
            lines.append(f"  Target Device:      {config.get('target_device', 'N/A')}")
            lines.append(f"  Optimization Level: {config.get('optimization_level', 'N/A')}")
            lines.append(f"  Quantization:       {config.get('quantization_mode', 'N/A')}")
            lines.append(f"  Pruning Sparsity:   {config.get('pruning_sparsity', 0):.1%}")
            lines.append("")

        # Performance comparison
        if "comparison" in results and results["comparison"]:
            comp = results["comparison"]
            if "improvements" in comp:
                imp = comp["improvements"]
                lines.append("📊 PERFORMANCE IMPROVEMENTS")
                lines.append("-" * 80)

                if "size_reduction_pct" in imp:
                    orig_size = comp["original"]["size_mb"]
                    opt_size = comp["optimized"]["size_mb"]
                    lines.append(f"  Size Reduction:")
                    lines.append(f"    Before: {orig_size:.2f} MB")
                    lines.append(f"    After:  {opt_size:.2f} MB")
                    lines.append(f"    Saved:  {imp['size_reduction_mb']:.2f} MB ({imp['size_reduction_str']})")
                    lines.append("")

                if "latency_speedup" in imp:
                    orig_lat = comp["original"]["mean_latency_ms"]
                    opt_lat = comp["optimized"]["mean_latency_ms"]
                    lines.append(f"  Latency Improvement:")
                    lines.append(f"    Before: {orig_lat:.2f} ms")
                    lines.append(f"    After:  {opt_lat:.2f} ms")
                    lines.append(f"    Speedup: {imp['latency_speedup_str']}")
                    lines.append("")

                if "memory_reduction_pct" in imp:
                    orig_mem = comp["original"]["peak_memory_mb"]
                    opt_mem = comp["optimized"]["peak_memory_mb"]
                    lines.append(f"  Memory Reduction:")
                    lines.append(f"    Before: {orig_mem:.2f} MB")
                    lines.append(f"    After:  {opt_mem:.2f} MB")
                    lines.append(f"    Saved:  {imp['memory_reduction_mb']:.2f} MB ({imp['memory_reduction_pct']:.1f}%)")
                    lines.append("")

        # Timing
        if "elapsed_time" in results:
            lines.append("⏱️  TIMING")
            lines.append("-" * 80)
            lines.append(f"  Optimization Time: {results['elapsed_time']:.2f} seconds")
            lines.append("")

        lines.append("=" * 80)
        lines.append("✅ Optimization completed successfully!")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _generate_json(self, results: Dict[str, Any]) -> str:
        """Generate JSON report"""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "modelblaze_version": "0.1.0",
            "results": results,
        }
        return json.dumps(report_data, indent=2)

    def _generate_markdown(self, results: Dict[str, Any]) -> str:
        """Generate Markdown report"""
        lines = []
        lines.append("# 🔥 ModelBlaze Optimization Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Original model
        if "original_model" in results:
            orig = results["original_model"]
            lines.append("## 📦 Original Model")
            lines.append("")
            lines.append(f"- **Framework:** {orig.get('framework', 'N/A')}")
            lines.append(f"- **Format:** {orig.get('format', 'N/A')}")
            lines.append(f"- **Size:** {orig.get('size_str', 'N/A')}")
            if "params_str" in orig:
                lines.append(f"- **Parameters:** {orig['params_str']}")
            lines.append("")

        # Optimized model
        if "optimized_model" in results:
            opt = results["optimized_model"]
            lines.append("## ✨ Optimized Model")
            lines.append("")
            lines.append(f"- **Framework:** {opt.get('framework', 'N/A')}")
            lines.append(f"- **Format:** {opt.get('format', 'N/A')}")
            lines.append(f"- **Size:** {opt.get('size_mb', 0):.2f} MB")
            lines.append(f"- **Path:** `{opt.get('path', 'N/A')}`")
            lines.append("")

        # Performance improvements
        if "comparison" in results and results["comparison"]:
            comp = results["comparison"]
            if "improvements" in comp:
                imp = comp["improvements"]
                lines.append("## 📊 Performance Improvements")
                lines.append("")

                # Create comparison table
                lines.append("| Metric | Before | After | Improvement |")
                lines.append("|--------|--------|-------|-------------|")

                if "size_reduction_pct" in imp:
                    orig_size = comp["original"]["size_mb"]
                    opt_size = comp["optimized"]["size_mb"]
                    lines.append(f"| Size | {orig_size:.2f} MB | {opt_size:.2f} MB | {imp['size_reduction_str']} ⬇️ |")

                if "latency_speedup" in imp:
                    orig_lat = comp["original"]["mean_latency_ms"]
                    opt_lat = comp["optimized"]["mean_latency_ms"]
                    lines.append(f"| Latency | {orig_lat:.2f} ms | {opt_lat:.2f} ms | {imp['latency_speedup_str']} ⚡ |")

                if "memory_reduction_pct" in imp:
                    orig_mem = comp["original"]["peak_memory_mb"]
                    opt_mem = comp["optimized"]["peak_memory_mb"]
                    lines.append(f"| Memory | {orig_mem:.2f} MB | {opt_mem:.2f} MB | {imp['memory_reduction_pct']:.1f}% ⬇️ |")

                lines.append("")

        # Configuration
        if "optimization_config" in results:
            config = results["optimization_config"]
            lines.append("## ⚙️ Configuration")
            lines.append("")
            lines.append(f"- **Target Device:** {config.get('target_device', 'N/A')}")
            lines.append(f"- **Optimization Level:** {config.get('optimization_level', 'N/A')}")
            lines.append(f"- **Quantization:** {config.get('quantization_mode', 'N/A')}")
            lines.append(f"- **Pruning Sparsity:** {config.get('pruning_sparsity', 0):.1%}")
            lines.append("")

        # Timing
        if "elapsed_time" in results:
            lines.append(f"**Optimization Time:** {results['elapsed_time']:.2f} seconds")
            lines.append("")

        lines.append("---")
        lines.append("*Generated by [ModelBlaze](https://github.com/anilyagiz/ModelBlaze) - Deploy AI Models 10x Faster on Edge*")

        return "\n".join(lines)

    def _generate_html(self, results: Dict[str, Any]) -> str:
        """Generate HTML report"""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ModelBlaze Optimization Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            color: #333;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section h2 {{
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}

        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}

        .metric-card h3 {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}

        .metric-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}

        .metric-card .improvement {{
            font-size: 1.1em;
            color: #28a745;
            font-weight: 600;
        }}

        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        .comparison-table th,
        .comparison-table td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}

        .comparison-table th {{
            background: #f8f9fa;
            color: #667eea;
            font-weight: 600;
        }}

        .comparison-table tr:hover {{
            background: #f8f9fa;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin-right: 10px;
        }}

        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}

        .badge-info {{
            background: #d1ecf1;
            color: #0c5460;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
        }}

        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 ModelBlaze</h1>
            <p>Model Optimization Report</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="content">
"""

        # Performance improvements section
        if "comparison" in results and results["comparison"]:
            comp = results["comparison"]
            if "improvements" in comp:
                imp = comp["improvements"]
                html += """
            <div class="section">
                <h2>📊 Performance Improvements</h2>
                <div class="metric-grid">
"""
                if "size_reduction_pct" in imp:
                    html += f"""
                    <div class="metric-card">
                        <h3>Size Reduction</h3>
                        <div class="value">{imp['size_reduction_str']}</div>
                        <div class="improvement">
                            {comp['original']['size_mb']:.2f} MB → {comp['optimized']['size_mb']:.2f} MB
                        </div>
                    </div>
"""

                if "latency_speedup" in imp:
                    html += f"""
                    <div class="metric-card">
                        <h3>Speed Improvement</h3>
                        <div class="value">{imp['latency_speedup_str']}</div>
                        <div class="improvement">
                            {comp['original']['mean_latency_ms']:.2f} ms → {comp['optimized']['mean_latency_ms']:.2f} ms
                        </div>
                    </div>
"""

                if "memory_reduction_pct" in imp:
                    html += f"""
                    <div class="metric-card">
                        <h3>Memory Savings</h3>
                        <div class="value">{imp['memory_reduction_pct']:.1f}%</div>
                        <div class="improvement">
                            {comp['original']['peak_memory_mb']:.2f} MB → {comp['optimized']['peak_memory_mb']:.2f} MB
                        </div>
                    </div>
"""

                html += """
                </div>
            </div>
"""

        # Configuration section
        if "optimization_config" in results:
            config = results["optimization_config"]
            html += f"""
            <div class="section">
                <h2>⚙️ Configuration</h2>
                <table class="comparison-table">
                    <tr>
                        <th>Setting</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Target Device</td>
                        <td><span class="badge badge-info">{config.get('target_device', 'N/A')}</span></td>
                    </tr>
                    <tr>
                        <td>Optimization Level</td>
                        <td><span class="badge badge-success">{config.get('optimization_level', 'N/A')}</span></td>
                    </tr>
                    <tr>
                        <td>Quantization</td>
                        <td>{config.get('quantization_mode', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Pruning Sparsity</td>
                        <td>{config.get('pruning_sparsity', 0):.1%}</td>
                    </tr>
                </table>
            </div>
"""

        # Model details section
        if "original_model" in results and "optimized_model" in results:
            orig = results["original_model"]
            opt = results["optimized_model"]
            html += f"""
            <div class="section">
                <h2>📦 Model Details</h2>
                <table class="comparison-table">
                    <tr>
                        <th>Property</th>
                        <th>Original</th>
                        <th>Optimized</th>
                    </tr>
                    <tr>
                        <td>Framework</td>
                        <td>{orig.get('framework', 'N/A')}</td>
                        <td>{opt.get('framework', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Format</td>
                        <td>{orig.get('format', 'N/A')}</td>
                        <td>{opt.get('format', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Size</td>
                        <td>{orig.get('size_str', 'N/A')}</td>
                        <td>{opt.get('size_mb', 0):.2f} MB</td>
                    </tr>
                </table>
            </div>
"""

        # Timing
        if "elapsed_time" in results:
            html += f"""
            <div class="section">
                <h2>⏱️ Performance</h2>
                <p style="font-size: 1.2em;">Optimization completed in <strong>{results['elapsed_time']:.2f} seconds</strong></p>
            </div>
"""

        html += """
        </div>

        <div class="footer">
            <p>Generated by <a href="https://github.com/anilyagiz/ModelBlaze" target="_blank">ModelBlaze</a></p>
            <p style="margin-top: 5px; font-size: 0.9em;">Deploy AI Models 10x Faster on Edge</p>
        </div>
    </div>
</body>
</html>
"""

        return html
