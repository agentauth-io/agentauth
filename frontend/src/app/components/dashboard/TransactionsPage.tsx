import { useState } from "react";
import { motion } from "motion/react";
import {
    Search,
    Download,
    MoreVertical,
} from "lucide-react";

interface TransactionsPageProps {
    showToast: (message: string, type: "success" | "error" | "info") => void;
    onExport: (type: string) => void;
}

export function TransactionsPage({ showToast, onExport }: TransactionsPageProps) {
    const [txSearch, setTxSearch] = useState("");
    const [txStatusFilter, setTxStatusFilter] = useState("all");
    const [txTimeFilter, setTxTimeFilter] = useState("7d");
    const [txPage, setTxPage] = useState(1);

    return (
        <motion.div
            key="transactions"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Filters */}
            <div className="flex items-center gap-4 mb-6">
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Search by transaction ID, merchant, or amount..."
                        value={txSearch}
                        onChange={(e) => setTxSearch(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-[#111] border border-[#222] rounded-lg text-white text-sm focus:outline-none focus:border-[#444]"
                    />
                </div>
                <select
                    value={txStatusFilter}
                    onChange={(e) => setTxStatusFilter(e.target.value)}
                    className="px-4 py-2.5 bg-[#111] border border-[#222] rounded-lg text-white text-sm focus:outline-none"
                >
                    <option value="all">All Status</option>
                    <option value="authorized">Authorized</option>
                    <option value="denied">Denied</option>
                    <option value="pending">Pending</option>
                </select>
                <select
                    value={txTimeFilter}
                    onChange={(e) => setTxTimeFilter(e.target.value)}
                    className="px-4 py-2.5 bg-[#111] border border-[#222] rounded-lg text-white text-sm focus:outline-none"
                >
                    <option value="7d">Last 7 days</option>
                    <option value="30d">Last 30 days</option>
                    <option value="90d">Last 90 days</option>
                    <option value="all">All time</option>
                </select>
                <button
                    onClick={() => onExport("transactions")}
                    className="flex items-center gap-2 px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-sm hover:bg-white/10"
                >
                    <Download className="w-4 h-4" />
                    Export
                </button>
            </div>

            {/* Transactions Table */}
            <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-[#222] bg-[#0d0d0d] text-left">
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Transaction ID</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Agent</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Merchant</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider"></th>
                        </tr>
                    </thead>
                    <tbody>
                        {[
                            { id: "txn_1a2b3c4d5e6f", agent: "procurement-bot", merchant: "AWS", amount: 1249.99, status: "authorized", time: "2 min ago" },
                            { id: "txn_2b3c4d5e6f7g", agent: "expense-agent", merchant: "Stripe", amount: 499.00, status: "authorized", time: "15 min ago" },
                            { id: "txn_3c4d5e6f7g8h", agent: "travel-assistant", merchant: "United Airlines", amount: 2847.50, status: "pending", time: "32 min ago" },
                            { id: "txn_4d5e6f7g8h9i", agent: "procurement-bot", merchant: "Gambling Site", amount: 500.00, status: "denied", time: "1 hr ago" },
                            { id: "txn_5e6f7g8h9i0j", agent: "subscription-mgr", merchant: "OpenAI", amount: 200.00, status: "authorized", time: "2 hr ago" },
                            { id: "txn_6f7g8h9i0j1k", agent: "inventory-bot", merchant: "Shopify", amount: 79.00, status: "authorized", time: "3 hr ago" },
                            { id: "txn_7g8h9i0j1k2l", agent: "expense-agent", merchant: "GitHub", amount: 44.00, status: "authorized", time: "5 hr ago" },
                            { id: "txn_8h9i0j1k2l3m", agent: "travel-assistant", merchant: "Marriott", amount: 892.00, status: "authorized", time: "6 hr ago" },
                        ].map((tx, i) => (
                            <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                                <td className="py-3.5 px-4">
                                    <code className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded">{tx.id}</code>
                                </td>
                                <td className="py-3.5 px-4">
                                    <code className="text-cyan-400 text-sm">{tx.agent}</code>
                                </td>
                                <td className="py-3.5 px-4 text-white text-sm">{tx.merchant}</td>
                                <td className="py-3.5 px-4 text-white font-medium">${tx.amount.toFixed(2)}</td>
                                <td className="py-3.5 px-4">
                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                                        tx.status === "authorized" ? "bg-emerald-500/10 text-emerald-500" :
                                        tx.status === "denied" ? "bg-red-500/10 text-red-500" :
                                        "bg-yellow-500/10 text-yellow-500"
                                    }`}>
                                        <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                        {tx.status.charAt(0).toUpperCase() + tx.status.slice(1)}
                                    </span>
                                </td>
                                <td className="py-3.5 px-4 text-gray-500 text-sm">{tx.time}</td>
                                <td className="py-3.5 px-4">
                                    <button
                                        onClick={() => showToast(`Transaction ${tx.id} details`, "info")}
                                        className="p-2 hover:bg-white/5 rounded-lg"
                                    >
                                        <MoreVertical className="w-4 h-4 text-gray-500" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-4">
                <span className="text-sm text-gray-500">Showing {(txPage - 1) * 8 + 1}-{Math.min(txPage * 8, 12847)} of 12,847 transactions</span>
                <div className="flex gap-2">
                    <button
                        onClick={() => setTxPage(p => Math.max(1, p - 1))}
                        disabled={txPage === 1}
                        className="px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-sm hover:bg-white/10 disabled:opacity-50"
                    >
                        Previous
                    </button>
                    {[1, 2, 3].map(p => (
                        <button
                            key={p}
                            onClick={() => setTxPage(p)}
                            className={`px-3 py-1.5 border rounded-lg text-sm ${txPage === p ? "bg-white/10 border-[#444]" : "bg-white/5 border-[#333] hover:bg-white/10"}`}
                        >
                            {p}
                        </button>
                    ))}
                    <span className="px-2 py-1.5 text-gray-500">...</span>
                    <button
                        onClick={() => setTxPage(1606)}
                        className={`px-3 py-1.5 border rounded-lg text-sm ${txPage === 1606 ? "bg-white/10 border-[#444]" : "bg-white/5 border-[#333] hover:bg-white/10"}`}
                    >
                        1606
                    </button>
                    <button
                        onClick={() => setTxPage(p => Math.min(1606, p + 1))}
                        disabled={txPage === 1606}
                        className="px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-sm hover:bg-white/10 disabled:opacity-50"
                    >
                        Next
                    </button>
                </div>
            </div>
        </motion.div>
    );
}
