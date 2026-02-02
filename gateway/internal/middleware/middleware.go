// Package middleware provides HTTP middleware for the gateway
package middleware

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/sha512"
	"encoding/hex"
	"io"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5/middleware"
	"github.com/rs/zerolog/log"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
)

// Context keys
type contextKey string

const (
	// RequestStartTimeKey is the context key for request start time
	RequestStartTimeKey contextKey = "request_start_time"
	// TraceIDKey is the context key for trace ID
	TraceIDKey contextKey = "trace_id"
	// SpanIDKey is the context key for span ID
	SpanIDKey contextKey = "span_id"
)

// RequestLogger logs HTTP requests with structured logging
func RequestLogger(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

		// Store start time in context
		ctx := context.WithValue(r.Context(), RequestStartTimeKey, start)
		r = r.WithContext(ctx)

		defer func() {
			duration := time.Since(start)
			
			log.Info().
				Str("method", r.Method).
				Str("path", r.URL.Path).
				Int("status", ww.Status()).
				Int("bytes", ww.BytesWritten()).
				Dur("duration", duration).
				Str("request_id", middleware.GetReqID(r.Context())).
				Str("remote_addr", r.RemoteAddr).
				Str("user_agent", r.UserAgent()).
				Msg("Request completed")
		}()

		next.ServeHTTP(ww, r)
	})
}

// SecurityHeaders adds security headers to responses
func SecurityHeaders(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Prevent XSS attacks
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("X-Frame-Options", "DENY")
		w.Header().Set("X-XSS-Protection", "1; mode=block")
		
		// Content Security Policy
		w.Header().Set("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
		
		// Referrer policy
		w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
		
		// HSTS (if using HTTPS)
		if r.TLS != nil {
			w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
		}
		
		// Remove server identification
		w.Header().Del("Server")
		w.Header().Del("X-Powered-By")

		next.ServeHTTP(w, r)
	})
}

// Tracing adds OpenTelemetry distributed tracing
func Tracing(next http.Handler) http.Handler {
	tracer := otel.Tracer("agentauth-gateway")

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ctx, span := tracer.Start(r.Context(), r.URL.Path,
			trace.WithAttributes(
				attribute.String("http.method", r.Method),
				attribute.String("http.url", r.URL.String()),
				attribute.String("http.user_agent", r.UserAgent()),
			),
		)
		defer span.End()

		// Add trace ID to response headers
		spanCtx := span.SpanContext()
		w.Header().Set("X-Trace-ID", spanCtx.TraceID().String())

		// Store in context
		ctx = context.WithValue(ctx, TraceIDKey, spanCtx.TraceID().String())
		ctx = context.WithValue(ctx, SpanIDKey, spanCtx.SpanID().String())

		next.ServeHTTP(w, r.WithContext(ctx))

		// Record response status
		ww, ok := w.(middleware.WrapResponseWriter)
		if ok {
			span.SetAttributes(attribute.Int("http.status_code", ww.Status()))
		}
	})
}

// SignatureVerification verifies HMAC signatures on requests
func SignatureVerification(secret []byte) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip signature verification for certain paths
			if r.URL.Path == "/health" || r.URL.Path == "/ready" || r.URL.Path == "/metrics" {
				next.ServeHTTP(w, r)
				return
			}

			// Check if signature header is present
			signature := r.Header.Get("X-Signature")
			if signature == "" {
				// Signature is optional for now (can be made required via config)
				next.ServeHTTP(w, r)
				return
			}

			// Get timestamp
			timestampStr := r.Header.Get("X-Timestamp")
			if timestampStr == "" {
				http.Error(w, `{"error":"missing X-Timestamp header"}`, http.StatusBadRequest)
				return
			}

			timestamp, err := strconv.ParseInt(timestampStr, 10, 64)
			if err != nil {
				http.Error(w, `{"error":"invalid X-Timestamp header"}`, http.StatusBadRequest)
				return
			}

			// Check timestamp freshness (30 second window)
			now := time.Now().Unix()
			if abs(now-timestamp) > 30 {
				http.Error(w, `{"error":"request timestamp too old or in future"}`, http.StatusUnauthorized)
				return
			}

			// Read body for signature verification
			body, err := io.ReadAll(r.Body)
			if err != nil {
				http.Error(w, `{"error":"failed to read request body"}`, http.StatusBadRequest)
				return
			}
			r.Body = io.NopCloser(bytes.NewBuffer(body))

			// Build signature content
			// Format: METHOD:PATH:TIMESTAMP:BODY
			content := []byte(r.Method + ":" + r.URL.Path + ":" + timestampStr + ":")
			content = append(content, body...)

			// Compute expected signature
			mac := hmac.New(sha512.New, secret)
			mac.Write(content)
			expectedSig := hex.EncodeToString(mac.Sum(nil))

			// Compare signatures in constant time
			if !hmac.Equal([]byte(signature), []byte(expectedSig)) {
				log.Warn().
					Str("path", r.URL.Path).
					Str("method", r.Method).
					Msg("Invalid request signature")
				http.Error(w, `{"error":"invalid signature"}`, http.StatusUnauthorized)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// ClientCertInfo extracts client certificate information for mTLS
func ClientCertInfo(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.TLS != nil && len(r.TLS.PeerCertificates) > 0 {
			clientCert := r.TLS.PeerCertificates[0]
			
			// Store client identity in context
			ctx := context.WithValue(r.Context(), "client_cn", clientCert.Subject.CommonName)
			ctx = context.WithValue(ctx, "client_serial", clientCert.SerialNumber.String())
			ctx = context.WithValue(ctx, "client_issuer", clientCert.Issuer.CommonName)
			
			log.Debug().
				Str("client_cn", clientCert.Subject.CommonName).
				Str("client_serial", clientCert.SerialNumber.String()).
				Msg("Client certificate verified")
			
			r = r.WithContext(ctx)
		}

		next.ServeHTTP(w, r)
	})
}

// abs returns absolute value of int64
func abs(n int64) int64 {
	if n < 0 {
		return -n
	}
	return n
}
