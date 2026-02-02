// CLI Types

export interface Config {
    apiKey?: string;
    apiUrl: string;
    defaultFormat: "table" | "json" | "yaml";
}

export interface Agent {
    id: string;
    name: string;
    status: "active" | "inactive" | "suspended";
    created_at: string;
    last_active?: string;
    transactions: number;
    volume: string;
    approval_rate: number;
}

export interface Authorization {
    id: string;
    request_id?: string;
    agent_id: string;
    user_id?: string;
    action?: string;
    intent?: string;
    max_amount?: number;
    amount?: number;
    currency?: string;
    status: "authorized" | "approved" | "denied" | "pending" | "expired";
    authorized?: boolean;
    reason?: string;
    policy_id?: string;
    token?: string;
    token_id?: string;
    risk_score?: number;
    merchant?: string;
    created_at?: string;
    expires_at?: string | number;
}

export interface Consent {
    consent_id: string;
    user_id: string;
    developer_id?: string;
    agent_id?: string;
    intent_description: string;
    constraints: {
        max_amount?: number;
        currency?: string;
        allowed_merchants?: string[];
        blocked_categories?: string[];
    };
    scope?: Record<string, unknown>;
    status?: "pending" | "approved" | "denied" | "revoked";
    is_active: boolean;
    created_at: string;
    expires_at?: string;
}

export interface Policy {
    id: string;
    name: string;
    type: "spending_limit" | "merchant_rule" | "category_rule" | "time_rule";
    config: Record<string, unknown>;
    enabled: boolean;
    created_at: string;
}

export interface ApiKey {
    id: string;
    name: string;
    key: string;
    type: "live" | "test";
    created_at: string;
    last_used?: string;
}

export interface LogEntry {
    id: string;
    type: "authorization" | "consent" | "config" | "security" | "api";
    action: string;
    details: string;
    timestamp: string;
    ip_address?: string;
    user_agent?: string;
}

export interface DashboardStats {
    total_authorizations: number;
    transaction_volume: number;
    approval_rate: number;
    avg_response_time: number;
    active_agents: number;
    pending_consents: number;
}

export interface TestResult {
    name: string;
    passed: boolean;
    duration: number;
    error?: string;
}

export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}
