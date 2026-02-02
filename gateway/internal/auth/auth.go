// Package auth provides authentication functionality for the gateway
package auth

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/agentauth/gateway/internal/config"
	"github.com/rs/zerolog/log"
)

// Context keys for auth information
type authContextKey string

const (
	// APIKeyContextKey stores the API key in context
	APIKeyContextKey authContextKey = "api_key"
	// APIKeyInfoContextKey stores API key info in context
	APIKeyInfoContextKey authContextKey = "api_key_info"
	// IsAdminContextKey stores admin status in context
	IsAdminContextKey authContextKey = "is_admin"
)

// APIKeyInfo contains information about an API key
type APIKeyInfo struct {
	KeyID     string    `json:"key_id"`
	Owner     string    `json:"owner"`
	Tier      string    `json:"tier"`
	Scopes    []string  `json:"scopes"`
	RateLimit int       `json:"rate_limit"`
	IsAdmin   bool      `json:"is_admin"`
	CreatedAt time.Time `json:"created_at"`
	ExpiresAt *time.Time `json:"expires_at,omitempty"`
}

// Authenticator handles API key authentication
type Authenticator struct {
	config config.AuthConfig
	cache  *keyCache
	client *http.Client
}

// keyCache provides thread-safe caching of validated API keys
type keyCache struct {
	mu      sync.RWMutex
	entries map[string]*cacheEntry
	ttl     time.Duration
}

type cacheEntry struct {
	info      *APIKeyInfo
	expiresAt time.Time
}

// NewAuthenticator creates a new authenticator
func NewAuthenticator(cfg config.AuthConfig) *Authenticator {
	return &Authenticator{
		config: cfg,
		cache: &keyCache{
			entries: make(map[string]*cacheEntry),
			ttl:     cfg.CacheTTL,
		},
		client: &http.Client{
			Timeout: 5 * time.Second,
		},
	}
}

// Middleware is the authentication middleware
func (a *Authenticator) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract API key from header or query parameter
		apiKey := r.Header.Get("X-API-Key")
		if apiKey == "" {
			apiKey = r.URL.Query().Get("api_key")
		}

		if apiKey == "" {
			a.sendError(w, http.StatusUnauthorized, "missing API key")
			return
		}

		// Validate API key
		keyInfo, err := a.validateKey(r.Context(), apiKey)
		if err != nil {
			log.Warn().Err(err).Str("key_prefix", maskKey(apiKey)).Msg("API key validation failed")
			a.sendError(w, http.StatusUnauthorized, "invalid API key")
			return
		}

		// Check expiration
		if keyInfo.ExpiresAt != nil && time.Now().After(*keyInfo.ExpiresAt) {
			a.sendError(w, http.StatusUnauthorized, "API key expired")
			return
		}

		// Store in context
		ctx := context.WithValue(r.Context(), APIKeyContextKey, apiKey)
		ctx = context.WithValue(ctx, APIKeyInfoContextKey, keyInfo)
		ctx = context.WithValue(ctx, IsAdminContextKey, keyInfo.IsAdmin)

		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// RequireAdmin middleware ensures the request is from an admin
func (a *Authenticator) RequireAdmin(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		isAdmin, ok := r.Context().Value(IsAdminContextKey).(bool)
		if !ok || !isAdmin {
			a.sendError(w, http.StatusForbidden, "admin access required")
			return
		}
		next.ServeHTTP(w, r)
	})
}

// Bootstrap handles the bootstrap endpoint for initial key generation
func (a *Authenticator) Bootstrap(w http.ResponseWriter, r *http.Request) {
	// Validate bootstrap secret
	secret := r.URL.Query().Get("bootstrap_secret")
	if secret == "" {
		secret = r.Header.Get("X-Bootstrap-Secret")
	}

	if secret != a.config.BootstrapSecret {
		log.Warn().Msg("Invalid bootstrap secret attempt")
		a.sendError(w, http.StatusForbidden, "invalid bootstrap secret")
		return
	}

	owner := r.URL.Query().Get("owner")
	if owner == "" {
		owner = "admin"
	}

	// Forward to upstream auth service
	upstreamURL := fmt.Sprintf("%s?bootstrap_secret=%s&owner=%s",
		strings.Replace(a.config.ValidationEndpoint, "/validate", "/bootstrap", 1),
		secret, owner)

	resp, err := a.client.Post(upstreamURL, "application/json", nil)
	if err != nil {
		log.Error().Err(err).Msg("Failed to forward bootstrap request")
		a.sendError(w, http.StatusServiceUnavailable, "upstream service unavailable")
		return
	}
	defer resp.Body.Close()

	// Forward response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)
	
	var body map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		log.Error().Err(err).Msg("Failed to decode bootstrap response")
		return
	}
	json.NewEncoder(w).Encode(body)

	log.Info().Str("owner", owner).Msg("Bootstrap key generated")
}

// validateKey validates an API key, using cache when possible
func (a *Authenticator) validateKey(ctx context.Context, key string) (*APIKeyInfo, error) {
	// Check cache first
	if info := a.cache.get(key); info != nil {
		return info, nil
	}

	// Parse key to determine tier
	tier := a.extractTier(key)
	isAdmin := strings.HasPrefix(key, a.config.AdminKeyPrefix)

	// Validate with upstream service
	req, err := http.NewRequestWithContext(ctx, "GET", a.config.ValidationEndpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create validation request: %w", err)
	}
	req.Header.Set("X-API-Key", key)

	resp, err := a.client.Do(req)
	if err != nil {
		// If upstream is unavailable but we have a valid format, allow with default permissions
		if a.isValidKeyFormat(key) {
			log.Warn().Msg("Upstream unavailable, using key format validation only")
			info := &APIKeyInfo{
				KeyID:     "unknown",
				Owner:     "unknown",
				Tier:      tier,
				Scopes:    []string{"read"},
				RateLimit: 100,
				IsAdmin:   isAdmin,
				CreatedAt: time.Now(),
			}
			a.cache.set(key, info)
			return info, nil
		}
		return nil, fmt.Errorf("upstream validation failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("key validation returned status %d", resp.StatusCode)
	}

	var info APIKeyInfo
	if err := json.NewDecoder(resp.Body).Decode(&info); err != nil {
		// If upstream returns unexpected format, construct from key
		info = APIKeyInfo{
			KeyID:     key[:16],
			Owner:     "validated",
			Tier:      tier,
			Scopes:    a.defaultScopes(tier),
			RateLimit: a.defaultRateLimit(tier),
			IsAdmin:   isAdmin,
			CreatedAt: time.Now(),
		}
	}

	info.IsAdmin = isAdmin
	a.cache.set(key, &info)
	return &info, nil
}

// extractTier extracts the tier from an API key
func (a *Authenticator) extractTier(key string) string {
	if !strings.HasPrefix(key, "aa_") {
		return "unknown"
	}
	parts := strings.SplitN(key, "_", 3)
	if len(parts) >= 2 {
		return parts[1]
	}
	return "unknown"
}

// isValidKeyFormat checks if the key has a valid format
func (a *Authenticator) isValidKeyFormat(key string) bool {
	return strings.HasPrefix(key, "aa_") && len(key) >= 20
}

// defaultScopes returns default scopes for a tier
func (a *Authenticator) defaultScopes(tier string) []string {
	switch tier {
	case "admin":
		return []string{"*"}
	case "live":
		return []string{"read", "write", "authorize"}
	case "dev":
		return []string{"read", "write", "authorize"}
	case "test":
		return []string{"read", "authorize"}
	default:
		return []string{"read"}
	}
}

// defaultRateLimit returns default rate limit for a tier
func (a *Authenticator) defaultRateLimit(tier string) int {
	switch tier {
	case "admin":
		return 5000
	case "enterprise":
		return 10000
	case "live":
		return 1000
	case "dev":
		return 100
	case "test":
		return 10
	default:
		return 10
	}
}

// sendError sends a JSON error response
func (a *Authenticator) sendError(w http.ResponseWriter, status int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]string{"error": message})
}

// Cache methods
func (c *keyCache) get(key string) *APIKeyInfo {
	c.mu.RLock()
	defer c.mu.RUnlock()

	entry, ok := c.entries[key]
	if !ok {
		return nil
	}

	if time.Now().After(entry.expiresAt) {
		return nil
	}

	return entry.info
}

func (c *keyCache) set(key string, info *APIKeyInfo) {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.entries[key] = &cacheEntry{
		info:      info,
		expiresAt: time.Now().Add(c.ttl),
	}
}

// maskKey masks an API key for logging
func maskKey(key string) string {
	if len(key) <= 10 {
		return "***"
	}
	return key[:10] + "..."
}

// GetAPIKeyInfo extracts API key info from context
func GetAPIKeyInfo(ctx context.Context) (*APIKeyInfo, bool) {
	info, ok := ctx.Value(APIKeyInfoContextKey).(*APIKeyInfo)
	return info, ok
}

// GetAPIKey extracts API key from context
func GetAPIKey(ctx context.Context) (string, bool) {
	key, ok := ctx.Value(APIKeyContextKey).(string)
	return key, ok
}

// IsAdmin checks if the request is from an admin
func IsAdmin(ctx context.Context) bool {
	isAdmin, ok := ctx.Value(IsAdminContextKey).(bool)
	return ok && isAdmin
}
