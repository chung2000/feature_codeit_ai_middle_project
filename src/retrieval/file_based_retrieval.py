"""File-based retrieval using JSON summaries."""

from pathlib import Path
from typing import Dict, List, Optional
import json
from rapidfuzz import fuzz
from src.common.logger import get_logger
from src.common.utils import load_json


class FileBasedRetrieval:
    """Retrieve chunks from file-based JSON summaries."""
    
    def __init__(self, summaries_dir: str):
        """
        Initialize file-based retrieval.
        
        Args:
            summaries_dir: Directory containing by_file JSON summaries
                          (e.g., data/features/summaries/by_file)
        """
        self.summaries_dir = Path(summaries_dir)
        self.logger = get_logger(__name__)
        self._file_cache: Dict[str, Dict] = {}
        
        if not self.summaries_dir.exists():
            self.logger.warning(f"Summaries directory not found: {summaries_dir}")
    
    def load_file_summary(self, doc_id: str) -> Optional[Dict]:
        """
        Load summary for a specific doc_id.
        
        Args:
            doc_id: Document ID
        
        Returns:
            File summary dictionary or None if not found
        """
        # Check cache first
        if doc_id in self._file_cache:
            return self._file_cache[doc_id]
        
        # Try to find file
        safe_filename = self._create_safe_filename(doc_id)
        file_path = self.summaries_dir / f"{safe_filename}.json"
        
        if not file_path.exists():
            # Try to find by searching all files
            for json_file in self.summaries_dir.glob("*.json"):
                try:
                    data = load_json(str(json_file))
                    if data.get("doc_id") == doc_id:
                        self._file_cache[doc_id] = data
                        return data
                except:
                    continue
            return None
        
        try:
            data = load_json(str(file_path))
            self._file_cache[doc_id] = data
            return data
        except Exception as e:
            self.logger.error(f"Failed to load file summary {file_path}: {e}")
            return None
    
    def search_in_file(
        self,
        doc_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for relevant chunks within a specific file.
        
        Args:
            doc_id: Document ID
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of relevant chunks with scores
        """
        summary = self.load_file_summary(doc_id)
        if not summary:
            self.logger.warning(f"File summary not found for doc_id: {doc_id}")
            return []
        
        chunks = summary.get("chunks", [])
        if not chunks:
            return []
        
        # Simple text matching (can be improved with embeddings)
        scored_chunks = []
        query_lower = query.lower()
        
        for chunk in chunks:
            chunk_text = chunk.get("chunk_text", "").lower()
            
            # Calculate relevance score
            # 1. Exact match
            if query_lower in chunk_text:
                score = 1.0
            # 2. Fuzzy match
            else:
                score = fuzz.partial_ratio(query_lower, chunk_text) / 100.0
            
            # Boost score if query words appear multiple times
            query_words = query_lower.split()
            word_matches = sum(1 for word in query_words if word in chunk_text)
            score += word_matches * 0.1
            
            scored_chunks.append({
                "chunk_id": chunk.get("chunk_id", ""),
                "chunk_index": chunk.get("chunk_index", 0),
                "chunk_text": chunk.get("chunk_text", ""),
                "score": min(score, 1.0),
                "metadata": summary.get("metadata", {}),
                "doc_id": doc_id,
                "file_name": summary.get("file_name", ""),
            })
        
        # Sort by score and return top_k
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]
    
    def get_all_chunks_from_file(self, doc_id: str) -> List[Dict]:
        """
        Get all chunks from a specific file.
        
        Args:
            doc_id: Document ID
        
        Returns:
            List of all chunks
        """
        summary = self.load_file_summary(doc_id)
        if not summary:
            return []
        
        chunks = summary.get("chunks", [])
        return [
            {
                **chunk,
                "metadata": summary.get("metadata", {}),
                "doc_id": doc_id,
                "file_name": summary.get("file_name", ""),
            }
            for chunk in chunks
        ]
    
    def list_available_files(self) -> List[Dict]:
        """
        List all available file summaries.
        
        Returns:
            List of file metadata
        """
        files = []
        
        if not self.summaries_dir.exists():
            return files
        
        for json_file in self.summaries_dir.glob("*.json"):
            try:
                data = load_json(str(json_file))
                files.append({
                    "doc_id": data.get("doc_id", ""),
                    "file_name": data.get("file_name", ""),
                    "file_type": data.get("file_type", ""),
                    "metadata": data.get("metadata", {}),
                    "chunking_statistics": data.get("chunking_statistics", {}),
                })
            except Exception as e:
                self.logger.warning(f"Failed to load {json_file}: {e}")
                continue
        
        return files
    
    def search_across_files(
        self,
        query: str,
        top_k: int = 10,
        file_filter: Optional[List[str]] = None,
        fallback_search: bool = True
    ) -> List[Dict]:
        """
        Search across multiple files.
        
        Args:
            query: Search query (e.g., "도시 사업", "스마트시티")
            top_k: Number of results to return
            file_filter: Optional list of doc_ids to search in
        
        Returns:
            List of relevant chunks from multiple files
        """
        all_results = []
        
        # Get files to search
        if file_filter:
            files_to_search = file_filter
        else:
            # Search all files
            available_files = self.list_available_files()
            files_to_search = [f["doc_id"] for f in available_files]
        
        # First, try to find files that match the query in metadata
        # This helps prioritize relevant documents
        query_lower = query.lower()
        relevant_files = []
        
        for file_info in available_files:
            if file_info["doc_id"] not in files_to_search:
                continue
            
            # Check if query matches file metadata
            metadata = file_info.get("metadata", {})
            file_name = file_info.get("file_name", "").lower()
            business_name = metadata.get("사업명", "").lower()
            institution = metadata.get("발주 기관", "").lower()
            
            # Calculate file relevance score
            file_score = 0.0
            if query_lower in file_name:
                file_score += 2.0
            if query_lower in business_name:
                file_score += 1.5
            if query_lower in institution:
                file_score += 0.5
            
            # Check individual words
            query_words = query_lower.split()
            for word in query_words:
                if word in file_name:
                    file_score += 0.5
                if word in business_name:
                    file_score += 0.3
            
            if file_score > 0:
                relevant_files.append((file_info["doc_id"], file_score))
        
        # Sort files by relevance
        relevant_files.sort(key=lambda x: x[1], reverse=True)
        
        # Search in most relevant files first, then others
        files_to_search_ordered = [f[0] for f in relevant_files] + [
            f for f in files_to_search if f not in [rf[0] for rf in relevant_files]
        ]
        
        # Search in each file (prioritize relevant ones)
        for doc_id in files_to_search_ordered:
            file_results = self.search_in_file(doc_id, query, top_k=top_k)
            # Boost scores for files that matched metadata
            if doc_id in [rf[0] for rf in relevant_files]:
                file_score = next((rf[1] for rf in relevant_files if rf[0] == doc_id), 0)
                for result in file_results:
                    result["score"] = min(result["score"] + (file_score * 0.1), 1.0)
            all_results.extend(file_results)
        
        # Sort by score and return top_k
        all_results.sort(key=lambda x: x["score"], reverse=True)
        results = all_results[:top_k]
        
        # If no results found and fallback_search is enabled, try partial keyword matching
        if not results and fallback_search:
            self.logger.info(f"No exact matches for '{query}', trying fallback search with partial keywords...")
            
            # Split query into individual words
            query_words = query.split()
            if len(query_words) > 1:
                # Try searching with individual words
                fallback_results = []
                for word in query_words:
                    if len(word) > 1:  # Skip single character words
                        word_results = self._search_with_keyword(word, files_to_search_ordered, top_k=top_k // len(query_words))
                        fallback_results.extend(word_results)
                
                # Remove duplicates and sort
                seen_chunk_ids = set()
                unique_results = []
                for result in fallback_results:
                    chunk_id = result.get("chunk_id", "")
                    if chunk_id not in seen_chunk_ids:
                        seen_chunk_ids.add(chunk_id)
                        # Reduce score for fallback results (they're less relevant)
                        result["score"] = result["score"] * 0.7
                        unique_results.append(result)
                
                unique_results.sort(key=lambda x: x["score"], reverse=True)
                results = unique_results[:top_k]
                
                if results:
                    self.logger.info(f"Found {len(results)} fallback results using partial keywords")
        
        return results
    
    def _search_with_keyword(
        self,
        keyword: str,
        files_to_search: List[str],
        top_k: int = 5
    ) -> List[Dict]:
        """Search with a single keyword across files."""
        all_results = []
        keyword_lower = keyword.lower()
        
        # Get available files for metadata matching
        available_files = self.list_available_files()
        
        # Find files that match keyword in metadata
        relevant_files = []
        for file_info in available_files:
            if file_info["doc_id"] not in files_to_search:
                continue
            
            metadata = file_info.get("metadata", {})
            file_name = file_info.get("file_name", "").lower()
            business_name = metadata.get("사업명", "").lower()
            
            if keyword_lower in file_name or keyword_lower in business_name:
                relevant_files.append(file_info["doc_id"])
        
        # Search in relevant files first
        files_ordered = relevant_files + [f for f in files_to_search if f not in relevant_files]
        
        for doc_id in files_ordered[:20]:  # Limit to top 20 files for performance
            file_results = self.search_in_file(doc_id, keyword, top_k=3)
            all_results.extend(file_results)
        
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:top_k]
    
    def _create_safe_filename(self, doc_id: str) -> str:
        """Create a safe filename from doc_id."""
        safe = doc_id.replace("/", "_").replace("\\", "_").replace(":", "_")
        safe = safe.replace("*", "_").replace("?", "_").replace('"', "_")
        safe = safe.replace("<", "_").replace(">", "_").replace("|", "_")
        if len(safe) > 200:
            safe = safe[:200]
        return safe

