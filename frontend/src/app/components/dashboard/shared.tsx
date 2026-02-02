// Shared UI components for Dashboard

import {
    Copy,
    Key,
    TrendingUp,
    TrendingDown,
} from "lucide-react";
import { Transaction } from "./types";

// Navigation Item Component
interface NavItemProps {
    icon: React.ElementType;
    label: string;
    active?: boolean;
    onClick?: () => void;
}

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
interface StatCardProps {
    label: string;
    value: string;
    change: string;
    positive?: boolean;
    icon: React.ElementType;
}

export const StatCard = ({
    label,
    value,
    change,
    positive = true,
    icon: Icon,
}: StatCardProps) => {
    const isNoData = change === "No data yet" || value === "0" || value === "$0" || value === "—";
    return (
        <div className="bg-[#111] border border-[#222] rounded-xl p-4 sm:p-5">
            <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-2">
                <Icon className="w-3.5 h-3.5" />
                <span className="truncate">{label}</span>
            </div>
            <div className="text-2xl sm:text-3xl font-semibold text-white mb-1">{value}</div>
            <div className={`text-xs flex items-center gap-1 ${isNoData ? "text-gray-500" : positive ? "text-emerald-500" : "text-red-500"}`}>
                {!isNoData && (positive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />)} {change}
            </div>
        </div>
    );
};

// Usage Bar Component
interface UsageBarProps {
    title: string;
    used: number;
    total: number;
    variant?: "normal" | "warning" | "danger";
}

export const UsageBar = ({
    title,
    used,
    total,
    variant = "normal",
}: UsageBarProps) => {
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

// Activity Chart Component
interface ActivityChartProps {
    data: number[];
    period: string;
    onPeriodChange: (p: string) => void;
}

export const ActivityChart = ({ data, period, onPeriodChange }: ActivityChartProps) => {
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
interface ApiKeyCardProps {
    name: string;
    createdAt: string;
    keyPreview: string;
    isLive: boolean;
}

export const ApiKeyCard = ({
    name,
    createdAt,
    keyPreview,
    isLive,
}: ApiKeyCardProps) => (
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
            <button className="w-9 h-9 rounded-lg bg-white/5 border border-[#333] text-gray-500 hover:bg-white/10 hover:text-white flex items-center justify-center">
                <Copy className="w-4 h-4" />
            </button>
        </div>
    </div>
);

// Transaction Row Component
interface TransactionRowProps {
    tx: Transaction;
}

export const TransactionRow = ({ tx }: TransactionRowProps) => {
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
interface QuickActionProps {
    icon: React.ElementType;
    title: string;
    description: string;
    onClick?: () => void;
}

export const QuickAction = ({
    icon: Icon,
    title,
    description,
    onClick,
}: QuickActionProps) => (
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

// Empty State Component
interface EmptyStateProps {
    icon: React.ElementType;
    title: string;
    description: string;
    actionLabel?: string;
    onAction?: () => void;
}

export const EmptyState = ({
    icon: Icon,
    title,
    description,
    actionLabel,
    onAction,
}: EmptyStateProps) => (
    <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-4">
            <Icon className="w-8 h-8 text-gray-500" />
        </div>
        <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
        <p className="text-sm text-gray-500 max-w-md mb-4">{description}</p>
        {actionLabel && onAction && (
            <button
                onClick={onAction}
                className="px-4 py-2 bg-white text-black rounded-lg text-sm font-medium hover:bg-gray-100 transition-colors"
            >
                {actionLabel}
            </button>
        )}
    </div>
);

// Loading Spinner
export const LoadingSpinner = () => (
    <div className="flex items-center justify-center py-16">
        <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
    </div>
);

// Section Header
interface SectionHeaderProps {
    title: string;
    description?: string;
    action?: React.ReactNode;
}

export const SectionHeader = ({ title, description, action }: SectionHeaderProps) => (
    <div className="flex items-center justify-between mb-6">
        <div>
            <h2 className="text-xl font-semibold text-white">{title}</h2>
            {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
        </div>
        {action}
    </div>
);
