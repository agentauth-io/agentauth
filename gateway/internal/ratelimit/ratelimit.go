// Package ratelimit provides rate limiting functionality
package ratelimit

import (
	"context"
	"encoding/json"
	"net/http"
	"strconv"
	"sync"
	"time"

	"github.com/agentauth/gateway/internal/auth"
	"github.com/agentauth/gateway/internal/config"
	"github.com/redis/go-redis/v9"
	"github.com/rs/zerolog/log"
	"golang.org/x/time/rate"
)

// RateLimiter provides rate limiting per API key
type RateLimiter struct {
	config     config.RateLimitConfig
	limiters   map[string]*rate.Limiter
	mu         sync.RWMutex
	redis      *redis.Client
	useRedis   bool
}

// New creates a new rate limiter
func New(cfg config.RateLimitConfig) *RateLimiter {
	rl := &RateLimiter{
		config:   cfg,
		limiters: make(map[string]*rate.Limiter),
		useRedis: cfg.UseRedis,
	}

	// Initialize Redis if configured
	if cfg.UseRedis {
		rl.redis = redis.NewClient(&redis.Options{
			Addr:     cfg.RedisAddr,
			Password: cfg.RedisPass,
			DB:       cfg.RedisDB,
		})

		// Test connection
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := rl.redis.Ping(ctx).Err(); err != nil {
			log.Warn().Err(err).Msg("Redis connection failed, falling back to in-memory rate limiting")
			rl.useRedis = false
		} else {
			log.Info().Str("addr", cfg.RedisAddr).Msg("Redis rate limiter initialized")
		}
	}

	// Start cleanup goroutine
	go rl.cleanup()

	return rl
}

// Middleware is the rate limiting middleware
func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip rate limiting for health endpoints
		if r.URL.Path == "/health" || r.URL.Path == "/ready" || r.URL.Path == "/metrics" {
			next.ServeHTTP(w, r)
			return
		}

		// Get API key info
		keyInfo, ok := auth.GetAPIKeyInfo(r.Context())
		if !ok {
			// No API key - use IP-based limiting
			key := r.RemoteAddr
			if !rl.allowIP(r.Context(), key) {
				rl.sendRateLimitError(w, 1) // 1 second wait
				return
			}
			next.ServeHTTP(w, r)
			return
		}

		// Get tier-based limits
		tier := keyInfo.Tier
		tierLimit, ok := rl.config.TierLimits[tier]
		if !ok {
			tierLimit = config.TierLimit{
				RPS:   rl.config.DefaultRPS,
				Burst: rl.config.DefaultBurst,
			}
		}

		// Check rate limit
		apiKey, _ := auth.GetAPIKey(r.Context())
		allowed, retryAfter := rl.allow(r.Context(), apiKey, tierLimit)

		// Set rate limit headers
		remaining := rl.remaining(r.Context(), apiKey, tierLimit)
		w.Header().Set("X-RateLimit-Limit", strconv.Itoa(tierLimit.RPS))
		w.Header().Set("X-RateLimit-Remaining", strconv.Itoa(remaining))
		w.Header().Set("X-RateLimit-Reset", strconv.FormatInt(time.Now().Add(time.Second).Unix(), 10))

		if !allowed {
			log.Warn().
				Str("tier", tier).
				Str("key_prefix", apiKey[:min(10, len(apiKey))]).
				Msg("Rate limit exceeded")
			rl.sendRateLimitError(w, retryAfter)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// allow checks if a request is allowed under rate limits
func (rl *RateLimiter) allow(ctx context.Context, key string, limit config.TierLimit) (bool, int) {
	if rl.useRedis {
		return rl.allowRedis(ctx, key, limit)
	}
	return rl.allowLocal(key, limit), 1
}

// allowLocal uses in-memory rate limiting
func (rl *RateLimiter) allowLocal(key string, limit config.TierLimit) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	limiter, ok := rl.limiters[key]
	if !ok {
		// Create new limiter for this key
		limiter = rate.NewLimiter(rate.Limit(limit.RPS), limit.Burst)
		rl.limiters[key] = limiter
	}

	return limiter.Allow()
}

// allowIP uses in-memory rate limiting for IP addresses
func (rl *RateLimiter) allowIP(ctx context.Context, ip string) bool {
	// Use very conservative limits for unauthenticated requests
	limit := config.TierLimit{RPS: 10, Burst: 20}
	return rl.allowLocal("ip:"+ip, limit)
}

// allowRedis uses Redis for distributed rate limiting
func (rl *RateLimiter) allowRedis(ctx context.Context, key string, limit config.TierLimit) (bool, int) {
	now := time.Now()
	windowKey := "ratelimit:" + key + ":" + strconv.FormatInt(now.Unix(), 10)

	// Sliding window counter using Redis
	pipe := rl.redis.Pipeline()
	incr := pipe.Incr(ctx, windowKey)
	pipe.Expire(ctx, windowKey, 2*time.Second)
	
	_, err := pipe.Exec(ctx)
	if err != nil {
		log.Error().Err(err).Msg("Redis rate limit check failed")
		return true, 0 // Allow on error
	}

	count := incr.Val()
	if count > int64(limit.RPS) {
		retryAfter := int(2 - (now.UnixMilli()%1000)/1000)
		if retryAfter < 1 {
			retryAfter = 1
		}
		return false, retryAfter
	}

	return true, 0
}

// remaining returns approximate remaining requests
func (rl *RateLimiter) remaining(ctx context.Context, key string, limit config.TierLimit) int {
	if rl.useRedis {
		now := time.Now()
		windowKey := "ratelimit:" + key + ":" + strconv.FormatInt(now.Unix(), 10)
		count, err := rl.redis.Get(ctx, windowKey).Int()
		if err != nil {
			return limit.RPS
		}
		remaining := limit.RPS - count
		if remaining < 0 {
			return 0
		}
		return remaining
	}

	// For local limiting, estimate based on limiter tokens
	rl.mu.RLock()
	limiter, ok := rl.limiters[key]
	rl.mu.RUnlock()

	if !ok {
		return limit.Burst
	}

	tokens := int(limiter.Tokens())
	if tokens < 0 {
		return 0
	}
	return tokens
}

// cleanup removes stale limiters periodically
func (rl *RateLimiter) cleanup() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		rl.mu.Lock()
		// Simple cleanup: reset all limiters every 5 minutes
		// In production, track last access time
		if len(rl.limiters) > 10000 {
			rl.limiters = make(map[string]*rate.Limiter)
			log.Info().Msg("Rate limiter cache cleared")
		}
		rl.mu.Unlock()
	}
}

// sendRateLimitError sends a rate limit exceeded response
func (rl *RateLimiter) sendRateLimitError(w http.ResponseWriter, retryAfter int) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Retry-After", strconv.Itoa(retryAfter))
	w.WriteHeader(http.StatusTooManyRequests)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"error":       "rate limit exceeded",
		"retry_after": retryAfter,
	})
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
