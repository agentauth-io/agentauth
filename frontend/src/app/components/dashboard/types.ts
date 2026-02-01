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

export interface NavItemProps {
    icon: React.ElementType;
    label: string;
    active?: boolean;
    onClick?: () => void;
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
    | "settings";

export type ToastType = "success" | "error" | "info";

export interface Toast {
    message: string;
    type: ToastType;
}
