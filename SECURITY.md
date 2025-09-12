# Security Documentation

## Security Measures Implemented

### 1. File Upload Security
- **File Type Validation**: Only allows specific MIME types (images, PDFs, text files)
- **File Size Limits**: Maximum 100MB per file
- **Filename Sanitization**: Removes dangerous characters and path traversal attempts
- **Content Validation**: Validates file content before processing

### 2. API Security
- **CORS Configuration**: Restricted to specific origins (localhost only in development)
- **Input Validation**: All inputs are validated and sanitized
- **SQL Injection Prevention**: Search queries are validated for dangerous keywords
- **Rate Limiting**: Consider implementing rate limiting for production

### 3. API Key Security
- **Encryption**: API keys are encrypted using Fernet encryption
- **Secure Storage**: Keys stored in encrypted files, not in plain text
- **Validation**: API key format validation before storage
- **No Exposure**: API key status endpoint doesn't expose actual keys

### 4. Data Security
- **Content Hashing**: SHA-256 hashing for deduplication
- **Secure File Processing**: No temporary files created on disk
- **Input Sanitization**: All user inputs are sanitized

## Security Testing

Run the security test suite:
```bash
pytest tests/test_security.py -v
```

## Production Security Checklist

- [ ] Update CORS origins to production domains
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Use HTTPS in production
- [ ] Regular security audits
- [ ] Monitor for suspicious activity
- [ ] Keep dependencies updated

## Vulnerability Reporting

If you discover a security vulnerability, please report it responsibly by contacting the development team.
