// Billing Page Component

import { motion } from "motion/react";
import { Package, CheckCircle, Download, Receipt } from "lucide-react";

interface BillingInvoice {
    id: string;
    date: string;
    amount: string;
    status: string;
}

interface BillingPageProps {
    currentPlan: string;
    billingHistory: BillingInvoice[];
    onUpgradePlan: () => void;
    onUpdatePayment: () => void;
    onDownloadInvoice: (invoiceId: string) => void;
}

export function BillingPage({
    currentPlan,
    billingHistory,
    onUpgradePlan,
    onUpdatePayment,
    onDownloadInvoice,
}: BillingPageProps) {
    return (
        <motion.div
            key="billing"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Current Plan */}
            <div className="bg-gradient-to-r from-emerald-500/10 to-zinc-700/50 border border-emerald-500/20 rounded-xl p-6 mb-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <Package className="w-5 h-5 text-emerald-500" />
                            <span className="text-white font-semibold text-lg">{currentPlan} Plan</span>
                            <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-500 text-xs rounded">Active</span>
                        </div>
                        <p className="text-gray-400 text-sm">50,000 MAA • Unlimited API calls • Priority support</p>
                        <p className="text-gray-500 text-xs mt-2">Next billing date: February 1, 2026</p>
                    </div>
                    <div className="text-left md:text-right">
                        <div className="text-3xl font-bold text-white">$199</div>
                        <div className="text-gray-500 text-sm">/month</div>
                        <button 
                            onClick={onUpgradePlan}
                            className="mt-3 px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-sm text-white"
                        >
                            Upgrade Plan
                        </button>
                    </div>
                </div>
            </div>

            {/* Usage This Period */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <p className="text-xs text-gray-500 mb-2">Monthly Active Agents</p>
                    <div className="flex items-end gap-2">
                        <span className="text-2xl font-semibold text-white">12,847</span>
                        <span className="text-gray-500 text-sm mb-1">/ 50,000</span>
                    </div>
                    <div className="mt-3 h-2 bg-[#222] rounded overflow-hidden">
                        <div className="h-full w-[26%] bg-gradient-to-r from-emerald-500 to-zinc-500 rounded" />
                    </div>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <p className="text-xs text-gray-500 mb-2">API Requests</p>
                    <div className="flex items-end gap-2">
                        <span className="text-2xl font-semibold text-white">847K</span>
                        <span className="text-gray-500 text-sm mb-1">/ unlimited</span>
                    </div>
                    <div className="mt-3 h-2 bg-[#222] rounded overflow-hidden">
                        <div className="h-full w-full bg-gradient-to-r from-emerald-500 to-zinc-500 rounded" />
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
                <div className="bg-[#111] border border-[#222] rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
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
                        onClick={onUpdatePayment}
                        className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-sm text-white"
                    >
                        Update
                    </button>
                </div>
            </div>

            {/* Invoices */}
            <div>
                <h3 className="text-white font-medium mb-4">Recent Invoices</h3>
                <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden overflow-x-auto">
                    <table className="w-full min-w-[500px]">
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
                            {billingHistory.map((invoice) => (
                                <tr key={invoice.id} className="border-b border-white/5 hover:bg-white/[0.02]">
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
                                            {invoice.status}
                                        </span>
                                    </td>
                                    <td className="py-3.5 px-4">
                                        <button 
                                            onClick={() => onDownloadInvoice(invoice.id)}
                                            className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs text-white"
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

export default BillingPage;
