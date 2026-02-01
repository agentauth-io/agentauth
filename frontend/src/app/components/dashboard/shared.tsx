import {
    Key,
    Copy,
    RefreshCw,
} from "lucide-react";
import type { NavItemProps, Transaction, NavSection } from "./types";

// Navigation Item Component
export const NavItem = ({ icon: Icon, label, active, onClick }: NavItemProps) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center gap-3 px-5 py-2.5 text-sm transition-all ${active
            ? "bg-white/5 text-white border-r-2 border-white"
            : "text-gray-500 hover:bg-white/5 hover:text-white"
            }`}
    >
        <Icon className="w-[18px] h-[18px] opacity-70" />
        {label}
    </button>
);

// Stat Card Component
export const StatCard = ({
    label,
    value,
    change,
    positive = true,
    icon: Icon,
}: {
    label: string;
    value: string;
    change: string;
    positive?: boolean;
    icon: React.ElementType;
}) => (
    <div className="bg-[#111] border border-[#222] rounded-xl p-5">
        <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-2">
            <Icon className="w-3.5 h-3.5" />
            {label}
        </div>
        <div className="text-3xl font-semibold text-white mb-1">{value}</div>
        <div className={`text-xs flex items-center gap-1 ${positive ? "text-emerald-500" : "text-red-500"}`}>
            {positive ? "↑" : "↓"} {change}
        </div>
    </div>
);

// Usage Bar Component
export const UsageBar = ({
    title,
    used,
    total,
    variant = "normal",
}: {
    title: string;
    used: number;
    total: number;
    variant?: "normal" | "warning" | "danger";
}) => {
    const percentage = (used / total) * 100;
    const gradientClass =
        variant === "danger"
            ? "from-red-500 to-red-600"
            : variant === "warning"
                ? "from-yellow-400 to-amber-500"
                : "from-emerald-500 to-emerald-600";

    return (
        <div className="bg-[#111] border border-[#222] rounded-xl p-5 mb-3">
            <div className="flex justify-between mb-2.5">
                <span className="text-sm font-medium text-white">{title}</span>
                <span className="text-sm text-gray-500">
                    {used.toLocaleString()} / {total.toLocaleString()}
                </span>
            </div>
            <div className="h-2 bg-[#222] rounded overflow-hidden">
                <div
                    className={`h-full bg-gradient-to-r ${gradientClass} rounded`}
                    style={{ width: `${Math.min(percentage, 100)}%` }}
                />
            </div>
        </div>
    );
};

// Chart Component
export const ActivityChart = ({ data, period, onPeriodChange }: {
    data: number[];
    period: string;
    onPeriodChange: (p: string) => void;
}) => {
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const maxValue = Math.max(...data, 1);

    return (
        <div className="bg-[#111] border border-[#222] rounded-xl p-6">
            <div className="flex justify-between items-center mb-5">
                <span className="text-sm font-medium text-white">Authorization Activity</span>
                <div className="flex gap-1">
                    {["24h", "7d", "30d", "90d"].map((p) => (
                        <button
                            key={p}
                            onClick={() => onPeriodChange(p)}
                            className={`px-3 py-1.5 rounded text-xs ${period === p ? "bg-white/10 text-white" : "text-gray-500 hover:text-white"
                                }`}
                        >
                            {p}
                        </button>
                    ))}
                </div>
            </div>
            <div className="flex items-end gap-2 h-44 pt-5">
                {data.map((value, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-2">
                        <div
                            className="w-full bg-gradient-to-t from-emerald-500 to-emerald-600 rounded-t min-h-1"
                            style={{ height: `${(value / maxValue) * 100}%` }}
                        />
                        <span className="text-[10px] text-gray-500">{days[i]}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

// API Key Card Component
export const ApiKeyCard = ({
    name,
    createdAt,
    keyPreview,
    isLive,
}: {
    name: string;
    createdAt: string;
    keyPreview: string;
    isLive: boolean;
}) => (
    <div className="bg-[#111] border border-[#222] rounded-xl p-4 flex justify-between items-center mb-3">
        <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center">
                <Key className={`w-[18px] h-[18px] ${isLive ? "text-emerald-500" : "text-gray-500"}`} />
            </div>
            <div>
                <h4 className="text-sm font-medium text-white">{name}</h4>
                <p className="text-xs text-gray-500">{createdAt}</p>
            </div>
        </div>
        <div className="flex items-center gap-3">
            <code className="text-sm text-gray-500 bg-white/5 px-3 py-2 rounded">{keyPreview}</code>
            <button
                onClick={() => navigator.clipboard?.writeText(keyPreview)}
                className="w-9 h-9 rounded-lg bg-white/5 border border-[#333] text-gray-500 hover:bg-white/10 hover:text-white flex items-center justify-center"
                title="Copy key"
            >
                <Copy className="w-4 h-4" />
            </button>
        </div>
    </div>
);

// Transaction Row Component
export const TransactionRow = ({ tx }: { tx: Transaction }) => {
    const statusStyles = {
        authorized: "bg-emerald-500/10 text-emerald-500",
        denied: "bg-red-500/10 text-red-500",
        pending: "bg-yellow-500/10 text-yellow-500",
    };

    const timeAgo = (date: string) => {
        const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
        if (seconds < 60) return `${seconds}s ago`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        return `${Math.floor(seconds / 86400)}d ago`;
    };

    return (
        <tr className="border-b border-white/5 hover:bg-white/[0.02]">
            <td className="py-3.5 px-4">
                <code className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded">
                    {tx.id.substring(0, 12)}...
                </code>
            </td>
            <td className="py-3.5 px-4 text-white">
                ${tx.amount.toFixed(2)} {tx.currency}
            </td>
            <td className="py-3.5 px-4">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusStyles[tx.status]}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                    {tx.status.charAt(0).toUpperCase() + tx.status.slice(1)}
                </span>
            </td>
            <td className="py-3.5 px-4 text-gray-500 text-sm">{timeAgo(tx.created_at)}</td>
        </tr>
    );
};

// Quick Action Component
export const QuickAction = ({
    icon: Icon,
    title,
    description,
    onClick,
}: {
    icon: React.ElementType;
    title: string;
    description: string;
    onClick?: () => void;
}) => (
    <button
        onClick={onClick}
        className="bg-[#111] border border-[#222] rounded-xl p-4 flex items-center gap-3 hover:bg-white/5 hover:border-[#333] transition-all text-left"
    >
        <div className="w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center text-emerald-500">
            <Icon className="w-5 h-5" />
        </div>
        <div>
            <h4 className="text-sm font-medium text-white">{title}</h4>
            <p className="text-xs text-gray-500">{description}</p>
        </div>
    </button>
);

// Color maps for Tailwind (static classes required - dynamic interpolation gets purged)
export const colorBgMap: Record<string, string> = {
    emerald: "bg-emerald-500/10",
    red: "bg-red-500/10",
    yellow: "bg-yellow-500/10",
    purple: "bg-purple-500/10",
    cyan: "bg-cyan-500/10",
    orange: "bg-orange-500/10",
    blue: "bg-blue-500/10",
};

export const colorTextMap: Record<string, string> = {
    emerald: "text-emerald-500",
    red: "text-red-500",
    yellow: "text-yellow-500",
    purple: "text-purple-500",
    cyan: "text-cyan-500",
    orange: "text-orange-500",
    blue: "text-blue-500",
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
};

// Format currency helper
export const formatCurrency = (amount: number) => {
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
    if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
    return `$${amount.toFixed(2)}`;
};
