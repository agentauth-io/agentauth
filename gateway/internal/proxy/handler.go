// Package proxy provides reverse proxy functionality
package proxy

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sync"
	"sync/atomic"
	"time"

	"github.com/agentauth/gateway/internal/auth"
	"github.com/agentauth/gateway/internal/config"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/rs/zerolog/log"
)

// Handler handles proxied requests to upstream services
type Handler struct {
	config        config.ProxyConfig
	client        *http.Client
	circuitBreaker *CircuitBreaker
	endpoints     []endpoint
	currentIndex  uint64
}

type endpoint struct {
	url     string
	healthy bool
	mu      sync.RWMutex
}

// CircuitBreaker implements the circuit breaker pattern
type CircuitBreaker struct {
	failures    int64
	threshold   int
	lastFailure time.Time
	timeout     time.Duration
	state       int32 // 0=closed, 1=open, 2=half-open
	mu          sync.RWMutex
}

// NewHandler creates a new proxy handler
func NewHandler(cfg config.ProxyConfig) *Handler {
	// Build endpoint list
	endpoints := make([]endpoint, 0)
	if len(cfg.Endpoints) > 0 {
		for _, url := range cfg.Endpoints {
			endpoints = append(endpoints, endpoint{url: url, healthy: true})
		}
	} else {
		endpoints = append(endpoints, endpoint{url: cfg.UpstreamURL, healthy: true})
	}

	h := &Handler{
		config: cfg,
		client: &http.Client{
			Timeout: cfg.Timeout,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 100,
				IdleConnTimeout:     90 * time.Second,
			},
		},
		circuitBreaker: &CircuitBreaker{
			threshold: cfg.CircuitBreakerThreshold,
			timeout:   cfg.CircuitBreakerTimeout,
		},
		endpoints: endpoints,
	}

	// Start health checker
	go h.healthCheck()

	return h
}

// Authorize proxies authorization requests
func (h *Handler) Authorize(w http.ResponseWriter, r *http.Request) {
	h.proxyRequest(w, r, "/v1/authorize", "POST")
}

// GetAuthorization proxies get authorization requests
func (h *Handler) GetAuthorization(w http.ResponseWriter, r *http.Request) {
	requestID := chi.URLParam(r, "requestID")
	h.proxyRequest(w, r, "/v1/authorize/"+requestID, "GET")
}

// RevokeAuthorization proxies revoke requests
func (h *Handler) RevokeAuthorization(w http.ResponseWriter, r *http.Request) {
	requestID := chi.URLParam(r, "requestID")
	h.proxyRequest(w, r, "/v1/authorize/"+requestID+"/revoke", "POST")
}

// ListPolicies proxies list policies requests
func (h *Handler) ListPolicies(w http.ResponseWriter, r *http.Request) {
	h.proxyRequest(w, r, "/v1/policies", "GET")
}

// CreatePolicy proxies create policy requests
func (h *Handler) CreatePolicy(w http.ResponseWriter, r *http.Request) {
	h.proxyRequest(w, r, "/v1/policies", "POST")
}

// GetPolicy proxies get policy requests
func (h *Handler) GetPolicy(w http.ResponseWriter, r *http.Request) {
	policyID := chi.URLParam(r, "policyID")
	h.proxyRequest(w, r, "/v1/policies/"+policyID, "GET")
}

// UpdatePolicy proxies update policy requests
func (h *Handler) UpdatePolicy(w http.ResponseWriter, r *http.Request) {
	policyID := chi.URLParam(r, "policyID")
	h.proxyRequest(w, r, "/v1/policies/"+policyID, "PUT")
}

// DeletePolicy proxies delete policy requests
func (h *Handler) DeletePolicy(w http.ResponseWriter, r *http.Request) {
	policyID := chi.URLParam(r, "policyID")
	h.proxyRequest(w, r, "/v1/policies/"+policyID, "DELETE")
}

// TogglePolicy proxies toggle policy requests
func (h *Handler) TogglePolicy(w http.ResponseWriter, r *http.Request) {
	policyID := chi.URLParam(r, "policyID")
	h.proxyRequest(w, r, "/v1/policies/"+policyID+"/toggle", "POST")
}

// ListAgents proxies list agents requests
func (h *Handler) ListAgents(w http.ResponseWriter, r *http.Request) {
	h.proxyRequest(w, r, "/v1/agents", "GET")
}

// RegisterAgent proxies register agent requests
func (h *Handler) RegisterAgent(w http.ResponseWriter, r *http.Request) {
	h.proxyRequest(w, r, "/v1/agents", "POST")
}

// GetAgent proxies get agent requests
func (h *Handler) GetAgent(w http.ResponseWriter, r *http.Request) {
	agentID := chi.URLParam(r, "agentID")
	h.proxyRequest(w, r, "/v1/agents/"+agentID, "GET")
}

// RevokeAgent proxies revoke agent requests
func (h *Handler) RevokeAgent(w http.ResponseWriter, r *http.Request) {
	agentID := chi.URLParam(r, "agentID")
	h.proxyRequest(w, r, "/v1/agents/"+agentID, "DELETE")
}

// ListAuditLogs proxies list audit logs requests
func (h *Handler) ListAuditLogs(w http.ResponseWriter, r *http.Request) {
	h.proxyRequest(w, r, "/v1/audit", "GET")
}

// GetAuditEntry proxies get audit entry requests
func (h *Handler) GetAuditEntry(w http.ResponseWriter, r *http.Request) {
	entryID := chi.URLParam(r, "entryID")
	h.proxyRequest(w, r, "/v1/audit/"+entryID, "GET")
}

// GetAuditProof proxies get audit proof requests
func (h *Handler) GetAuditProof(w http.ResponseWriter, r *http.Request) {
	entryID := chi.URLParam(r, "entryID")
	h.proxyRequest(w, r, "/v1/audit/"+entryID+"/proof", "GET")
}

// VerifyToken proxies token verification requests
func (h *Handler) VerifyToken(w http.ResponseWriter, r *http.Request) {
	h.proxyRequest(w, r, "/v1/tokens/verify", "POST")
}

// ListKeys proxies list keys requests
func (h *Handler) ListKeys(w http.ResponseWriter, r *http.Request) {
	h.proxyRequest(w, r, "/v1/keys", "GET")
}

// RotateKeys proxies rotate keys requests
func (h *Handler) RotateKeys(w http.ResponseWriter, r *http.Request) {
	h.proxyRequest(w, r, "/v1/keys/rotate", "POST")
}

// proxyRequest forwards a request to the upstream service
func (h *Handler) proxyRequest(w http.ResponseWriter, r *http.Request, path string, method string) {
	// Check circuit breaker
	if !h.circuitBreaker.Allow() {
		log.Warn().Msg("Circuit breaker open, rejecting request")
		h.sendError(w, http.StatusServiceUnavailable, "service temporarily unavailable")
		return
	}

	// Get upstream URL (round-robin load balancing)
	upstreamURL := h.getUpstream()
	if upstreamURL == "" {
		h.sendError(w, http.StatusServiceUnavailable, "no healthy upstream available")
		return
	}

	// Read request body
	var body []byte
	var err error
	if r.Body != nil {
		body, err = io.ReadAll(r.Body)
		if err != nil {
			h.sendError(w, http.StatusBadRequest, "failed to read request body")
			return
		}
	}

	// Retry logic
	var lastErr error
	for attempt := 0; attempt <= h.config.RetryCount; attempt++ {
		if attempt > 0 {
			time.Sleep(h.config.RetryDelay * time.Duration(attempt))
		}

		err = h.doRequest(w, r, upstreamURL+path, method, body)
		if err == nil {
			h.circuitBreaker.RecordSuccess()
			return
		}

		lastErr = err
		log.Warn().
			Err(err).
			Int("attempt", attempt+1).
			Str("path", path).
			Msg("Request failed, retrying")
	}

	// All retries failed
	h.circuitBreaker.RecordFailure()
	log.Error().Err(lastErr).Str("path", path).Msg("All retry attempts failed")
	h.sendError(w, http.StatusBadGateway, "upstream request failed")
}

// doRequest performs the actual HTTP request
func (h *Handler) doRequest(w http.ResponseWriter, r *http.Request, url string, method string, body []byte) error {
	ctx, cancel := context.WithTimeout(r.Context(), h.config.Timeout)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, method, url, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	// Copy relevant headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Request-ID", middleware.GetReqID(r.Context()))
	
	// Forward API key
	if apiKey, ok := auth.GetAPIKey(r.Context()); ok {
		req.Header.Set("X-API-Key", apiKey)
	}

	// Forward additional headers
	for _, header := range []string{"X-Forwarded-For", "X-Real-IP", "Accept", "Accept-Language"} {
		if val := r.Header.Get(header); val != "" {
			req.Header.Set(header, val)
		}
	}

	// Add gateway identification
	req.Header.Set("X-Gateway-ID", "agentauth-gateway")
	req.Header.Set("X-Forwarded-Host", r.Host)

	// Perform request
	resp, err := h.client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read response
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read response: %w", err)
	}

	// Copy response headers
	for key, values := range resp.Header {
		for _, value := range values {
			w.Header().Add(key, value)
		}
	}

	// Write response
	w.WriteHeader(resp.StatusCode)
	w.Write(respBody)

	return nil
}

// getUpstream returns the next healthy upstream URL
func (h *Handler) getUpstream() string {
	for i := 0; i < len(h.endpoints); i++ {
		idx := atomic.AddUint64(&h.currentIndex, 1) % uint64(len(h.endpoints))
		ep := &h.endpoints[idx]
		
		ep.mu.RLock()
		healthy := ep.healthy
		url := ep.url
		ep.mu.RUnlock()

		if healthy {
			return url
		}
	}
	return ""
}

// healthCheck periodically checks upstream health
func (h *Handler) healthCheck() {
	ticker := time.NewTicker(h.config.HealthCheckInterval)
	defer ticker.Stop()

	for range ticker.C {
		for i := range h.endpoints {
			ep := &h.endpoints[i]
			
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			req, _ := http.NewRequestWithContext(ctx, "GET", ep.url+"/health", nil)
			resp, err := h.client.Do(req)
			cancel()

			ep.mu.Lock()
			if err != nil || resp.StatusCode != http.StatusOK {
				if ep.healthy {
					log.Warn().Str("url", ep.url).Msg("Upstream marked unhealthy")
				}
				ep.healthy = false
			} else {
				if !ep.healthy {
					log.Info().Str("url", ep.url).Msg("Upstream marked healthy")
				}
				ep.healthy = true
			}
			ep.mu.Unlock()

			if resp != nil {
				resp.Body.Close()
			}
		}
	}
}

// sendError sends a JSON error response
func (h *Handler) sendError(w http.ResponseWriter, status int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]string{"error": message})
}

// Circuit breaker methods
func (cb *CircuitBreaker) Allow() bool {
	state := atomic.LoadInt32(&cb.state)
	
	switch state {
	case 0: // Closed
		return true
	case 1: // Open
		cb.mu.RLock()
		elapsed := time.Since(cb.lastFailure)
		cb.mu.RUnlock()
		
		if elapsed > cb.timeout {
			// Transition to half-open
			atomic.StoreInt32(&cb.state, 2)
			return true
		}
		return false
	case 2: // Half-open
		return true
	}
	
	return true
}

func (cb *CircuitBreaker) RecordSuccess() {
	atomic.StoreInt64(&cb.failures, 0)
	atomic.StoreInt32(&cb.state, 0) // Close circuit
}

func (cb *CircuitBreaker) RecordFailure() {
	failures := atomic.AddInt64(&cb.failures, 1)
	
	cb.mu.Lock()
	cb.lastFailure = time.Now()
	cb.mu.Unlock()

	if failures >= int64(cb.threshold) {
		atomic.StoreInt32(&cb.state, 1) // Open circuit
		log.Warn().Int64("failures", failures).Msg("Circuit breaker opened")
	}
}
