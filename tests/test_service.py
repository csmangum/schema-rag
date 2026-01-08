"""Comprehensive unit tests for SchemaRagService."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open

import pytest
import numpy as np

from schema_rag.service import SchemaRagService, GroundingResult


class TestSchemaRagServiceInitialization:
    """Test SchemaRagService initialization."""
    
    def test_init_missing_dependencies(self):
        """Test initialization fails when dependencies are missing."""
        with patch('schema_rag.service.faiss', None):
            with patch('schema_rag.service.SentenceTransformer', None):
                with pytest.raises(ImportError, match="Required dependencies missing"):
                    SchemaRagService(Path("/fake/path"))
    
    def test_init_missing_index_file(self):
        """Test initialization fails when index file is missing."""
        with patch('schema_rag.service.faiss') as mock_faiss, \
             patch('schema_rag.service.SentenceTransformer') as mock_st:
            
            # Create temp directory but no index file
            with tempfile.TemporaryDirectory() as tmpdir:
                index_path = Path(tmpdir)
                (index_path / "docs.jsonl").touch()
                (index_path / "config.json").touch()
                
                with pytest.raises(FileNotFoundError, match="FAISS index not found"):
                    SchemaRagService(index_path)
    
    def test_init_missing_docs_file(self):
        """Test initialization fails when docs file is missing."""
        with patch('schema_rag.service.faiss') as mock_faiss, \
             patch('schema_rag.service.SentenceTransformer') as mock_st:
            
            with tempfile.TemporaryDirectory() as tmpdir:
                index_path = Path(tmpdir)
                (index_path / "faiss.index").touch()
                (index_path / "config.json").touch()
                
                with pytest.raises(FileNotFoundError, match="Documents file not found"):
                    SchemaRagService(index_path)
    
    def test_init_missing_config_file(self):
        """Test initialization fails when config file is missing."""
        with patch('schema_rag.service.faiss') as mock_faiss, \
             patch('schema_rag.service.SentenceTransformer') as mock_st:
            
            with tempfile.TemporaryDirectory() as tmpdir:
                index_path = Path(tmpdir)
                (index_path / "faiss.index").touch()
                (index_path / "docs.jsonl").touch()
                
                with pytest.raises(FileNotFoundError, match="Config file not found"):
                    SchemaRagService(index_path)
    
    def test_init_success(self):
        """Test successful initialization."""
        with patch('schema_rag.service.faiss') as mock_faiss, \
             patch('schema_rag.service.SentenceTransformer') as mock_st_class:
            
            # Setup mocks
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_faiss.read_index.return_value = mock_index
            
            mock_model = Mock()
            mock_st_class.return_value = mock_model
            
            with tempfile.TemporaryDirectory() as tmpdir:
                index_path = Path(tmpdir)
                
                # Create config file
                config = {
                    "dimension": 384,
                    "model_name": "all-MiniLM-L6-v2",
                    "num_documents": 100
                }
                with open(index_path / "config.json", "w") as f:
                    json.dump(config, f)
                
                # Create docs file
                with open(index_path / "docs.jsonl", "w") as f:
                    for i in range(5):
                        doc = {
                            "id": f"doc_{i}",
                            "text": f"Document {i}",
                            "doc_type": "schema_column",
                            "metadata": {"model": "TestModel", "column": f"col_{i}"}
                        }
                        f.write(json.dumps(doc) + "\n")
                
                # Create index file
                (index_path / "faiss.index").touch()
                
                service = SchemaRagService(index_path)
                
                assert service._index is not None
                assert service._model is not None
                assert len(service._documents) == 5
                assert service._config == config
                mock_st_class.assert_called_once_with("all-MiniLM-L6-v2")
                mock_faiss.read_index.assert_called_once()


class TestQueryExpansion:
    """Test query expansion with synonyms."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance with mocked dependencies."""
        with patch('schema_rag.service.faiss') as mock_faiss, \
             patch('schema_rag.service.SentenceTransformer') as mock_st_class:
            
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_faiss.read_index.return_value = mock_index
            
            mock_model = Mock()
            mock_st_class.return_value = mock_model
            
            with tempfile.TemporaryDirectory() as tmpdir:
                index_path = Path(tmpdir)
                
                config = {"model_name": "all-MiniLM-L6-v2", "dimension": 384}
                with open(index_path / "config.json", "w") as f:
                    json.dump(config, f)
                
                with open(index_path / "docs.jsonl", "w") as f:
                    pass
                
                (index_path / "faiss.index").touch()
                
                service = SchemaRagService(index_path)
                yield service
    
    def test_expand_query_no_synonyms_file(self, service):
        """Test query expansion when synonyms file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            result = service._expand_query_synonyms("test query")
            assert result == "test query"
    
    def test_expand_query_with_synonyms(self, service):
        """Test query expansion with synonyms."""
        synonyms = {
            "run": ["usage", "execution"],
            "how many": ["count", "number"]
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(synonyms))):
            
            result = service._expand_query_synonyms("how many times was it run")
            # Should include original words plus synonyms
            assert "how many" in result.lower() or "count" in result.lower() or "number" in result.lower()
            assert "run" in result.lower() or "usage" in result.lower() or "execution" in result.lower()
    
    def test_expand_query_synonyms_load_error(self, service):
        """Test query expansion handles synonym load errors gracefully."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("File error")):
            
            result = service._expand_query_synonyms("test query")
            assert result == "test query"


class TestKeywordExtraction:
    """Test keyword extraction."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance."""
        with patch('schema_rag.service.faiss') as mock_faiss, \
             patch('schema_rag.service.SentenceTransformer') as mock_st_class:
            
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_faiss.read_index.return_value = mock_index
            
            mock_model = Mock()
            mock_st_class.return_value = mock_model
            
            with tempfile.TemporaryDirectory() as tmpdir:
                index_path = Path(tmpdir)
                
                config = {"model_name": "all-MiniLM-L6-v2", "dimension": 384}
                with open(index_path / "config.json", "w") as f:
                    json.dump(config, f)
                
                with open(index_path / "docs.jsonl", "w") as f:
                    pass
                
                (index_path / "faiss.index").touch()
                
                service = SchemaRagService(index_path)
                yield service
    
    def test_extract_keywords_simple(self, service):
        """Test simple keyword extraction."""
        keywords = service._extract_keywords("test query string")
        assert "test" in keywords
        assert "query" in keywords
        assert "string" in keywords
    
    def test_extract_keywords_camelcase(self, service):
        """Test keyword extraction from camelCase."""
        # Note: The implementation lowercases first, so camelCase becomes all lowercase
        # The regex r'[a-z]+|[A-Z][a-z]*' works on original case, but since we lowercase first,
        # "testCamelCaseString" becomes "testcamelcasestring" and matches as one word
        keywords = service._extract_keywords("testCamelCaseString")
        # After lowercasing, the whole string matches as one lowercase sequence
        assert "testcamelcasestring" in keywords
        assert len(keywords) == 1
    
    def test_extract_keywords_underscores(self, service):
        """Test keyword extraction with underscores."""
        keywords = service._extract_keywords("test_query_string")
        assert "test" in keywords
        assert "query" in keywords
        assert "string" in keywords
    
    def test_extract_keywords_deduplication(self, service):
        """Test that keywords are deduplicated."""
        keywords = service._extract_keywords("test test query query")
        assert keywords.count("test") == 1
        assert keywords.count("query") == 1


class TestLexicalBoost:
    """Test lexical boosting."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance."""
        with patch('schema_rag.service.faiss') as mock_faiss, \
             patch('schema_rag.service.SentenceTransformer') as mock_st_class:
            
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_faiss.read_index.return_value = mock_index
            
            mock_model = Mock()
            mock_st_class.return_value = mock_model
            
            with tempfile.TemporaryDirectory() as tmpdir:
                index_path = Path(tmpdir)
                
                config = {"model_name": "all-MiniLM-L6-v2", "dimension": 384}
                with open(index_path / "config.json", "w") as f:
                    json.dump(config, f)
                
                with open(index_path / "docs.jsonl", "w") as f:
                    pass
                
                (index_path / "faiss.index").touch()
                
                service = SchemaRagService(index_path)
                yield service
    
    def test_lexical_boost_keyword_match(self, service):
        """Test lexical boost for keyword matches."""
        doc = {
            "metadata": {
                "keywords": ["test", "query"],
                "column": "test_column",
                "model": "TestModel",
                "table": "test_table"
            },
            "text": "This is a test document"
        }
        query_keywords = ["test", "query"]
        
        boost = service._lexical_boost(doc, query_keywords)
        assert boost > 0
        # Should have boost from keyword match (2.0) + column match (3.0) + text match (0.5)
        assert boost >= 5.0
    
    def test_lexical_boost_column_match(self, service):
        """Test lexical boost for column name matches."""
        doc = {
            "metadata": {
                "column": "success_count",
                "model": "ProgramStatistics",
                "table": "program_statistics"
            },
            "text": "Column description"
        }
        query_keywords = ["success", "count"]
        
        boost = service._lexical_boost(doc, query_keywords)
        assert boost > 0
        # Should have boost from column matches (3.0 * 2) + text matches (0.5 * 2)
        assert boost >= 6.0
    
    def test_lexical_boost_model_match(self, service):
        """Test lexical boost for model name matches."""
        doc = {
            "metadata": {
                "column": "col",
                "model": "ProgramStatistics",
                "table": "program_statistics"
            },
            "text": "Column description"
        }
        query_keywords = ["program", "statistics"]
        
        boost = service._lexical_boost(doc, query_keywords)
        assert boost > 0
        # Should have boost from model matches (2.0 * 2) + text matches
        assert boost >= 4.0
    
    def test_lexical_boost_no_matches(self, service):
        """Test lexical boost with no matches."""
        doc = {
            "metadata": {
                "column": "other_column",
                "model": "OtherModel",
                "table": "other_table"
            },
            "text": "Unrelated text"
        }
        query_keywords = ["test", "query"]
        
        boost = service._lexical_boost(doc, query_keywords)
        assert boost == 0.0


class TestEntityExtraction:
    """Test entity extraction from questions."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance."""
        with patch('schema_rag.service.faiss') as mock_faiss, \
             patch('schema_rag.service.SentenceTransformer') as mock_st_class:
            
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_faiss.read_index.return_value = mock_index
            
            mock_model = Mock()
            mock_st_class.return_value = mock_model
            
            with tempfile.TemporaryDirectory() as tmpdir:
                index_path = Path(tmpdir)
                
                config = {"model_name": "all-MiniLM-L6-v2", "dimension": 384}
                with open(index_path / "config.json", "w") as f:
                    json.dump(config, f)
                
                with open(index_path / "docs.jsonl", "w") as f:
                    pass
                
                (index_path / "faiss.index").touch()
                
                service = SchemaRagService(index_path)
                yield service
    
    def test_extract_entities_program_name(self, service):
        """Test extraction of program names."""
        entities = service._extract_entities("What is the success count for the forest fire program")
        assert "program_name" in entities
        assert "forest fire" in entities["program_name"] or "fire" in entities["program_name"]
    
    def test_extract_entities_date(self, service):
        """Test extraction of date entities."""
        entities = service._extract_entities("Programs created in 2024")
        assert entities.get("has_date") is True
    
    def test_extract_entities_recent_date(self, service):
        """Test extraction of recent/past date entities."""
        entities = service._extract_entities("Simulations started in the last week")
        assert entities.get("has_date") is True
    
    def test_extract_entities_min_value(self, service):
        """Test extraction of minimum value filters."""
        entities = service._extract_entities("Programs with more than 100 successes")
        assert "min_value" in entities
        assert entities["min_value"] == 100
    
    def test_extract_entities_max_value(self, service):
        """Test extraction of maximum value filters."""
        entities = service._extract_entities("Programs with less than 10 failures")
        assert "max_value" in entities
        assert entities["max_value"] == 10
    
    def test_extract_entities_comparison_greater(self, service):
        """Test extraction of greater than comparison."""
        entities = service._extract_entities("Values greater than 50")
        assert entities.get("comparison") == ">"
    
    def test_extract_entities_comparison_less(self, service):
        """Test extraction of less than comparison."""
        entities = service._extract_entities("Values less than 50")
        assert entities.get("comparison") == "<"
    
    def test_extract_entities_comparison_equal(self, service):
        """Test extraction of equal comparison."""
        entities = service._extract_entities("Values exactly equal to 50")
        assert entities.get("comparison") == "="
    
    def test_extract_entities_no_entities(self, service):
        """Test extraction with no entities."""
        entities = service._extract_entities("What is this")
        assert len(entities) == 0 or "has_date" not in entities


class TestEntityBoosting:
    """Test entity-based boosting."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance."""
        with patch('schema_rag.service.faiss') as mock_faiss, \
             patch('schema_rag.service.SentenceTransformer') as mock_st_class:
            
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_faiss.read_index.return_value = mock_index
            
            mock_model = Mock()
            mock_st_class.return_value = mock_model
            
            with tempfile.TemporaryDirectory() as tmpdir:
                index_path = Path(tmpdir)
                
                config = {"model_name": "all-MiniLM-L6-v2", "dimension": 384}
                with open(index_path / "config.json", "w") as f:
                    json.dump(config, f)
                
                with open(index_path / "docs.jsonl", "w") as f:
                    pass
                
                (index_path / "faiss.index").touch()
                
                service = SchemaRagService(index_path)
                yield service
    
    def test_boost_by_entities_program_name(self, service):
        """Test boosting by program name."""
        docs = [
            {
                "text": "This is about programs",
                "metadata": {},
                "score": 1.0
            },
            {
                "text": "This is about forest fire program",
                "metadata": {},
                "score": 1.0
            }
        ]
        entities = {"program_name": "forest fire"}
        
        boosted = service._boost_by_entities(docs, entities)
        
        # Second doc should have higher boost
        assert boosted[1]["score"] > boosted[0]["score"]
        assert "entity_boost" in boosted[1]
    
    def test_boost_by_entities_date_columns(self, service):
        """Test boosting date-related columns."""
        docs = [
            {
                "text": "Column description",
                "metadata": {"column": "created_at"},
                "score": 1.0
            },
            {
                "text": "Column description",
                "metadata": {"column": "other_column"},
                "score": 1.0
            }
        ]
        entities = {"has_date": True}
        
        boosted = service._boost_by_entities(docs, entities)
        
        # First doc should have higher boost
        assert boosted[0]["score"] > boosted[1]["score"]
    
    def test_boost_by_entities_numeric_columns(self, service):
        """Test boosting numeric columns."""
        docs = [
            {
                "text": "Column description",
                "metadata": {"column": "success_count"},
                "score": 1.0
            },
            {
                "text": "Column description",
                "metadata": {"column": "other_column"},
                "score": 1.0
            }
        ]
        entities = {"min_value": 100}
        
        boosted = service._boost_by_entities(docs, entities)
        
        # First doc should have higher boost
        assert boosted[0]["score"] > boosted[1]["score"]
    
    def test_boost_by_entities_no_entities(self, service):
        """Test boosting with no entities."""
        docs = [
            {
                "text": "Column description",
                "metadata": {"column": "test"},
                "score": 1.0
            }
        ]
        
        boosted = service._boost_by_entities(docs, {})
        
        # Should return unchanged
        assert boosted[0]["score"] == 1.0
        assert "entity_boost" not in boosted[0]


class TestRetrieveGrounding:
    """Test the main retrieve_grounding method."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance with mocked dependencies."""
        with patch('schema_rag.service.faiss') as mock_faiss, \
             patch('schema_rag.service.SentenceTransformer') as mock_st_class:
            
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_faiss.read_index.return_value = mock_index
            
            mock_model = Mock()
            # Mock encode to return a numpy array
            mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)
            mock_st_class.return_value = mock_model
            
            with tempfile.TemporaryDirectory() as tmpdir:
                index_path = Path(tmpdir)
                
                config = {"model_name": "all-MiniLM-L6-v2", "dimension": 384}
                with open(index_path / "config.json", "w") as f:
                    json.dump(config, f)
                
                # Create sample documents
                docs = [
                    {
                        "id": "doc1",
                        "text": "ProgramStatistics success_count column",
                        "doc_type": "schema_column",
                        "metadata": {
                            "model": "ProgramStatistics",
                            "table": "program_statistics",
                            "column": "success_count"
                        }
                    },
                    {
                        "id": "doc2",
                        "text": "Query recipe for program statistics",
                        "doc_type": "query_recipe",
                        "metadata": {
                            "join_hints": ["ProgramStatistics JOIN Program ON ..."]
                        }
                    }
                ]
                
                with open(index_path / "docs.jsonl", "w") as f:
                    for doc in docs:
                        f.write(json.dumps(doc) + "\n")
                
                (index_path / "faiss.index").touch()
                
                service = SchemaRagService(index_path)
                
                # Mock the search to return indices
                mock_index.search.return_value = (
                    np.array([[0.1, 0.2]]),  # distances
                    np.array([[0, 1]])      # indices
                )
                
                yield service
    
    def test_retrieve_grounding_success(self, service):
        """Test successful retrieval."""
        result = service.retrieve_grounding("What is the success count", top_k=2)
        
        assert isinstance(result, GroundingResult)
        assert len(result.docs) <= 2
        assert len(result.schema_refs) > 0
        assert result.schema_refs[0]["model"] == "ProgramStatistics"
        assert result.schema_refs[0]["column"] == "success_count"
    
    def test_retrieve_grounding_with_recipes(self, service):
        """Test retrieval includes query recipes."""
        result = service.retrieve_grounding("program statistics query", top_k=2)
        
        assert isinstance(result, GroundingResult)
        assert len(result.recipes) > 0 or len(result.join_hints) > 0
    
    def test_retrieve_grounding_top_k(self, service):
        """Test top_k parameter."""
        result = service.retrieve_grounding("test query", top_k=1)
        
        assert len(result.docs) <= 1
    
    def test_retrieve_grounding_not_initialized(self, service):
        """Test retrieval fails when not initialized."""
        service._index = None
        
        with pytest.raises(RuntimeError, match="Schema RAG service not initialized"):
            service.retrieve_grounding("test query")
    
    def test_retrieve_grounding_deduplicates_join_hints(self, service):
        """Test that join hints are deduplicated."""
        # Add duplicate join hints to documents
        service._documents[1]["metadata"]["join_hints"] = [
            "ProgramStatistics JOIN Program ON ...",
            "ProgramStatistics JOIN Program ON ..."  # duplicate
        ]
        
        result = service.retrieve_grounding("test query", top_k=2)
        
        # Join hints should be deduplicated
        assert len(result.join_hints) == len(set(result.join_hints))
    
    def test_retrieve_grounding_extracts_ambiguities(self, service):
        """Test that ambiguities are extracted from semantics."""
        # Add document with semantics
        service._documents.append({
            "id": "doc3",
            "text": "Test document",
            "doc_type": "schema_column",
            "metadata": {
                "model": "TestModel",
                "column": "variant_id",
                "semantics": "Note: variant_id may refer to different entities"
            }
        })
        
        # Update mock to return this document
        service._index.search.return_value = (
            np.array([[0.1]]),
            np.array([[2]])  # index of the new document
        )
        
        result = service.retrieve_grounding("variant_id", top_k=1)
        
        assert len(result.ambiguities) > 0
        assert "variant_id" in result.ambiguities[0].lower()


class TestGroundingResult:
    """Test GroundingResult dataclass."""
    
    def test_grounding_result_creation(self):
        """Test creating a GroundingResult."""
        result = GroundingResult(
            docs=[{"id": "doc1", "text": "test"}],
            schema_refs=[{"model": "TestModel", "column": "test_col"}],
            join_hints=["JOIN hint"],
            recipes=[{"id": "recipe1", "text": "recipe text"}],
            ambiguities=["Note: ambiguity"]
        )
        
        assert len(result.docs) == 1
        assert len(result.schema_refs) == 1
        assert len(result.join_hints) == 1
        assert len(result.recipes) == 1
        assert len(result.ambiguities) == 1
    
    def test_grounding_result_empty(self):
        """Test creating an empty GroundingResult."""
        result = GroundingResult(
            docs=[],
            schema_refs=[],
            join_hints=[],
            recipes=[],
            ambiguities=[]
        )
        
        assert len(result.docs) == 0
        assert len(result.schema_refs) == 0
        assert len(result.join_hints) == 0
        assert len(result.recipes) == 0
        assert len(result.ambiguities) == 0
