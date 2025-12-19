"""Data preprocessor - clean and enhance metadata based on EDA insights."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path
from src.common.logger import get_logger


class DataPreprocessor:
    """Preprocess and clean metadata based on EDA insights."""
    
    def __init__(self, config: Dict):
        self.config = config.get("preprocessing", {})
        self.logger = get_logger(__name__)
    
    def preprocess_metadata_csv(self, csv_path: str, output_path: Optional[str] = None) -> pd.DataFrame:
        """
        Preprocess metadata CSV based on EDA insights.
        
        Issues to fix:
        - Missing values: 공고 번호 18%, 공고 차수 18%, 입찰 시작일 26%
        - Outliers: 예산 이상치 14개
        - Data types: 날짜, 숫자 변환
        
        Args:
            csv_path: Input CSV path
            output_path: Optional output CSV path
        
        Returns:
            Cleaned DataFrame
        """
        self.logger.info(f"Preprocessing metadata CSV: {csv_path}")
        
        # Load CSV
        try:
            df = pd.read_csv(csv_path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding="cp949")
        
        original_count = len(df)
        self.logger.info(f"Loaded {original_count} rows")
        
        # 1. Fill missing 공고 번호 from 파일명 or generate
        if "공고 번호" in df.columns and "파일명" in df.columns:
            missing_announcement = df["공고 번호"].isna()
            if missing_announcement.sum() > 0:
                # Try to extract from filename
                for idx in df[missing_announcement].index:
                    filename = str(df.loc[idx, "파일명"])
                    # Try to find announcement number pattern in filename
                    import re
                    match = re.search(r'(\d{11,13})', filename)
                    if match:
                        df.loc[idx, "공고 번호"] = match.group(1)
                
                # Generate for remaining missing
                remaining = df["공고 번호"].isna().sum()
                if remaining > 0:
                    # Try to get max announcement number
                    try:
                        existing = df["공고 번호"].dropna().astype(str)
                        if not existing.empty:
                            # Extract numeric part
                            numeric_parts = existing.str.extract(r'(\d+)')[0]
                            if not numeric_parts.empty:
                                max_announcement = numeric_parts.astype(float).max()
                            else:
                                max_announcement = 0
                        else:
                            max_announcement = 0
                    except:
                        max_announcement = 0
                    
                    for idx in df[df["공고 번호"].isna()].index:
                        max_announcement += 1
                        df.loc[idx, "공고 번호"] = f"{int(max_announcement):013d}"
                
                self.logger.info(f"Fixed {missing_announcement.sum()} missing 공고 번호")
        
        # 2. Fill missing 공고 차수 (default to 0)
        if "공고 차수" in df.columns:
            df["공고 차수"] = df["공고 차수"].fillna(0).astype(float)
            self.logger.info("Fixed missing 공고 차수")
        
        # 3. Clean and convert 사업 금액
        if "사업 금액" in df.columns:
            # Convert to numeric
            df["사업 금액"] = pd.to_numeric(df["사업 금액"], errors="coerce")
            
            # Handle outliers (IQR method)
            q1 = df["사업 금액"].quantile(0.25)
            q3 = df["사업 금액"].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            # Log outliers but keep them (they might be valid)
            outliers = df[(df["사업 금액"] < lower_bound) | (df["사업 금액"] > upper_bound)]
            if len(outliers) > 0:
                self.logger.warning(f"Found {len(outliers)} budget outliers (keeping them): min={outliers['사업 금액'].min():,.0f}, max={outliers['사업 금액'].max():,.0f}")
        
        # 4. Parse and fix dates
        date_columns = ["공개 일자", "입찰 참여 시작일", "입찰 참여 마감일"]
        for col in date_columns:
            if col in df.columns:
                # Try multiple date formats
                df[col] = pd.to_datetime(df[col], errors="coerce", format="%Y-%m-%d %H:%M:%S")
                if df[col].isna().sum() > 0:
                    # Try alternative format
                    df[col] = pd.to_datetime(df[col], errors="coerce", format="%Y-%m-%d")
        
        # 5. Fill missing 입찰 참여 시작일 from 공개 일자
        if "입찰 참여 시작일" in df.columns and "공개 일자" in df.columns:
            missing_start = df["입찰 참여 시작일"].isna()
            if missing_start.sum() > 0:
                # Use 공개 일자 + 1 hour as default
                df.loc[missing_start, "입찰 참여 시작일"] = df.loc[missing_start, "공개 일자"] + pd.Timedelta(hours=1)
                self.logger.info(f"Fixed {missing_start.sum()} missing 입찰 참여 시작일")
        
        # 6. Normalize institution names (basic)
        if "발주 기관" in df.columns:
            # Remove extra spaces
            df["발주 기관"] = df["발주 기관"].str.strip()
            # Basic normalization (could be improved)
            df["발주 기관"] = df["발주 기관"].str.replace("  ", " ", regex=False)
        
        # 7. Generate summary statistics
        summary = {
            "total_rows": len(df),
            "missing_values": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.astype(str).to_dict(),
        }
        self.logger.info(f"Preprocessing complete: {len(df)} rows, missing values: {df.isnull().sum().sum()}")
        
        # Save if output path provided
        if output_path:
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            self.logger.info(f"Saved preprocessed CSV: {output_path}")
        
        return df
    
    def generate_data_summary(self, df: pd.DataFrame, output_path: Optional[str] = None) -> Dict:
        """
        Generate data summary based on EDA insights.
        
        Args:
            df: DataFrame
            output_path: Optional output JSON path
        
        Returns:
            Summary dictionary
        """
        summary = {
            "total_documents": len(df),
            "file_type_distribution": {},
            "metadata_completeness": {},
            "budget_statistics": {},
            "temporal_statistics": {},
        }
        
        # File type distribution
        if "파일명" in df.columns:
            df["file_type"] = df["파일명"].apply(
                lambda x: Path(str(x)).suffix.lower().replace(".", "").upper() if pd.notna(x) else "UNKNOWN"
            )
            summary["file_type_distribution"] = df["file_type"].value_counts().to_dict()
        
        # Metadata completeness
        for col in df.columns:
            if col != "file_type":
                missing = df[col].isnull().sum()
                summary["metadata_completeness"][col] = {
                    "missing": int(missing),
                    "completeness": float(1 - missing / len(df)) if len(df) > 0 else 0.0,
                }
        
        # Budget statistics
        if "사업 금액" in df.columns:
            budgets = pd.to_numeric(df["사업 금액"], errors="coerce").dropna()
            if not budgets.empty:
                summary["budget_statistics"] = {
                    "mean": float(budgets.mean()),
                    "median": float(budgets.median()),
                    "min": float(budgets.min()),
                    "max": float(budgets.max()),
                    "count": int(len(budgets)),
                }
        
        # Temporal statistics
        if "공개 일자" in df.columns:
            dates = pd.to_datetime(df["공개 일자"], errors="coerce").dropna()
            if not dates.empty:
                summary["temporal_statistics"] = {
                    "earliest": dates.min().strftime("%Y-%m-%d"),
                    "latest": dates.max().strftime("%Y-%m-%d"),
                    "year_distribution": dates.dt.year.value_counts().to_dict(),
                }
        
        # Save if output path provided
        if output_path:
            from src.common.utils import save_json
            save_json(summary, output_path)
            self.logger.info(f"Saved data summary: {output_path}")
        
        return summary

