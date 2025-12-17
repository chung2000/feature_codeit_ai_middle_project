"""Integration tests for the RFP RAG pipeline."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.common.config import load_config
from src.common.logger import get_logger
from src.common.utils import ensure_dir


def test_config_loading():
    """Test configuration loading."""
    logger = get_logger(__name__)
    logger.info("Testing configuration loading...")
    
    try:
        config = load_config("config/local.yaml")
        assert "ingest" in config
        assert "chunking" in config
        assert "indexing" in config
        assert "retrieval" in config
        assert "generation" in config
        logger.info("✓ Configuration loading passed")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration loading failed: {e}")
        return False


def test_module_imports():
    """Test that all modules can be imported."""
    logger = get_logger(__name__)
    logger.info("Testing module imports...")
    
    modules = [
        "src.common.logger",
        "src.common.config",
        "src.common.utils",
        "src.common.constants",
        "src.ingest.ingest_agent",
        "src.chunking.chunking_agent",
        "src.indexing.indexing_agent",
        "src.retrieval.retrieval_agent",
        "src.generation.generation_agent",
        "src.eval.eval_agent",
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            logger.info(f"  ✓ {module}")
        except Exception as e:
            logger.error(f"  ✗ {module}: {e}")
            failed.append(module)
    
    if failed:
        logger.error(f"✗ Module imports failed for: {failed}")
        return False
    
    logger.info("✓ All module imports passed")
    return True


def test_agent_initialization():
    """Test that agents can be initialized (without full execution)."""
    logger = get_logger(__name__)
    logger.info("Testing agent initialization...")
    
    try:
        config = load_config("config/local.yaml")
        
        # Test IngestAgent
        from src.ingest.ingest_agent import IngestAgent
        ingest_agent = IngestAgent(config)
        logger.info("  ✓ IngestAgent initialized")
        
        # Test ChunkingAgent
        from src.chunking.chunking_agent import ChunkingAgent
        chunking_agent = ChunkingAgent(config)
        logger.info("  ✓ ChunkingAgent initialized")
        
        # Test IndexingAgent
        from src.indexing.indexing_agent import IndexingAgent
        indexing_agent = IndexingAgent(config)
        logger.info("  ✓ IndexingAgent initialized")
        
        # Test RetrievalAgent (requires vector_store and embedder)
        from src.indexing.vector_store import VectorStore
        from src.indexing.embedder import Embedder
        vector_store = VectorStore(config["indexing"])
        embedder = Embedder(config["indexing"])
        
        from src.retrieval.retrieval_agent import RetrievalAgent
        retrieval_agent = RetrievalAgent(config, vector_store, embedder)
        logger.info("  ✓ RetrievalAgent initialized")
        
        # Test GenerationAgent (requires LLM and retrieval_agent)
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=config["generation"]["llm"]["model"],
            temperature=config["generation"]["llm"]["temperature"],
            max_tokens=config["generation"]["llm"]["max_tokens"],
        )
        
        from src.generation.generation_agent import GenerationAgent
        generation_agent = GenerationAgent(config["generation"], llm, retrieval_agent)
        logger.info("  ✓ GenerationAgent initialized")
        
        # Test EvalAgent
        from src.eval.eval_agent import EvalAgent
        eval_agent = EvalAgent(config["eval"], retrieval_agent, generation_agent)
        logger.info("  ✓ EvalAgent initialized")
        
        logger.info("✓ All agent initialization passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Agent initialization failed: {e}", exc_info=True)
        return False


def test_directory_structure():
    """Test that required directories exist or can be created."""
    logger = get_logger(__name__)
    logger.info("Testing directory structure...")
    
    try:
        config = load_config("config/local.yaml")
        
        dirs = [
            config["ingest"]["output_dir"],
            config["chunking"].get("output_dir", "data/features"),
            config["indexing"]["vector_store"]["persist_dir"],
            config["eval"]["output_dir"],
        ]
        
        for dir_path in dirs:
            ensure_dir(dir_path)
            logger.info(f"  ✓ {dir_path}")
        
        logger.info("✓ Directory structure test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Directory structure test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Integration Tests Started")
    logger.info("=" * 60)
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Module Imports", test_module_imports),
        ("Directory Structure", test_directory_structure),
        ("Agent Initialization", test_agent_initialization),
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\n--- {name} ---")
        result = test_func()
        results.append((name, result))
    
    logger.info("\n" + "=" * 60)
    logger.info("Integration Test Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("=" * 60)
        logger.info("All integration tests passed!")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("=" * 60)
        logger.error("Some integration tests failed!")
        logger.error("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

