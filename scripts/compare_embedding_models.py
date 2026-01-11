#!/usr/bin/env python3
"""Compare different embedding models for Schema RAG.

This script:
1. Builds indices with different embedding models
2. Runs the same test suite on each model
3. Compares results and generates a comparison report
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

try:
    import psutil
    import tracemalloc
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Add schema_rag to path
schema_rag_path = Path(__file__).parent.parent
sys.path.insert(0, str(schema_rag_path))

from schema_rag import SchemaRagService


def load_test_questions(questions_file: Path) -> List[Dict[str, Any]]:
    """Load test questions from JSON file."""
    with open(questions_file, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_result(question: Dict[str, Any], result) -> Dict[str, Any]:
    """Evaluate a single query result."""
    evaluation = {
        "question_id": question["id"],
        "question": question["question"],
        "expected_model": question.get("expected_model"),
        "expected_column": question.get("expected_column"),
        "found_expected": False,
        "found_model": False,
        "found_column": False,
        "top_doc_type": None,
        "top_doc_id": None,
        "top_score": None,
        "num_docs": len(result.docs),
        "num_schema_refs": len(result.schema_refs),
        "num_join_hints": len(result.join_hints),
        "num_recipes": len(result.recipes),
    }
    
    # Check if expected model/column found
    if question.get("expected_model") and question.get("expected_column"):
        for ref in result.schema_refs:
            if ref.get("model") == question["expected_model"]:
                evaluation["found_model"] = True
                if ref.get("column") == question["expected_column"]:
                    evaluation["found_column"] = True
                    evaluation["found_expected"] = True
                    break
    
    # Get top document info
    if result.docs:
        top_doc = result.docs[0]
        evaluation["top_doc_type"] = top_doc.get("doc_type")
        evaluation["top_doc_id"] = top_doc.get("id")
        evaluation["top_score"] = top_doc.get("score")
    
    return evaluation


def get_file_size(path: Path) -> int:
    """Get file size in bytes."""
    if path.is_file():
        return path.stat().st_size
    elif path.is_dir():
        total = 0
        for item in path.rglob('*'):
            if item.is_file():
                total += item.stat().st_size
        return total
    return 0


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def get_index_size(index_path: Path) -> Dict[str, Any]:
    """Get size information for index directory."""
    sizes = {}
    
    # Index file
    index_file = index_path / "faiss.index"
    if index_file.exists():
        sizes["index_file"] = get_file_size(index_file)
    
    # Docs file
    docs_file = index_path / "docs.jsonl"
    if docs_file.exists():
        sizes["docs_file"] = get_file_size(docs_file)
    
    # Config file
    config_file = index_path / "config.json"
    if config_file.exists():
        sizes["config_file"] = get_file_size(config_file)
    
    # Total
    sizes["total"] = sum(sizes.values())
    
    return sizes


def get_memory_usage() -> Dict[str, Any]:
    """Get current memory usage."""
    memory_info = {}
    
    if PSUTIL_AVAILABLE:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        memory_info["rss"] = mem_info.rss  # Resident Set Size
        memory_info["vms"] = mem_info.vms  # Virtual Memory Size
        
        # System memory
        sys_mem = psutil.virtual_memory()
        memory_info["system_available"] = sys_mem.available
        memory_info["system_total"] = sys_mem.total
        memory_info["system_percent"] = sys_mem.percent
    
    # Tracemalloc if available
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        memory_info["tracemalloc_current"] = current
        memory_info["tracemalloc_peak"] = peak
    
    return memory_info


def run_tests_for_model(
    model_name: str,
    index_path: Path,
    questions: List[Dict[str, Any]],
    measure_performance: bool = True,
) -> Dict[str, Any]:
    """Run test suite for a specific model."""
    print(f"\n{'='*80}")
    print(f"Testing model: {model_name}")
    print(f"Index path: {index_path}")
    print(f"{'='*80}")
    
    if not index_path.exists():
        print(f"ERROR: Index path does not exist: {index_path}")
        return {
            "model_name": model_name,
            "index_path": str(index_path),
            "error": f"Index path does not exist: {index_path}",
        }
    
    # Get index size before loading
    index_sizes = get_index_size(index_path)
    
    # Measure service initialization time and memory
    init_start_time = time.time()
    init_memory_before = get_memory_usage()
    
    if measure_performance and PSUTIL_AVAILABLE:
        tracemalloc.start()
    
    try:
        service = SchemaRagService(index_path)
    except Exception as e:
        print(f"ERROR: Failed to load service: {e}")
        return {
            "model_name": model_name,
            "index_path": str(index_path),
            "error": str(e),
        }
    
    init_time = time.time() - init_start_time
    init_memory_after = get_memory_usage()
    
    # Calculate memory used by service
    service_memory = {}
    if PSUTIL_AVAILABLE:
        service_memory["rss_delta"] = init_memory_after.get("rss", 0) - init_memory_before.get("rss", 0)
        service_memory["vms_delta"] = init_memory_after.get("vms", 0) - init_memory_before.get("vms", 0)
    
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        service_memory["tracemalloc_peak"] = peak
    
    print(f"Service initialization time: {init_time:.3f}s")
    if service_memory:
        print(f"Service memory (RSS): {format_bytes(service_memory.get('rss_delta', 0))}")
    
    print(f"Running {len(questions)} questions...")
    results = []
    query_times = []
    
    # Warm-up query (not counted)
    try:
        service.retrieve_grounding("test query", top_k=5)
    except:
        pass
    
    for i, question in enumerate(questions, 1):
        if i % 20 == 0:
            print(f"  Progress: {i}/{len(questions)}")
        
        query_start = time.time()
        try:
            result = service.retrieve_grounding(question["question"], top_k=5)
            query_time = time.time() - query_start
            query_times.append(query_time)
            
            evaluation = evaluate_result(question, result)
            evaluation["success"] = True
            evaluation["error"] = None
            evaluation["query_time"] = query_time
        except Exception as e:
            query_time = time.time() - query_start
            query_times.append(query_time)
            evaluation = {
                "question_id": question["id"],
                "question": question["question"],
                "success": False,
                "error": str(e),
                "query_time": query_time,
            }
        
        results.append(evaluation)
    
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    
    # Calculate query time statistics
    query_time_stats = {}
    if query_times:
        query_time_stats["mean"] = sum(query_times) / len(query_times)
        query_time_stats["min"] = min(query_times)
        query_time_stats["max"] = max(query_times)
        query_time_stats["total"] = sum(query_times)
        query_time_stats["p50"] = sorted(query_times)[len(query_times) // 2]
        query_time_stats["p95"] = sorted(query_times)[int(len(query_times) * 0.95)]
        query_time_stats["p99"] = sorted(query_times)[int(len(query_times) * 0.99)]
    
    # Calculate statistics
    total = len(results)
    successful = sum(1 for r in results if r.get("success", False))
    found_expected = sum(1 for r in results if r.get("found_expected", False))
    found_model = sum(1 for r in results if r.get("found_model", False))
    found_column = sum(1 for r in results if r.get("found_column", False))
    
    avg_docs = sum(r.get("num_docs", 0) for r in results) / total if total > 0 else 0
    avg_schema_refs = sum(r.get("num_schema_refs", 0) for r in results) / total if total > 0 else 0
    avg_score = sum(r.get("top_score", 0) or 0 for r in results) / successful if successful > 0 else 0
    
    summary = {
        "model_name": model_name,
        "index_path": str(index_path),
        "total_questions": total,
        "successful_queries": successful,
        "success_rate": successful / total if total > 0 else 0,
        "found_expected_model_column": found_expected,
        "expected_match_rate": found_expected / total if total > 0 else 0,
        "found_expected_model": found_model,
        "model_match_rate": found_model / total if total > 0 else 0,
        "found_expected_column": found_column,
        "column_match_rate": found_column / total if total > 0 else 0,
        "average_docs_returned": avg_docs,
        "average_schema_refs": avg_schema_refs,
        "average_top_score": avg_score,
    }
    
    # Add performance metrics
    performance = {
        "initialization_time_seconds": init_time,
        "query_time_stats": query_time_stats,
        "index_sizes": {k: v for k, v in index_sizes.items()},
        "service_memory": service_memory,
    }
    
    return {
        "summary": summary,
        "performance": performance,
        "results": results,
    }


def compare_results(results1: Dict[str, Any], results2: Dict[str, Any]) -> Dict[str, Any]:
    """Compare results from two models."""
    summary1 = results1.get("summary", {})
    summary2 = results2.get("summary", {})
    perf1 = results1.get("performance", {})
    perf2 = results2.get("performance", {})
    
    comparison = {
        "model1": summary1.get("model_name", "unknown"),
        "model2": summary2.get("model_name", "unknown"),
        "metrics": {},
        "performance": {},
        "question_by_question": [],
    }
    
    # Compare summary metrics
    metrics_to_compare = [
        "expected_match_rate",
        "model_match_rate",
        "column_match_rate",
        "average_docs_returned",
        "average_schema_refs",
        "average_top_score",
    ]
    
    for metric in metrics_to_compare:
        val1 = summary1.get(metric, 0)
        val2 = summary2.get(metric, 0)
        diff = val2 - val1
        diff_pct = (diff / val1 * 100) if val1 > 0 else 0
        
        comparison["metrics"][metric] = {
            "model1": val1,
            "model2": val2,
            "difference": diff,
            "difference_percent": diff_pct,
        }
    
    # Question-by-question comparison
    results1_list = results1.get("results", [])
    results2_list = results2.get("results", [])
    
    # Create lookup by question_id
    results1_dict = {r.get("question_id"): r for r in results1_list}
    results2_dict = {r.get("question_id"): r for r in results2_list}
    
    all_question_ids = set(results1_dict.keys()) | set(results2_dict.keys())
    
    for qid in sorted(all_question_ids):
        r1 = results1_dict.get(qid, {})
        r2 = results2_dict.get(qid, {})
        
        question_comparison = {
            "question_id": qid,
            "question": r1.get("question") or r2.get("question"),
            "model1_found_expected": r1.get("found_expected", False),
            "model2_found_expected": r2.get("found_expected", False),
            "model1_found_model": r1.get("found_model", False),
            "model2_found_model": r2.get("found_model", False),
            "model1_found_column": r1.get("found_column", False),
            "model2_found_column": r2.get("found_column", False),
            "model1_score": r1.get("top_score"),
            "model2_score": r2.get("top_score"),
            "improved": False,
            "regressed": False,
        }
        
        # Determine if model2 improved or regressed
        if r1.get("found_expected", False) != r2.get("found_expected", False):
            if r2.get("found_expected", False):
                question_comparison["improved"] = True
            else:
                question_comparison["regressed"] = True
        
        comparison["question_by_question"].append(question_comparison)
    
    # Calculate improvement statistics
    improved = sum(1 for q in comparison["question_by_question"] if q["improved"])
    regressed = sum(1 for q in comparison["question_by_question"] if q["regressed"])
    
    comparison["improvement_stats"] = {
        "questions_improved": improved,
        "questions_regressed": regressed,
        "net_improvement": improved - regressed,
    }
    
    # Compare performance metrics
    perf_comparison = {}
    
    # Initialization time
    init1 = perf1.get("initialization_time_seconds", 0)
    init2 = perf2.get("initialization_time_seconds", 0)
    if init1 > 0:
        perf_comparison["initialization_time"] = {
            "model1": init1,
            "model2": init2,
            "difference": init2 - init1,
            "difference_percent": ((init2 - init1) / init1 * 100) if init1 > 0 else 0,
        }
    
    # Query time
    qtime1 = perf1.get("query_time_stats", {})
    qtime2 = perf2.get("query_time_stats", {})
    if qtime1.get("mean") and qtime2.get("mean"):
        perf_comparison["query_time_mean"] = {
            "model1": qtime1["mean"],
            "model2": qtime2["mean"],
            "difference": qtime2["mean"] - qtime1["mean"],
            "difference_percent": ((qtime2["mean"] - qtime1["mean"]) / qtime1["mean"] * 100) if qtime1["mean"] > 0 else 0,
        }
        perf_comparison["query_time_p95"] = {
            "model1": qtime1.get("p95", 0),
            "model2": qtime2.get("p95", 0),
            "difference": qtime2.get("p95", 0) - qtime1.get("p95", 0),
        }
    
    # Index sizes
    sizes1 = perf1.get("index_sizes", {})
    sizes2 = perf2.get("index_sizes", {})
    if sizes1.get("total") and sizes2.get("total"):
        perf_comparison["index_size"] = {
            "model1": sizes1["total"],
            "model2": sizes2["total"],
            "difference": sizes2["total"] - sizes1["total"],
            "difference_percent": ((sizes2["total"] - sizes1["total"]) / sizes1["total"] * 100) if sizes1["total"] > 0 else 0,
        }
    
    # Memory usage
    mem1 = perf1.get("service_memory", {})
    mem2 = perf2.get("service_memory", {})
    if mem1.get("rss_delta") and mem2.get("rss_delta"):
        perf_comparison["memory_rss"] = {
            "model1": mem1["rss_delta"],
            "model2": mem2["rss_delta"],
            "difference": mem2["rss_delta"] - mem1["rss_delta"],
            "difference_percent": ((mem2["rss_delta"] - mem1["rss_delta"]) / mem1["rss_delta"] * 100) if mem1["rss_delta"] > 0 else 0,
        }
    
    comparison["performance"] = perf_comparison
    
    return comparison


def generate_comparison_report(comparison: Dict[str, Any], output_file: Path):
    """Generate a human-readable comparison report."""
    lines = []
    lines.append("=" * 80)
    lines.append("EMBEDDING MODEL COMPARISON REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Model 1: {comparison['model1']}")
    lines.append(f"Model 2: {comparison['model2']}")
    lines.append("")
    lines.append("-" * 80)
    lines.append("SUMMARY METRICS COMPARISON")
    lines.append("-" * 80)
    lines.append("")
    
    for metric, data in comparison["metrics"].items():
        lines.append(f"{metric.replace('_', ' ').title()}:")
        lines.append(f"  Model 1: {data['model1']:.4f}")
        lines.append(f"  Model 2: {data['model2']:.4f}")
        lines.append(f"  Difference: {data['difference']:+.4f} ({data['difference_percent']:+.2f}%)")
        lines.append("")
    
    lines.append("-" * 80)
    lines.append("PERFORMANCE COMPARISON")
    lines.append("-" * 80)
    lines.append("")
    
    perf = comparison.get("performance", {})
    
    if "initialization_time" in perf:
        it = perf["initialization_time"]
        lines.append(f"Initialization Time:")
        lines.append(f"  Model 1: {it['model1']:.3f}s")
        lines.append(f"  Model 2: {it['model2']:.3f}s")
        lines.append(f"  Difference: {it['difference']:+.3f}s ({it['difference_percent']:+.2f}%)")
        lines.append("")
    
    if "query_time_mean" in perf:
        qt = perf["query_time_mean"]
        lines.append(f"Query Time (Mean):")
        lines.append(f"  Model 1: {qt['model1']*1000:.2f}ms")
        lines.append(f"  Model 2: {qt['model2']*1000:.2f}ms")
        lines.append(f"  Difference: {qt['difference']*1000:+.2f}ms ({qt['difference_percent']:+.2f}%)")
        lines.append("")
        
        if "query_time_p95" in perf:
            qt95 = perf["query_time_p95"]
            lines.append(f"Query Time (P95):")
            lines.append(f"  Model 1: {qt95['model1']*1000:.2f}ms")
            lines.append(f"  Model 2: {qt95['model2']*1000:.2f}ms")
            lines.append(f"  Difference: {qt95['difference']*1000:+.2f}ms")
            lines.append("")
    
    if "index_size" in perf:
        isize = perf["index_size"]
        lines.append(f"Index Size:")
        lines.append(f"  Model 1: {format_bytes(isize['model1'])}")
        lines.append(f"  Model 2: {format_bytes(isize['model2'])}")
        lines.append(f"  Difference: {format_bytes(isize['difference'])} ({isize['difference_percent']:+.2f}%)")
        lines.append("")
    
    if "memory_rss" in perf:
        mem = perf["memory_rss"]
        lines.append(f"Memory Usage (RSS):")
        lines.append(f"  Model 1: {format_bytes(mem['model1'])}")
        lines.append(f"  Model 2: {format_bytes(mem['model2'])}")
        lines.append(f"  Difference: {format_bytes(mem['difference'])} ({mem['difference_percent']:+.2f}%)")
        lines.append("")
    
    lines.append("-" * 80)
    lines.append("IMPROVEMENT STATISTICS")
    lines.append("-" * 80)
    lines.append("")
    stats = comparison["improvement_stats"]
    lines.append(f"Questions improved: {stats['questions_improved']}")
    lines.append(f"Questions regressed: {stats['questions_regressed']}")
    lines.append(f"Net improvement: {stats['net_improvement']:+d}")
    lines.append("")
    
    # Show questions that improved
    improved_questions = [q for q in comparison["question_by_question"] if q["improved"]]
    if improved_questions:
        lines.append("-" * 80)
        lines.append(f"QUESTIONS WHERE MODEL 2 IMPROVED ({len(improved_questions)})")
        lines.append("-" * 80)
        lines.append("")
        for q in improved_questions[:20]:  # Show first 20
            lines.append(f"  Q{q['question_id']}: {q['question']}")
        if len(improved_questions) > 20:
            lines.append(f"  ... and {len(improved_questions) - 20} more")
        lines.append("")
    
    # Show questions that regressed
    regressed_questions = [q for q in comparison["question_by_question"] if q["regressed"]]
    if regressed_questions:
        lines.append("-" * 80)
        lines.append(f"QUESTIONS WHERE MODEL 2 REGRESSED ({len(regressed_questions)})")
        lines.append("-" * 80)
        lines.append("")
        for q in regressed_questions[:20]:  # Show first 20
            lines.append(f"  Q{q['question_id']}: {q['question']}")
        if len(regressed_questions) > 20:
            lines.append(f"  ... and {len(regressed_questions) - 20} more")
        lines.append("")
    
    lines.append("=" * 80)
    
    report_text = "\n".join(lines)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    print("\n" + report_text)
    
    return report_text


def compare_multiple_models(
    model_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Compare multiple models and generate comprehensive comparison."""
    if len(model_results) < 2:
        return {}
    
    comparisons = {}
    
    # Compare each pair
    for i in range(len(model_results)):
        for j in range(i + 1, len(model_results)):
            model1_name = model_results[i]["summary"]["model_name"]
            model2_name = model_results[j]["summary"]["model_name"]
            key = f"{model1_name}_vs_{model2_name}"
            comparisons[key] = compare_results(model_results[i], model_results[j])
    
    # Generate summary table
    summary_table = []
    for result in model_results:
        summary = result.get("summary", {})
        perf = result.get("performance", {})
        summary_table.append({
            "model": summary.get("model_name", "unknown"),
            "expected_match_rate": summary.get("expected_match_rate", 0),
            "model_match_rate": summary.get("model_match_rate", 0),
            "column_match_rate": summary.get("column_match_rate", 0),
            "avg_query_time_ms": perf.get("query_time_stats", {}).get("mean", 0) * 1000,
            "index_size_mb": perf.get("index_sizes", {}).get("total", 0) / (1024 * 1024),
            "init_time_s": perf.get("initialization_time_seconds", 0),
        })
    
    return {
        "pairwise_comparisons": comparisons,
        "summary_table": summary_table,
    }


def generate_multi_model_report(
    comparison: Dict[str, Any],
    model_results: List[Dict[str, Any]],
    output_file: Path
):
    """Generate a comprehensive report comparing multiple models."""
    lines = []
    lines.append("=" * 80)
    lines.append("MULTI-MODEL EMBEDDING COMPARISON REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    # Summary table
    lines.append("-" * 80)
    lines.append("SUMMARY TABLE")
    lines.append("-" * 80)
    lines.append("")
    lines.append(f"{'Model':<30} {'Match%':<10} {'Query(ms)':<12} {'Index(MB)':<12} {'Init(s)':<10}")
    lines.append("-" * 80)
    
    for row in comparison.get("summary_table", []):
        lines.append(
            f"{row['model']:<30} "
            f"{row['expected_match_rate']*100:>6.2f}%  "
            f"{row['avg_query_time_ms']:>8.2f}  "
            f"{row['index_size_mb']:>8.2f}  "
            f"{row['init_time_s']:>8.2f}"
        )
    lines.append("")
    
    # Pairwise comparisons
    lines.append("-" * 80)
    lines.append("PAIRWISE COMPARISONS")
    lines.append("-" * 80)
    lines.append("")
    
    for key, pair_comp in comparison.get("pairwise_comparisons", {}).items():
        lines.append(f"Comparison: {key}")
        lines.append("")
        
        # Metrics
        for metric, data in pair_comp.get("metrics", {}).items():
            lines.append(f"  {metric.replace('_', ' ').title()}:")
            lines.append(f"    Model 1: {data['model1']:.4f}")
            lines.append(f"    Model 2: {data['model2']:.4f}")
            lines.append(f"    Difference: {data['difference']:+.4f} ({data['difference_percent']:+.2f}%)")
            lines.append("")
        
        # Performance
        perf = pair_comp.get("performance", {})
        if perf:
            lines.append("  Performance:")
            if "query_time_mean" in perf:
                qt = perf["query_time_mean"]
                lines.append(f"    Query Time: {qt['model1']*1000:.2f}ms → {qt['model2']*1000:.2f}ms ({qt['difference']*1000:+.2f}ms)")
            if "index_size" in perf:
                isize = perf["index_size"]
                lines.append(f"    Index Size: {format_bytes(isize['model1'])} → {format_bytes(isize['model2'])} ({format_bytes(isize['difference'])})")
            lines.append("")
        
        lines.append("-" * 80)
        lines.append("")
    
    lines.append("=" * 80)
    
    report_text = "\n".join(lines)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    print("\n" + report_text)
    
    return report_text


def main():
    parser = argparse.ArgumentParser(
        description="Compare different embedding models for Schema RAG"
    )
    parser.add_argument(
        "--questions",
        type=str,
        default="artifacts/schema_rag_test_questions.json",
        help="Path to questions JSON file",
    )
    parser.add_argument(
        "--model1-index",
        type=str,
        help="Path to index directory for model 1",
    )
    parser.add_argument(
        "--model2-index",
        type=str,
        help="Path to index directory for model 2",
    )
    parser.add_argument(
        "--model3-index",
        type=str,
        help="Path to index directory for model 3",
    )
    parser.add_argument(
        "--model-indices",
        type=str,
        nargs="+",
        help="Paths to index directories for multiple models (alternative to --model1-index, etc.)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/embedding_model_comparison.json",
        help="Path to output comparison JSON file",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="artifacts/EMBEDDING_MODEL_COMPARISON_REPORT.md",
        help="Path to output comparison report markdown file",
    )
    args = parser.parse_args()
    
    questions_path = Path(args.questions)
    output_path = Path(args.output)
    report_path = Path(args.report)
    
    if not questions_path.exists():
        print(f"Error: Questions file not found: {questions_path}")
        return 1
    
    # Collect model indices
    model_indices = []
    if args.model_indices:
        model_indices = [Path(p) for p in args.model_indices]
    else:
        if args.model1_index:
            model_indices.append(Path(args.model1_index))
        if args.model2_index:
            model_indices.append(Path(args.model2_index))
        if args.model3_index:
            model_indices.append(Path(args.model3_index))
    
    if len(model_indices) < 2:
        print("Error: Need at least 2 model indices to compare")
        print("Use --model1-index and --model2-index, or --model-indices")
        return 1
    
    # Load questions
    print(f"Loading questions from {questions_path}...")
    questions = load_test_questions(questions_path)
    print(f"Loaded {len(questions)} questions")
    
    # Get model names from configs
    def get_model_name(index_path: Path) -> str:
        config_path = index_path / "config.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("model_name", "unknown")
        return "unknown"
    
    # Run tests for all models
    print(f"\nTesting {len(model_indices)} models...")
    all_results = []
    
    for i, index_path in enumerate(model_indices, 1):
        model_name = get_model_name(index_path)
        print(f"\n[{i}/{len(model_indices)}] Model: {model_name}")
        result = run_tests_for_model(model_name, index_path, questions)
        if "error" in result:
            print(f"ERROR: Failed to test model {model_name}: {result.get('error')}")
            continue
        all_results.append(result)
    
    if len(all_results) < 2:
        print("\nERROR: Need at least 2 successful model tests to compare")
        return 1
    
    # Compare results
    print("\n" + "=" * 80)
    print("COMPARING RESULTS")
    print("=" * 80)
    
    if len(all_results) == 2:
        # Simple pairwise comparison
        comparison = compare_results(all_results[0], all_results[1])
        
        # Save comparison JSON
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "comparison": comparison,
                "model1_results": all_results[0],
                "model2_results": all_results[1],
            }, f, indent=2, ensure_ascii=False)
        print(f"\nSaved comparison JSON to {output_path}")
        
        # Generate report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        generate_comparison_report(comparison, report_path)
        print(f"Saved comparison report to {report_path}")
    else:
        # Multi-model comparison
        comparison = compare_multiple_models(all_results)
        
        # Save comparison JSON
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "comparison": comparison,
                "model_results": all_results,
            }, f, indent=2, ensure_ascii=False)
        print(f"\nSaved comparison JSON to {output_path}")
        
        # Generate multi-model report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        generate_multi_model_report(comparison, all_results, report_path)
        print(f"Saved comparison report to {report_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
