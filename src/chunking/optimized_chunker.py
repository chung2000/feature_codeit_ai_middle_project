"""Optimized chunker based on EDA insights."""

from typing import List, Dict, Optional
import re
from src.common.logger import get_logger
from src.common.constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    MIN_CHUNK_SIZE,
)


class OptimizedChunker:
    """Optimized chunker based on EDA analysis.
    
    Improvements:
    - File type specific chunk sizes (PDF longer, HWP shorter)
    - Better overlap handling (reduce from 91% to ~20%)
    - Sentence/paragraph boundary awareness
    - Metadata-aware chunking
    """
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        min_chunk_size: int = MIN_CHUNK_SIZE,
    ):
        self.base_chunk_size = chunk_size
        self.base_chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.logger = get_logger(__name__)
        
        # File type specific settings (based on EDA: PDF avg 85K, HWP avg 6K)
        self.file_type_settings = {
            "PDF": {"chunk_size": 1200, "chunk_overlap": 200},  # Larger chunks for PDF
            "HWP": {"chunk_size": 800, "chunk_overlap": 150},   # Smaller chunks for HWP
            "DOCX": {"chunk_size": 1000, "chunk_overlap": 200}, # Default
        }
    
    def _get_chunk_settings(self, file_type: str) -> Dict:
        """Get chunk settings for file type."""
        file_type_upper = file_type.upper()
        if file_type_upper in self.file_type_settings:
            return self.file_type_settings[file_type_upper]
        return {"chunk_size": self.base_chunk_size, "chunk_overlap": self.base_chunk_overlap}
    
    def _find_sentence_boundary(self, text: str, start_pos: int, direction: int = 1) -> int:
        """
        Find sentence boundary near position.
        
        Args:
            text: Full text
            start_pos: Starting position
            direction: 1 for forward, -1 for backward
        
        Returns:
            Position of sentence boundary
        """
        # Sentence endings
        sentence_endings = ['. ', '.\n', '! ', '!\n', '? ', '?\n', '。', '\n\n']
        
        search_start = start_pos
        search_end = min(start_pos + 100 * direction, len(text)) if direction > 0 else max(start_pos - 100, 0)
        
        if direction > 0:
            for i in range(search_start, search_end):
                for ending in sentence_endings:
                    if text[i:i+len(ending)] == ending:
                        return i + len(ending)
        else:
            for i in range(search_start, search_end, -1):
                for ending in sentence_endings:
                    if text[i-len(ending):i] == ending:
                        return i
        
        return start_pos  # No boundary found
    
    def chunk(
        self,
        text: str,
        doc_id: str,
        metadata: Optional[Dict] = None,
        file_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Chunk text with optimizations.
        
        Args:
            text: Text to chunk
            doc_id: Document ID
            metadata: Metadata dictionary
            file_type: File type (PDF, HWP, DOCX)
        
        Returns:
            List of chunk dictionaries
        """
        if not text:
            return []
        
        metadata = metadata or {}
        
        # Get file type specific settings
        if file_type:
            settings = self._get_chunk_settings(file_type)
            chunk_size = settings["chunk_size"]
            chunk_overlap = settings["chunk_overlap"]
        else:
            chunk_size = self.base_chunk_size
            chunk_overlap = self.base_chunk_overlap
        
        # Ensure overlap is reasonable (max 30% of chunk size)
        chunk_overlap = min(chunk_overlap, chunk_size // 3)
        
        chunks: List[Dict] = []
        n = len(text)
        index = 0
        chunk_index = 0
        
        while index < n:
            # Calculate end position
            end = min(index + chunk_size, n)
            
            # Try to find sentence boundary near end
            if end < n:
                boundary_pos = self._find_sentence_boundary(text, end - 50, direction=-1)
                if boundary_pos > index + self.min_chunk_size:
                    end = boundary_pos
            
            chunk_text = text[index:end]
            
            # Skip if too short (will be merged later)
            if len(chunk_text.strip()) < self.min_chunk_size and index > 0:
                # Merge with previous chunk
                if chunks:
                    chunks[-1]["chunk_text"] += chunk_text
                    chunks[-1]["char_offset_end"] = end
                index = end
                continue
            
            chunks.append({
                "chunk_id": f"{doc_id}_{chunk_index}",
                "doc_id": doc_id,
                "chunk_index": chunk_index,
                "chunk_text": chunk_text,
                "char_offset_start": index,
                "char_offset_end": end,
                "metadata": {**metadata, "chunk_size": len(chunk_text)},
            })
            
            chunk_index += 1
            
            if end >= n:
                break
            
            # Next start: apply overlap but ensure minimum progress
            next_start = max(end - chunk_overlap, index + self.min_chunk_size)
            
            # Try to find sentence boundary for next start
            if next_start < n:
                boundary_pos = self._find_sentence_boundary(text, next_start, direction=1)
                if boundary_pos < end:
                    next_start = boundary_pos
            
            index = next_start
        
        # Merge last chunk if too small
        if len(chunks) >= 2 and len(chunks[-1]["chunk_text"]) < self.min_chunk_size:
            last = chunks.pop()
            prev = chunks[-1]
            prev["chunk_text"] += last["chunk_text"]
            prev["char_offset_end"] = last["char_offset_end"]
            prev["metadata"]["chunk_size"] = len(prev["chunk_text"])
        
        return chunks

