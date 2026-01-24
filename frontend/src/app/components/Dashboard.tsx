import { useState, useEffect } from "react";
import { motion } from "motion/react";
import {
    LayoutDashboard,
    BarChart3,
    Shield,
    Clock,
    Users,
    FileText,
    Key,
    Link2,
    BookOpen,
    CreditCard,
    Settings,
    Zap,
    Plus,
    Copy,
    RefreshCw,
    ChevronRight,
    LogOut,
} from "lucide-react";

// Types
interface Transaction {
    id: string;
    amount: number;
    currency: string;
    status: "authorized" | "denied" | "pending";
    merchant: string;
    created_at: string;
    description: string;
}

interface DashboardStats {
    total_authorizations: number;
    transaction_volume: number;
    approval_rate: number;
    avg_response_time: number;
    transactions: Transaction[];
}

interface NavItemProps {
    icon: React.ElementType;
    label: string;
    active?: boolean;
    onClick?: () => void;
}

// Navigation Item Component
const NavItem = ({ icon: Icon, label, active, onClick }: NavItemProps) => (
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
const StatCard = ({
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
const UsageBar = ({
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
const ActivityChart = ({ data, period, onPeriodChange }: {
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
const ApiKeyCard = ({
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
            <button className="w-9 h-9 rounded-lg bg-white/5 border border-[#333] text-gray-500 hover:bg-white/10 hover:text-white flex items-center justify-center">
                <Copy className="w-4 h-4" />
            </button>
        </div>
    </div>
);

// Transaction Row Component
const TransactionRow = ({ tx }: { tx: Transaction }) => {
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
const QuickAction = ({
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

// Main Dashboard Component
export function Dashboard() {
    const [activeNav, setActiveNav] = useState("dashboard");
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [period, setPeriod] = useState("7d");
    const [chartData, setChartData] = useState([65, 80, 45, 90, 70, 55, 40]);

    const fetchData = async () => {
        try {
            setIsLoading(true);
            const apiBase = window.location.hostname === "localhost" ? "http://localhost:8000" : window.location.origin;
            const response = await fetch(`${apiBase}/.netlify/functions/get-stripe-transactions?period=${period}&limit=20`);
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (error) {
            console.error("Failed to fetch dashboard data:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [period]);

    const handleLogout = () => {
        localStorage.removeItem("admin_token");
        localStorage.removeItem("admin_expires");
        window.location.href = "/";
    };

    // Format currency
    const formatCurrency = (amount: number) => {
        if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
        if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
        return `$${amount.toFixed(2)}`;
    };

    return (
        <div className="flex min-h-screen bg-[#0a0a0a] text-white font-['Inter',sans-serif]">
            {/* Sidebar */}
            <aside className="w-60 bg-[#111] border-r border-[#222] flex flex-col">
                {/* Logo */}
                <div className="flex items-center gap-2.5 px-5 py-5 border-b border-[#222]">
                    <img src="/agentauth-icon-dark.svg" alt="AgentAuth" className="w-7 h-7" />
                    <span className="text-base font-semibold">
                        Agent<span className="text-gray-500">Auth</span>
                    </span>
                </div>

                {/* Navigation */}
                <nav className="flex-1 py-5">
                    <div className="mb-6">
                        <div className="px-5 mb-2 text-[10px] uppercase tracking-wider text-gray-600">
                            Overview
                        </div>
                        <NavItem icon={LayoutDashboard} label="Dashboard" active={activeNav === "dashboard"} onClick={() => setActiveNav("dashboard")} />
                        <NavItem icon={BarChart3} label="Analytics" onClick={() => setActiveNav("analytics")} />
                    </div>

                    <div className="mb-6">
                        <div className="px-5 mb-2 text-[10px] uppercase tracking-wider text-gray-600">
                            Authorization
                        </div>
                        <NavItem icon={Shield} label="Transactions" onClick={() => setActiveNav("transactions")} />
                        <NavItem icon={Clock} label="Consents" onClick={() => setActiveNav("consents")} />
                        <NavItem icon={Users} label="Agents" onClick={() => setActiveNav("agents")} />
                        <NavItem icon={FileText} label="Audit Logs" onClick={() => setActiveNav("logs")} />
                    </div>

                    <div className="mb-6">
                        <div className="px-5 mb-2 text-[10px] uppercase tracking-wider text-gray-600">
                            Developers
                        </div>
                        <NavItem icon={Key} label="API Keys" onClick={() => setActiveNav("apikeys")} />
                        <NavItem icon={Link2} label="Webhooks" onClick={() => setActiveNav("webhooks")} />
                        <NavItem icon={BookOpen} label="Documentation" onClick={() => window.location.href = "/docs"} />
                    </div>

                    <div className="mb-6">
                        <div className="px-5 mb-2 text-[10px] uppercase tracking-wider text-gray-600">
                            Settings
                        </div>
                        <NavItem icon={Users} label="Team" onClick={() => setActiveNav("team")} />
                        <NavItem icon={CreditCard} label="Billing" onClick={() => setActiveNav("billing")} />
                        <NavItem icon={Settings} label="Settings" onClick={() => setActiveNav("settings")} />
                    </div>
                </nav>

                {/* Plan Badge */}
                <div className="p-5 border-t border-[#222]">
                    <div className="flex items-center gap-2 bg-white/5 p-3 rounded-lg">
                        <Zap className="w-4 h-4 text-emerald-500" />
                        <div>
                            <div className="text-sm font-medium text-emerald-500">Pro Plan</div>
                            <div className="text-xs text-gray-500">
                                {stats?.total_authorizations || 0} / 50,000 MAA
                            </div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                {/* Header */}
                <header className="flex justify-between items-center px-8 py-5 border-b border-[#222]">
                    <h1 className="text-xl font-semibold">Dashboard</h1>
                    <div className="flex gap-3">
                        <button
                            onClick={fetchData}
                            disabled={isLoading}
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-sm transition-colors"
                        >
                            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
                            Refresh
                        </button>
                        <a
                            href="/docs"
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-sm transition-colors"
                        >
                            <BookOpen className="w-4 h-4" />
                            Docs
                        </a>
                        <button className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-gray-200 text-black rounded-lg text-sm font-medium transition-colors">
                            <Plus className="w-4 h-4" />
                            New API Key
                        </button>
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 rounded-lg text-sm transition-colors"
                        >
                            <LogOut className="w-4 h-4" />
                            Logout
                        </button>
                    </div>
                </header>

                {/* Content */}
                <div className="p-8">
                    {/* Stats Grid */}
                    <div className="grid grid-cols-4 gap-4 mb-8">
                        <StatCard
                            label="Total Authorizations"
                            value={stats?.total_authorizations?.toLocaleString() || "0"}
                            change="+12.5% from last month"
                            positive
                            icon={Shield}
                        />
                        <StatCard
                            label="Transaction Volume"
                            value={formatCurrency(stats?.transaction_volume || 0)}
                            change="+8.2% from last month"
                            positive
                            icon={CreditCard}
                        />
                        <StatCard
                            label="Approval Rate"
                            value={`${stats?.approval_rate || 0}%`}
                            change="+0.3% from last month"
                            positive
                            icon={Shield}
                        />
                        <StatCard
                            label="Avg Response Time"
                            value={`${stats?.avg_response_time || 8.3}ms`}
                            change="-1.2ms improvement"
                            positive
                            icon={Clock}
                        />
                    </div>

                    {/* Quick Actions */}
                    <div className="grid grid-cols-4 gap-3 mb-8">
                        <QuickAction icon={Key} title="Create API Key" description="Generate credentials" />
                        <QuickAction icon={Settings} title="Configure Policy" description="Set spending limits" />
                        <QuickAction icon={Link2} title="Setup Webhook" description="Receive events" />
                        <QuickAction icon={FileText} title="View Logs" description="Audit trail" />
                    </div>

                    {/* Usage Section */}
                    <div className="mb-8">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-base font-semibold">Usage This Month</h2>
                            <span className="text-xs text-gray-500">Resets in 7 days</span>
                        </div>
                        <UsageBar
                            title="Monthly Active Agents (MAA)"
                            used={stats?.total_authorizations || 0}
                            total={50000}
                            variant={(stats?.total_authorizations || 0) > 37500 ? "warning" : "normal"}
                        />
                        <UsageBar
                            title="API Requests"
                            used={847293}
                            total={1000000}
                            variant="danger"
                        />
                        <UsageBar
                            title="Webhook Deliveries"
                            used={12384}
                            total={100000}
                        />
                    </div>

                    {/* Chart */}
                    <div className="mb-8">
                        <ActivityChart
                            data={chartData}
                            period={period}
                            onPeriodChange={setPeriod}
                        />
                    </div>

                    {/* Two Column Layout */}
                    <div className="grid grid-cols-2 gap-6">
                        {/* API Keys */}
                        <div>
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-base font-semibold">API Keys</h2>
                                <button className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs transition-colors">
                                    + New
                                </button>
                            </div>
                            <ApiKeyCard
                                name="Production Key"
                                createdAt="Created Jan 15, 2026"
                                keyPreview="aa_live_****...k8Jx"
                                isLive={true}
                            />
                            <ApiKeyCard
                                name="Test Key"
                                createdAt="Created Jan 10, 2026"
                                keyPreview="aa_test_****...m2Pq"
                                isLive={false}
                            />
                        </div>

                        {/* Recent Transactions */}
                        <div>
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-base font-semibold">Recent Transactions</h2>
                                <button className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs transition-colors">
                                    View All
                                </button>
                            </div>
                            <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-[#222] bg-[#0d0d0d] text-left">
                                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Transaction ID</th>
                                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {stats?.transactions && stats.transactions.length > 0 ? (
                                            stats.transactions.slice(0, 5).map((tx) => (
                                                <TransactionRow key={tx.id} tx={tx} />
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan={4} className="py-8 text-center text-gray-500">
                                                    {isLoading ? (
                                                        <div className="flex items-center justify-center gap-2">
                                                            <RefreshCw className="w-4 h-4 animate-spin" />
                                                            Loading transactions...
                                                        </div>
                                                    ) : (
                                                        "No transactions yet"
                                                    )}
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
