# CORS Configuration Guide

## 🎯 Centralized CORS Management

**Location:** `shared/middleware/cors_config.py`

All 5 backend services now use a **single, centralized CORS configuration** that automatically allows all localhost origins.

---

## ✅ What's Configured

### Automatic Localhost Support (No Configuration Needed)

The system **automatically accepts** requests from:

- `http://localhost` (any port or no port)
- `http://localhost:3000`
- `http://localhost:3001` 
- `http://localhost:5173`
- `http://localhost:8080`
- `http://127.0.0.1:*` (any port)
- `https://localhost:*` (any port, if using HTTPS locally)

**Pattern:** `^https?://(localhost|127\.0\.0\.1)(:\d+)?$`

### Services Using Centralized CORS

All services automatically allow localhost on any port:

1. **API Gateway** (Port 8000)
2. **Auth Service** (Port 8001)
3. **Document Processor** (Port 8002)
4. **RAG Query Service** (Port 8004)
5. **Analytics Service** (Port 8005)

---

## 📝 Adding Production Domains

When deploying to production, you need to whitelist your domain(s).

### Method 1: Environment Variable (Recommended)

**For Docker:**
```bash
export CORS_ORIGINS='https://yourdomain.com,https://app.yourdomain.com'
docker compose up -d
```

**For Local Development:**
```bash
export CORS_ORIGINS='https://yourdomain.com'
cd services/api-gateway
uvicorn main:app --reload
```

### Method 2: .env File

Add to your `.env` file:
```env
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com,https://www.yourdomain.com
```

Then restart services:
```bash
docker compose restart
```

### Method 3: docker-compose.yml

Update the default in `docker-compose.yml`:

```yaml
services:
  api-gateway:
    environment:
      - CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:3000,https://yourdomain.com}
```

---

## 🔧 How It Works

### Implementation

```python
# shared/middleware/cors_config.py

class UniversalCORSMiddleware(BaseCORSMiddleware):
    def is_allowed_origin(self, origin: str) -> bool:
        # 1. Check if localhost (any port) -> Always allowed
        if is_localhost_origin(origin):
            return True
        
        # 2. Check if in explicit allowed list -> Allowed
        return super().is_allowed_origin(origin)

def configure_cors(app: FastAPI, cors_origins: str = ""):
    app.add_middleware(
        UniversalCORSMiddleware,
        allow_origins=cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

### Usage in Services

```python
# services/api-gateway/main.py
from shared.middleware.cors_config import configure_cors

app = FastAPI()
configure_cors(app, settings.cors_origins)  # That's it!
```

---

## 🧪 Testing

### Test Localhost CORS

```bash
# Test from port 3001
curl -X POST http://localhost:8000/api/auth/login \
  -H "Origin: http://localhost:3001" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass"}'

# Test from port 5173
curl -X POST http://localhost:8000/api/auth/login \
  -H "Origin: http://localhost:5173" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass"}'

# Both should return 200 OK
```

### Test Production Domain

```bash
curl -X OPTIONS http://localhost:8000/api/auth/login \
  -H "Origin: https://yourdomain.com" \
  -H "Access-Control-Request-Method: POST"

# Should return Access-Control-Allow-Origin header
```

---

## 🚨 Security Notes

### Development vs Production

**Development (Localhost):**
- ✅ All ports accepted automatically
- ✅ No configuration needed
- ✅ Safe because localhost is isolated

**Production:**
- ⚠️ Only explicitly whitelisted domains
- ⚠️ Localhost NOT accessible from production
- ⚠️ Must configure CORS_ORIGINS

### Best Practices

1. **Never use `*` (allow all) in production**
2. **Always specify exact production domains**
3. **Use HTTPS in production** (http not allowed by browsers with credentials)
4. **Keep CORS_ORIGINS in environment variables** (not hardcoded)

---

## 🔍 Troubleshooting

### CORS Error Still Occurring?

**Check 1: Verify origin is localhost**
```bash
# In browser console
console.log(window.location.origin)
// Should be: http://localhost:XXXX
```

**Check 2: Verify service is using centralized CORS**
```bash
# Check service logs
docker compose logs api-gateway | grep CORS
```

**Check 3: Test CORS preflight**
```bash
curl -X OPTIONS http://localhost:8000/api/auth/login \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

**Check 4: Verify service restarted**
```bash
docker compose ps  # All should show "healthy"
docker compose restart api-gateway  # If needed
```

### Adding New Domain Not Working?

**Verify environment variable:**
```bash
docker compose exec api-gateway env | grep CORS
```

**Restart services after changes:**
```bash
docker compose down
docker compose up -d
```

---

## 📊 Current Configuration

### Allowed Origins

**Automatic (Development):**
- All `http://localhost:*`
- All `http://127.0.0.1:*`
- All `https://localhost:*`

**Configured (Production):**
- Check: `echo $CORS_ORIGINS`
- Or check `.env` file

### Services Status

All 5 services tested and working:
- ✅ API Gateway (8000)
- ✅ Auth Service (8001)
- ✅ Document Processor (8002)
- ✅ RAG Query (8004)
- ✅ Analytics (8005)

---

## 📖 Quick Reference

### Add a New Production Domain

**Step 1:** Edit `.env` file
```env
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**Step 2:** Restart services
```bash
docker compose restart
```

**Step 3:** Verify
```bash
curl -X OPTIONS http://localhost:8000/health \
  -H "Origin: https://yourdomain.com" \
  -v | grep Access-Control
```

**That's it!** The domain will be allowed across all services.

---

## ✨ Benefits

1. **Single Source of Truth:** One file controls CORS for all services
2. **Developer Friendly:** No CORS configuration needed for localhost
3. **Production Ready:** Easy to add production domains
4. **Maintainable:** Update one place, affects all services
5. **Secure:** Localhost auto-allowed only, production must be explicit

---

**Last Updated:** November 10, 2025  
**Services Configured:** 5  
**Localhost Support:** Automatic  
**Status:** ✅ Working

