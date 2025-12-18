import os
import subprocess
from typing import List, Dict, Any
from abc import ABC, abstractmethod
import pypdf

from langchain_core.documents import Document

class BaseLoader(ABC):
    def __init__(self, file_path: str):
        self.file_path = file_path

    @abstractmethod
    def load(self) -> List[Document]:
        """Load document and return a list of Document objects."""
        pass

class PDFLoader(BaseLoader):
    def load(self) -> List[Document]:
        try:
            reader = pypdf.PdfReader(self.file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return [Document(page_content=text, metadata={"source": self.file_path, "type": "pdf"})]
        except Exception as e:
            print(f"Error reading PDF {self.file_path}: {e}")
            return []

class HWPLoader(BaseLoader):
    def load(self) -> List[Document]:
        try:
            # Use hwp5txt command line tool from pyhwp
            # Must be in PATH (or venv bin)
            command = ["hwp5txt", self.file_path]
            
            # If hwp5txt is not in PATH, this will raise FileNotFoundError
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                encoding="utf-8",
                check=False
            )
            
            if result.returncode != 0:
                print(f"hwp5txt failed for {os.path.basename(self.file_path)}: {result.stderr[:200]}")
                return []
            
            text = result.stdout
            if not text.strip():
                 print(f"Warning: Empty text extracted from {self.file_path}")

            return [Document(page_content=text, metadata={"source": self.file_path, "type": "hwp"})]
        
        except FileNotFoundError:
             print(f"Error: 'hwp5txt' command not found while processing {self.file_path}. Please ensure pyhwp is installed.")
             return []
        except Exception as e:
             print(f"Error reading HWP {self.file_path}: {e}")
             return []

class TextLoader(BaseLoader):
    def load(self) -> List[Document]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return [Document(page_content=content, metadata={"source": self.file_path, "type": "text"})]

def get_loader(file_path: str) -> BaseLoader:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return PDFLoader(file_path)
    elif ext == ".hwp":
        return HWPLoader(file_path)
    elif ext in [".txt", ".md"]:
        return TextLoader(file_path)
    else:
        # Fallback for unknown extensions, or just ignore
        raise ValueError(f"Unsupported file extension: {ext}")
