// Transactions Page Component

import { motion } from "motion/react";
import { Search, RefreshCw, Download, Shield } from "lucide-react";
import { Transaction } from "./types";

interface TransactionsPageProps {
    transactions: Transaction[];
    transactionsLoading: boolean;
    transactionsTotal: number;
    transactionsPage: number;
    transactionSearch: string;
    transactionStatus: string;
    onSearchChange: (value: string) => void;
    onStatusChange: (value: string) => void;
    onFetchTransactions: (page: number) => void;
    onExportTransactions: () => void;
}

export function TransactionsPage({
    transactions,
    transactionsLoading,
    transactionsTotal,
    transactionsPage,
    transactionSearch,
    transactionStatus,
    onSearchChange,
    onStatusChange,
    onFetchTransactions,
    onExportTransactions,
}: TransactionsPageProps) {
    const filteredTransactions = transactions
        .filter(tx => transactionStatus === "all" || 
            (transactionStatus === "active" && tx.is_active) || 
            (transactionStatus === "expired" && !tx.is_active))
        .filter(tx => !transactionSearch || 
            tx.id?.toLowerCase().includes(transactionSearch.toLowerCase()) ||
            tx.intent?.toLowerCase().includes(transactionSearch.toLowerCase()));

    return (
        <motion.div
            key="transactions"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Filters */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 mb-6">
                <div className="flex-1 min-w-[200px] relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Search by transaction ID, merchant, or amount..."
                        value={transactionSearch}
                        onChange={(e) => onSearchChange(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-[#111] border border-[#222] rounded-lg text-white text-sm focus:outline-none focus:border-[#444]"
                    />
                </div>
                <select 
                    value={transactionStatus}
                    onChange={(e) => onStatusChange(e.target.value)}
                    className="px-4 py-2.5 bg-[#111] border border-[#222] rounded-lg text-white text-sm focus:outline-none"
                >
                    <option value="all">All Status</option>
                    <option value="active">Authorized</option>
                    <option value="expired">Expired</option>
                </select>
                <button 
                    onClick={() => onFetchTransactions(1)}
                    className="flex items-center justify-center gap-2 px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-sm hover:bg-white/10 text-white"
                >
                    <RefreshCw className={`w-4 h-4 ${transactionsLoading ? 'animate-spin' : ''}`} />
                    Refresh
                </button>
                <button 
                    onClick={onExportTransactions}
                    className="flex items-center justify-center gap-2 px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-sm hover:bg-white/10 text-white"
                >
                    <Download className="w-4 h-4" />
                    Export
                </button>
            </div>

            {/* Transactions Table */}
            <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden overflow-x-auto">
                {transactionsLoading ? (
                    <div className="p-8 text-center">
                        <RefreshCw className="w-8 h-8 text-gray-500 animate-spin mx-auto mb-4" />
                        <p className="text-gray-500">Loading transactions...</p>
                    </div>
                ) : transactions.length === 0 ? (
                    <div className="p-8 text-center">
                        <Shield className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                        <h3 className="text-white font-medium mb-2">No Transactions Yet</h3>
                        <p className="text-gray-500 text-sm">Transactions will appear here once your agents start making authorized requests.</p>
                    </div>
                ) : (
                    <table className="w-full min-w-[600px]">
                        <thead>
                            <tr className="border-b border-[#222] bg-[#0d0d0d] text-left">
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Intent</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredTransactions.map((tx, i) => (
                                <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                                    <td className="py-3.5 px-4">
                                        <code className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded">
                                            {tx.id?.substring(0, 16)}...
                                        </code>
                                    </td>
                                    <td className="py-3.5 px-4 text-white text-sm max-w-[200px] truncate">
                                        {tx.intent || "N/A"}
                                    </td>
                                    <td className="py-3.5 px-4 text-white font-medium">
                                        ${(tx.max_amount || 0).toFixed(2)} {tx.currency}
                                    </td>
                                    <td className="py-3.5 px-4">
                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                                            tx.is_active ? "bg-emerald-500/10 text-emerald-500" : "bg-gray-500/10 text-gray-500"
                                        }`}>
                                            <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                            {tx.is_active ? "Active" : "Expired"}
                                        </span>
                                    </td>
                                    <td className="py-3.5 px-4 text-gray-500 text-sm">
                                        {tx.created_at ? new Date(tx.created_at).toLocaleDateString() : "N/A"}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Pagination */}
            {transactionsTotal > 0 && (
                <div className="flex items-center justify-between mt-4">
                    <span className="text-sm text-gray-500">
                        Showing {((transactionsPage - 1) * 10) + 1}-{Math.min(transactionsPage * 10, transactionsTotal)} of {transactionsTotal} transactions
                    </span>
                    <div className="flex gap-2">
                        <button 
                            onClick={() => onFetchTransactions(transactionsPage - 1)}
                            disabled={transactionsPage <= 1}
                            className="px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-sm hover:bg-white/10 disabled:opacity-50"
                        >
                            Previous
                        </button>
                        <span className="px-3 py-1.5 text-gray-400">Page {transactionsPage}</span>
                        <button 
                            onClick={() => onFetchTransactions(transactionsPage + 1)}
                            disabled={transactionsPage * 10 >= transactionsTotal}
                            className="px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-sm hover:bg-white/10 disabled:opacity-50"
                        >
                            Next
                        </button>
                    </div>
                </div>
            )}
        </motion.div>
    );
}

export default TransactionsPage;
