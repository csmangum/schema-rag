#!/usr/bin/env python3
"""Generate visualization charts for embedding model comparison."""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any

try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Install with: pip install matplotlib")


def load_comparison_data(json_path: Path) -> Dict[str, Any]:
    """Load comparison data from JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_model_data(comparison_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract model data from comparison results."""
    model_results = comparison_data.get("model_results", [])
    
    models = []
    for result in model_results:
        summary = result.get("summary", {})
        perf = result.get("performance", {})
        
        model_name = summary.get("model_name", "unknown")
        # Shorten model names for display
        display_name = model_name.replace("intfloat/", "").replace("all-", "").replace("multi-qa-", "").replace("-base-dot-v1", "").replace("-base-v2", "").replace("-v2", "").replace("-v1", "")
        
        models.append({
            "name": model_name,
            "display_name": display_name,
            "match_rate": summary.get("expected_match_rate", 0) * 100,
            "query_time_ms": perf.get("query_time_stats", {}).get("mean", 0) * 1000,
            "index_size_mb": perf.get("index_sizes", {}).get("total", 0) / (1024 * 1024),
            "init_time_s": perf.get("initialization_time_seconds", 0),
            "model_match_rate": summary.get("model_match_rate", 0) * 100,
            "column_match_rate": summary.get("column_match_rate", 0) * 100,
        })
    
    return models


def create_accuracy_vs_speed_chart(models: List[Dict[str, Any]], output_path: Path):
    """Create scatter plot: Accuracy vs Query Time."""
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Extract data
    match_rates = [m["match_rate"] for m in models]
    query_times = [m["query_time_ms"] for m in models]
    names = [m["display_name"] for m in models]
    
    # Create scatter plot
    ax.scatter(query_times, match_rates, s=200, alpha=0.7, c=range(len(models)), cmap='viridis')
    
    # Add labels
    for i, (name, x, y) in enumerate(zip(names, query_times, match_rates)):
        ax.annotate(name, (x, y), xytext=(5, 5), textcoords='offset points', fontsize=9)
    
    ax.set_xlabel('Query Time (ms)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Match Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Embedding Models: Accuracy vs Speed Trade-off', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add quadrant lines
    median_time = np.median(query_times)
    median_accuracy = np.median(match_rates)
    ax.axvline(median_time, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax.axhline(median_accuracy, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    plt.tight_layout()
    plt.savefig(output_path / 'accuracy_vs_speed.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path / 'accuracy_vs_speed.png'}")
    plt.close()


def create_index_size_chart(models: List[Dict[str, Any]], output_path: Path):
    """Create bar chart: Index Size comparison."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    names = [m["display_name"] for m in models]
    sizes = [m["index_size_mb"] for m in models]
    
    ax.barh(names, sizes, color='steelblue', alpha=0.7)
    
    # Add value labels
    for i, (name, size) in enumerate(zip(names, sizes)):
        ax.text(size + 0.05, i, f'{size:.2f} MB', va='center', fontsize=9)
    
    ax.set_xlabel('Index Size (MB)', fontsize=12, fontweight='bold')
    ax.set_title('Index Size Comparison', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(output_path / 'index_size_comparison.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path / 'index_size_comparison.png'}")
    plt.close()


def create_performance_radar_chart(models: List[Dict[str, Any]], output_path: Path):
    """Create radar chart comparing multiple metrics."""
    # Select top 3-4 models for readability
    top_models = sorted(models, key=lambda x: x["match_rate"], reverse=True)[:4]
    
    # Normalize metrics (0-100 scale)
    categories = ['Match Rate', 'Speed\n(lower=better)', 'Storage\n(lower=better)', 'Model Match', 'Column Match']
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    # Calculate angles
    num_vars = len(categories)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(top_models)))
    
    for i, model in enumerate(top_models):
        # Normalize values (invert speed and storage so higher is better)
        values = [
            model["match_rate"],  # Already 0-100
            100 - (model["query_time_ms"] / 30 * 100),  # Invert: lower time = higher score
            100 - (model["index_size_mb"] / 4 * 100),  # Invert: smaller size = higher score
            model["model_match_rate"],  # Already 0-100
            model["column_match_rate"],  # Already 0-100
        ]
        values += values[:1]  # Complete the circle
        
        ax.plot(angles, values, 'o-', linewidth=2, label=model["display_name"], color=colors[i])
        ax.fill(angles, values, alpha=0.15, color=colors[i])
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=8)
    ax.grid(True)
    
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
    plt.title('Multi-Metric Comparison (Top Models)', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path / 'performance_radar.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path / 'performance_radar.png'}")
    plt.close()


def create_summary_comparison_chart(models: List[Dict[str, Any]], output_path: Path):
    """Create a comprehensive comparison chart with multiple subplots."""
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    names = [m["display_name"] for m in models]
    colors = plt.cm.viridis(np.linspace(0, 1, len(models)))
    
    # 1. Match Rate
    ax1 = fig.add_subplot(gs[0, 0])
    match_rates = [m["match_rate"] for m in models]
    bars1 = ax1.barh(names, match_rates, color=colors)
    ax1.set_xlabel('Match Rate (%)', fontweight='bold')
    ax1.set_title('Accuracy (Match Rate)', fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='x')
    for i, (bar, rate) in enumerate(zip(bars1, match_rates)):
        ax1.text(rate + 0.5, i, f'{rate:.1f}%', va='center', fontsize=9)
    
    # 2. Query Time
    ax2 = fig.add_subplot(gs[0, 1])
    query_times = [m["query_time_ms"] for m in models]
    bars2 = ax2.barh(names, query_times, color=colors)
    ax2.set_xlabel('Query Time (ms)', fontweight='bold')
    ax2.set_title('Speed (Lower is Better)', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')
    for i, (bar, time) in enumerate(zip(bars2, query_times)):
        ax2.text(time + 0.3, i, f'{time:.1f}ms', va='center', fontsize=9)
    
    # 3. Index Size
    ax3 = fig.add_subplot(gs[0, 2])
    index_sizes = [m["index_size_mb"] for m in models]
    bars3 = ax3.barh(names, index_sizes, color=colors)
    ax3.set_xlabel('Index Size (MB)', fontweight='bold')
    ax3.set_title('Storage (Lower is Better)', fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='x')
    for i, (bar, size) in enumerate(zip(bars3, index_sizes)):
        ax3.text(size + 0.05, i, f'{size:.2f}MB', va='center', fontsize=9)
    
    # 4. Accuracy vs Speed Scatter
    ax4 = fig.add_subplot(gs[1, :2])
    ax4.scatter(query_times, match_rates, s=300, alpha=0.7, c=range(len(models)), cmap='viridis', edgecolors='black', linewidth=1.5)
    for i, (name, x, y) in enumerate(zip(names, query_times, match_rates)):
        ax4.annotate(name, (x, y), xytext=(5, 5), textcoords='offset points', fontsize=10, fontweight='bold')
    ax4.set_xlabel('Query Time (ms)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Match Rate (%)', fontsize=11, fontweight='bold')
    ax4.set_title('Accuracy vs Speed Trade-off', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # 5. Model Match Rate
    ax5 = fig.add_subplot(gs[1, 2])
    model_match_rates = [m["model_match_rate"] for m in models]
    bars5 = ax5.barh(names, model_match_rates, color=colors)
    ax5.set_xlabel('Model Match Rate (%)', fontweight='bold')
    ax5.set_title('Model Matching', fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='x')
    for i, (bar, rate) in enumerate(zip(bars5, model_match_rates)):
        ax5.text(rate + 0.5, i, f'{rate:.1f}%', va='center', fontsize=9)
    
    plt.suptitle('Embedding Models Comprehensive Comparison', fontsize=16, fontweight='bold', y=0.98)
    plt.savefig(output_path / 'comprehensive_comparison.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path / 'comprehensive_comparison.png'}")
    plt.close()


def create_efficiency_score_chart(models: List[Dict[str, Any]], output_path: Path):
    """Create chart showing efficiency score (accuracy / (time * size))."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    names = [m["display_name"] for m in models]
    # Efficiency = accuracy / (normalized_time * normalized_size)
    # Higher is better
    efficiencies = []
    for m in models:
        # Normalize: time penalty (ms/10), size penalty (MB/2)
        time_penalty = 1 + (m["query_time_ms"] / 10)
        size_penalty = 1 + (m["index_size_mb"] / 2)
        efficiency = m["match_rate"] / (time_penalty * size_penalty)
        efficiencies.append(efficiency)
    
    ax.barh(names, efficiencies, color='coral', alpha=0.7)
    
    # Add value labels
    for i, (name, eff) in enumerate(zip(names, efficiencies)):
        ax.text(eff + 0.5, i, f'{eff:.2f}', va='center', fontsize=9)
    
    ax.set_xlabel('Efficiency Score (Accuracy / (Time × Size))', fontsize=12, fontweight='bold')
    ax.set_title('Model Efficiency Ranking', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(output_path / 'efficiency_score.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path / 'efficiency_score.png'}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Generate visualization charts for embedding model comparison")
    parser.add_argument(
        "--input",
        type=str,
        default="artifacts/embedding_model_comparison.json",
        help="Path to comparison JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="artifacts/charts",
        help="Directory to save charts",
    )
    args = parser.parse_args()
    
    if not MATPLOTLIB_AVAILABLE:
        print("Error: matplotlib is required. Install with: pip install matplotlib")
        return 1
    
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    print(f"Loading comparison data from {input_path}...")
    comparison_data = load_comparison_data(input_path)
    
    print("Extracting model data...")
    models = extract_model_data(comparison_data)
    
    print(f"\nGenerating charts for {len(models)} models...")
    print(f"Output directory: {output_dir}\n")
    
    # Generate all charts
    create_accuracy_vs_speed_chart(models, output_dir)
    create_index_size_chart(models, output_dir)
    create_performance_radar_chart(models, output_dir)
    create_summary_comparison_chart(models, output_dir)
    create_efficiency_score_chart(models, output_dir)
    
    print(f"\n✓ All charts generated successfully in {output_dir}")
    return 0


if __name__ == "__main__":
    exit(main())
