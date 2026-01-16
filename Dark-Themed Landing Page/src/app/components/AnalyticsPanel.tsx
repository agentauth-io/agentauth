import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { BarChart3, TrendingUp, TrendingDown, CheckCircle, XCircle } from "lucide-react";

const API_BASE = window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "https://agentauth-production.up.railway.app";

interface AnalyticsSummary {
    total_authorizations: number;
    total_approved: number;
    total_denied: number;
    total_amount: string;
    approval_rate: number;
    today_authorizations: number;
    today_approved: number;
    today_denied: number;
    today_amount: string;
    month_authorizations: number;
    month_amount: string;
    top_merchants: { merchant: string; count: number; amount: string }[];
    top_agents: { agent_id: string; count: number; amount: string }[];
}

interface TrendData {
    dates: string[];
    authorizations: number[];
    amounts: number[];
    approval_rates: number[];
}

export function AnalyticsPanel() {
    const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
    const [trends, setTrends] = useState<TrendData | null>(null);

    useEffect(() => {
        fetchAnalytics();
    }, []);

    const fetchAnalytics = async () => {
        try {
            const [summaryRes, trendsRes] = await Promise.all([
                fetch(`${API_BASE}/v1/analytics/summary`),
                fetch(`${API_BASE}/v1/analytics/trends?days=7`)
            ]);
            if (summaryRes.ok) setSummary(await summaryRes.json());
            if (trendsRes.ok) setTrends(await trendsRes.json());
        } catch (err) {
            console.error("Failed to fetch analytics:", err);
        }
    };

    const maxAuth = trends ? Math.max(...trends.authorizations, 1) : 1;

    return (
        <motion.div
            className="rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.03] to-transparent overflow-hidden"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
        >
            <div className="px-6 py-4 border-b border-white/10">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-cyan-400" />
                    Analytics
                </h2>
                <p className="text-sm text-gray-400">Authorization metrics and trends</p>
            </div>

            <div className="p-6">
                {/* Summary Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                        <div className="flex items-center gap-2 mb-1">
                            <CheckCircle className="w-4 h-4 text-green-400" />
                            <span className="text-xs text-gray-400">Approved</span>
                        </div>
                        <p className="text-xl font-bold text-green-400">{summary?.total_approved || 0}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                        <div className="flex items-center gap-2 mb-1">
                            <XCircle className="w-4 h-4 text-red-400" />
                            <span className="text-xs text-gray-400">Denied</span>
                        </div>
                        <p className="text-xl font-bold text-red-400">{summary?.total_denied || 0}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                        <div className="flex items-center gap-2 mb-1">
                            <TrendingUp className="w-4 h-4 text-cyan-400" />
                            <span className="text-xs text-gray-400">Approval Rate</span>
                        </div>
                        <p className="text-xl font-bold text-cyan-400">{summary?.approval_rate || 0}%</p>
                    </div>
                    <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                        <div className="flex items-center gap-2 mb-1">
                            <TrendingDown className="w-4 h-4 text-purple-400" />
                            <span className="text-xs text-gray-400">Total Volume</span>
                        </div>
                        <p className="text-xl font-bold text-purple-400">${summary?.total_amount || "0"}</p>
                    </div>
                </div>

                {/* 7-Day Chart */}
                <div className="mb-6">
                    <h3 className="text-sm font-medium text-gray-400 mb-3">Last 7 Days</h3>
                    <div className="flex items-end gap-1 h-32">
                        {trends?.authorizations.slice(-7).map((count, i) => {
                            const height = (count / maxAuth) * 100;
                            const date = trends.dates.slice(-7)[i];
                            const day = new Date(date).toLocaleDateString("en", { weekday: "short" });
                            return (
                                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                                    <motion.div
                                        className="w-full bg-gradient-to-t from-cyan-500/50 to-purple-500/50 rounded-t-sm"
                                        initial={{ height: 0 }}
                                        animate={{ height: `${Math.max(height, 4)}%` }}
                                        transition={{ delay: i * 0.05 }}
                                    />
                                    <span className="text-[10px] text-gray-500">{day}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Top Merchants */}
                {summary?.top_merchants && summary.top_merchants.length > 0 && (
                    <div>
                        <h3 className="text-sm font-medium text-gray-400 mb-2">Top Merchants</h3>
                        <div className="space-y-2">
                            {summary.top_merchants.slice(0, 3).map((m, i) => (
                                <div key={i} className="flex items-center justify-between text-sm">
                                    <span className="text-gray-300">{m.merchant || "Unknown"}</span>
                                    <span className="text-gray-500">{m.count} txns • ${m.amount}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Empty State */}
                {!summary?.total_authorizations && (
                    <div className="text-center py-8 text-gray-500">
                        <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-30" />
                        <p>No authorization data yet</p>
                        <p className="text-xs">Stats will appear after agents make requests</p>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
