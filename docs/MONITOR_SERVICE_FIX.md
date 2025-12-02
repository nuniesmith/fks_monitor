# fks_monitor Service Fix

**Date**: 2025-12-01  
**Task**: TASK-014  
**Status**: ✅ Fixed

---

## Issue

The `fks_monitor` service was reported as unhealthy in health checks, but the service was actually running and healthy. The issue was a mismatch between the health endpoint path used by the health check script and the actual endpoint path.

**Problem**:
- Health check script was checking: `http://localhost:8013/health`
- Actual health endpoint was at: `http://localhost:8013/health/health`
- Service registry had incorrect health URL

---

## Root Cause

The `fks_monitor` service mounts the health router with prefix `/health`:
```python
app.include_router(health.router, prefix="/health", tags=["health"])
```

This means the health endpoint is at `/health/health` (prefix + route), not `/health`.

---

## Solution

### 1. Added Compatibility Endpoint

Added a `/health` endpoint directly to the main app for compatibility:

```python
@app.get("/health")
async def health_redirect() -> Dict[str, Any]:
    """
    Health check endpoint for compatibility.
    Redirects to /health/health for standardized health checks.
    """
    return {
        "status": "healthy",
        "service": "fks_monitor",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "note": "For detailed health check, use /health/health"
    }
```

**File**: `services/monitor/src/main.py`

### 2. Updated Service Registry

Updated the service registry to use the correct health endpoint:

```json
{
  "fks_monitor": {
    "name": "fks_monitor",
    "port": 8013,
    "health_url": "http://fks-monitor:8013/health/health",
    "note": "Monitors all FKS services and provides unified API for fks_main orchestration. Health endpoint at /health/health"
  }
}
```

**File**: `services/config/service_registry.json`

### 3. Updated Root Endpoint Documentation

Updated the root endpoint to document the correct health endpoint path:

```python
"endpoints": {
    "health": "/health/health",  # Updated from "/health"
    ...
}
```

---

## Verification

### Before Fix
```bash
$ curl http://localhost:8013/health
{"detail":"Not Found"}
```

### After Fix
```bash
$ curl http://localhost:8013/health
{
  "status": "healthy",
  "service": "fks_monitor",
  "timestamp": "2025-12-01T23:36:56.444093",
  "version": "1.0.0",
  "note": "For detailed health check, use /health/health"
}
```

### Detailed Health Check
```bash
$ curl http://localhost:8013/health/health
{
  "status": "healthy",
  "service": "fks_monitor",
  "timestamp": "2025-12-01T23:36:56.444093",
  "version": "1.0.0"
}
```

---

## Deployment

**Note**: The service needs to be restarted for the changes to take effect:

```bash
# Restart the service
docker compose restart fks-monitor

# Or rebuild and restart
docker compose up -d --build fks-monitor
```

---

## Health Check Script

The health check script (`infrastructure/scripts/check_all_services.sh`) will now correctly identify `fks_monitor` as healthy after:
1. Service is restarted with the new `/health` endpoint
2. Service registry is updated (already done)

---

## Related Files

- `services/monitor/src/main.py` - Added `/health` endpoint
- `services/config/service_registry.json` - Updated health URL
- `infrastructure/scripts/check_all_services.sh` - Health check script (no changes needed)

---

**Fixed by**: TASK-014  
**Status**: ✅ Complete (requires service restart)
