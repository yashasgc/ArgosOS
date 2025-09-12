# Security Policy

## Security Features

ArgosOS implements multiple layers of security to protect user data and prevent common vulnerabilities.

### 🔐 API Key Security
- **Encryption**: API keys are encrypted using Fernet (AES 128) before storage
- **No Exposure**: API keys are never exposed via HTTP endpoints
- **Secure Storage**: Keys stored in encrypted files, not in environment variables
- **Validation**: API key format validation before storage

### 🛡️ Input Validation
- **File Validation**: Comprehensive file type, size, and name validation
- **Path Traversal Protection**: Prevents directory traversal attacks
- **MIME Type Validation**: Strict MIME type checking
- **Size Limits**: 100MB maximum file size limit
- **Filename Sanitization**: Removes dangerous characters from filenames

### 🚫 SQL Injection Protection
- **Parameterized Queries**: All database queries use SQLAlchemy ORM
- **Raw SQL Disabled**: LLM-generated SQL queries are disabled for security
- **Input Sanitization**: Search queries are validated for SQL keywords
- **ORM Usage**: Database operations use ORM methods, not raw SQL

### 🌐 CORS Security
- **Restricted Origins**: Only allows specific localhost origins
- **Header Restrictions**: Limits allowed headers to essential ones
- **Credential Control**: Proper credential handling configuration

### 📁 File Upload Security
- **Type Validation**: Only allows specific file types
- **Size Validation**: Enforces file size limits
- **Content Validation**: Validates file content before processing
- **Safe Storage**: Files processed in memory, not saved to disk

## Security Checklist

- [x] API keys encrypted at rest
- [x] No hardcoded secrets in code
- [x] Input validation on all endpoints
- [x] SQL injection protection
- [x] Path traversal protection
- [x] CORS properly configured
- [x] File upload validation
- [x] Error handling without information disclosure
- [x] Secure file processing
- [x] Content validation

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:

1. **DO NOT** create a public issue
2. Email security concerns to: [security@example.com]
3. Include detailed steps to reproduce
4. Allow reasonable time for response before disclosure

## Security Updates

Security updates are released as needed. Please keep your installation updated.

## Dependencies

All dependencies are regularly updated and monitored for security vulnerabilities.

## Data Privacy

- No data is sent to external services except OpenAI (when configured)
- All processing happens locally
- Database files are stored locally
- No telemetry or analytics collection