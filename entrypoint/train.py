"""Training pipeline entrypoint - processes documents through ingest, chunking, and indexing."""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, skip

from src.common.config import load_config
from src.common.logger import get_logger
from src.common.utils import ensure_dir


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description="RFP RAG Training Pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="config/local.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--step",
        type=str,
        choices=["ingest", "chunking", "indexing", "all"],
        default="all",
        help="Pipeline step to execute",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    logger = get_logger(__name__, log_level=config.get("logging", {}).get("level", "INFO"))
    
    logger.info("=" * 60)
    logger.info("RFP RAG Training Pipeline Started")
    logger.info("=" * 60)
    
    # Ensure output directories exist
    ensure_dir(config["ingest"]["output_dir"])
    ensure_dir(config["chunking"].get("output_dir", "data/features"))
    ensure_dir(config["indexing"]["vector_store"]["persist_dir"])
    
    try:
        if args.step in ["ingest", "all"]:
            logger.info("Step 1: Enhanced Ingest Agent - Document Parsing with Preprocessing")
            from src.ingest.enhanced_ingest_agent import EnhancedIngestAgent
            
            # Check if enhanced ingest is enabled
            use_enhanced = config.get("ingest", {}).get("use_enhanced", True)
            
            if use_enhanced:
                ingest_agent = EnhancedIngestAgent(config)
                result = ingest_agent.preprocess_and_ingest(
                    input_dir=config["ingest"]["input_dir"],
                    output_dir=config["ingest"]["output_dir"],
                    csv_path=config["ingest"]["metadata_csv"],
                )
                logger.info(f"✓ Enhanced ingest step completed")
                logger.info(f"  - Preprocessed CSV: {result.get('preprocessed_csv')}")
                logger.info(f"  - Data summary: {result.get('summary')}")
            else:
                from src.ingest.ingest_agent import IngestAgent
                ingest_agent = IngestAgent(config)
                ingest_agent.process_batch(
                    input_dir=config["ingest"]["input_dir"],
                    output_dir=config["ingest"]["output_dir"],
                    csv_path=config["ingest"]["metadata_csv"],
                )
                logger.info("✓ Ingest step completed")
        
        if args.step in ["chunking", "all"]:
            logger.info("Step 2: Chunking Agent - Text Chunking")
            from src.chunking.chunking_agent import ChunkingAgent
            
            chunking_agent = ChunkingAgent(config)
            chunks_path = "data/features/chunks.jsonl"
            chunking_agent.process_batch(
                input_dir=config["ingest"]["output_dir"],
                output_path=chunks_path,
            )
            
            # Check if chunks file was created
            chunks_file = Path(chunks_path)
            if not chunks_file.exists():
                raise FileNotFoundError(
                    f"Chunks file not created: {chunks_path}. "
                    "Check if ingest step completed successfully and produced JSON files."
                )
            
            logger.info("✓ Chunking step completed")
        
        if args.step in ["indexing", "all"]:
            logger.info("Step 3: Indexing Agent - Vector Embedding & Indexing")
            from src.indexing.indexing_agent import IndexingAgent
            
            chunks_path = "data/features/chunks.jsonl"
            chunks_file = Path(chunks_path)
            
            if not chunks_file.exists():
                raise FileNotFoundError(
                    f"Chunks file not found: {chunks_path}. "
                    "Please run chunking step first: --step chunking"
                )
            
            indexing_agent = IndexingAgent(config)
            report = indexing_agent.index_chunks(chunks_path)
            logger.info(f"✓ Indexing step completed: {report}")
        
        logger.info("=" * 60)
        logger.info("Training Pipeline Completed Successfully!")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

