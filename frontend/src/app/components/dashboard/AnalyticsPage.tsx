import { motion } from "motion/react";
import {
    CheckCircle,
    XCircle,
    TrendingUp,
    DollarSign,
    Bot,
} from "lucide-react";

export function AnalyticsPage() {
    return (
        <motion.div
            key="analytics"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Summary Stats */}
            <div className="grid grid-cols-4 gap-4 mb-8">
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <div className="flex items-center gap-2 text-emerald-500 mb-2">
                        <CheckCircle className="w-5 h-5" />
                        <span className="text-xs text-gray-500">Approved</span>
                    </div>
                    <div className="text-3xl font-semibold text-white">12,847</div>
                    <div className="text-xs text-emerald-500 mt-1">↑ 8.3% from last week</div>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <div className="flex items-center gap-2 text-red-500 mb-2">
                        <XCircle className="w-5 h-5" />
                        <span className="text-xs text-gray-500">Denied</span>
                    </div>
                    <div className="text-3xl font-semibold text-white">342</div>
                    <div className="text-xs text-emerald-500 mt-1">↓ 12.1% from last week</div>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <div className="flex items-center gap-2 text-cyan-500 mb-2">
                        <TrendingUp className="w-5 h-5" />
                        <span className="text-xs text-gray-500">Approval Rate</span>
                    </div>
                    <div className="text-3xl font-semibold text-white">97.4%</div>
                    <div className="text-xs text-emerald-500 mt-1">↑ 0.3% from last week</div>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <div className="flex items-center gap-2 text-purple-500 mb-2">
                        <DollarSign className="w-5 h-5" />
                        <span className="text-xs text-gray-500">Total Volume</span>
                    </div>
                    <div className="text-3xl font-semibold text-white">$847.2K</div>
                    <div className="text-xs text-emerald-500 mt-1">↑ 15.7% from last week</div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-2 gap-6 mb-8">
                {/* Authorization Trends */}
                <div className="bg-[#111] border border-[#222] rounded-xl p-6">
                    <h3 className="text-sm font-medium text-white mb-4">Authorization Trends</h3>
                    <div className="flex items-end gap-2 h-48">
                        {[65, 78, 52, 91, 84, 73, 95, 88, 76, 82, 69, 94].map((value, i) => (
                            <div key={i} className="flex-1 flex flex-col items-center gap-2">
                                <div
                                    className="w-full bg-gradient-to-t from-emerald-500 to-emerald-600 rounded-t min-h-1"
                                    style={{ height: `${value}%` }}
                                />
                            </div>
                        ))}
                    </div>
                    <div className="flex justify-between mt-3 text-xs text-gray-500">
                        <span>Jan</span>
                        <span>Feb</span>
                        <span>Mar</span>
                        <span>Apr</span>
                        <span>May</span>
                        <span>Jun</span>
                        <span>Jul</span>
                        <span>Aug</span>
                        <span>Sep</span>
                        <span>Oct</span>
                        <span>Nov</span>
                        <span>Dec</span>
                    </div>
                </div>

                {/* Volume by Category */}
                <div className="bg-[#111] border border-[#222] rounded-xl p-6">
                    <h3 className="text-sm font-medium text-white mb-4">Volume by Category</h3>
                    <div className="space-y-4">
                        {[
                            { name: "SaaS Subscriptions", value: 45, amount: "$381.2K" },
                            { name: "E-commerce", value: 28, amount: "$237.2K" },
                            { name: "Cloud Services", value: 15, amount: "$127.1K" },
                            { name: "Travel & Transport", value: 8, amount: "$67.8K" },
                            { name: "Other", value: 4, amount: "$33.9K" },
                        ].map((cat, i) => (
                            <div key={i}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">{cat.name}</span>
                                    <span className="text-white">{cat.amount}</span>
                                </div>
                                <div className="h-2 bg-[#222] rounded overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded"
                                        style={{ width: `${cat.value}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Top Merchants & Agents */}
            <div className="grid grid-cols-2 gap-6">
                <div className="bg-[#111] border border-[#222] rounded-xl p-6">
                    <h3 className="text-sm font-medium text-white mb-4">Top Merchants</h3>
                    <div className="space-y-3">
                        {[
                            { name: "AWS", count: 2847, amount: "$156.2K" },
                            { name: "Stripe", count: 1923, amount: "$89.4K" },
                            { name: "OpenAI", count: 1456, amount: "$72.8K" },
                            { name: "Vercel", count: 892, amount: "$44.6K" },
                            { name: "GitHub", count: 734, amount: "$36.7K" },
                        ].map((m, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-white/[0.02] rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-white/5 rounded-lg flex items-center justify-center text-gray-400 text-xs font-bold">
                                        {i + 1}
                                    </div>
                                    <span className="text-white">{m.name}</span>
                                </div>
                                <div className="text-right">
                                    <div className="text-white text-sm">{m.amount}</div>
                                    <div className="text-xs text-gray-500">{m.count} txns</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-[#111] border border-[#222] rounded-xl p-6">
                    <h3 className="text-sm font-medium text-white mb-4">Top Agents</h3>
                    <div className="space-y-3">
                        {[
                            { name: "procurement-bot", count: 3421, amount: "$289.3K" },
                            { name: "expense-agent", count: 2156, amount: "$187.2K" },
                            { name: "travel-assistant", count: 1823, amount: "$156.8K" },
                            { name: "subscription-mgr", count: 1245, amount: "$112.4K" },
                            { name: "inventory-bot", count: 987, amount: "$101.5K" },
                        ].map((a, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-white/[0.02] rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-emerald-500/10 rounded-lg flex items-center justify-center">
                                        <Bot className="w-4 h-4 text-emerald-500" />
                                    </div>
                                    <code className="text-cyan-400 text-sm">{a.name}</code>
                                </div>
                                <div className="text-right">
                                    <div className="text-white text-sm">{a.amount}</div>
                                    <div className="text-xs text-gray-500">{a.count} txns</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
