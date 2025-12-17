"""HWP parser module."""

from pathlib import Path
from typing import Dict
import olefile
from src.common.logger import get_logger

# Try to import pyhwp/hwp5 for better HWP parsing
HAS_HWP5 = False
HWP5_METHOD = None

try:
    import hwp5
    from hwp5.proc import restext
    HAS_HWP5 = True
    HWP5_METHOD = "hwp5"
except ImportError:
    try:
        import pyhwp
        HAS_HWP5 = True
        HWP5_METHOD = "pyhwp"
    except ImportError:
        pass


class HWPParser:
    """Parse HWP files and extract text using pyhwp/hwp5 or fallback to olefile."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        if HAS_HWP5:
            self.logger.info("Using pyhwp/hwp5 for HWP parsing")
        else:
            self.logger.warning(
                "pyhwp/hwp5 not available, using basic olefile parser. "
                "Install with: pip install pyhwp"
            )
    
    def parse(self, file_path: str) -> Dict:
        """
        Parse HWP file and extract text.
        
        Args:
            file_path: Path to HWP file
        
        Returns:
            Dictionary with text and metadata
        """
        hwp_path = Path(file_path)
        
        if not hwp_path.exists():
            raise FileNotFoundError(f"HWP file not found: {file_path}")
        
        try:
            # Try to extract text using olefile
            text = self._extract_text(str(hwp_path))
            metadata = self._extract_metadata(str(hwp_path))
            
            if not text or len(text.strip()) < 10:
                self.logger.warning(
                    f"Extracted text from HWP is very short or empty: {file_path}"
                )
            
            return {
                "text": text,
                "metadata": {
                    "file_path": str(hwp_path),
                    "file_size": hwp_path.stat().st_size,
                    **metadata
                }
            }
        
        except Exception as e:
            self.logger.error(f"Failed to parse HWP {file_path}: {e}")
            # Return empty text instead of raising error
            return {
                "text": "",
                "metadata": {
                    "file_path": str(hwp_path),
                    "error": str(e)
                }
            }
    
    def _extract_text(self, hwp_path: str) -> str:
        """
        Extract text from HWP file.
        
        Tries pyhwp/hwp5 first, falls back to olefile if not available.
        """
        # Try pyhwp/hwp5 first
        if HAS_HWP5:
            try:
                text = self._extract_with_hwp5(hwp_path)
                if text and len(text.strip()) > 10:
                    return text
                else:
                    self.logger.debug(f"hwp5 extracted empty/short text, trying fallback")
            except Exception as e:
                self.logger.debug(f"hwp5 extraction failed: {e}, trying fallback")
        
        # Fallback to olefile
        return self._extract_with_olefile(hwp_path)
    
    def _extract_with_hwp5(self, hwp_path: str) -> str:
        """Extract text using hwp5 library."""
        try:
            if HWP5_METHOD == "hwp5":
                # hwp5.proc.restext를 사용하여 텍스트 추출
                import hwp5
                from hwp5.proc import restext
                
                # hwp5 파일 열기
                hwp5_file = hwp5.open(hwp_path)
                
                # 텍스트 추출
                text_parts = []
                for text in restext.extract(hwp5_file):
                    if text:
                        text_parts.append(str(text))
                
                return "\n".join(text_parts)
            
            elif HWP5_METHOD == "pyhwp":
                # pyhwp 사용 (API가 다를 수 있음)
                import pyhwp
                hwp_file = pyhwp.HWPDocument(hwp_path)
                return hwp_file.body_text or ""
            
            else:
                # Should not reach here, but just in case
                self.logger.warning(f"Unknown HWP5 method: {HWP5_METHOD}")
                return ""
            
        except Exception as e:
            self.logger.warning(f"hwp5 extraction error: {e}")
            raise
    
    def _extract_with_olefile(self, hwp_path: str) -> str:
        """Extract text using olefile (fallback method)."""
        text_parts = []
        
        try:
            if not olefile.isOleFile(hwp_path):
                self.logger.warning(f"File is not a valid OLE file: {hwp_path}")
                return ""
            
            ole = olefile.OleFileIO(hwp_path)
            
            # Try to read BodyText stream (common in HWP files)
            try:
                if ole.exists("BodyText"):
                    stream = ole.openstream("BodyText")
                    data = stream.read()
                    # Basic text extraction (HWP format is complex)
                    # This is a simplified approach
                    try:
                        text = data.decode("utf-8", errors="ignore")
                        # Filter out non-printable characters
                        text = "".join(c for c in text if c.isprintable() or c in "\n\r\t")
                        text_parts.append(text)
                    except Exception:
                        pass
            except Exception as e:
                self.logger.debug(f"Could not read BodyText stream: {e}")
            
            ole.close()
            
            return "\n".join(text_parts)
        
        except Exception as e:
            self.logger.warning(f"Error reading HWP with olefile {hwp_path}: {e}")
            return ""
    
    def _extract_metadata(self, hwp_path: str) -> Dict:
        """Extract metadata from HWP file."""
        metadata = {}
        
        try:
            if olefile.isOleFile(hwp_path):
                ole = olefile.OleFileIO(hwp_path)
                
                # Try to get summary information
                if ole.exists("\x05SummaryInformation"):
                    try:
                        summary = ole.get_metadata()
                        if summary:
                            metadata.update({
                                "title": summary.title or "",
                                "author": summary.author or "",
                                "subject": summary.subject or "",
                            })
                    except Exception:
                        pass
                
                ole.close()
        
        except Exception as e:
            self.logger.debug(f"Could not extract metadata: {e}")
        
        return metadata

