// Package main is the entry point for the AgentAuth Gateway
// A high-performance, security-focused edge gateway with mTLS support.
package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/agentauth/gateway/internal/auth"
	"github.com/agentauth/gateway/internal/config"
	"github.com/agentauth/gateway/internal/middleware"
	"github.com/agentauth/gateway/internal/proxy"
	"github.com/agentauth/gateway/internal/ratelimit"
	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

func main() {
	// Initialize structured logging
	zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr})

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to load configuration")
	}

	log.Info().
		Str("version", cfg.Version).
		Str("environment", cfg.Environment).
		Int("port", cfg.Port).
		Bool("mtls_enabled", cfg.MTLSEnabled).
		Msg("Starting AgentAuth Gateway")

	// Initialize components
	rateLimiter := ratelimit.New(cfg.RateLimitConfig)
	authenticator := auth.NewAuthenticator(cfg.AuthConfig)
	proxyHandler := proxy.NewHandler(cfg.ProxyConfig)

	// Create router
	r := chi.NewRouter()

	// Global middleware
	r.Use(chimiddleware.RequestID)
	r.Use(chimiddleware.RealIP)
	r.Use(middleware.RequestLogger)
	r.Use(chimiddleware.Recoverer)
	r.Use(middleware.SecurityHeaders)
	r.Use(middleware.Tracing)

	// CORS configuration
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   cfg.CORSOrigins,
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-API-Key", "X-Request-ID", "X-Signature", "X-Timestamp"},
		ExposedHeaders:   []string{"X-Request-ID", "X-RateLimit-Remaining"},
		AllowCredentials: true,
		MaxAge:           300,
	}))

	// Health endpoints (no auth required)
	r.Get("/health", healthHandler)
	r.Get("/ready", readyHandler)
	r.Handle("/metrics", promhttp.Handler())

	// API routes with authentication
	r.Route("/v1", func(r chi.Router) {
		// Rate limiting per API key
		r.Use(rateLimiter.Middleware)

		// Request signature verification
		r.Use(middleware.SignatureVerification(cfg.SigningSecret))

		// API key authentication
		r.Use(authenticator.Middleware)

		// Authorization endpoints
		r.Post("/authorize", proxyHandler.Authorize)
		r.Get("/authorize/{requestID}", proxyHandler.GetAuthorization)
		r.Post("/authorize/{requestID}/revoke", proxyHandler.RevokeAuthorization)

		// Policy endpoints
		r.Route("/policies", func(r chi.Router) {
			r.Get("/", proxyHandler.ListPolicies)
			r.Post("/", proxyHandler.CreatePolicy)
			r.Get("/{policyID}", proxyHandler.GetPolicy)
			r.Put("/{policyID}", proxyHandler.UpdatePolicy)
			r.Delete("/{policyID}", proxyHandler.DeletePolicy)
			r.Post("/{policyID}/toggle", proxyHandler.TogglePolicy)
		})

		// Agent endpoints
		r.Route("/agents", func(r chi.Router) {
			r.Get("/", proxyHandler.ListAgents)
			r.Post("/", proxyHandler.RegisterAgent)
			r.Get("/{agentID}", proxyHandler.GetAgent)
			r.Delete("/{agentID}", proxyHandler.RevokeAgent)
		})

		// Audit endpoints
		r.Route("/audit", func(r chi.Router) {
			r.Get("/", proxyHandler.ListAuditLogs)
			r.Get("/{entryID}", proxyHandler.GetAuditEntry)
			r.Get("/{entryID}/proof", proxyHandler.GetAuditProof)
		})

		// Token verification
		r.Post("/tokens/verify", proxyHandler.VerifyToken)

		// Key management (admin only)
		r.Route("/keys", func(r chi.Router) {
			r.Use(authenticator.RequireAdmin)
			r.Get("/", proxyHandler.ListKeys)
			r.Post("/rotate", proxyHandler.RotateKeys)
		})
	})

	// Bootstrap endpoint (protected by bootstrap secret)
	r.Post("/v1/bootstrap", authenticator.Bootstrap)

	// Create server
	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Port),
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Configure TLS if enabled
	if cfg.MTLSEnabled {
		tlsConfig, err := configureMTLS(cfg)
		if err != nil {
			log.Fatal().Err(err).Msg("Failed to configure mTLS")
		}
		server.TLSConfig = tlsConfig
	}

	// Start server in goroutine
	go func() {
		var err error
		if cfg.MTLSEnabled {
			log.Info().Int("port", cfg.Port).Msg("Starting HTTPS server with mTLS")
			err = server.ListenAndServeTLS(cfg.TLSCertFile, cfg.TLSKeyFile)
		} else {
			log.Info().Int("port", cfg.Port).Msg("Starting HTTP server")
			err = server.ListenAndServe()
		}
		if err != nil && err != http.ErrServerClosed {
			log.Fatal().Err(err).Msg("Server failed")
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info().Msg("Shutting down server...")

	// Graceful shutdown with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Error().Err(err).Msg("Server forced to shutdown")
	}

	log.Info().Msg("Server stopped")
}

// configureMTLS sets up mutual TLS authentication
// Uses X25519 (Curve25519) for key exchange - NOT P-256/NIST curves
// Security rationale:
// - X25519 designed by DJB with full transparency (no NSA influence)
// - Resistant to timing/side-channel attacks
// - Faster than NIST curves
// - Used by Signal, WireGuard, SSH, Tor
func configureMTLS(cfg *config.Config) (*tls.Config, error) {
	// Load CA certificate for client verification
	caCert, err := os.ReadFile(cfg.TLSCAFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read CA certificate: %w", err)
	}

	caCertPool := x509.NewCertPool()
	if !caCertPool.AppendCertsFromPEM(caCert) {
		return nil, fmt.Errorf("failed to parse CA certificate")
	}

	// Load server certificate
	serverCert, err := tls.LoadX509KeyPair(cfg.TLSCertFile, cfg.TLSKeyFile)
	if err != nil {
		return nil, fmt.Errorf("failed to load server certificate: %w", err)
	}

	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{serverCert},
		ClientCAs:    caCertPool,
		ClientAuth:   tls.RequireAndVerifyClientCert,
		MinVersion:   tls.VersionTLS13,
		// TLS 1.3 cipher suites (Go handles these automatically in TLS 1.3)
		// All use AEAD and are considered secure
		CipherSuites: []uint16{
			tls.TLS_CHACHA20_POLY1305_SHA256, // Prefer ChaCha20 (faster on non-AES-NI)
			tls.TLS_AES_256_GCM_SHA384,
			tls.TLS_AES_128_GCM_SHA256,
		},
		// Explicitly prefer X25519 over NIST P-256 curves
		// X25519 is immune to timing attacks and has no NSA influence
		CurvePreferences: []tls.CurveID{
			tls.X25519,    // Curve25519 - PREFERRED (DJB, transparent design)
			// NOTE: We explicitly EXCLUDE P-256 due to NSA concerns
			// tls.CurveP256 - EXCLUDED (NIST, potential backdoors)
			// tls.CurveP384 - EXCLUDED (NIST)
			// tls.CurveP521 - EXCLUDED (NIST)
		},
		PreferServerCipherSuites: true,
		// Additional security hardening
		SessionTicketsDisabled: false, // Enable for performance
		Renegotiation:          tls.RenegotiateNever,
	}

	return tlsConfig, nil
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"healthy","service":"agentauth-gateway"}`))
}

func readyHandler(w http.ResponseWriter, r *http.Request) {
	// TODO: Add actual readiness checks (database, cache, upstream)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"ready"}`))
}
