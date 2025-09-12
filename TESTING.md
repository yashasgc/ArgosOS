# Testing Documentation

## Test Coverage

The test suite covers the following areas:

### 1. Security Tests (`tests/test_security.py`)
- File validation (filename, type, size)
- API key security and encryption
- CORS configuration
- Input sanitization

### 2. File Processing Tests (`tests/test_file_processing.py`)
- Text extraction from various formats
- OCR functionality
- PDF processing
- DOCX processing
- Content hashing

### 3. API Endpoint Tests (`tests/test_api_endpoints.py`)
- Health check endpoints
- File upload endpoints
- Search functionality
- Document management
- Error handling

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Security tests
pytest tests/test_security.py -v

# File processing tests
pytest tests/test_file_processing.py -v

# API endpoint tests
pytest tests/test_api_endpoints.py -v
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

## Test Data

Tests use mock data and temporary files to avoid affecting production data.

## Continuous Integration

Tests should be run on every commit and pull request to ensure code quality and security.

## Adding New Tests

When adding new features:
1. Write unit tests for core functionality
2. Write integration tests for API endpoints
3. Write security tests for any new input validation
4. Update this documentation
