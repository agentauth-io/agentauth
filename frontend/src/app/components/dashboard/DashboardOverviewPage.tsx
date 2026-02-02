// Dashboard Overview Page Component

import { motion } from "motion/react";
import {
    Key,
    Settings,
    Webhook,
    FileText,
    Shield,
    CreditCard,
    Clock,
    RefreshCw,
    Landmark,
    AlertTriangle,
} from "lucide-react";
import { StatCard, UsageBar, ActivityChart, QuickAction, TransactionRow } from "./shared";
import { DashboardStats, formatCurrency } from "./types";

interface DashboardOverviewPageProps {
    stats: DashboardStats | null;
    isLoading: boolean;
    chartData: number[];
    period: "day" | "week" | "month";
    connectedAccounts: Array<{ id: string }>;
    connectError: string;
    isConnecting: boolean;
    onPeriodChange: (period: "day" | "week" | "month") => void;
    onNavigate: (nav: string) => void;
    onConnectStripe: () => void;
}

export function DashboardOverviewPage({
    stats,
    isLoading,
    chartData,
    period,
    connectedAccounts,
    connectError,
    isConnecting,
    onPeriodChange,
    onNavigate,
    onConnectStripe,
}: DashboardOverviewPageProps) {
    return (
        <motion.div
            key="dashboard"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Onboarding Banner for New Users */}
            {connectedAccounts.length === 0 && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8 bg-gradient-to-r from-[#635BFF]/20 via-[#0ea5e9]/20 to-[#10b981]/20 border border-[#635BFF]/30 rounded-2xl p-6"
                >
                    <div className="flex items-start gap-4">
                        <div className="w-14 h-14 bg-[#635BFF]/20 rounded-xl flex items-center justify-center flex-shrink-0">
                            <Landmark className="w-7 h-7 text-[#635BFF]" />
                        </div>
                        <div className="flex-1">
                            <h2 className="text-xl font-semibold text-white mb-2">Welcome to AgentAuth! 🚀</h2>
                            <p className="text-gray-400 mb-4">
                                Connect your Stripe account to start accepting payments from AI agents. 
                                This enables your agents to make authorized purchases on your behalf.
                            </p>
                            <div className="flex items-center gap-3">
                                <button 
                                    onClick={onConnectStripe}
                                    disabled={isConnecting}
                                    className="flex items-center gap-2 px-5 py-2.5 bg-[#635BFF] hover:bg-[#5851ea] text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                                >
                                    {isConnecting ? (
                                        <>
                                            <RefreshCw className="w-4 h-4 animate-spin" />
                                            Connecting...
                                        </>
                                    ) : (
                                        <>
                                            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                                                <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-6.99-2.109l-.9 5.555C5.175 22.99 8.385 24 11.714 24c2.641 0 4.843-.624 6.328-1.813 1.664-1.305 2.525-3.236 2.525-5.732 0-4.128-2.524-5.851-6.591-7.305z"/>
                                            </svg>
                                            Connect Stripe Account
                                        </>
                                    )}
                                </button>
                                <button 
                                    onClick={() => onNavigate("connected-accounts")}
                                    className="px-4 py-2.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-sm text-gray-300 transition-colors"
                                >
                                    Learn More
                                </button>
                            </div>
                            {connectError && (
                                <div className="mt-3 flex items-center gap-2 text-red-400 text-sm">
                                    <AlertTriangle className="w-4 h-4" />
                                    {connectError}
                                </div>
                            )}
                        </div>
                    </div>
                </motion.div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-4 gap-4 mb-8">
                <StatCard
                    label="Total Authorizations"
                    value={stats?.total_authorizations?.toLocaleString() || "0"}
                    change={stats?.total_authorizations ? "+12.5% from last month" : "No data yet"}
                    positive={!!stats?.total_authorizations}
                    icon={Shield}
                />
                <StatCard
                    label="Transaction Volume"
                    value={formatCurrency(stats?.transaction_volume || 0)}
                    change={stats?.transaction_volume ? "+8.2% from last month" : "No data yet"}
                    positive={!!stats?.transaction_volume}
                    icon={CreditCard}
                />
                <StatCard
                    label="Approval Rate"
                    value={stats?.total_authorizations ? `${stats?.approval_rate || 0}%` : "—"}
                    change={stats?.total_authorizations ? "+0.3% from last month" : "No data yet"}
                    positive={!!stats?.total_authorizations}
                    icon={Shield}
                />
                <StatCard
                    label="Avg Response Time"
                    value={stats?.total_authorizations ? `${stats?.avg_response_time || 8.3}ms` : "—"}
                    change={stats?.total_authorizations ? "-1.2ms improvement" : "No data yet"}
                    positive={!!stats?.total_authorizations}
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
                    used={0}
                    total={1000000}
                />
                <UsageBar
                    title="Webhook Deliveries"
                    used={0}
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
                    {/* Empty state for new users */}
                    <div className="bg-[#111] border border-[#222] border-dashed rounded-xl p-6 text-center">
                        <Key className="w-8 h-8 text-gray-600 mx-auto mb-3" />
                        <p className="text-gray-400 text-sm mb-3">No API keys yet</p>
                        <button 
                            onClick={() => onNavigate("apikeys")}
                            className="px-4 py-2 bg-white hover:bg-gray-200 text-black rounded-lg text-sm font-medium transition-colors"
                        >
                            Create Your First Key
                        </button>
                    </div>
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

export default DashboardOverviewPage;
