# Security Fixes - Quick Action Guide

## ✅ COMPLETED (7/12)

1. ✅ **CRITICAL**: Fixed CORS configuration
2. ✅ **CRITICAL**: Added API key validation  
3. ✅ **HIGH**: Removed database from repo
4. ✅ **HIGH**: Created logger utility
5. ✅ **MEDIUM**: Added input validation
6. ✅ **MEDIUM**: Added rate limiting infrastructure
7. ✅ **LOW**: Fixed debug mode

---

## 🚀 NEXT ACTIONS REQUIRED

### TODAY (Critical)

#### 1. Install New Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### 2. Set Environment Variables
```bash
# Edit backend/.env
MINO_API_KEY=your_actual_key_here
FLASK_ENV=development  # or production
ALLOWED_ORIGINS=https://yourdomain.com  # for production only
```

#### 3. Test the Backend
```bash
cd backend
python app.py
# Should start successfully with proper env vars
```

---

### THIS WEEK (High Priority)

#### 4. Apply Rate Limiting to Endpoints

**File:** `backend/app.py`

Add at top:
```python
from rate_limit import init_rate_limiter, SEARCH_LIMIT, COMPARE_LIMIT

limiter = init_rate_limiter(app)
```

Apply to endpoints:
```python
@app.route("/api/search", methods=["POST"])
@limiter.limit(SEARCH_LIMIT)
def search_model():
    # ...

@app.route("/api/compare", methods=["POST"])
@limiter.limit(COMPARE_LIMIT)
def compare_models():
    # ...
```

#### 5. Replace Console Logs in Frontend

**Files to update:**
- `src/pages/Index.tsx`
- `src/pages/Home.tsx`
- `src/pages/CompareSimple.tsx`
- `src/pages/Benchmarks.tsx`
- `src/hooks/useModelComparison.ts`
- `src/components/MultimodalRecommendation.tsx`

**Find & Replace:**
```typescript
// Before
console.log(...)
console.error(...)

// After
import { logger } from '@/lib/logger';
logger.log(...)
logger.error(...)
```

#### 6. Fix Hardcoded URLs

**Files to update:** All files with `|| 'http://localhost:5000'`

**Change:**
```typescript
// Before
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// After
const API_BASE_URL = import.meta.env.VITE_API_URL;
if (!API_BASE_URL) {
  throw new Error('VITE_API_URL environment variable is required');
}
```

---

### THIS MONTH (Medium Priority)

#### 7. Add Security Headers

**File:** `backend/app.py`

Add after CORS:
```python
from flask_talisman import Talisman

Talisman(app,
    force_https=True,
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,
    content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'"],
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", "data:", "https:"],
    },
    content_security_policy_nonce_in=['script-src']
)
```

#### 8. Refactor SQL Queries

**File:** `backend/phase2/database.py:355-369`

Use named parameters:
```python
def get_regression_history(conn, model_id=None, severity=None, limit=50):
    conditions = []
    params = {}
    
    if model_id:
        conditions.append("model_id = :model_id")
        params["model_id"] = model_id
    
    if severity:
        conditions.append("severity = :severity")
        params["severity"] = severity
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT * FROM regression_events WHERE {where_clause} ORDER BY detected_at DESC LIMIT :limit"
    params["limit"] = limit
    
    cursor.execute(query, params)
```

---

## 📋 Testing Checklist

Before deploying:

```bash
# Test 1: API key validation
unset MINO_API_KEY
python backend/app.py
# Should fail with clear error message

# Test 2: CORS in production
export FLASK_ENV=production
export MINO_API_KEY=test_key_1234567890
python backend/app.py
# Should warn about missing ALLOWED_ORIGINS

# Test 3: Input validation
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"model_name": "../../etc/passwd"}'
# Should return validation error

# Test 4: Rate limiting (after applying decorators)
for i in {1..15}; do 
  curl http://localhost:5000/api/sources
done
# Should eventually return 429 Too Many Requests
```

---

## 🔒 Production Deployment Checklist

- [ ] `MINO_API_KEY` set in production environment
- [ ] `ALLOWED_ORIGINS` set to your domain(s)
- [ ] `FLASK_ENV=production`
- [ ] `FLASK_DEBUG=false` or not set
- [ ] Rate limiting configured (Redis recommended)
- [ ] Security headers enabled (Talisman)
- [ ] All console.log replaced with logger
- [ ] HTTPS enforced
- [ ] Error tracking configured (Sentry/Rollbar)
- [ ] Security audit completed

---

## 📞 Support

**Documentation:**
- Full Report: `SECURITY_AUDIT_REPORT.md`
- Fixes Applied: `SECURITY_FIXES_APPLIED.md`
- Vulnerabilities Summary: `VULNERABILITIES_SUMMARY.md`

**Quick Commands:**
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run tests
python -m pytest backend/tests/

# Check for security issues
pip-audit
npm audit
```

---

**Last Updated:** 2026-01-23  
**Status:** 7/12 Fixed - Ready for Next Phase
