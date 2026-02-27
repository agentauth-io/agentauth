"""
Security headers middleware.

Adds standard security headers to all responses.
"""

from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Production-ready CSP with support for legitimate resources
        settings = get_settings()
        if settings.environment == "production":
            # Strict CSP for production
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'nonce-{nonce}'",
                "style-src 'self' 'unsafe-inline'",
                "font-src 'self' data:",
                "img-src 'self' data: https:",
                "connect-src 'self' https://api.stripe.com",
                "frame-src 'self' https://js.stripe.com",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        else:
            # More permissive CSP for development
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                "font-src 'self' https://fonts.gstatic.com data:",
                "img-src 'self' data: https: http:",
                "connect-src 'self' https://api.stripe.com ws://localhost:* ws://127.0.0.1:*",
                "frame-src 'self' https://js.stripe.com",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        return response
