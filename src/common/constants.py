"""Constants used across the project."""

# File extensions
SUPPORTED_PDF_EXTENSIONS = [".pdf"]
SUPPORTED_HWP_EXTENSIONS = [".hwp"]
SUPPORTED_DOCX_EXTENSIONS = [".docx"]
SUPPORTED_EXTENSIONS = SUPPORTED_PDF_EXTENSIONS + SUPPORTED_HWP_EXTENSIONS + SUPPORTED_DOCX_EXTENSIONS

# Text processing
MIN_TEXT_LENGTH = 100
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
MIN_CHUNK_SIZE = 100

# Separators for text chunking
DEFAULT_SEPARATORS = [
    "\n\n",      # Paragraph break
    "\n",        # Line break
    ". ",        # Sentence end (English/Korean)
    "。",        # Sentence end (Korean)
    "! ",        # Exclamation
    "? ",        # Question
    " ",         # Space
]

# Metadata field names (from CSV)
METADATA_FIELDS = [
    "공고 번호",
    "공고 차수",
    "사업명",
    "사업 금액",
    "발주 기관",
    "공개 일자",
    "입찰 참여 시작일",
    "입찰 참여 마감일",
    "사업 요약",
    "파일명",
]

# Vector store
DEFAULT_COLLECTION_NAME = "rfp_chunks"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"
DEFAULT_EMBEDDING_DIMENSION = 3072  # text-embedding-3-large dimension

# Retrieval
DEFAULT_TOP_K = 10
MAX_TOP_K = 20
DEFAULT_MMR_LAMBDA = 0.5
DEFAULT_FUZZY_THRESHOLD = 0.8

# Generation
DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 2000
DEFAULT_CONTEXT_MAX_TOKENS = 8000

# Evaluation
DEFAULT_K_VALUES = [1, 5, 10, 20]

# Status codes
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_WARNING = "warning"

# Error messages
ERROR_FILE_NOT_FOUND = "File not found: {}"
ERROR_PARSING_FAILED = "Failed to parse file: {}"
ERROR_EMPTY_TEXT = "Extracted text is empty or too short"
ERROR_INVALID_FORMAT = "Unsupported file format: {}"

