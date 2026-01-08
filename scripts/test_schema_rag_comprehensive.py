#!/usr/bin/env python3
"""Comprehensive test suite for Schema RAG.

Generates 100 natural language questions based on the SQLAlchemy models,
runs them through the SchemaRagService, and evaluates the results.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add schema_rag to path
schema_rag_path = Path(__file__).parent.parent
sys.path.insert(0, str(schema_rag_path))

from schema_rag import SchemaRagService


def generate_test_questions() -> List[Dict[str, Any]]:
    """Generate 100 test questions based on the models."""
    questions = []
    
    # Program-related questions (20 questions)
    program_questions = [
        {"question": "What is the success count for the forest fire program", "expected_model": "ProgramStatistics", "expected_column": "success_count"},
        {"question": "How many failures for program forest fire", "expected_model": "ProgramStatistics", "expected_column": "failure_count"},
        {"question": "How many times was forest fire run", "expected_model": "ProgramStatistics", "expected_column": "usage_count"},
        {"question": "Average execution time for forest fire program", "expected_model": "ProgramStatistics", "expected_column": "avg_execution_time"},
        {"question": "What programs have more than 100 successes", "expected_model": "ProgramStatistics", "expected_column": "success_count"},
        {"question": "Show me programs with less than 10 failures", "expected_model": "ProgramStatistics", "expected_column": "failure_count"},
        {"question": "Which program has the highest usage count", "expected_model": "ProgramStatistics", "expected_column": "usage_count"},
        {"question": "Memory usage for program execution", "expected_model": "ProgramExecution", "expected_column": "memory_usage"},
        {"question": "Execution time for program runs", "expected_model": "ProgramExecution", "expected_column": "execution_time"},
        {"question": "Failed program executions", "expected_model": "ProgramExecution", "expected_column": "success"},
        {"question": "Program variants for a specific program", "expected_model": "ProgramVariant", "expected_column": "name"},
        {"question": "List all program names", "expected_model": "Program", "expected_column": "name"},
        {"question": "Program descriptions", "expected_model": "Program", "expected_column": "description"},
        {"question": "Programs created in 2024", "expected_model": "Program", "expected_column": "created_at"},
        {"question": "Program categories", "expected_model": "Program", "expected_column": "category"},
        {"question": "Success rate for programs", "expected_model": "ProgramStatistics", "expected_column": "success_count"},
        {"question": "Program execution history", "expected_model": "ProgramExecution", "expected_column": "executed_at"},
        {"question": "Programs with variants", "expected_model": "ProgramVariant", "expected_column": "program_id"},
        {"question": "Average memory usage across all programs", "expected_model": "ProgramStatistics", "expected_column": "avg_memory_usage"},
        {"question": "Programs last used recently", "expected_model": "ProgramStatistics", "expected_column": "last_used_at"},
    ]
    questions.extend(program_questions)
    
    # Simulation-related questions (20 questions)
    simulation_questions = [
        {"question": "How many simulations are running", "expected_model": "Simulation", "expected_column": "status"},
        {"question": "Simulation names and descriptions", "expected_model": "Simulation", "expected_column": "name"},
        {"question": "Total steps for a simulation", "expected_model": "Simulation", "expected_column": "total_steps"},
        {"question": "Final population of simulations", "expected_model": "Simulation", "expected_column": "final_population"},
        {"question": "Simulations started in the last week", "expected_model": "Simulation", "expected_column": "started_at"},
        {"question": "Completed simulations", "expected_model": "Simulation", "expected_column": "status"},
        {"question": "Simulation configuration parameters", "expected_model": "SimulationConfig", "expected_column": "parameters"},
        {"question": "Simulation template names", "expected_model": "SimulationConfig", "expected_column": "template_name"},
        {"question": "Metrics for simulation step 100", "expected_model": "SimulationMetrics", "expected_column": "metrics"},
        {"question": "Simulation metrics by step", "expected_model": "SimulationMetrics", "expected_column": "step"},
        {"question": "Agent snapshots at step 50", "expected_model": "AgentSnapshot", "expected_column": "agent_data"},
        {"question": "Agent positions in simulation", "expected_model": "AgentSnapshot", "expected_column": "agent_data"},
        {"question": "Agent introspection data", "expected_model": "AgentIntrospection", "expected_column": "memory_state"},
        {"question": "Agent health values", "expected_model": "AgentIntrospection", "expected_column": "health"},
        {"question": "Agent resources", "expected_model": "AgentIntrospection", "expected_column": "resources"},
        {"question": "Agent lineage parent relationships", "expected_model": "AgentLineage", "expected_column": "parent_id"},
        {"question": "Agent birth steps", "expected_model": "AgentLineage", "expected_column": "birth_step"},
        {"question": "Agent death steps", "expected_model": "AgentLineage", "expected_column": "death_step"},
        {"question": "Agent mutations", "expected_model": "AgentLineage", "expected_column": "mutations"},
        {"question": "Simulation current step", "expected_model": "Simulation", "expected_column": "current_step"},
    ]
    questions.extend(simulation_questions)
    
    # Experiment-related questions (15 questions)
    experiment_questions = [
        {"question": "Experiment names and hypotheses", "expected_model": "Experiment", "expected_column": "name"},
        {"question": "Experiments with status completed", "expected_model": "Experiment", "expected_column": "status"},
        {"question": "Experiment base parameters", "expected_model": "Experiment", "expected_column": "base_parameters"},
        {"question": "Target iterations for experiments", "expected_model": "Experiment", "expected_column": "target_iterations"},
        {"question": "Completed iterations count", "expected_model": "Experiment", "expected_column": "completed_iterations"},
        {"question": "Experiment success criteria", "expected_model": "Experiment", "expected_column": "success_criteria"},
        {"question": "Experiment results summary", "expected_model": "Experiment", "expected_column": "results_summary"},
        {"question": "Experiments started at timestamp", "expected_model": "Experiment", "expected_column": "started_at"},
        {"question": "Experiments completed at timestamp", "expected_model": "Experiment", "expected_column": "completed_at"},
        {"question": "Experiment simulation links", "expected_model": "ExperimentSimulation", "expected_column": "simulation_id"},
        {"question": "Experiment iteration numbers", "expected_model": "ExperimentSimulation", "expected_column": "iteration"},
        {"question": "Parameter overrides for experiment simulations", "expected_model": "ExperimentSimulation", "expected_column": "parameters_override"},
        {"question": "Experiments linked to research", "expected_model": "Experiment", "expected_column": "research_id"},
        {"question": "Experiment assumptions", "expected_model": "Experiment", "expected_column": "assumptions"},
        {"question": "Experiment metrics list", "expected_model": "Experiment", "expected_column": "metrics"},
    ]
    questions.extend(experiment_questions)
    
    # Research-related questions (15 questions)
    research_questions = [
        {"question": "Research project names", "expected_model": "Research", "expected_column": "name"},
        {"question": "Research descriptions", "expected_model": "Research", "expected_column": "description"},
        {"question": "Research goals", "expected_model": "Research", "expected_column": "goals"},
        {"question": "Research methodology", "expected_model": "Research", "expected_column": "methodology"},
        {"question": "Research status active", "expected_model": "Research", "expected_column": "status"},
        {"question": "Research questions prompts", "expected_model": "ResearchQuestion", "expected_column": "prompt"},
        {"question": "Research question answers", "expected_model": "ResearchQuestion", "expected_column": "answer"},
        {"question": "Research question status", "expected_model": "ResearchQuestion", "expected_column": "status"},
        {"question": "Research question priority", "expected_model": "ResearchQuestion", "expected_column": "priority"},
        {"question": "Research insights", "expected_model": "Research", "expected_column": "insights"},
        {"question": "Research tags", "expected_model": "Research", "expected_column": "tags"},
        {"question": "Research structured methodology", "expected_model": "Research", "expected_column": "methodology_structured"},
        {"question": "Research questions related experiments", "expected_model": "ResearchQuestion", "expected_column": "related_experiment_ids"},
        {"question": "Research questions related simulations", "expected_model": "ResearchQuestion", "expected_column": "related_simulation_ids"},
        {"question": "Research updated recently", "expected_model": "Research", "expected_column": "updated_at"},
    ]
    questions.extend(research_questions)
    
    # Chat and messaging questions (10 questions)
    chat_questions = [
        {"question": "Chat messages for a simulation", "expected_model": "ChatMessage", "expected_column": "content"},
        {"question": "Chat message types", "expected_model": "ChatMessage", "expected_column": "message_type"},
        {"question": "Chat messages by session", "expected_model": "ChatMessage", "expected_column": "session_id"},
        {"question": "Chat message metadata", "expected_model": "ChatMessage", "expected_column": "message_metadata"},
        {"question": "Assistant ratings for messages", "expected_model": "AssistantRating", "expected_column": "rating"},
        {"question": "Assistant rating comments", "expected_model": "AssistantRating", "expected_column": "comment"},
        {"question": "Assistant studio traces", "expected_model": "AssistantStudioTrace", "expected_column": "user_message"},
        {"question": "Assistant studio response content", "expected_model": "AssistantStudioTrace", "expected_column": "response_content"},
        {"question": "Tool calls in assistant traces", "expected_model": "AssistantStudioTrace", "expected_column": "tool_calls"},
        {"question": "Token usage in assistant traces", "expected_model": "AssistantStudioTrace", "expected_column": "token_usage"},
    ]
    questions.extend(chat_questions)
    
    # Metrics and telemetry questions (10 questions)
    metrics_questions = [
        {"question": "Metric definition keys", "expected_model": "MetricDefinition", "expected_column": "key"},
        {"question": "Metric definition labels", "expected_model": "MetricDefinition", "expected_column": "label"},
        {"question": "Metric categories", "expected_model": "MetricDefinition", "expected_column": "category"},
        {"question": "Metric format types", "expected_model": "MetricDefinition", "expected_column": "format"},
        {"question": "Metric tags", "expected_model": "MetricTag", "expected_column": "name"},
        {"question": "Tool telemetry events", "expected_model": "ToolTelemetryEvent", "expected_column": "tool_name"},
        {"question": "Tool execution duration", "expected_model": "ToolTelemetryEvent", "expected_column": "duration_ms"},
        {"question": "Tool success status", "expected_model": "ToolTelemetryEvent", "expected_column": "success"},
        {"question": "Tool error messages", "expected_model": "ToolTelemetryEvent", "expected_column": "error_message"},
        {"question": "Tool telemetry metadata", "expected_model": "ToolTelemetryEvent", "expected_column": "metadata"},
    ]
    questions.extend(metrics_questions)
    
    # User and session questions (10 questions)
    user_questions = [
        {"question": "User sessions", "expected_model": "UserSession", "expected_column": "session_id"},
        {"question": "User selected models", "expected_model": "UserSession", "expected_column": "selected_model"},
        {"question": "User research events", "expected_model": "UserResearchEvent", "expected_column": "event_type"},
        {"question": "User research event categories", "expected_model": "UserResearchEvent", "expected_column": "category"},
        {"question": "User research event importance", "expected_model": "UserResearchEvent", "expected_column": "importance"},
        {"question": "User research profiles", "expected_model": "UserResearchProfile", "expected_column": "display_name"},
        {"question": "User research interests", "expected_model": "UserResearchProfile", "expected_column": "research_interests"},
        {"question": "User short term goals", "expected_model": "UserResearchProfile", "expected_column": "short_term_goals"},
        {"question": "User long term goals", "expected_model": "UserResearchProfile", "expected_column": "long_term_goals"},
        {"question": "Research flow session state", "expected_model": "ResearchFlowSession", "expected_column": "state"},
    ]
    questions.extend(user_questions)
    
    # Notes and templates questions (10 questions)
    notes_questions = [
        {"question": "User notes content", "expected_model": "Note", "expected_column": "content"},
        {"question": "Notes for research projects", "expected_model": "Note", "expected_column": "research_id"},
        {"question": "Notes for experiments", "expected_model": "Note", "expected_column": "experiment_id"},
        {"question": "Simulation template names", "expected_model": "SimulationTemplate", "expected_column": "name"},
        {"question": "Simulation template descriptions", "expected_model": "SimulationTemplate", "expected_column": "description"},
        {"question": "Simulation template parameters", "expected_model": "SimulationTemplate", "expected_column": "parameters"},
        {"question": "Simulation template categories", "expected_model": "SimulationTemplate", "expected_column": "category"},
        {"question": "Local LLM decision run status", "expected_model": "LocalLLMDecisionRun", "expected_column": "status"},
        {"question": "Local LLM accuracy", "expected_model": "LocalLLMDecisionRun", "expected_column": "accuracy"},
        {"question": "Local LLM latency metrics", "expected_model": "LocalLLMDecisionRun", "expected_column": "latency_median_ms"},
    ]
    questions.extend(notes_questions)
    
    # Add IDs to questions
    for i, q in enumerate(questions, 1):
        q["id"] = i
        q["category"] = q.get("category", "general")
    
    return questions


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


def run_comprehensive_test(questions_file: Path, index_path: Path, output_file: Path):
    """Run comprehensive test suite."""
    print(f"Loading questions from {questions_file}...")
    with open(questions_file, "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    print(f"Loading Schema RAG service from {index_path}...")
    service = SchemaRagService(index_path)
    
    print(f"Running {len(questions)} questions...")
    results = []
    
    for i, question in enumerate(questions, 1):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(questions)}")
        
        try:
            result = service.retrieve_grounding(question["question"], top_k=5)
            evaluation = evaluate_result(question, result)
            evaluation["success"] = True
            evaluation["error"] = None
        except Exception as e:
            evaluation = {
                "question_id": question["id"],
                "question": question["question"],
                "success": False,
                "error": str(e),
            }
        
        results.append(evaluation)
    
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
    
    output_data = {
        "summary": summary,
        "results": results,
    }
    
    print(f"\nWriting results to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total questions: {total}")
    print(f"Successful queries: {successful} ({successful/total*100:.1f}%)")
    print(f"Found expected model+column: {found_expected} ({found_expected/total*100:.1f}%)")
    print(f"Found expected model: {found_model} ({found_model/total*100:.1f}%)")
    print(f"Found expected column: {found_column} ({found_column/total*100:.1f}%)")
    print(f"Average docs returned: {avg_docs:.2f}")
    print(f"Average schema refs: {avg_schema_refs:.2f}")
    print(f"Average top score: {avg_score:.4f}")
    print("=" * 80)
    
    return output_data


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Schema RAG test suite")
    parser.add_argument(
        "--questions",
        type=str,
        default="artifacts/schema_rag_test_questions.json",
        help="Path to questions JSON file",
    )
    parser.add_argument(
        "--index",
        type=str,
        default="artifacts/schema_rag_index",
        help="Path to schema RAG index directory",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/schema_rag_test_results.json",
        help="Path to output results JSON file",
    )
    parser.add_argument(
        "--generate-questions",
        action="store_true",
        help="Generate questions file and exit",
    )
    args = parser.parse_args()
    
    questions_path = Path(args.questions)
    index_path = Path(args.index)
    output_path = Path(args.output)
    
    if args.generate_questions:
        print("Generating test questions...")
        questions = generate_test_questions()
        questions_path.parent.mkdir(parents=True, exist_ok=True)
        with open(questions_path, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        print(f"✓ Generated {len(questions)} questions to {questions_path}")
        return 0
    
    if not questions_path.exists():
        print(f"Error: Questions file not found: {questions_path}")
        print("Run with --generate-questions first")
        return 1
    
    if not index_path.exists():
        print(f"Error: Index path does not exist: {index_path}")
        return 1
    
    run_comprehensive_test(questions_path, index_path, output_path)
    return 0


if __name__ == "__main__":
    exit(main())
