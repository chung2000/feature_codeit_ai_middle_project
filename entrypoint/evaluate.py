"""Evaluation pipeline entrypoint - system performance evaluation."""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.common.config import load_config
from src.common.logger import get_logger


def main():
    """Main evaluation pipeline."""
    parser = argparse.ArgumentParser(description="RFP RAG Evaluation Pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="config/local.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--test-set",
        type=str,
        help="Path to test set JSONL file",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    logger = get_logger(__name__, log_level=config.get("logging", {}).get("level", "INFO"))
    
    test_set_path = args.test_set or config["eval"]["test_set_path"]
    
    logger.info("=" * 60)
    logger.info("RFP RAG Evaluation Pipeline")
    logger.info("=" * 60)
    
    try:
        # Initialize agents
        from src.indexing.vector_store import VectorStore
        from src.indexing.embedder import Embedder
        from src.retrieval.retrieval_agent import RetrievalAgent
        from src.generation.generation_agent import GenerationAgent
        from src.eval.eval_agent import EvalAgent
        from langchain_openai import ChatOpenAI
        
        # Vector store and embedder
        vector_store = VectorStore(config["indexing"])
        embedder = Embedder(config["indexing"])
        
        # Retrieval agent
        retrieval_agent = RetrievalAgent(config["retrieval"], vector_store, embedder)
        
        # LLM
        llm = ChatOpenAI(
            model=config["generation"]["llm"]["model"],
            temperature=config["generation"]["llm"]["temperature"],
            max_tokens=config["generation"]["llm"]["max_tokens"],
        )
        
        # Generation agent
        generation_agent = GenerationAgent(config["generation"], llm, retrieval_agent)
        
        # Eval agent
        eval_agent = EvalAgent(config["eval"], retrieval_agent, generation_agent)
        
        # Run full evaluation
        logger.info(f"Loading test set from: {test_set_path}")
        results = eval_agent.run_full_evaluation(test_set_path)
        
        # Generate report
        from src.eval.reporter import Reporter
        reporter = Reporter()
        
        output_path = f"{config['eval']['output_dir']}/report_{Path(test_set_path).stem}.json"
        reporter.generate_report(results, output_path)
        
        # Print summary
        summary = reporter.generate_summary(results)
        print("\n" + "=" * 60)
        print("Evaluation Summary")
        print("=" * 60)
        print(summary)
        
        logger.info(f"Evaluation report saved to: {output_path}")
        logger.info("=" * 60)
        logger.info("Evaluation completed successfully!")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

