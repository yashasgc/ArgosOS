"""
Constants for the ArgosOS application
"""

# File size limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_FILENAME_LENGTH = 255

# Text processing limits
MAX_TEXT_LENGTH = 1000000
MAX_QUERY_LENGTH = 1000
MAX_API_KEY_LENGTH = 200

# LLM token limits - REMOVED FOR ACCURACY FOCUS
# No character limits on summary/tags to prioritize accuracy

# Response limits
MAX_SUMMARY_PREVIEW = 100
MAX_TEXT_PREVIEW = 200
MAX_CONTENT_PREVIEW = 500

# Database limits
DEFAULT_DOCUMENT_LIMIT = 100
MAX_DOCUMENT_LIMIT = 1000
MAX_SEARCH_LIMIT = 100

# HTTP status codes
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_413_PAYLOAD_TOO_LARGE = 413
HTTP_500_INTERNAL_SERVER_ERROR = 500

# CORS origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173", 
    "http://localhost:5174",
    "http://localhost:5175"
]

# Text encodings to try
TEXT_ENCODINGS = ['utf-8', 'utf-16', 'latin-1', 'cp1252']

# LLM response limits - REMOVED FOR ACCURACY FOCUS
# No token limits on summary/tags to prioritize accuracy
VISION_MAX_TOKENS = 1000
SQL_MAX_TOKENS = 200
DIRECT_ANSWER_MAX_TOKENS = 300
PROCESSING_MAX_TOKENS = 1500
