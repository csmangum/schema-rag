# Embedding Model Comparison Charts

This directory contains visualization charts comparing 5 embedding models for Schema RAG.

## Generated Charts

### 1. `accuracy_vs_speed.png`
**Accuracy vs Speed Trade-off Scatter Plot**
- X-axis: Query Time (ms) - lower is better
- Y-axis: Match Rate (%) - higher is better
- Shows the trade-off between accuracy and query latency
- Models in the top-left quadrant are best (high accuracy, low latency)

### 2. `index_size_comparison.png`
**Index Size Comparison Bar Chart**
- Horizontal bar chart showing disk storage requirements
- Lower is better for storage efficiency
- Shows the storage cost of different embedding dimensions

### 3. `performance_radar.png`
**Multi-Metric Radar Chart**
- Compares top 4 models across multiple dimensions:
  - Match Rate (accuracy)
  - Speed (inverted - higher is better)
  - Storage (inverted - higher is better)
  - Model Match Rate
  - Column Match Rate
- Larger area = better overall performance

### 4. `comprehensive_comparison.png`
**Comprehensive Multi-Panel Comparison**
- 5 subplots showing:
  1. Accuracy (Match Rate)
  2. Speed (Query Time)
  3. Storage (Index Size)
  4. Accuracy vs Speed scatter plot
  5. Model Match Rate
- Best single chart for overall comparison

### 5. `efficiency_score.png`
**Efficiency Score Ranking**
- Calculates: `Accuracy / (Time × Size)`
- Higher score = better efficiency (more accuracy per unit of time and storage)
- Helps identify the best value model

## Models Compared

1. **all-MiniLM-L6-v2** - Baseline lightweight model (384 dims)
2. **all-MiniLM-L12-v2** - Deeper lightweight model (384 dims)
3. **all-mpnet-base-v2** - Balanced model (768 dims) ⭐ Best overall
4. **multi-qa-mpnet-base-dot-v1** - Q&A optimized (768 dims)
5. **intfloat/e5-large-v2** - State-of-the-art (1024 dims)

## Key Findings

- **Best Accuracy**: `all-mpnet-base-v2` and `e5-large-v2` (tied at 89.09%)
- **Fastest**: `all-MiniLM-L6-v2` (8.26ms)
- **Best Efficiency**: `all-mpnet-base-v2` (best balance of accuracy, speed, and storage)
- **Smallest Storage**: `all-MiniLM-L6-v2` and `all-MiniLM-L12-v2` (1.66 MB)

## Regenerate Charts

To regenerate these charts:

```bash
python scripts/generate_comparison_charts.py
```

Or with custom paths:

```bash
python scripts/generate_comparison_charts.py \
  --input artifacts/embedding_model_comparison.json \
  --output-dir artifacts/charts
```
