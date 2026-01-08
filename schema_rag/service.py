"""Schema-aware RAG service for retrieving database schema information.

This service uses FAISS to retrieve relevant schema documents (models, columns, recipes)
based on natural language questions, enabling agents to ground responses in the database schema.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import faiss
    from sentence_transformers import SentenceTransformer
except ImportError:
    faiss = None
    SentenceTransformer = None

logger = logging.getLogger(__name__)


@dataclass
class GroundingResult:
    """Result of schema grounding retrieval."""
    
    docs: List[Dict[str, Any]]  # Retrieved documents with scores
    schema_refs: List[Dict[str, Any]]  # Normalized schema references
    join_hints: List[str]  # Join path strings
    recipes: List[Dict[str, Any]]  # Query recipe matches
    ambiguities: List[str]  # Semantic notes (e.g., variant_id handling)


class SchemaRagService:
    """Service for retrieving schema grounding using FAISS vector search."""
    
    def __init__(self, index_path: Path) -> None:
        """Initialize the schema RAG service.
        
        Args:
            index_path: Path to directory containing faiss.index, docs.jsonl, and config.json
        """
        if faiss is None or SentenceTransformer is None:
            raise ImportError(
                "Required dependencies missing. Install: pip install faiss-cpu sentence-transformers"
            )
        
        self.index_path = Path(index_path)
        self._index: Optional[faiss.Index] = None
        self._documents: List[Dict[str, Any]] = []
        self._model: Optional[SentenceTransformer] = None
        self._config: Optional[Dict[str, Any]] = None
        
        self._load_index()
    
    def _load_index(self) -> None:
        """Load FAISS index and documents."""
        index_file = self.index_path / "faiss.index"
        docs_file = self.index_path / "docs.jsonl"
        config_file = self.index_path / "config.json"
        
        if not index_file.exists():
            raise FileNotFoundError(f"FAISS index not found: {index_file}")
        if not docs_file.exists():
            raise FileNotFoundError(f"Documents file not found: {docs_file}")
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        # Load config
        with open(config_file, "r", encoding="utf-8") as f:
            self._config = json.load(f)
        
        model_name = self._config.get("model_name", "all-MiniLM-L6-v2")
        
        # Load embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self._model = SentenceTransformer(model_name)
        
        # Load documents
        logger.info(f"Loading documents from {docs_file}")
        with open(docs_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self._documents.append(json.loads(line))
        
        # Load FAISS index
        logger.info(f"Loading FAISS index from {index_file}")
        self._index = faiss.read_index(str(index_file))
        
        logger.info(
            f"Schema RAG service initialized: {len(self._documents)} documents, "
            f"index size: {self._index.ntotal}"
        )
    
    def _expand_query_synonyms(self, question: str) -> str:
        """Expand query with synonyms from dictionary."""
        synonyms_path = Path(__file__).parent / "schema_synonyms.json"
        if not synonyms_path.exists():
            return question
        
        try:
            with open(synonyms_path, "r", encoding="utf-8") as f:
                synonyms = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load schema synonyms: {e}")
            return question
        
        # Split into words and phrases
        words = question.lower().split()
        expanded = []
        
        for word in words:
            expanded.append(word)
            # Check for exact match
            if word in synonyms:
                expanded.extend(synonyms[word])
            # Check for phrase matches (2-word phrases)
            if len(expanded) >= 2:
                phrase = f"{expanded[-2]} {expanded[-1]}"
                if phrase in synonyms:
                    expanded.extend(synonyms[phrase])
        
        return " ".join(expanded)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for lexical matching."""
        # Tokenize: split on spaces, underscores, camelCase
        words = re.findall(r'[a-z]+|[A-Z][a-z]*', text.lower())
        return list(set(words))
    
    def _lexical_boost(self, doc: Dict[str, Any], query_keywords: List[str]) -> float:
        """Calculate lexical boost score for a document."""
        boost = 0.0
        
        # Check metadata keywords
        doc_keywords = doc.get("metadata", {}).get("keywords", [])
        for qkw in query_keywords:
            if qkw in doc_keywords:
                boost += 2.0  # Strong boost for keyword match
        
        # Check column/model names
        col_name = doc.get("metadata", {}).get("column", "")
        model_name = doc.get("metadata", {}).get("model", "")
        table_name = doc.get("metadata", {}).get("table", "")
        
        for qkw in query_keywords:
            if qkw in col_name.lower():
                boost += 3.0  # Very strong boost for column name match
            if qkw in model_name.lower():
                boost += 2.0
            if qkw in table_name.lower():
                boost += 1.5
        
        # Check doc text for exact matches
        doc_text = doc.get("text", "").lower()
        for qkw in query_keywords:
            if qkw in doc_text:
                boost += 0.5
        
        return boost
    
    def _extract_entities(self, question: str) -> Dict[str, Any]:
        """Extract entities from question with improved patterns."""
        entities = {}
        question_lower = question.lower()
        
        # Program name patterns - improved matching
        patterns = [
            r'(?:for|program|named)\s+([a-z\s]+?)(?:\s+program|\s|$)',
            r'program\s+([a-z\s]+?)(?:\s|$)',
            r'([a-z\s]+?)\s+program',
        ]
        for pattern in patterns:
            match = re.search(pattern, question_lower)
            if match:
                name = match.group(1).strip()
                # Filter out common stop words and very short matches
                if len(name) > 2 and name not in ["the", "a", "an", "for", "with"]:
                    entities["program_name"] = name
                    break
        
        # Date patterns (simplified for POC)
        if re.search(r'\d{4}', question):
            entities["has_date"] = True
        if re.search(r'(?:last|past|recent|since)', question_lower):
            entities["has_date"] = True
        
        # Numeric filters
        numeric_patterns = [
            r'(?:more|greater|over)\s+than\s+(\d+)',
            r'(\d+)\s+(?:or\s+)?more',
            r'(?:less|fewer|under)\s+than\s+(\d+)',
            r'(\d+)\s+(?:or\s+)?less',
        ]
        for pattern in numeric_patterns:
            match = re.search(pattern, question_lower)
            if match:
                value = int(match.group(1))
                if "more" in pattern or "greater" in pattern or "over" in pattern:
                    entities["min_value"] = value
                elif "less" in pattern or "fewer" in pattern or "under" in pattern:
                    entities["max_value"] = value
                break
        
        # Comparison operators
        if re.search(r'(?:greater|more|higher|above)\s+than', question_lower):
            entities["comparison"] = ">"
        elif re.search(r'(?:less|fewer|lower|below)\s+than', question_lower):
            entities["comparison"] = "<"
        elif re.search(r'(?:equal|same|exactly)', question_lower):
            entities["comparison"] = "="
        
        return entities
    
    def _boost_by_entities(self, docs: List[Dict[str, Any]], entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Boost documents based on extracted entities."""
        if not entities:
            return docs
        
        boosted_docs = []
        for doc in docs:
            boost = 0.0
            metadata = doc.get("metadata", {})
            
            # Boost if program name matches
            if "program_name" in entities:
                program_name = entities["program_name"]
                # Check if document is related to programs
                if "program" in doc.get("text", "").lower():
                    boost += 2.0
                # Check if document mentions the specific program name
                if program_name in doc.get("text", "").lower():
                    boost += 3.0
            
            # Boost date-related columns if date entities present
            if entities.get("has_date"):
                col_name = metadata.get("column", "").lower()
                if any(term in col_name for term in ["date", "time", "at", "created", "updated"]):
                    boost += 1.5
            
            # Boost numeric columns if numeric filters present
            if "min_value" in entities or "max_value" in entities:
                col_name = metadata.get("column", "").lower()
                if any(term in col_name for term in ["count", "total", "sum", "avg", "average"]):
                    boost += 1.0
            
            if boost > 0:
                doc = doc.copy()
                doc["score"] = doc.get("score", 0.0) + boost
                doc["entity_boost"] = boost
            
            boosted_docs.append(doc)
        
        return boosted_docs
    
    def retrieve_grounding(self, question: str, top_k: int = 5) -> GroundingResult:
        """Retrieve schema grounding for a question.
        
        Args:
            question: Natural language question
            top_k: Number of documents to retrieve
            
        Returns:
            GroundingResult with retrieved documents, schema refs, join hints, etc.
        """
        if self._index is None or self._model is None:
            raise RuntimeError("Schema RAG service not initialized")
        
        # Expand query with synonyms
        expanded_question = self._expand_query_synonyms(question)
        logger.debug(f"Query expansion: {question} -> {expanded_question}")
        
        # Extract entities
        entities = self._extract_entities(question)
        logger.debug(f"Extracted entities: {entities}")
        
        # Generate query embedding (use expanded query for better semantic matching)
        query_embedding = self._model.encode([expanded_question], convert_to_numpy=True)
        
        # FAISS search
        k = min(top_k * 2, self._index.ntotal)  # Retrieve more for re-ranking
        distances, indices = self._index.search(query_embedding, k)
        
        # Extract keywords for lexical boosting
        query_keywords = self._extract_keywords(question)
        
        # Re-rank with hybrid scoring
        scored_docs = []
        for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
            if idx >= len(self._documents):
                continue
            
            doc = self._documents[idx].copy()
            vector_score = 1.0 / (1.0 + distance)  # Convert distance to similarity
            
            # Apply lexical boost
            lexical_boost = self._lexical_boost(doc, query_keywords)
            final_score = vector_score + lexical_boost
            
            doc["score"] = float(final_score)
            doc["vector_score"] = float(vector_score)
            doc["lexical_boost"] = float(lexical_boost)
            scored_docs.append(doc)
        
        # Apply entity-based boosting
        scored_docs = self._boost_by_entities(scored_docs, entities)
        
        # Sort by final score and take top-k
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        top_docs = scored_docs[:top_k]
        
        # Extract schema references, join hints, recipes, ambiguities
        schema_refs = []
        join_hints = []
        recipes = []
        ambiguities = []
        
        for doc in top_docs:
            metadata = doc.get("metadata", {})
            doc_type = doc.get("doc_type", "")
            
            if doc_type == "schema_column":
                schema_refs.append({
                    "model": metadata.get("model"),
                    "table": metadata.get("table"),
                    "column": metadata.get("column"),
                    "source_file": metadata.get("source_file"),
                })
            
            if doc_type == "query_recipe":
                recipes.append({
                    "id": doc.get("id"),
                    "text": doc.get("text"),
                    "join_hints": metadata.get("join_hints", []),
                })
                join_hints.extend(metadata.get("join_hints", []))
            
            # Extract join hints from any document
            if "join_hints" in metadata:
                join_hints.extend(metadata["join_hints"])
            
            # Check for ambiguities
            semantics = metadata.get("semantics")
            if semantics:
                ambiguities.append(semantics)
        
        # Deduplicate join hints
        join_hints = list(dict.fromkeys(join_hints))
        
        return GroundingResult(
            docs=top_docs,
            schema_refs=schema_refs,
            join_hints=join_hints,
            recipes=recipes,
            ambiguities=ambiguities,
        )
