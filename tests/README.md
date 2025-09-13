# ArgosOS Test Suite

## Overview
This test suite provides comprehensive testing for the ArgosOS application with mocked LLM calls and end-to-end scenarios.

## Test Structure

### Core Test Files
- `test_llm_mocks.py` - LLM mock functionality and validation
- `test_simplified.py` - Comprehensive unit and integration tests

### Test Categories

#### 1. LLM Mock Tests (`test_llm_mocks.py`)
- **Mock LLM Availability**: Tests mock LLM provider initialization
- **Mock Summarization**: Tests text summarization with different content lengths
- **Mock Tag Generation**: Tests tag generation for different document types
- **Mock Chat Completion**: Tests structured JSON responses for different query types

#### 2. Agent Tests (`test_simplified.py`)

##### RetrievalAgent Tests
- **Search with LLM**: Tests document search when LLM is available
- **Search Fallback**: Tests fallback search when LLM is unavailable
- **JSON Parsing**: Tests robust JSON parsing with fallback to comma parsing
- **Tag Generation**: Tests intelligent tag generation and validation

##### PostProcessorAgent Tests
- **Document Processing**: Tests document processing workflow
- **Processing Decision**: Tests LLM-based processing decision logic
- **Additional Processing**: Tests execution of additional processing steps

##### Database Operations Tests
- **Document CRUD**: Tests document creation, reading, and searching
- **Tag CRUD**: Tests tag creation, retrieval, and management
- **Search Functionality**: Tests database search with various queries

##### LLM Integration Tests
- **Mock Functionality**: Tests all LLM mock methods work correctly
- **Response Validation**: Tests mock responses match expected formats

##### End-to-End Tests
- **Complete Workflow**: Tests full search and processing pipeline
- **Integration**: Tests agent interaction and data flow

## Test Features

### Mocking Strategy
- **LLM Provider Mocking**: Complete mock of OpenAI API calls
- **File System Mocking**: Mock file operations for testing
- **Database Mocking**: In-memory SQLite for isolated testing

### Test Data
- **Sample Documents**: Pre-configured test documents with realistic data
- **Mock Responses**: Structured mock responses for different scenarios
- **Error Scenarios**: Tests for various error conditions and fallbacks

### Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Full workflow testing
- **Error Handling**: Exception and error scenario testing

## Running Tests

### Run All Tests
```bash
poetry run python -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# LLM Mock Tests
poetry run python -m pytest tests/test_llm_mocks.py -v

# Agent Tests
poetry run python -m pytest tests/test_simplified.py -v

# Specific Test Class
poetry run python -m pytest tests/test_simplified.py::TestRetrievalAgent -v
```

### Test Output
- **Verbose Mode**: `-v` flag for detailed output
- **Short Traceback**: `--tb=short` for concise error reporting
- **Color Output**: `--color=yes` for better readability

## Test Results
✅ **16/16 tests passing**
- 4 LLM Mock Tests
- 12 Comprehensive Agent Tests

## Key Test Scenarios

### 1. LLM Integration
- Mock LLM responses for all agent operations
- JSON parsing with fallback mechanisms
- Error handling for LLM unavailability

### 2. Document Processing
- PDF, image, and text document processing
- OCR extraction and text processing
- Content storage and retrieval

### 3. Search Functionality
- Tag-based document search
- Fallback search when LLM unavailable
- Query processing and result formatting

### 4. Database Operations
- Document CRUD operations
- Tag management and normalization
- Search and filtering capabilities

### 5. Error Handling
- LLM unavailability scenarios
- File processing errors
- Database constraint violations

## Test Quality
- **Comprehensive Coverage**: Tests all major components and workflows
- **Mocked Dependencies**: No external API calls or file system dependencies
- **Isolated Tests**: Each test runs independently
- **Realistic Scenarios**: Tests reflect real-world usage patterns
- **Error Scenarios**: Tests handle various error conditions gracefully

## Maintenance
- Tests are updated when core functionality changes
- Mock responses are designed to be realistic and maintainable
- Test data is kept minimal but comprehensive
- Error scenarios are regularly updated to match current behavior
