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
    """Generate comprehensive test questions covering all models, features, and edge cases."""
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
    
    # Synonym expansion tests (15 questions) - Test query expansion features
    synonym_questions = [
        {"question": "How many runs for program test", "expected_model": "ProgramStatistics", "expected_column": "usage_count", "category": "synonym_expansion"},
        {"question": "Number of executions for forest fire", "expected_model": "ProgramStatistics", "expected_column": "usage_count", "category": "synonym_expansion"},
        {"question": "Total times program was executed", "expected_model": "ProgramStatistics", "expected_column": "usage_count", "category": "synonym_expansion"},
        {"question": "Count of program runs", "expected_model": "ProgramStatistics", "expected_column": "usage_count", "category": "synonym_expansion"},
        {"question": "Programs that succeeded", "expected_model": "ProgramStatistics", "expected_column": "success_count", "category": "synonym_expansion"},
        {"question": "Programs that failed", "expected_model": "ProgramStatistics", "expected_column": "failure_count", "category": "synonym_expansion"},
        {"question": "Mean execution duration", "expected_model": "ProgramStatistics", "expected_column": "avg_execution_time", "category": "synonym_expansion"},
        {"question": "Average memory consumption", "expected_model": "ProgramStatistics", "expected_column": "avg_memory_usage", "category": "synonym_expansion"},
        {"question": "Programs that are active", "expected_model": "Simulation", "expected_column": "status", "category": "synonym_expansion"},
        {"question": "Finished simulations", "expected_model": "Simulation", "expected_column": "status", "category": "synonym_expansion"},
        {"question": "Simulations that are done", "expected_model": "Simulation", "expected_column": "status", "category": "synonym_expansion"},
        {"question": "Experiments modified recently", "expected_model": "Experiment", "expected_column": "updated_at", "category": "synonym_expansion"},
        {"question": "Research projects created last month", "expected_model": "Research", "expected_column": "created_at", "category": "synonym_expansion"},
        {"question": "Programs last used in the past week", "expected_model": "ProgramStatistics", "expected_column": "last_used_at", "category": "synonym_expansion"},
        {"question": "Experiments started since 2024", "expected_model": "Experiment", "expected_column": "started_at", "category": "synonym_expansion"},
    ]
    questions.extend(synonym_questions)
    
    # Join hints and relationship queries (15 questions) - Test relationship/join detection
    relationship_questions = [
        {"question": "Which experiments belong to a research project", "expected_model": "Experiment", "expected_column": "research_id", "category": "relationship"},
        {"question": "Simulations linked to an experiment", "expected_model": "Simulation", "expected_column": "experiment_id", "category": "relationship"},
        {"question": "Program variants for a program", "expected_model": "ProgramVariant", "expected_column": "program_id", "category": "relationship"},
        {"question": "Statistics for a specific program", "expected_model": "ProgramStatistics", "expected_column": "program_id", "category": "relationship"},
        {"question": "Executions for a program variant", "expected_model": "ProgramExecution", "expected_column": "variant_id", "category": "relationship"},
        {"question": "Research questions for a research project", "expected_model": "ResearchQuestion", "expected_column": "research_id", "category": "relationship"},
        {"question": "Notes attached to a research project", "expected_model": "Note", "expected_column": "research_id", "category": "relationship"},
        {"question": "Notes attached to an experiment", "expected_model": "Note", "expected_column": "experiment_id", "category": "relationship"},
        {"question": "Simulation configuration for a simulation", "expected_model": "SimulationConfig", "expected_column": "simulation_id", "category": "relationship"},
        {"question": "Metrics for a specific simulation", "expected_model": "SimulationMetrics", "expected_column": "simulation_id", "category": "relationship"},
        {"question": "Agent snapshots for a simulation", "expected_model": "AgentSnapshot", "expected_column": "simulation_id", "category": "relationship"},
        {"question": "Agent introspection for a simulation", "expected_model": "AgentIntrospection", "expected_column": "simulation_id", "category": "relationship"},
        {"question": "Agent lineage for a simulation", "expected_model": "AgentLineage", "expected_column": "simulation_id", "category": "relationship"},
        {"question": "Chat messages for a simulation", "expected_model": "ChatMessage", "expected_column": "simulation_id", "category": "relationship"},
        {"question": "Experiment simulations linking experiments to simulations", "expected_model": "ExperimentSimulation", "expected_column": "experiment_id", "category": "relationship"},
    ]
    questions.extend(relationship_questions)
    
    # Query recipe and complex pattern tests (15 questions) - Test recipe matching
    recipe_questions = [
        {"question": "Success count for program named forest fire", "expected_model": "ProgramStatistics", "expected_column": "success_count", "category": "query_recipe"},
        {"question": "Failure count for program forest fire", "expected_model": "ProgramStatistics", "expected_column": "failure_count", "category": "query_recipe"},
        {"question": "How many times was program forest fire executed", "expected_model": "ProgramStatistics", "expected_column": "usage_count", "category": "query_recipe"},
        {"question": "Average execution time for program forest fire", "expected_model": "ProgramStatistics", "expected_column": "avg_execution_time", "category": "query_recipe"},
        {"question": "Programs with success count greater than 100", "expected_model": "ProgramStatistics", "expected_column": "success_count", "category": "query_recipe"},
        {"question": "Programs with failure count less than 10", "expected_model": "ProgramStatistics", "expected_column": "failure_count", "category": "query_recipe"},
        {"question": "Simulations that are currently running", "expected_model": "Simulation", "expected_column": "status", "category": "query_recipe"},
        {"question": "Simulations that have completed", "expected_model": "Simulation", "expected_column": "status", "category": "query_recipe"},
        {"question": "Experiments with status completed", "expected_model": "Experiment", "expected_column": "status", "category": "query_recipe"},
        {"question": "Research projects with active status", "expected_model": "Research", "expected_column": "status", "category": "query_recipe"},
        {"question": "Simulations started in the last 7 days", "expected_model": "Simulation", "expected_column": "started_at", "category": "query_recipe"},
        {"question": "Experiments created in 2024", "expected_model": "Experiment", "expected_column": "created_at", "category": "query_recipe"},
        {"question": "Programs last used in the past month", "expected_model": "ProgramStatistics", "expected_column": "last_used_at", "category": "query_recipe"},
        {"question": "Research projects updated recently", "expected_model": "Research", "expected_column": "updated_at", "category": "query_recipe"},
        {"question": "Program executions that succeeded", "expected_model": "ProgramExecution", "expected_column": "success", "category": "query_recipe"},
    ]
    questions.extend(recipe_questions)
    
    # Ambiguity detection tests (5 questions) - Test variant_id handling
    ambiguity_questions = [
        {"question": "Program statistics with variant information", "expected_model": "ProgramStatistics", "expected_column": "variant_id", "category": "ambiguity"},
        {"question": "Statistics for program variants", "expected_model": "ProgramStatistics", "expected_column": "variant_id", "category": "ambiguity"},
        {"question": "Program statistics that include variant data", "expected_model": "ProgramStatistics", "expected_column": "variant_id", "category": "ambiguity"},
        {"question": "Variant-specific program statistics", "expected_model": "ProgramStatistics", "expected_column": "variant_id", "category": "ambiguity"},
        {"question": "Program statistics aggregated by variant", "expected_model": "ProgramStatistics", "expected_column": "variant_id", "category": "ambiguity"},
    ]
    questions.extend(ambiguity_questions)
    
    # Entity extraction edge cases (15 questions) - Complex temporal, numeric, and entity queries
    entity_questions = [
        {"question": "Programs created after 2023", "expected_model": "Program", "expected_column": "created_at", "category": "entity_extraction"},
        {"question": "Programs created before 2025", "expected_model": "Program", "expected_column": "created_at", "category": "entity_extraction"},
        {"question": "Simulations started during 2024", "expected_model": "Simulation", "expected_column": "started_at", "category": "entity_extraction"},
        {"question": "Experiments completed in the last 30 days", "expected_model": "Experiment", "expected_column": "completed_at", "category": "entity_extraction"},
        {"question": "Programs with more than 50 successes", "expected_model": "ProgramStatistics", "expected_column": "success_count", "category": "entity_extraction"},
        {"question": "Programs with fewer than 5 failures", "expected_model": "ProgramStatistics", "expected_column": "failure_count", "category": "entity_extraction"},
        {"question": "Programs with usage count over 1000", "expected_model": "ProgramStatistics", "expected_column": "usage_count", "category": "entity_extraction"},
        {"question": "Simulations with total steps greater than 1000", "expected_model": "Simulation", "expected_column": "total_steps", "category": "entity_extraction"},
        {"question": "Experiments with target iterations above 10", "expected_model": "Experiment", "expected_column": "target_iterations", "category": "entity_extraction"},
        {"question": "Experiments with completed iterations below 5", "expected_model": "Experiment", "expected_column": "completed_iterations", "category": "entity_extraction"},
        {"question": "Agent lineage with birth step after 100", "expected_model": "AgentLineage", "expected_column": "birth_step", "category": "entity_extraction"},
        {"question": "Agent lineage with death step before 500", "expected_model": "AgentLineage", "expected_column": "death_step", "category": "entity_extraction"},
        {"question": "Simulations with current step greater than 50", "expected_model": "Simulation", "expected_column": "current_step", "category": "entity_extraction"},
        {"question": "Research questions with priority higher than 5", "expected_model": "ResearchQuestion", "expected_column": "priority", "category": "entity_extraction"},
        {"question": "Local LLM runs with accuracy above 0.9", "expected_model": "LocalLLMDecisionRun", "expected_column": "accuracy", "category": "entity_extraction"},
    ]
    questions.extend(entity_questions)
    
    # Missing columns and advanced features (20 questions) - Cover important columns not yet tested
    advanced_questions = [
        {"question": "Program inline code", "expected_model": "Program", "expected_column": "inline_code", "category": "advanced"},
        {"question": "Program script file path", "expected_model": "Program", "expected_column": "script_file", "category": "advanced"},
        {"question": "Program output schema", "expected_model": "Program", "expected_column": "output_schema", "category": "advanced"},
        {"question": "Program post processing config", "expected_model": "Program", "expected_column": "post_processing_config", "category": "advanced"},
        {"question": "Program variant parameter overrides", "expected_model": "ProgramVariant", "expected_column": "parameter_overrides", "category": "advanced"},
        {"question": "Program variant code overrides", "expected_model": "ProgramVariant", "expected_column": "code_overrides", "category": "advanced"},
        {"question": "Program statistics output metrics", "expected_model": "ProgramStatistics", "expected_column": "output_metrics", "category": "advanced"},
        {"question": "Program statistics parameter stats", "expected_model": "ProgramStatistics", "expected_column": "parameter_stats", "category": "advanced"},
        {"question": "Program execution output data", "expected_model": "ProgramExecution", "expected_column": "output_data", "category": "advanced"},
        {"question": "Program execution post processed output", "expected_model": "ProgramExecution", "expected_column": "post_processed_output", "category": "advanced"},
        {"question": "Program execution error message", "expected_model": "ProgramExecution", "expected_column": "error_message", "category": "advanced"},
        {"question": "Simulation config template version", "expected_model": "SimulationConfig", "expected_column": "template_version", "category": "advanced"},
        {"question": "Simulation metrics timestamp", "expected_model": "SimulationMetrics", "expected_column": "timestamp", "category": "advanced"},
        {"question": "Agent snapshot timestamp", "expected_model": "AgentSnapshot", "expected_column": "timestamp", "category": "advanced"},
        {"question": "Agent introspection position x", "expected_model": "AgentIntrospection", "expected_column": "position_x", "category": "advanced"},
        {"question": "Agent introspection position y", "expected_model": "AgentIntrospection", "expected_column": "position_y", "category": "advanced"},
        {"question": "Agent introspection age", "expected_model": "AgentIntrospection", "expected_column": "age", "category": "advanced"},
        {"question": "Agent introspection policy state", "expected_model": "AgentIntrospection", "expected_column": "policy_state", "category": "advanced"},
        {"question": "Agent introspection attention", "expected_model": "AgentIntrospection", "expected_column": "attention", "category": "advanced"},
        {"question": "Agent lineage metabolism rate", "expected_model": "AgentLineage", "expected_column": "metabolism_rate", "category": "advanced"},
    ]
    questions.extend(advanced_questions)
    
    # Additional missing columns (15 questions)
    additional_questions = [
        {"question": "Agent lineage max health", "expected_model": "AgentLineage", "expected_column": "max_health", "category": "additional"},
        {"question": "Agent lineage max resources", "expected_model": "AgentLineage", "expected_column": "max_resources", "category": "additional"},
        {"question": "Experiment description", "expected_model": "Experiment", "expected_column": "description", "category": "additional"},
        {"question": "Experiment hypothesis", "expected_model": "Experiment", "expected_column": "hypothesis", "category": "additional"},
        {"question": "Experiment parameter variations", "expected_model": "Experiment", "expected_column": "parameter_variations", "category": "additional"},
        {"question": "Experiment tags", "expected_model": "Experiment", "expected_column": "tags", "category": "additional"},
        {"question": "Experiment notes", "expected_model": "Experiment", "expected_column": "notes", "category": "additional"},
        {"question": "Research sub name", "expected_model": "Research", "expected_column": "sub_name", "category": "additional"},
        {"question": "Research session id", "expected_model": "Research", "expected_column": "session_id", "category": "additional"},
        {"question": "Research question details", "expected_model": "ResearchQuestion", "expected_column": "details", "category": "additional"},
        {"question": "Research question tags", "expected_model": "ResearchQuestion", "expected_column": "tags", "category": "additional"},
        {"question": "Research flow session form data", "expected_model": "ResearchFlowSession", "expected_column": "form_data", "category": "additional"},
        {"question": "Research flow session state metadata", "expected_model": "ResearchFlowSession", "expected_column": "state_metadata", "category": "additional"},
        {"question": "Research flow session history", "expected_model": "ResearchFlowSession", "expected_column": "history", "category": "additional"},
        {"question": "Research flow session summary", "expected_model": "ResearchFlowSession", "expected_column": "summary", "category": "additional"},
    ]
    questions.extend(additional_questions)
    
    # Assistant and telemetry advanced features (15 questions)
    assistant_questions = [
        {"question": "Assistant rating message id", "expected_model": "AssistantRating", "expected_column": "message_id", "category": "assistant"},
        {"question": "Assistant rating simulation id", "expected_model": "AssistantRating", "expected_column": "simulation_id", "category": "assistant"},
        {"question": "Assistant studio trace system prompt", "expected_model": "AssistantStudioTrace", "expected_column": "system_prompt", "category": "assistant"},
        {"question": "Assistant studio trace context snapshot", "expected_model": "AssistantStudioTrace", "expected_column": "context_snapshot", "category": "assistant"},
        {"question": "Assistant studio trace timings", "expected_model": "AssistantStudioTrace", "expected_column": "timings_ms", "category": "assistant"},
        {"question": "Assistant studio trace validation", "expected_model": "AssistantStudioTrace", "expected_column": "validation", "category": "assistant"},
        {"question": "Assistant studio trace metadata", "expected_model": "AssistantStudioTrace", "expected_column": "trace_metadata", "category": "assistant"},
        {"question": "Chat message experiment id", "expected_model": "ChatMessage", "expected_column": "experiment_id", "category": "assistant"},
        {"question": "Tool telemetry start timestamp", "expected_model": "ToolTelemetryEvent", "expected_column": "start_timestamp", "category": "assistant"},
        {"question": "Tool telemetry end timestamp", "expected_model": "ToolTelemetryEvent", "expected_column": "end_timestamp", "category": "assistant"},
        {"question": "Tool telemetry experiment id", "expected_model": "ToolTelemetryEvent", "expected_column": "experiment_id", "category": "assistant"},
        {"question": "User session api key id", "expected_model": "UserSession", "expected_column": "api_key_id", "category": "assistant"},
        {"question": "User session expires at", "expected_model": "UserSession", "expected_column": "expires_at", "category": "assistant"},
        {"question": "User research event title", "expected_model": "UserResearchEvent", "expected_column": "title", "category": "assistant"},
        {"question": "User research event body", "expected_model": "UserResearchEvent", "expected_column": "body", "category": "assistant"},
    ]
    questions.extend(assistant_questions)
    
    # Local LLM and metric definition advanced (10 questions)
    llm_metric_questions = [
        {"question": "Local LLM decision run error", "expected_model": "LocalLLMDecisionRun", "expected_column": "error", "category": "llm_metric"},
        {"question": "Local LLM decision run base url", "expected_model": "LocalLLMDecisionRun", "expected_column": "base_url", "category": "llm_metric"},
        {"question": "Local LLM decision run model", "expected_model": "LocalLLMDecisionRun", "expected_column": "model", "category": "llm_metric"},
        {"question": "Local LLM decision run throughput", "expected_model": "LocalLLMDecisionRun", "expected_column": "throughput_total", "category": "llm_metric"},
        {"question": "Metric definition description", "expected_model": "MetricDefinition", "expected_column": "description", "category": "llm_metric"},
        {"question": "Metric definition color scheme", "expected_model": "MetricDefinition", "expected_column": "color_scheme", "category": "llm_metric"},
        {"question": "Metric definition unit", "expected_model": "MetricDefinition", "expected_column": "unit", "category": "llm_metric"},
        {"question": "Metric definition icon", "expected_model": "MetricDefinition", "expected_column": "icon", "category": "llm_metric"},
        {"question": "Metric definition priority", "expected_model": "MetricDefinition", "expected_column": "priority", "category": "llm_metric"},
        {"question": "Metric definition threshold", "expected_model": "MetricDefinition", "expected_column": "threshold", "category": "llm_metric"},
    ]
    questions.extend(llm_metric_questions)
    
    # Add IDs to questions
    for i, q in enumerate(questions, 1):
        q["id"] = i
        if "category" not in q:
            q["category"] = "general"
    
    return questions


def evaluate_result(question: Dict[str, Any], result) -> Dict[str, Any]:
    """Evaluate a single query result."""
    evaluation = {
        "question_id": question["id"],
        "question": question["question"],
        "category": question.get("category", "general"),
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
        "num_ambiguities": len(result.ambiguities),
        "has_join_hints": len(result.join_hints) > 0,
        "has_recipes": len(result.recipes) > 0,
        "has_ambiguities": len(result.ambiguities) > 0,
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
    avg_join_hints = sum(r.get("num_join_hints", 0) for r in results) / total if total > 0 else 0
    avg_recipes = sum(r.get("num_recipes", 0) for r in results) / total if total > 0 else 0
    avg_ambiguities = sum(r.get("num_ambiguities", 0) for r in results) / total if total > 0 else 0
    avg_score = sum(r.get("top_score", 0) or 0 for r in results) / successful if successful > 0 else 0
    
    # Category-based statistics
    categories = {}
    for r in results:
        cat = r.get("category", "general")
        if cat not in categories:
            categories[cat] = {"total": 0, "found_expected": 0, "found_model": 0, "found_column": 0}
        categories[cat]["total"] += 1
        if r.get("found_expected", False):
            categories[cat]["found_expected"] += 1
        if r.get("found_model", False):
            categories[cat]["found_model"] += 1
        if r.get("found_column", False):
            categories[cat]["found_column"] += 1
    
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
        "average_join_hints": avg_join_hints,
        "average_recipes": avg_recipes,
        "average_ambiguities": avg_ambiguities,
        "average_top_score": avg_score,
        "category_statistics": {
            cat: {
                "total": stats["total"],
                "found_expected": stats["found_expected"],
                "found_expected_rate": stats["found_expected"] / stats["total"] if stats["total"] > 0 else 0,
                "found_model": stats["found_model"],
                "found_model_rate": stats["found_model"] / stats["total"] if stats["total"] > 0 else 0,
                "found_column": stats["found_column"],
                "found_column_rate": stats["found_column"] / stats["total"] if stats["total"] > 0 else 0,
            }
            for cat, stats in categories.items()
        },
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
    print(f"\nRetrieval Metrics:")
    print(f"  Average docs returned: {avg_docs:.2f}")
    print(f"  Average schema refs: {avg_schema_refs:.2f}")
    print(f"  Average join hints: {avg_join_hints:.2f}")
    print(f"  Average recipes: {avg_recipes:.2f}")
    print(f"  Average ambiguities: {avg_ambiguities:.2f}")
    print(f"  Average top score: {avg_score:.4f}")
    
    print(f"\nCategory Performance:")
    for cat, stats in sorted(categories.items()):
        total_cat = stats["total"]
        found_exp = stats["found_expected"]
        found_mod = stats["found_model"]
        found_col = stats["found_column"]
        print(f"  {cat}:")
        print(f"    Total: {total_cat}")
        print(f"    Model+Column: {found_exp}/{total_cat} ({found_exp/total_cat*100:.1f}%)")
        print(f"    Model: {found_mod}/{total_cat} ({found_mod/total_cat*100:.1f}%)")
        print(f"    Column: {found_col}/{total_cat} ({found_col/total_cat*100:.1f}%)")
    
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
