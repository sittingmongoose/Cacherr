# Mount Problem Documentation

This document tracks all attempts and fixes related to mount issues in the Cacherr Docker container.

## Issue: Plex Token SecretStr Error in Test Mode

**Date:** 2025-01-11  
**Error:** `Header part (SecretStr('**********')) from ('X-Plex-Token', SecretStr('**********')) must be of type str or bytes, not <class 'pydantic.types.SecretStr'>`

### Problem Description
When hitting test mode on the dashboard, the application was failing with a SecretStr type error when trying to fetch watchlist media from Plex. The error occurred because the Plex token was stored as a Pydantic `SecretStr` object, but the `MyPlexAccount` constructor expected a plain string.

### Root Cause
In `src/core/plex_operations.py`, the `fetch_watchlist_media()` method was passing `self.config.plex.token` directly to `MyPlexAccount(token=...)` without converting the `SecretStr` object to a string first.

### Solution Applied
Modified the `fetch_watchlist_media()` method in `src/core/plex_operations.py` to properly handle the `SecretStr` token conversion:

```python
# Convert SecretStr to string if needed
token_value = None
if getattr(self.config.plex, 'token', None) is not None:
    try:
        token_value = self.config.plex.token.get_secret_value()  # type: ignore[attr-defined]
    except Exception:
        token_value = str(self.config.plex.token)

if not token_value or not str(token_value).strip():
    self.logger.error("No valid Plex token available for watchlist access")
    return []

account = MyPlexAccount(token=token_value)
```

### Files Modified
- `src/core/plex_operations.py` - Fixed SecretStr to string conversion in `fetch_watchlist_media()` method

### Verification
- No linting errors introduced
- Pattern matches existing token handling in `get_plex_connection()` method
- Consistent with token handling in `plex_cache_engine.py`

### Status
✅ **RESOLVED** - Test mode should now work without SecretStr errors when fetching watchlist media.
