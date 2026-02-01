import { motion } from "motion/react";
import {
    Package,
    CheckCircle,
    Download,
    Receipt,
} from "lucide-react";

interface BillingPageProps {
    showToast: (message: string, type: "success" | "error" | "info") => void;
    onExport: (type: string) => void;
}

export function BillingPage({ showToast, onExport }: BillingPageProps) {
    const handleUpgradePlan = () => {
        const apiBase = window.location.hostname === "localhost" ? "http://localhost:8000" : window.location.origin;
        window.open(`${apiBase}/.netlify/functions/checkout?plan=enterprise`, "_blank");
    };

    const handleUpdatePayment = () => {
        showToast("Redirecting to payment portal...", "info");
        const apiBase = window.location.hostname === "localhost" ? "http://localhost:8000" : window.location.origin;
        window.open(`${apiBase}/.netlify/functions/checkout?update=true`, "_blank");
    };

    return (
        <motion.div
            key="billing"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Current Plan */}
            <div className="bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20 rounded-xl p-6 mb-6">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <Package className="w-5 h-5 text-emerald-500" />
                            <span className="text-white font-semibold text-lg">Pro Plan</span>
                            <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-500 text-xs rounded">Active</span>
                        </div>
                        <p className="text-gray-400 text-sm">50,000 MAA • Unlimited API calls • Priority support</p>
                        <p className="text-gray-500 text-xs mt-2">Next billing date: February 1, 2026</p>
                    </div>
                    <div className="text-right">
                        <div className="text-3xl font-bold text-white">$199</div>
                        <div className="text-gray-500 text-sm">/month</div>
                        <button
                            onClick={handleUpgradePlan}
                            className="mt-3 px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-sm"
                        >
                            Upgrade Plan
                        </button>
                    </div>
                </div>
            </div>

            {/* Usage This Period */}
            <div className="grid grid-cols-3 gap-4 mb-8">
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <p className="text-xs text-gray-500 mb-2">Monthly Active Agents</p>
                    <div className="flex items-end gap-2">
                        <span className="text-2xl font-semibold text-white">12,847</span>
                        <span className="text-gray-500 text-sm mb-1">/ 50,000</span>
                    </div>
                    <div className="mt-3 h-2 bg-[#222] rounded overflow-hidden">
                        <div className="h-full w-[26%] bg-gradient-to-r from-emerald-500 to-cyan-500 rounded" />
                    </div>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <p className="text-xs text-gray-500 mb-2">API Requests</p>
                    <div className="flex items-end gap-2">
                        <span className="text-2xl font-semibold text-white">847K</span>
                        <span className="text-gray-500 text-sm mb-1">/ unlimited</span>
                    </div>
                    <div className="mt-3 h-2 bg-[#222] rounded overflow-hidden">
                        <div className="h-full w-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded" />
                    </div>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <p className="text-xs text-gray-500 mb-2">Transaction Volume</p>
                    <div className="flex items-end gap-2">
                        <span className="text-2xl font-semibold text-white">$847.2K</span>
                    </div>
                    <p className="text-xs text-emerald-500 mt-2">↑ 15.7% from last month</p>
                </div>
            </div>

            {/* Payment Method */}
            <div className="mb-8">
                <h3 className="text-white font-medium mb-4">Payment Method</h3>
                <div className="bg-[#111] border border-[#222] rounded-xl p-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-400 rounded flex items-center justify-center text-white text-xs font-bold">
                            VISA
                        </div>
                        <div>
                            <p className="text-white text-sm">Visa ending in 4242</p>
                            <p className="text-gray-500 text-xs">Expires 12/2028</p>
                        </div>
                    </div>
                    <button
                        onClick={handleUpdatePayment}
                        className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-sm"
                    >
                        Update
                    </button>
                </div>
            </div>

            {/* Invoices */}
            <div>
                <h3 className="text-white font-medium mb-4">Recent Invoices</h3>
                <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-[#222] bg-[#0d0d0d] text-left">
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {[
                                { id: "INV-2026-001", date: "Jan 1, 2026", amount: "$199.00", status: "paid" },
                                { id: "INV-2025-012", date: "Dec 1, 2025", amount: "$199.00", status: "paid" },
                                { id: "INV-2025-011", date: "Nov 1, 2025", amount: "$199.00", status: "paid" },
                                { id: "INV-2025-010", date: "Oct 1, 2025", amount: "$199.00", status: "paid" },
                            ].map((invoice, i) => (
                                <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                                    <td className="py-3.5 px-4">
                                        <div className="flex items-center gap-2">
                                            <Receipt className="w-4 h-4 text-gray-500" />
                                            <span className="text-white text-sm">{invoice.id}</span>
                                        </div>
                                    </td>
                                    <td className="py-3.5 px-4 text-gray-500 text-sm">{invoice.date}</td>
                                    <td className="py-3.5 px-4 text-white font-medium">{invoice.amount}</td>
                                    <td className="py-3.5 px-4">
                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-500">
                                            <CheckCircle className="w-3 h-3" />
                                            Paid
                                        </span>
                                    </td>
                                    <td className="py-3.5 px-4">
                                        <button
                                            onClick={() => onExport(`invoice ${invoice.id}`)}
                                            className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs"
                                        >
                                            <Download className="w-3.5 h-3.5 inline mr-1" />
                                            PDF
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </motion.div>
    );
}
