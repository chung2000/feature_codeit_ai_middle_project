import unittest
from src.common.config import ConfigLoader
from src.ingest.loader import get_loader, Document
from src.chunking.splitter import TextSplitter

class TestBasic(unittest.TestCase):
    def test_config_loader(self):
        loader = ConfigLoader("config/local.yaml")
        self.assertIsNotNone(loader.config)
        self.assertEqual(loader.get("project_name"), "bid_mate_rag")

    def test_text_loader(self):
        # Create a dummy file
        with open("test_dummy.txt", "w") as f:
            f.write("Hello World")
        
        try:
            loader = get_loader("test_dummy.txt")
            docs = loader.load()
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0].content, "Hello World")
        finally:
            import os
            if os.path.exists("test_dummy.txt"):
                os.remove("test_dummy.txt")

    def test_splitter(self):
        splitter = TextSplitter(chunk_size=10, chunk_overlap=0)
        docs = [Document(content="Short text", metadata={})]
        chunks = splitter.split_documents(docs)
        self.assertEqual(len(chunks), 1)

if __name__ == '__main__':
    unittest.main()
