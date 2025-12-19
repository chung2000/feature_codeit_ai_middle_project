"""Enhanced Ingest Agent with preprocessing and data summary."""

from pathlib import Path
from typing import Dict, Optional
from tqdm import tqdm

from src.ingest.ingest_agent import IngestAgent
from src.ingest.data_preprocessor import DataPreprocessor
from src.common.logger import get_logger
from src.common.utils import ensure_dir


class EnhancedIngestAgent(IngestAgent):
    """Enhanced ingest agent with preprocessing and summary generation."""
    
    def __init__(self, config: Dict):
        """
        Initialize Enhanced Ingest Agent.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.preprocessor = DataPreprocessor(config)
        self.logger = get_logger(__name__)
    
    def preprocess_and_ingest(
        self,
        input_dir: str,
        output_dir: str,
        csv_path: str,
        preprocessed_csv_path: Optional[str] = None,
        summary_path: Optional[str] = None
    ) -> Dict:
        """
        Preprocess metadata and then ingest documents.
        
        Args:
            input_dir: Input directory with documents
            output_dir: Output directory for preprocessed JSON
            csv_path: Input CSV metadata path
            preprocessed_csv_path: Optional path to save preprocessed CSV
            summary_path: Optional path to save data summary
        
        Returns:
            Dictionary with processing results
        """
        self.logger.info("=" * 60)
        self.logger.info("Enhanced Ingest Pipeline with Preprocessing")
        self.logger.info("=" * 60)
        
        # Step 1: Preprocess metadata CSV
        self.logger.info("Step 1: Preprocessing metadata CSV...")
        if preprocessed_csv_path is None:
            preprocessed_csv_path = str(Path(csv_path).parent / "data_list_preprocessed.csv")
        
        df_preprocessed = self.preprocessor.preprocess_metadata_csv(
            csv_path=csv_path,
            output_path=preprocessed_csv_path
        )
        
        # Step 2: Generate data summary
        self.logger.info("Step 2: Generating data summary...")
        if summary_path is None:
            summary_path = str(Path(output_dir).parent / "data_summary.json")
        
        summary = self.preprocessor.generate_data_summary(
            df=df_preprocessed,
            output_path=summary_path
        )
        
        # Step 3: Reload metadata with preprocessed CSV
        self.logger.info("Step 3: Reloading preprocessed metadata...")
        self.metadata_loader.load_from_csv(preprocessed_csv_path)
        
        # Step 4: Process documents (use parent class method)
        self.logger.info("Step 4: Processing documents...")
        self.process_batch(
            input_dir=input_dir,
            output_dir=output_dir,
            csv_path=preprocessed_csv_path
        )
        
        self.logger.info("=" * 60)
        self.logger.info("Enhanced Ingest Pipeline Completed")
        self.logger.info("=" * 60)
        
        return {
            "preprocessed_csv": preprocessed_csv_path,
            "summary": summary_path,
            "output_dir": output_dir,
        }

