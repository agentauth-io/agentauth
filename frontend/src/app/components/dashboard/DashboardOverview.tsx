import { motion } from "motion/react";
import {
    Shield,
    CreditCard,
    Clock,
    Key,
    Settings,
    Webhook,
    FileText,
    RefreshCw,
} from "lucide-react";
import type { DashboardStats, NavSection } from "./types";
import { StatCard, UsageBar, ActivityChart, ApiKeyCard, TransactionRow, QuickAction, formatCurrency } from "./shared";

interface DashboardOverviewProps {
    stats: DashboardStats | null;
    isLoading: boolean;
    chartData: number[];
    period: string;
    onPeriodChange: (p: string) => void;
    onNavigate: (section: NavSection) => void;
}

export function DashboardOverview({
    stats,
    isLoading,
    chartData,
    period,
    onPeriodChange,
    onNavigate,
}: DashboardOverviewProps) {
    return (
        <motion.div
            key="dashboard"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
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
                <QuickAction icon={Key} title="Create API Key" description="Generate credentials" onClick={() => onNavigate("apikeys")} />
                <QuickAction icon={Settings} title="Configure Policy" description="Set spending limits" onClick={() => onNavigate("settings")} />
                <QuickAction icon={Webhook} title="Setup Webhook" description="Receive events" onClick={() => onNavigate("webhooks")} />
                <QuickAction icon={FileText} title="View Logs" description="Audit trail" onClick={() => onNavigate("logs")} />
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
                    onPeriodChange={onPeriodChange}
                />
            </div>

            {/* Two Column Layout */}
            <div className="grid grid-cols-2 gap-6">
                {/* API Keys */}
                <div>
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-base font-semibold">API Keys</h2>
                        <button onClick={() => onNavigate("apikeys")} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs transition-colors">
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
                        <button onClick={() => onNavigate("transactions")} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs transition-colors">
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
        </motion.div>
    );
}
