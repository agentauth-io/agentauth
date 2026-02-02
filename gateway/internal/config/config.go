// Package config provides configuration management for the gateway
package config

import (
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/spf13/viper"
)

// Config holds all gateway configuration
type Config struct {
	// General settings
	Version     string
	Environment string
	Port        int
	Debug       bool

	// TLS/mTLS settings
	MTLSEnabled bool
	TLSCertFile string
	TLSKeyFile  string
	TLSCAFile   string

	// Authentication
	AuthConfig    AuthConfig
	SigningSecret []byte

	// Rate limiting
	RateLimitConfig RateLimitConfig

	// Proxy settings
	ProxyConfig ProxyConfig

	// CORS
	CORSOrigins []string

	// Observability
	TracingEnabled bool
	TracingEndpoint string
	MetricsEnabled bool
}

// AuthConfig holds authentication settings
type AuthConfig struct {
	// Bootstrap secret for initial API key generation
	BootstrapSecret string

	// API key validation endpoint (upstream auth service)
	ValidationEndpoint string

	// Key cache TTL
	CacheTTL time.Duration

	// Require HMAC signature on requests
	RequireSignature bool

	// Signature timestamp tolerance
	TimestampTolerance time.Duration

	// Admin key prefix
	AdminKeyPrefix string
}

// RateLimitConfig holds rate limiting settings
type RateLimitConfig struct {
	// Default requests per second
	DefaultRPS int

	// Default burst size
	DefaultBurst int

	// Rate limits by tier
	TierLimits map[string]TierLimit

	// Redis connection for distributed rate limiting
	RedisAddr string
	RedisPass string
	RedisDB   int

	// Use Redis for distributed limiting
	UseRedis bool
}

// TierLimit defines rate limits for a specific tier
type TierLimit struct {
	RPS   int
	Burst int
}

// ProxyConfig holds reverse proxy settings
type ProxyConfig struct {
	// Upstream service URL
	UpstreamURL string

	// Request timeout
	Timeout time.Duration

	// Retry count
	RetryCount int

	// Retry delay
	RetryDelay time.Duration

	// Circuit breaker settings
	CircuitBreakerThreshold int
	CircuitBreakerTimeout   time.Duration

	// Load balancing endpoints (if multiple)
	Endpoints []string

	// Health check interval
	HealthCheckInterval time.Duration
}

// Load reads configuration from environment and files
func Load() (*Config, error) {
	v := viper.New()

	// Set defaults
	v.SetDefault("version", "1.0.0")
	v.SetDefault("environment", "development")
	v.SetDefault("port", 8443)
	v.SetDefault("debug", false)

	// mTLS defaults
	v.SetDefault("mtls.enabled", false)
	v.SetDefault("mtls.cert_file", "/etc/agentauth/certs/server.crt")
	v.SetDefault("mtls.key_file", "/etc/agentauth/certs/server.key")
	v.SetDefault("mtls.ca_file", "/etc/agentauth/certs/ca.crt")

	// Auth defaults
	v.SetDefault("auth.bootstrap_secret", "")
	v.SetDefault("auth.validation_endpoint", "http://localhost:8080/internal/validate")
	v.SetDefault("auth.cache_ttl", "5m")
	v.SetDefault("auth.require_signature", true)
	v.SetDefault("auth.timestamp_tolerance", "30s")
	v.SetDefault("auth.admin_prefix", "aa_admin_")

	// Rate limit defaults
	v.SetDefault("ratelimit.default_rps", 100)
	v.SetDefault("ratelimit.default_burst", 200)
	v.SetDefault("ratelimit.use_redis", false)
	v.SetDefault("ratelimit.redis_addr", "localhost:6379")

	// Proxy defaults
	v.SetDefault("proxy.upstream_url", "http://localhost:8080")
	v.SetDefault("proxy.timeout", "30s")
	v.SetDefault("proxy.retry_count", 3)
	v.SetDefault("proxy.retry_delay", "100ms")
	v.SetDefault("proxy.circuit_breaker_threshold", 5)
	v.SetDefault("proxy.circuit_breaker_timeout", "30s")
	v.SetDefault("proxy.health_check_interval", "10s")

	// CORS defaults
	v.SetDefault("cors.origins", []string{"http://localhost:5173", "http://localhost:3000"})

	// Observability defaults
	v.SetDefault("tracing.enabled", false)
	v.SetDefault("tracing.endpoint", "http://localhost:14268/api/traces")
	v.SetDefault("metrics.enabled", true)

	// Read from environment
	v.SetEnvPrefix("AGENTAUTH")
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	v.AutomaticEnv()

	// Read from config file if exists
	v.SetConfigName("gateway")
	v.SetConfigType("yaml")
	v.AddConfigPath("/etc/agentauth/")
	v.AddConfigPath(".")
	if err := v.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return nil, fmt.Errorf("error reading config file: %w", err)
		}
	}

	// Build config struct
	cfg := &Config{
		Version:     v.GetString("version"),
		Environment: v.GetString("environment"),
		Port:        v.GetInt("port"),
		Debug:       v.GetBool("debug"),

		MTLSEnabled: v.GetBool("mtls.enabled"),
		TLSCertFile: v.GetString("mtls.cert_file"),
		TLSKeyFile:  v.GetString("mtls.key_file"),
		TLSCAFile:   v.GetString("mtls.ca_file"),

		AuthConfig: AuthConfig{
			BootstrapSecret:    v.GetString("auth.bootstrap_secret"),
			ValidationEndpoint: v.GetString("auth.validation_endpoint"),
			CacheTTL:           v.GetDuration("auth.cache_ttl"),
			RequireSignature:   v.GetBool("auth.require_signature"),
			TimestampTolerance: v.GetDuration("auth.timestamp_tolerance"),
			AdminKeyPrefix:     v.GetString("auth.admin_prefix"),
		},

		SigningSecret: []byte(v.GetString("auth.signing_secret")),

		RateLimitConfig: RateLimitConfig{
			DefaultRPS:   v.GetInt("ratelimit.default_rps"),
			DefaultBurst: v.GetInt("ratelimit.default_burst"),
			UseRedis:     v.GetBool("ratelimit.use_redis"),
			RedisAddr:    v.GetString("ratelimit.redis_addr"),
			RedisPass:    v.GetString("ratelimit.redis_pass"),
			RedisDB:      v.GetInt("ratelimit.redis_db"),
			TierLimits: map[string]TierLimit{
				"test":       {RPS: 10, Burst: 20},
				"dev":        {RPS: 100, Burst: 200},
				"live":       {RPS: 1000, Burst: 2000},
				"admin":      {RPS: 5000, Burst: 10000},
				"enterprise": {RPS: 10000, Burst: 20000},
			},
		},

		ProxyConfig: ProxyConfig{
			UpstreamURL:             v.GetString("proxy.upstream_url"),
			Timeout:                 v.GetDuration("proxy.timeout"),
			RetryCount:              v.GetInt("proxy.retry_count"),
			RetryDelay:              v.GetDuration("proxy.retry_delay"),
			CircuitBreakerThreshold: v.GetInt("proxy.circuit_breaker_threshold"),
			CircuitBreakerTimeout:   v.GetDuration("proxy.circuit_breaker_timeout"),
			HealthCheckInterval:     v.GetDuration("proxy.health_check_interval"),
		},

		CORSOrigins: v.GetStringSlice("cors.origins"),

		TracingEnabled:  v.GetBool("tracing.enabled"),
		TracingEndpoint: v.GetString("tracing.endpoint"),
		MetricsEnabled:  v.GetBool("metrics.enabled"),
	}

	// Override from environment for sensitive values
	if secret := os.Getenv("AGENTAUTH_BOOTSTRAP_SECRET"); secret != "" {
		cfg.AuthConfig.BootstrapSecret = secret
	}
	if signingSecret := os.Getenv("AGENTAUTH_SIGNING_SECRET"); signingSecret != "" {
		cfg.SigningSecret = []byte(signingSecret)
	}

	return cfg, nil
}
