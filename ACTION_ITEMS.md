# Action Items from Repository Review

This document tracks specific, actionable improvements identified during the repository review.

## 🔴 Critical Priority (Do First)

### 1. Add Test Suite
**Issue:** No test files found in the repository  
**Impact:** High - Affects code confidence, maintainability, and refactoring safety  
**Effort:** High  
**Files to create:**
- `tests/test_juspay_mcp/` (unit tests for core APIs)
- `tests/test_juspay_dashboard_mcp/` (unit tests for dashboard APIs)
- `tests/conftest.py` (pytest fixtures)
- `tests/integration/` (integration tests)

**Tasks:**
- [ ] Set up pytest framework
- [ ] Add unit tests for each API module (aim for >80% coverage)
- [ ] Add integration tests for critical flows
- [ ] Configure coverage reporting
- [ ] Add tests to CI/CD pipeline

### 2. Fix Empty Function
**Issue:** `get_base64_auth()` in `juspay_dashboard_mcp/config.py` (line 44-46) is empty  
**Impact:** Medium - Could cause runtime errors if called  
**Effort:** Low  
**File:** `juspay_dashboard_mcp/config.py`

```python
# Current (line 44-46):
def get_base64_auth():
    """Returns the base64 encoded auth string."""
    pass

# Should either:
# Option 1: Implement it if needed
# Option 2: Remove it if unused
```

**Tasks:**
- [ ] Determine if function is needed
- [ ] Implement or remove function
- [ ] Search codebase for any calls to this function

### 3. Standardize HTTP Client Library
**Issue:** Using both `httpx` (async) and `requests` (sync)  
**Impact:** Medium - Can cause confusion and potential async/sync mixing issues  
**Effort:** Medium  
**Files affected:**
- `pyproject.toml` (remove requests dependency)
- Any file using `import requests`

**Tasks:**
- [ ] Search for all `requests` usage: `grep -r "import requests\|from requests" .`
- [ ] Replace with `httpx` equivalents
- [ ] Remove `requests` from dependencies
- [ ] Test all affected endpoints

---

## 🟡 Medium Priority (Do Soon)

### 4. Improve Dynamic Import Pattern
**Issue:** Using `__import__` with deprecated parameters in `juspay_dashboard_mcp/api/__init__.py`  
**Impact:** Medium - Makes static analysis difficult, potential future compatibility issues  
**Effort:** Low  
**File:** `juspay_dashboard_mcp/api/__init__.py` (lines 14-23)

**Current code:**
```python
for module in modules:
    module_name = os.path.basename(module)[:-3]
    if module_name != "__init__":
        __all__.append(module_name)
        __import__(f"{__name__}.{module_name}", globals(), locals(), [], 0)
```

**Recommended replacement:**
```python
import importlib

for module in modules:
    module_name = os.path.basename(module)[:-3]
    if module_name != "__init__":
        __all__.append(module_name)
        importlib.import_module(f"{__name__}.{module_name}")
```

**Tasks:**
- [ ] Replace `__import__` with `importlib.import_module`
- [ ] Test that all modules still import correctly
- [ ] Consider if this pattern is even needed (could just use explicit imports)

### 5. Add Custom Exception Classes
**Issue:** Using generic `Exception` throughout codebase  
**Impact:** Medium - Makes error handling less precise  
**Effort:** Medium  
**Files to create:** 
- `juspay_mcp/exceptions.py`
- `juspay_dashboard_mcp/exceptions.py`

**Suggested exceptions:**
```python
class JuspayAPIError(Exception):
    """Base exception for Juspay API errors"""
    pass

class JuspayAuthenticationError(JuspayAPIError):
    """Authentication failed"""
    pass

class JuspayValidationError(JuspayAPIError):
    """Request validation failed"""
    pass

class JuspayNotFoundError(JuspayAPIError):
    """Resource not found"""
    pass

class JuspayRateLimitError(JuspayAPIError):
    """Rate limit exceeded"""
    pass
```

**Tasks:**
- [ ] Create exception classes
- [ ] Update API handlers to use specific exceptions
- [ ] Update error messages to be user-friendly
- [ ] Document exception types in API documentation

### 6. Make Timeouts Configurable
**Issue:** Hardcoded 30-second timeout in `httpx.AsyncClient(timeout=30.0)`  
**Impact:** Low-Medium - Some operations might need different timeouts  
**Effort:** Low  
**Files affected:**
- `juspay_mcp/api/utils.py`
- `juspay_dashboard_mcp/api/utils.py`

**Tasks:**
- [ ] Add `JUSPAY_API_TIMEOUT` environment variable
- [ ] Update config.py to read timeout value
- [ ] Update all AsyncClient instantiations to use config
- [ ] Document in README

### 7. Add Configuration Validation
**Issue:** No startup validation of all required configurations  
**Impact:** Medium - Can lead to runtime failures  
**Effort:** Low  

**Tasks:**
- [ ] Create `validate_config()` function in each config.py
- [ ] Call validation on server startup
- [ ] Provide clear error messages for missing/invalid configs
- [ ] Add config schema documentation

### 8. Improve Error Response Standardization
**Issue:** Inconsistent error response formats  
**Impact:** Medium - Makes client-side error handling difficult  
**Effort:** Medium  

**Recommended standard format:**
```python
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "User-friendly message",
        "details": {...},
        "request_id": "mcp-tool-abc123"
    }
}
```

**Tasks:**
- [ ] Define standard error response schema
- [ ] Update all error handlers to use standard format
- [ ] Document error codes and their meanings
- [ ] Add to response_schema.py files

---

## 🟢 Low Priority (Nice to Have)

### 9. Add CONTRIBUTING.md
**Impact:** Low - Improves contributor experience  
**Effort:** Low  

**Should include:**
- [ ] Code style guidelines
- [ ] How to run tests
- [ ] How to submit PRs
- [ ] Issue reporting guidelines
- [ ] Development setup
- [ ] Commit message conventions

### 10. Implement Connection Pooling
**Issue:** Creating new HTTP client for each request  
**Impact:** Low - Small performance improvement  
**Effort:** Medium  

**Tasks:**
- [ ] Create shared AsyncClient instance
- [ ] Implement proper lifecycle management
- [ ] Configure connection pool size
- [ ] Benchmark performance improvement

### 11. Add Caching Layer
**Issue:** No caching for repeated requests  
**Impact:** Low - Performance optimization  
**Effort:** Medium  

**Suggested caching targets:**
- Gateway configurations (rarely change)
- User lists
- Settings

**Tasks:**
- [ ] Choose caching library (e.g., aiocache)
- [ ] Add cache configuration
- [ ] Implement cache decorators
- [ ] Add cache invalidation logic
- [ ] Document caching behavior

### 12. Add Type Checking with mypy
**Impact:** Low - Improves type safety  
**Effort:** Medium  

**Tasks:**
- [ ] Add mypy to dev dependencies
- [ ] Create mypy.ini configuration
- [ ] Fix any type errors found
- [ ] Add mypy to CI pipeline
- [ ] Configure strict mode gradually

### 13. Reduce Code Duplication
**Issue:** Similar patterns in juspay_mcp and juspay_dashboard_mcp  
**Impact:** Low - Code maintainability  
**Effort:** Medium  

**Tasks:**
- [ ] Identify common patterns (tool registration, error handling, etc.)
- [ ] Extract to shared utilities module
- [ ] Update both modules to use shared code
- [ ] Ensure tests still pass

### 14. Add Architecture Diagrams
**Impact:** Low - Better documentation  
**Effort:** Low  

**Diagrams needed:**
- [ ] Overall system architecture
- [ ] Authentication flow
- [ ] Request/response flow
- [ ] Module dependencies

### 15. Add Security Headers
**Issue:** Missing security headers in HTTP responses  
**Impact:** Low - Security best practice  
**Effort:** Low  

**Headers to add:**
```python
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

**Tasks:**
- [ ] Add security headers middleware
- [ ] Configure CORS properly
- [ ] Document security configuration

### 16. Implement Rate Limiting
**Issue:** No rate limiting on MCP endpoints  
**Impact:** Low - Prevents abuse  
**Effort:** Medium  

**Tasks:**
- [ ] Choose rate limiting library
- [ ] Add rate limit middleware
- [ ] Configure limits per endpoint
- [ ] Return proper 429 responses
- [ ] Document rate limits

---

## Dependency Updates

### 17. Pin Dependency Versions
**Issue:** Most dependencies use minimum versions (>=)  
**Impact:** Low - Prevents unexpected behavior  
**Effort:** Low  

**Current:**
```toml
click >= 8.1.8
httpx >= 0.28.1
mcp >= 1.6.0
```

**Tasks:**
- [ ] Review current working versions
- [ ] Pin to known-good versions with compatible ranges
- [ ] Set up dependabot for automated updates
- [ ] Document dependency update policy

---

## Documentation Improvements

### 18. Add API Reference Documentation
**Impact:** Medium - Better developer experience  
**Effort:** Medium  

**Tasks:**
- [ ] Set up Sphinx or MkDocs
- [ ] Generate API docs from docstrings
- [ ] Add usage examples
- [ ] Deploy to GitHub Pages or similar

### 19. Add CHANGELOG.md
**Impact:** Low - Better version tracking  
**Effort:** Low  

**Tasks:**
- [ ] Create CHANGELOG.md following Keep a Changelog format
- [ ] Document current version features
- [ ] Update for each release
- [ ] Link from README

### 20. Add Troubleshooting Guide
**Impact:** Medium - Reduces support burden  
**Effort:** Low  

**Common issues to document:**
- [ ] Authentication failures
- [ ] Connection issues
- [ ] Configuration errors
- [ ] Environment setup problems
- [ ] Docker issues

---

## Testing Checklist

Once tests are added, ensure coverage of:

- [ ] All API endpoint wrappers
- [ ] Authentication mechanisms (env vars + headers)
- [ ] Error handling paths
- [ ] Configuration validation
- [ ] Tool registration and invocation
- [ ] Request/response serialization
- [ ] Edge cases and error conditions
- [ ] Integration with MCP protocol

---

## Progress Tracking

**Last Updated:** October 13, 2025

### Completed Items
- [x] Initial repository review

### In Progress
- [ ] (None currently)

### Blocked
- [ ] (None currently)

---

**Note:** These action items are prioritized based on impact vs effort. Start with critical items and work down. Each item should be tracked as a separate issue in the repository for better project management.
