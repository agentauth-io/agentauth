import { useState, useEffect } from "react";
import { motion } from "motion/react";
import {
    Activity,
    Users,
    CreditCard,
    TrendingUp,
    RefreshCw,
    Clock,
    CheckCircle,
    XCircle,
    AlertCircle,
    LogOut,
} from "lucide-react";
import { SpendingLimitsCard } from "./SpendingLimitsCard";
import { RulesManager } from "./RulesManager";
import { AnalyticsPanel } from "./AnalyticsPanel";

// API base URL - use localhost for local dev, production URL otherwise
const API_BASE = window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "https://agentauth-production.up.railway.app";

interface DashboardStats {
    total_consents: number;
    active_consents: number;
    consents_today: number;
    avg_max_amount: number;
    api_status: string;
    last_updated: string;
}

interface Transaction {
    id: string;
    user_id: string;
    agent_id: string;
    intent: string;
    max_amount: number;
    currency: string;
    is_active: boolean;
    created_at: string;
}

interface AnalyticsData {
    date: string;
    consents: number;
    authorizations: number;
}

const StatCard = ({
    title,
    value,
    icon: Icon,
    trend,
    color = "white",
}: {
    title: string;
    value: string | number;
    icon: any;
    trend?: string;
    color?: string;
}) => (
    <motion.div
        className="relative p-6 rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.05] to-transparent backdrop-blur-sm overflow-hidden"
        whileHover={{ y: -4, transition: { duration: 0.2 } }}
    >
        <div className="flex items-start justify-between">
            <div>
                <p className="text-sm text-gray-400 mb-1">{title}</p>
                <p className="text-3xl font-bold text-white">{value}</p>
                {trend && (
                    <p className="text-sm text-green-400 mt-2 flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        {trend}
                    </p>
                )}
            </div>
            <div className={`p-3 rounded-xl bg-${color}/10`}>
                <Icon className={`w-6 h-6 text-${color}`} />
            </div>
        </div>
    </motion.div>
);

const TransactionRow = ({ tx }: { tx: Transaction }) => (
    <motion.tr
        className="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
    >
        <td className="py-4 px-4">
            <code className="text-xs text-cyan-400 bg-cyan-400/10 px-2 py-1 rounded">
                {tx.id.substring(0, 12)}...
            </code>
        </td>
        <td className="py-4 px-4 text-gray-300">{tx.user_id}</td>
        <td className="py-4 px-4 text-gray-300">{tx.agent_id}</td>
        <td className="py-4 px-4 text-gray-400 max-w-[200px] truncate">
            {tx.intent}
        </td>
        <td className="py-4 px-4 text-right font-medium text-white">
            ${tx.max_amount.toFixed(2)}
        </td>
        <td className="py-4 px-4">
            {tx.is_active ? (
                <span className="inline-flex items-center gap-1 text-green-400 text-sm">
                    <CheckCircle className="w-4 h-4" /> Active
                </span>
            ) : (
                <span className="inline-flex items-center gap-1 text-gray-500 text-sm">
                    <XCircle className="w-4 h-4" /> Revoked
                </span>
            )}
        </td>
        <td className="py-4 px-4 text-gray-500 text-sm">
            {new Date(tx.created_at).toLocaleString()}
        </td>
    </motion.tr>
);

export function Dashboard() {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

    const fetchData = async () => {
        try {
            setIsLoading(true);
            setError(null);

            // Fetch stats
            const statsRes = await fetch(`${API_BASE}/v1/dashboard/stats`);
            if (statsRes.ok) {
                const statsData = await statsRes.json();
                setStats(statsData);
            }

            // Fetch transactions
            const txRes = await fetch(`${API_BASE}/v1/dashboard/transactions?limit=20`);
            if (txRes.ok) {
                const txData = await txRes.json();
                setTransactions(txData.transactions || []);
            }

            setLastRefresh(new Date());
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch data");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();

        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <section className="relative px-6 py-12 min-h-screen bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <motion.div
                    className="flex items-center justify-between mb-8"
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
                        <p className="text-gray-400">
                            Real-time monitoring for AgentAuth
                        </p>
                    </div>

                    <div className="flex items-center gap-4">
                        <span className="text-sm text-gray-500 flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Last updated: {lastRefresh.toLocaleTimeString()}
                        </span>
                        <motion.button
                            onClick={fetchData}
                            disabled={isLoading}
                            className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm transition-colors disabled:opacity-50"
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
                            Refresh
                        </motion.button>
                    </div>
                </motion.div>

                {/* Error Banner */}
                {error && (
                    <motion.div
                        className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3"
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <span className="text-red-400">{error}</span>
                    </motion.div>
                )}

                {/* Stats Grid */}
                <motion.div
                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.1 }}
                >
                    <StatCard
                        title="Total Consents"
                        value={stats?.total_consents ?? "-"}
                        icon={Users}
                        color="cyan"
                    />
                    <StatCard
                        title="Active Consents"
                        value={stats?.active_consents ?? "-"}
                        icon={Activity}
                        trend={stats ? `${((stats.active_consents / (stats.total_consents || 1)) * 100).toFixed(0)}% active` : undefined}
                        color="green"
                    />
                    <StatCard
                        title="Today's Consents"
                        value={stats?.consents_today ?? "-"}
                        icon={TrendingUp}
                        color="purple"
                    />
                    <StatCard
                        title="Avg Max Amount"
                        value={stats ? `$${stats.avg_max_amount}` : "-"}
                        icon={CreditCard}
                        color="yellow"
                    />
                </motion.div>

                {/* API Status */}
                <motion.div
                    className="mb-8 p-4 rounded-xl border border-white/10 bg-white/[0.02] flex items-center justify-between"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                >
                    <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${stats?.api_status === "healthy" ? "bg-green-500" : "bg-red-500"} animate-pulse`} />
                        <span className="text-white font-medium">API Status</span>
                        <span className="text-gray-400">{API_BASE}</span>
                    </div>
                    <span className={`text-sm ${stats?.api_status === "healthy" ? "text-green-400" : "text-red-400"}`}>
                        {stats?.api_status === "healthy" ? "All systems operational" : "Connection issues"}
                    </span>
                </motion.div>

                {/* Spending Limits & Rules Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <SpendingLimitsCard />
                    <RulesManager />
                </div>

                {/* Analytics Panel */}
                <div className="mb-8">
                    <AnalyticsPanel />
                </div>

                {/* Transactions Table */}
                <motion.div
                    className="rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.03] to-transparent overflow-hidden"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <div className="px-6 py-4 border-b border-white/10">
                        <h2 className="text-lg font-semibold text-white">Recent Transactions</h2>
                        <p className="text-sm text-gray-400">Latest consent records</p>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-white/10 text-left text-gray-400 text-sm">
                                    <th className="py-3 px-4 font-medium">Consent ID</th>
                                    <th className="py-3 px-4 font-medium">User</th>
                                    <th className="py-3 px-4 font-medium">Agent</th>
                                    <th className="py-3 px-4 font-medium">Intent</th>
                                    <th className="py-3 px-4 font-medium text-right">Max Amount</th>
                                    <th className="py-3 px-4 font-medium">Status</th>
                                    <th className="py-3 px-4 font-medium">Created</th>
                                </tr>
                            </thead>
                            <tbody>
                                {transactions.length > 0 ? (
                                    transactions.map((tx) => (
                                        <TransactionRow key={tx.id} tx={tx} />
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={7} className="py-12 text-center text-gray-500">
                                            {isLoading ? (
                                                <div className="flex items-center justify-center gap-2">
                                                    <RefreshCw className="w-5 h-5 animate-spin" />
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
                </motion.div>
            </div>
        </section>
    );
}
