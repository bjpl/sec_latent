# Code Review Standards - SEC Filing Analysis Platform

**Version**: 1.0
**Last Updated**: 2025-10-18
**Owner**: QA Reviewer Agent

---

## Purpose

This document defines mandatory code review standards for the SEC filing analysis platform. All code changes MUST pass these security and quality checks before merging to main branch.

---

## Review Process

### 1. Review Requirements

**Every Pull Request MUST Have**:
- Minimum 1 approving reviewer (security-critical code requires 2)
- All automated checks passing
- No unresolved review comments
- Updated tests with ≥80% coverage
- Updated documentation if applicable

### 2. Review Timeline

- **Small PRs (<200 lines)**: Review within 24 hours
- **Medium PRs (200-500 lines)**: Review within 48 hours
- **Large PRs (>500 lines)**: Should be split; if not, review within 72 hours
- **Critical Security Fixes**: Review within 4 hours

---

## Security Review Checklist

### 🔴 CRITICAL SECURITY CHECKS (Must Pass)

#### 1. Credentials & Secrets
```python
# ❌ FAIL - Hardcoded credentials
API_KEY = "sk-1234567890abcdef"
DATABASE_URL = "postgresql://admin:password@localhost/db"

# ✅ PASS - Environment variables
import os
API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
```

**Review Questions**:
- [ ] Are all API keys, passwords, and tokens in environment variables?
- [ ] Are no credentials in code, comments, or test files?
- [ ] Are example credentials clearly marked as fake/invalid?
- [ ] Is `.env` in `.gitignore`?

#### 2. SQL Injection Prevention
```python
# ❌ FAIL - String interpolation
cursor.execute(f"SELECT * FROM filings WHERE cik = '{cik}'")
cursor.execute("SELECT * FROM users WHERE id = " + user_id)

# ✅ PASS - Parameterized queries
cursor.execute("SELECT * FROM filings WHERE cik = %s", (cik,))
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# ✅ PASS - ORM
filing = session.query(Filing).filter(Filing.cik == cik).first()
```

**Review Questions**:
- [ ] Are all database queries using parameterized statements or ORM?
- [ ] Are no raw SQL strings concatenated with user input?
- [ ] Are stored procedures using bind variables?

#### 3. Input Validation
```python
# ❌ FAIL - No validation
def get_filing(cik: str):
    return db.query(f"SELECT * FROM filings WHERE cik = '{cik}'")

# ✅ PASS - Proper validation
def get_filing(cik: str) -> Filing:
    # Validate CIK format (10 digits)
    if not re.match(r'^\d{10}$', cik):
        raise ValidationError(f"Invalid CIK format: {cik}")

    # Additional checks
    if len(cik) != 10:
        raise ValidationError("CIK must be exactly 10 digits")

    return db.query(Filing).filter(Filing.cik == cik).first()
```

**Review Questions**:
- [ ] Are all user inputs validated before use?
- [ ] Are validation errors handled gracefully?
- [ ] Are input lengths checked to prevent buffer overflows?
- [ ] Are special characters escaped or rejected?
- [ ] Are file uploads validated (type, size, content)?

#### 4. Authentication & Authorization
```python
# ❌ FAIL - No auth check
@app.route('/api/filings/<cik>')
def get_filing(cik):
    return Filing.query.filter_by(cik=cik).first()

# ✅ PASS - Auth required
@app.route('/api/filings/<cik>')
@require_authentication
@require_permission('read:filings')
def get_filing(cik):
    filing = Filing.query.filter_by(cik=cik).first()
    if not can_access_filing(current_user, filing):
        abort(403)
    return filing
```

**Review Questions**:
- [ ] Are authentication checks present on all protected endpoints?
- [ ] Are authorization checks verifying user permissions?
- [ ] Is the principle of least privilege followed?
- [ ] Are admin functions properly restricted?
- [ ] Are session tokens securely managed?

#### 5. Error Handling & Information Disclosure
```python
# ❌ FAIL - Exposes internals
except Exception as e:
    return f"Error: {str(e)}", 500
    # Might expose: "psycopg2.errors.InvalidPassword: password authentication failed for user 'admin'"

# ✅ PASS - Generic user message, detailed logging
except Exception as e:
    logger.error(f"Database error processing filing {cik}", exc_info=True)
    return {"error": "An error occurred processing your request"}, 500
```

**Review Questions**:
- [ ] Are error messages generic and safe for users?
- [ ] Are detailed errors logged securely (not exposed to users)?
- [ ] Are stack traces never shown to end users?
- [ ] Are database errors sanitized before logging?

#### 6. Logging Security
```python
# ❌ FAIL - Logs sensitive data
logger.info(f"User login: {username} / {password}")
logger.debug(f"API call with key: {api_key}")

# ✅ PASS - No sensitive data
logger.info(f"User login attempt", extra={"username": username})
logger.debug(f"API call", extra={"user_id": user_id, "endpoint": endpoint})
```

**Review Questions**:
- [ ] Are passwords, API keys, and tokens NEVER logged?
- [ ] Are user inputs sanitized before logging?
- [ ] Are log levels appropriate (debug, info, warning, error)?
- [ ] Are logs structured and searchable?

---

## Code Quality Checks

### 1. Code Organization
- [ ] Functions are single-purpose (≤50 lines ideal)
- [ ] Classes follow Single Responsibility Principle
- [ ] Module imports are organized and minimal
- [ ] No circular dependencies
- [ ] Dead code removed

### 2. Naming Conventions
```python
# ❌ FAIL - Unclear names
def proc(u, p):
    return u.pts > p

# ✅ PASS - Clear names
def calculate_user_discount(user: User, minimum_points: int) -> float:
    return user.points > minimum_points
```

- [ ] Variables have descriptive names
- [ ] Functions/methods clearly describe their action
- [ ] Constants are UPPER_SNAKE_CASE
- [ ] Classes are PascalCase
- [ ] Functions are snake_case (Python) or camelCase (JS/TS)

### 3. Type Safety
```python
# ❌ FAIL - No type hints
def get_filing(cik):
    return db.query(...)

# ✅ PASS - Full type hints
def get_filing(cik: str) -> Optional[Filing]:
    return db.query(Filing).filter_by(cik=cik).first()
```

- [ ] Type hints on all function signatures (Python)
- [ ] TypeScript used with strict mode (if applicable)
- [ ] Generics used where appropriate
- [ ] mypy or TypeScript compiler passes with no errors

### 4. Documentation
```python
# ✅ GOOD - Comprehensive docstring
def extract_latent_signals(filing: Filing, signal_types: List[str]) -> Dict[str, Any]:
    """
    Extract latent signals from SEC filing using multiple analyzers.

    Args:
        filing: The SEC filing to analyze
        signal_types: List of signal types to extract (linguistic, structural, etc.)

    Returns:
        Dictionary mapping signal types to extracted signals

    Raises:
        ValidationError: If filing or signal_types are invalid
        ProcessingError: If signal extraction fails

    Example:
        >>> signals = extract_latent_signals(filing, ['linguistic', 'sentiment'])
        >>> signals['linguistic']['complexity_score']
        7.8
    """
```

- [ ] All public functions have docstrings
- [ ] Complex logic has inline comments
- [ ] API endpoints are documented
- [ ] README updated if behavior changes

### 5. Performance Considerations
- [ ] Database queries are optimized (no N+1 queries)
- [ ] Large datasets processed in batches
- [ ] Caching used appropriately
- [ ] No blocking operations in async code
- [ ] Resource cleanup (file handles, connections)

---

## Testing Requirements

### 1. Test Coverage
- [ ] Unit tests for all new functions (≥80% coverage)
- [ ] Integration tests for API endpoints
- [ ] Security tests for input validation
- [ ] Edge cases tested (empty inputs, large inputs, invalid data)

### 2. Test Quality
```python
# ❌ FAIL - Tests implementation, not behavior
def test_get_filing():
    assert Filing.query.filter_by is called

# ✅ PASS - Tests behavior
def test_get_filing_returns_valid_filing():
    filing = get_filing("0001234567")
    assert filing.cik == "0001234567"
    assert filing.form_type in ["10-K", "10-Q"]

def test_get_filing_raises_on_invalid_cik():
    with pytest.raises(ValidationError):
        get_filing("invalid")
```

- [ ] Tests are clear and maintainable
- [ ] Tests don't depend on order of execution
- [ ] Mock external dependencies (APIs, databases)
- [ ] Test names describe what they test
- [ ] No commented-out tests

### 3. Security Tests
```python
# Security test examples
def test_sql_injection_prevention():
    malicious_cik = "0001234567'; DROP TABLE filings;--"
    with pytest.raises(ValidationError):
        get_filing(malicious_cik)

def test_path_traversal_prevention():
    malicious_path = "../../etc/passwd"
    with pytest.raises(ValidationError):
        load_file(malicious_path)

def test_rate_limiting():
    for i in range(100):
        response = client.get('/api/filings/0001234567')
    assert response.status_code == 429  # Too Many Requests
```

- [ ] Input validation tests (including malicious inputs)
- [ ] Authentication/authorization tests
- [ ] Rate limiting tests
- [ ] Error handling tests

---

## Python-Specific Standards

### 1. Style & Formatting
- [ ] Follows PEP 8 style guide
- [ ] Black formatter applied (line length 88-100)
- [ ] isort for import sorting
- [ ] No trailing whitespace

### 2. Python Best Practices
```python
# ✅ GOOD - Context managers for resources
with open(file_path, 'r') as f:
    data = f.read()

# ✅ GOOD - List comprehensions for simple cases
squares = [x**2 for x in range(10)]

# ✅ GOOD - Explicit exceptions
raise ValidationError(f"Invalid CIK: {cik}")

# ❌ BAD - Bare except
try:
    process()
except:  # Catches everything including KeyboardInterrupt!
    pass
```

- [ ] Context managers used for resource management
- [ ] List comprehensions for simple transformations
- [ ] Specific exceptions (not bare `except`)
- [ ] F-strings for string formatting (Python 3.6+)

### 3. Async Code
- [ ] Async functions use `async def`
- [ ] `await` used with async operations
- [ ] No blocking code in async functions
- [ ] Proper error handling in async code

---

## TypeScript/JavaScript-Specific Standards

### 1. TypeScript Configuration
- [ ] Strict mode enabled
- [ ] No implicit any
- [ ] No unused variables
- [ ] ES2020+ target

### 2. Modern JavaScript
```typescript
// ✅ GOOD - Modern JavaScript
const getFilings = async (ciks: string[]): Promise<Filing[]> => {
    const filings = await Promise.all(
        ciks.map(cik => fetchFiling(cik))
    );
    return filings.filter(f => f !== null);
};

// ✅ GOOD - Destructuring
const { cik, formType, filingDate } = filing;

// ✅ GOOD - Optional chaining
const companyName = filing?.company?.name ?? 'Unknown';
```

- [ ] Arrow functions for callbacks
- [ ] Async/await instead of callbacks
- [ ] Destructuring for clarity
- [ ] Optional chaining (?.) and nullish coalescing (??)

---

## Dependencies & Libraries

### 1. Dependency Management
- [ ] All dependencies in `requirements.txt` or `package.json`
- [ ] Versions pinned (not using `*` or `latest`)
- [ ] No unused dependencies
- [ ] Security audit passed (`pip-audit`, `npm audit`)

### 2. New Dependencies
**Before adding a new dependency, verify**:
- [ ] Is it actively maintained?
- [ ] Are there known security vulnerabilities?
- [ ] Is the license compatible?
- [ ] Is it actually needed (vs implementing ourselves)?
- [ ] Are there better alternatives?

---

## Git & PR Best Practices

### 1. Commit Messages
```bash
# ❌ FAIL
"fixed bug"
"update"
"wip"

# ✅ PASS
"fix: Prevent SQL injection in filing query endpoint"
"feat: Add latent signal extraction for 10-K filings"
"test: Add security tests for input validation"
```

- [ ] Descriptive commit messages
- [ ] Conventional commit format (fix:, feat:, test:, docs:)
- [ ] One logical change per commit
- [ ] No merge commits (use rebase)

### 2. Pull Request Description
**Every PR must include**:
- [ ] What: What does this PR do?
- [ ] Why: Why is this change needed?
- [ ] How: How does it work?
- [ ] Testing: How was it tested?
- [ ] Screenshots: If UI changes
- [ ] Related Issues: Link to issue tracker

### 3. PR Size
- **Small** (<200 lines): Ideal, quick to review
- **Medium** (200-500 lines): Acceptable
- **Large** (>500 lines): Should be split
- **Exception**: Generated code, migrations, major refactors (with justification)

---

## Automated Checks (CI/CD)

### Pre-Merge Checks (Must Pass)
- [ ] **Linting**: flake8, pylint, ESLint
- [ ] **Type Checking**: mypy, TypeScript compiler
- [ ] **Security Scanning**: bandit, npm audit
- [ ] **Unit Tests**: pytest, jest (≥80% coverage)
- [ ] **Integration Tests**: API tests pass
- [ ] **Secret Scanning**: No secrets detected
- [ ] **Dependency Audit**: No high/critical vulnerabilities

### Optional Checks (Should Pass)
- [ ] **Code Complexity**: McCabe complexity < 10
- [ ] **Duplicate Code**: <5% duplication
- [ ] **Documentation**: Docstrings present

---

## Review Workflow

### 1. Author Responsibilities
1. **Before Creating PR**:
   - Run all tests locally
   - Run linters and formatters
   - Write clear PR description
   - Self-review the diff

2. **During Review**:
   - Respond to comments promptly
   - Make requested changes
   - Re-request review after changes
   - Keep PR up-to-date with main branch

### 2. Reviewer Responsibilities
1. **Review Focus**:
   - Security first (critical checks)
   - Correctness (does it work?)
   - Maintainability (can we maintain it?)
   - Performance (is it efficient?)

2. **Providing Feedback**:
   - Be constructive and specific
   - Explain the "why" behind suggestions
   - Distinguish between "must fix" and "nice to have"
   - Acknowledge good practices

3. **Approval Criteria**:
   - All automated checks pass
   - Security checklist completed
   - Code quality standards met
   - Tests adequate
   - No unresolved comments

### 3. Review Comments Format
```markdown
# 🔴 BLOCKER - Must fix before merge
**Security**: This endpoint is missing authentication
Please add @require_authentication decorator

# ⚠️ IMPORTANT - Should fix before merge
**Performance**: This query causes N+1 problem
Consider using eager loading: .options(joinedload(Filing.company))

# 💡 SUGGESTION - Nice to have
**Style**: Consider using a list comprehension here
filings = [f for f in all_filings if f.form_type == '10-K']

# ✅ APPROVAL
LGTM! Great work on the comprehensive tests.
```

---

## Special Review Cases

### 1. Security-Critical Code
**Requires 2 reviewers, including 1 security reviewer**

Examples:
- Authentication/authorization code
- Cryptography implementation
- Input validation
- API key management
- Database queries

### 2. Performance-Critical Code
**Requires performance testing**

Examples:
- Database queries for large datasets
- AI model inference
- File processing
- API endpoints under heavy load

### 3. Database Migrations
**Requires extra scrutiny**

- [ ] Migration is reversible (down migration provided)
- [ ] No data loss
- [ ] Tested on production-like data
- [ ] Performance impact assessed
- [ ] Backup plan documented

---

## Review Checklist Template

Copy this checklist into each PR for manual verification:

```markdown
## Security Review
- [ ] No hardcoded credentials or secrets
- [ ] All inputs validated and sanitized
- [ ] SQL queries use parameterized statements
- [ ] Authentication/authorization present
- [ ] Error messages don't expose internals
- [ ] Logging excludes sensitive data
- [ ] Rate limiting where appropriate

## Code Quality
- [ ] Code is readable and maintainable
- [ ] Functions/classes are appropriately sized
- [ ] Type hints/types present
- [ ] Documentation updated
- [ ] No code duplication

## Testing
- [ ] Unit tests added (≥80% coverage)
- [ ] Integration tests for new APIs
- [ ] Security tests for validation
- [ ] Edge cases tested
- [ ] All tests pass

## Dependencies
- [ ] No new dependencies without justification
- [ ] Security audit passed
- [ ] Versions pinned

## Git/PR
- [ ] Clear commit messages
- [ ] PR description complete
- [ ] Related issues linked
- [ ] CI/CD checks passing

## Reviewer Approval
- [ ] Reviewed by: _______________
- [ ] Security reviewer (if required): _______________
```

---

## Escalation

### When to Escalate
- Critical security vulnerability discovered
- Disagreement on security requirements
- Uncertain about security implications
- Major architectural changes

### Escalation Path
1. **Technical Lead**: Architecture and design questions
2. **Security Reviewer**: Security-specific concerns
3. **Project Manager**: Timeline or resource concerns
4. **Engineering Manager**: Unresolved conflicts

---

## Review Metrics

### Track These Metrics
- Average PR review time
- Number of security issues found in review
- Test coverage percentage
- Number of revisions before approval
- Critical issues in production (goal: 0)

### Monthly Review
- Review metrics with team
- Identify improvement areas
- Update standards as needed
- Share lessons learned

---

## Continuous Improvement

This document is living and should be updated based on:
- Security incidents and lessons learned
- New tools and best practices
- Team feedback
- Industry standards

**Last Review**: 2025-10-18
**Next Review**: After Sprint 2
**Owner**: QA Reviewer Agent

---

## Resources

- **Python**: PEP 8, OWASP Python Security
- **TypeScript**: TSLint, TypeScript Handbook
- **Security**: OWASP Top 10, CWE Top 25
- **Testing**: Pytest docs, Jest docs
- **Git**: Conventional Commits

---

## Questions?

Contact the QA Reviewer or Security Team for clarification on any review standards.
