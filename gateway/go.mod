module github.com/agentauth/gateway

go 1.22

require (
	github.com/go-chi/chi/v5 v5.0.12
	github.com/go-chi/httprate v0.9.0
	github.com/go-chi/cors v1.2.1
	github.com/golang-jwt/jwt/v5 v5.2.0
	github.com/hashicorp/vault/api v1.12.0
	github.com/prometheus/client_golang v1.18.0
	github.com/redis/go-redis/v9 v9.4.0
	github.com/rs/zerolog v1.31.0
	github.com/spf13/cobra v1.8.0
	github.com/spf13/viper v1.18.2
	go.opentelemetry.io/otel v1.22.0
	go.opentelemetry.io/otel/exporters/jaeger v1.17.0
	go.opentelemetry.io/otel/sdk v1.22.0
	go.opentelemetry.io/otel/trace v1.22.0
	golang.org/x/crypto v0.18.0
	golang.org/x/time v0.5.0
	google.golang.org/grpc v1.61.0
	google.golang.org/protobuf v1.32.0
)
