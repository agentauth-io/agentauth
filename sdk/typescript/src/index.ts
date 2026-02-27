/**
 * AgentAuth TypeScript SDK
 *
 * Authorization layer for AI agent commerce.
 * Uses native fetch — zero dependencies.
 *
 * @example
 * ```ts
 * import { AgentAuth } from "@agentauth/sdk";
 *
 * const client = new AgentAuth({ apiKey: "aa_live_xxx" });
 * const decision = await client.authorize({
 *   agentId: "shopping-bot",
 *   userId: "user_123",
 *   action: "purchase",
 *   amount: 49.99,
 *   category: "groceries",
 * });
 * console.log(decision.allowed); // true
 * ```
 */

// ─── Types ───────────────────────────────────────────────────────────

export interface AgentAuthConfig {
    apiKey?: string;
    baseUrl?: string;
    timeout?: number;
    maxRetries?: number;
}

export interface AuthorizeRequest {
    agentId: string;
    userId: string;
    action: string;
    amount?: number;
    currency?: string;
    merchantId?: string;
    merchantName?: string;
    category?: string;
    metadata?: Record<string, unknown>;
}

export interface AuthorizeResponse {
    status: "approved" | "denied" | "requires_approval" | "rate_limited" | "error";
    authorized: boolean;
    request_id: string;
    token?: string;
    reason: string;
    risk_score: number;
    policy_id?: string;
    constraints: Record<string, unknown>;
    evaluation_time_ms: number;
}

export interface ConsentRequest {
    userId: string;
    intent: string;
    maxAmount: number;
    currency?: string;
    allowedMerchants?: string[];
    allowedCategories?: string[];
    expiresInSeconds?: number;
    singleUse?: boolean;
}

export interface ConsentResponse {
    consent_id: string;
    delegation_token: string;
    status: string;
    expires_at: string;
}

export interface PolicyCondition {
    attribute: string;
    operator: string;
    value: unknown;
}

export interface PolicyRule {
    conditions: PolicyCondition[];
    logic?: "and" | "or";
}

export interface PolicyDef {
    id?: string;
    name: string;
    effect: "allow" | "deny" | "require_approval";
    priority?: number;
    description?: string;
    rules?: PolicyRule[];
    constraints?: Record<string, unknown>;
}

export interface PolicyResponse {
    id: string;
    name: string;
    effect: string;
    priority: number;
    enabled: boolean;
    rules: Record<string, unknown>;
    constraints: Record<string, unknown>;
}

export interface PlaygroundRequest {
    policies: PolicyDef[];
    context: Record<string, unknown>;
    combineAlgorithm?: "deny_overrides" | "allow_overrides" | "first_applicable" | "unanimous";
}

export interface TraceEntry {
    policy_id: string;
    policy_name: string;
    effect: string;
    applies: boolean;
    explanation: string;
}

export interface PlaygroundResponse {
    decision: string;
    allowed: boolean;
    explanation: string;
    risk_score: number;
    evaluation_time_ms: number;
    policies_evaluated: number;
    deciding_policy_id?: string;
    deciding_policy_name?: string;
    constraints: Record<string, unknown>;
    trace: TraceEntry[];
}

export interface SpendingResponse {
    user_id: string;
    daily_spent: number;
    monthly_spent: number;
    daily_limit: number;
    monthly_limit: number;
    daily_remaining: number;
}

export interface VerifyRequest {
    authorizationCode: string;
    amount: number;
    currency?: string;
    merchantId?: string;
}

export interface VerifyResponse {
    valid: boolean;
    status: string;
    token_id: string;
}

// ─── Errors ──────────────────────────────────────────────────────────

export class AgentAuthError extends Error {
    constructor(
        message: string,
        public statusCode?: number,
        public detail?: string,
    ) {
        super(message);
        this.name = "AgentAuthError";
    }
}

export class AuthorizationDenied extends AgentAuthError {
    constructor(
        public reason: string,
        public riskScore: number,
    ) {
        super(`Authorization denied: ${reason}`);
        this.name = "AuthorizationDenied";
    }
}

export class RateLimitExceeded extends AgentAuthError {
    constructor(public retryAfter?: number) {
        super("Rate limit exceeded");
        this.name = "RateLimitExceeded";
    }
}

// ─── Client ──────────────────────────────────────────────────────────

const DEFAULT_BASE_URL = "https://agentauth-api.koyeb.app";
const DEFAULT_TIMEOUT = 30_000;
const DEFAULT_MAX_RETRIES = 3;

export class AgentAuth {
    private apiKey: string;
    private baseUrl: string;
    private timeout: number;
    private maxRetries: number;

    constructor(config: AgentAuthConfig = {}) {
        this.apiKey = config.apiKey || "";
        this.baseUrl = (config.baseUrl || DEFAULT_BASE_URL).replace(/\/$/, "");
        this.timeout = config.timeout || DEFAULT_TIMEOUT;
        this.maxRetries = config.maxRetries || DEFAULT_MAX_RETRIES;
    }

    // ── Core methods ──

    /** Authorize an agent action against configured policies. */
    async authorize(req: AuthorizeRequest): Promise<AuthorizeResponse> {
        return this.post<AuthorizeResponse>("/v1/authorize", {
            agent_id: req.agentId,
            user_id: req.userId,
            action: req.action,
            amount: req.amount,
            currency: req.currency || "USD",
            merchant_id: req.merchantId,
            merchant_name: req.merchantName,
            category: req.category,
            metadata: req.metadata,
        });
    }

    /** Verify an authorization code (merchant-side). */
    async verify(req: VerifyRequest): Promise<VerifyResponse> {
        return this.post<VerifyResponse>("/v1/token/verify", {
            authorization_code: req.authorizationCode,
            amount: req.amount,
            currency: req.currency || "USD",
            merchant_id: req.merchantId,
        });
    }

    /** Revoke an authorization token. */
    async revokeToken(tokenId: string): Promise<void> {
        await this.post("/v1/token/revoke", { token_id: tokenId });
    }

    // ── Consent ──

    /** Create a user consent for agent spending. */
    async createConsent(req: ConsentRequest): Promise<ConsentResponse> {
        return this.post<ConsentResponse>("/v1/consents", {
            user_id: req.userId,
            intent: req.intent,
            max_amount: req.maxAmount,
            currency: req.currency || "USD",
            allowed_merchants: req.allowedMerchants,
            allowed_categories: req.allowedCategories,
            expires_in_seconds: req.expiresInSeconds || 3600,
            single_use: req.singleUse ?? true,
            signature: "sdk_generated",
            public_key: "sdk_key",
        });
    }

    // ── Policies ──

    /** List all policies. */
    async listPolicies(): Promise<PolicyResponse[]> {
        const res = await this.get<{ policies: PolicyResponse[] }>("/v1/policies");
        return res.policies;
    }

    /** Create a new policy. */
    async createPolicy(policy: PolicyDef): Promise<PolicyResponse> {
        return this.post<PolicyResponse>("/v1/policies", policy);
    }

    /** Get a policy by ID. */
    async getPolicy(policyId: string): Promise<PolicyResponse> {
        return this.get<PolicyResponse>(`/v1/policies/${policyId}`);
    }

    /** Update a policy. */
    async updatePolicy(policyId: string, policy: Partial<PolicyDef>): Promise<PolicyResponse> {
        return this.put<PolicyResponse>(`/v1/policies/${policyId}`, policy);
    }

    /** Delete a policy. */
    async deletePolicy(policyId: string): Promise<void> {
        await this.del(`/v1/policies/${policyId}`);
    }

    /** Toggle a policy on/off. */
    async togglePolicy(policyId: string): Promise<PolicyResponse> {
        return this.post<PolicyResponse>(`/v1/policies/${policyId}/toggle`, {});
    }

    // ── Playground ──

    /** Evaluate policies against a context (no auth required). */
    async evaluate(req: PlaygroundRequest): Promise<PlaygroundResponse> {
        return this.post<PlaygroundResponse>("/v1/playground/evaluate", {
            policies: req.policies,
            context: req.context,
            combine_algorithm: req.combineAlgorithm || "deny_overrides",
        });
    }

    /** Get preset playground templates. */
    async getPlaygroundTemplates(): Promise<Record<string, unknown>> {
        const res = await this.get<{ templates: Record<string, unknown> }>("/v1/playground/templates");
        return res.templates;
    }

    // ── Spending ──

    /** Get spending summary for a user. */
    async getSpending(userId: string): Promise<SpendingResponse> {
        return this.get<SpendingResponse>(`/v1/user/${userId}/spending`);
    }

    /** Update spending limits for a user. */
    async updateLimits(userId: string, limits: { dailyLimit?: number; monthlyLimit?: number }): Promise<void> {
        await this.put(`/v1/user/${userId}/limits`, {
            daily_limit: limits.dailyLimit,
            monthly_limit: limits.monthlyLimit,
        });
    }

    // ── Audit ──

    /** Get audit trail entries. */
    async getAuditTrail(opts?: { limit?: number; agentId?: string }): Promise<unknown[]> {
        const params = new URLSearchParams();
        if (opts?.limit) params.set("limit", String(opts.limit));
        if (opts?.agentId) params.set("agent_id", opts.agentId);
        const qs = params.toString();
        return this.get<unknown[]>(`/v1/audit${qs ? `?${qs}` : ""}`);
    }

    // ── Billing ──

    /** Get available billing plans. */
    async getBillingPlans(): Promise<unknown> {
        return this.get("/v1/billing/plans");
    }

    /** Get billing usage. */
    async getBillingUsage(): Promise<unknown> {
        return this.get("/v1/billing/usage");
    }

    // ── System ──

    /** Health check. */
    async health(): Promise<{ status: string; version: string }> {
        return this.get("/health");
    }

    // ── Internal HTTP helpers ────────────────────────────────────────────

    private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
        const url = `${this.baseUrl}${path}`;
        const headers: Record<string, string> = {
            "Content-Type": "application/json",
        };
        if (this.apiKey) headers["X-API-Key"] = this.apiKey;

        let lastError: Error | null = null;

        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            if (attempt > 0) {
                // Exponential backoff: 200ms, 400ms, 800ms …
                await new Promise((r) => setTimeout(r, 200 * Math.pow(2, attempt - 1)));
            }

            try {
                const controller = new AbortController();
                const timer = setTimeout(() => controller.abort(), this.timeout);

                const res = await fetch(url, {
                    method,
                    headers,
                    body: body ? JSON.stringify(body) : undefined,
                    signal: controller.signal,
                });

                clearTimeout(timer);

                if (res.status === 429) {
                    const retryAfter = parseInt(res.headers.get("Retry-After") || "5", 10);
                    if (attempt < this.maxRetries) {
                        await new Promise((r) => setTimeout(r, retryAfter * 1000));
                        continue;
                    }
                    throw new RateLimitExceeded(retryAfter);
                }

                if (!res.ok) {
                    const err = await res.json().catch(() => ({ detail: res.statusText }));
                    throw new AgentAuthError(
                        err.detail || `HTTP ${res.status}`,
                        res.status,
                        err.detail,
                    );
                }

                return (await res.json()) as T;
            } catch (e) {
                if (e instanceof AgentAuthError) throw e;
                lastError = e as Error;
                if (attempt === this.maxRetries) break;
            }
        }

        throw new AgentAuthError(lastError?.message || "Request failed");
    }

    private get<T>(path: string): Promise<T> {
        return this.request<T>("GET", path);
    }

    private post<T>(path: string, body: unknown): Promise<T> {
        return this.request<T>("POST", path, body);
    }

    private put<T>(path: string, body: unknown): Promise<T> {
        return this.request<T>("PUT", path, body);
    }

    private del(path: string): Promise<unknown> {
        return this.request("DELETE", path);
    }
}

// ─── Default export ──────────────────────────────────────────────────

export default AgentAuth;
