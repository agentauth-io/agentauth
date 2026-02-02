// Dashboard shared types

export interface Transaction {
    id: string;
    amount: number;
    currency: string;
    status: "authorized" | "denied" | "pending";
    merchant: string;
    created_at: string;
    description: string;
}

export interface DashboardStats {
    total_authorizations: number;
    transaction_volume: number;
    approval_rate: number;
    avg_response_time: number;
    transactions: Transaction[];
}

export interface Agent {
    id: string;
    name: string;
    status: "active" | "inactive" | "suspended";
    lastActive: string;
    transactions: number;
    volume: string;
    approvalRate: number;
}

export interface Consent {
    consent_id: string;
    user_id: string;
    developer_id?: string;
    intent_description?: string;
    constraints?: Record<string, any>;
    scope?: Record<string, any>;
    is_active: boolean;
    created_at?: string;
    expires_at?: string;
}

export interface ApiKey {
    id: string;
    name: string;
    key: string;
    created: string;
    lastUsed: string;
    isLive: boolean;
}

export interface Webhook {
    id: string;
    url: string;
    events: string[];
    status: "active" | "inactive" | "failed";
    lastTriggered?: string;
    failureCount: number;
}

export interface TeamMember {
    id: string;
    name: string;
    email: string;
    role: string;
    avatar: string;
}

export interface ConnectedAccount {
    id: string;
    provider: string;
    status: "pending" | "active" | "failed";
    email: string;
    created_at: string;
}

export interface NotificationSettings {
    authAlerts: boolean;
    deniedTx: boolean;
    dailyDigest: boolean;
    weeklyReport: boolean;
}

export type NavSection = 
    | "dashboard" 
    | "analytics" 
    | "transactions" 
    | "consents" 
    | "agents" 
    | "logs" 
    | "apikeys" 
    | "webhooks" 
    | "team" 
    | "billing" 
    | "settings" 
    | "account" 
    | "connected-accounts";

// Production backend URL
export const BACKEND_URL = import.meta.env.VITE_API_URL || "https://characteristic-inessa-agentauth-0a540dd6.koyeb.app";

// Helper functions
export const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(amount);
};

export const timeAgo = (date: string): string => {
    const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
};

// Page title mapping
export const pageTitles: Record<NavSection, string> = {
    dashboard: "Dashboard",
    analytics: "Analytics",
    transactions: "Transactions",
    consents: "Consents",
    agents: "Agents",
    logs: "Audit Logs",
    apikeys: "API Keys",
    webhooks: "Webhooks",
    team: "Team",
    billing: "Billing",
    settings: "Settings",
    account: "My Account",
    "connected-accounts": "Connected Accounts",
};
