// Consents Page Component

import { motion } from "motion/react";
import { CheckCircle, XCircle, Clock, RefreshCw } from "lucide-react";
import { Consent } from "./types";

interface ConsentsPageProps {
    consents: Consent[];
    consentsLoading: boolean;
    onFetchConsents: () => void;
    onApproveConsent: (consentId: string) => void;
    onDenyConsent: (consentId: string) => void;
    onRevokeConsent: (consentId: string) => void;
}

export function ConsentsPage({
    consents,
    consentsLoading,
    onFetchConsents,
    onApproveConsent,
    onDenyConsent,
    onRevokeConsent,
}: ConsentsPageProps) {
    const activeConsents = consents.filter(c => c.is_active).length;
    const expiredConsents = consents.filter(c => !c.is_active).length;

    return (
        <motion.div
            key="consents"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <div className="flex items-center gap-2 text-emerald-500 mb-2">
                        <CheckCircle className="w-5 h-5" />
                        <span className="text-xs text-gray-500">Active Consents</span>
                    </div>
                    <div className="text-3xl font-semibold text-white">{activeConsents}</div>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <div className="flex items-center gap-2 text-gray-500 mb-2">
                        <XCircle className="w-5 h-5" />
                        <span className="text-xs text-gray-500">Expired</span>
                    </div>
                    <div className="text-3xl font-semibold text-white">{expiredConsents}</div>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <div className="flex items-center gap-2 text-cyan-500 mb-2">
                        <Clock className="w-5 h-5" />
                        <span className="text-xs text-gray-500">Total Consents</span>
                    </div>
                    <div className="text-3xl font-semibold text-white">{consents.length}</div>
                </div>
            </div>

            {/* Refresh Button */}
            <div className="mb-4 flex justify-end">
                <button 
                    onClick={onFetchConsents}
                    className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-[#333] rounded-lg text-sm hover:bg-white/10"
                >
                    <RefreshCw className={`w-4 h-4 ${consentsLoading ? 'animate-spin' : ''}`} />
                    Refresh
                </button>
            </div>

            {/* Active Consents */}
            <div>
                <h3 className="text-sm font-medium text-white mb-4">All Consents</h3>
                {consentsLoading ? (
                    <div className="bg-[#111] border border-[#222] rounded-xl p-8 text-center">
                        <RefreshCw className="w-8 h-8 text-gray-500 animate-spin mx-auto mb-4" />
                        <p className="text-gray-500">Loading consents...</p>
                    </div>
                ) : consents.length === 0 ? (
                    <div className="bg-[#111] border border-[#222] rounded-xl p-8 text-center">
                        <Clock className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                        <h3 className="text-white font-medium mb-2">No Consents Yet</h3>
                        <p className="text-gray-500 text-sm">Consents will appear here once users grant permissions to agents.</p>
                    </div>
                ) : (
                    <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden overflow-x-auto">
                        <table className="w-full min-w-[700px]">
                            <thead>
                                <tr className="border-b border-[#222] bg-[#0d0d0d] text-left">
                                    <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                                    <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Intent</th>
                                    <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Max Amount</th>
                                    <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                                    <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {consents.slice(0, 20).map((c, i) => (
                                    <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                                        <td className="py-3.5 px-4">
                                            <code className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded">
                                                {c.consent_id?.substring(0, 12)}...
                                            </code>
                                        </td>
                                        <td className="py-3.5 px-4 text-white text-sm max-w-[200px] truncate">
                                            {c.intent_description || "N/A"}
                                        </td>
                                        <td className="py-3.5 px-4 text-white text-sm">
                                            ${c.constraints?.max_amount?.toFixed(2) || "0.00"} {c.constraints?.currency || "USD"}
                                        </td>
                                        <td className="py-3.5 px-4 text-gray-500 text-sm">
                                            {c.created_at ? new Date(c.created_at).toLocaleDateString() : "N/A"}
                                        </td>
                                        <td className="py-3.5 px-4">
                                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                                                c.is_active ? "bg-emerald-500/10 text-emerald-500" : 
                                                c.status === "pending" ? "bg-yellow-500/10 text-yellow-500" :
                                                "bg-gray-500/10 text-gray-500"
                                            }`}>
                                                <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                                {c.status === "pending" ? "Pending" : c.is_active ? "Active" : "Expired"}
                                            </span>
                                        </td>
                                        <td className="py-3.5 px-4">
                                            <div className="flex items-center gap-2">
                                                {c.status === "pending" ? (
                                                    <>
                                                        <button
                                                            onClick={() => onApproveConsent(c.consent_id)}
                                                            className="px-3 py-1.5 bg-emerald-500/10 text-emerald-500 rounded-lg text-xs font-medium hover:bg-emerald-500/20"
                                                        >
                                                            Approve
                                                        </button>
                                                        <button
                                                            onClick={() => onDenyConsent(c.consent_id)}
                                                            className="px-3 py-1.5 bg-red-500/10 text-red-500 rounded-lg text-xs font-medium hover:bg-red-500/20"
                                                        >
                                                            Deny
                                                        </button>
                                                    </>
                                                ) : c.is_active ? (
                                                    <button
                                                        onClick={() => onRevokeConsent(c.consent_id)}
                                                        className="px-3 py-1.5 bg-orange-500/10 text-orange-500 rounded-lg text-xs font-medium hover:bg-orange-500/20"
                                                    >
                                                        Revoke
                                                    </button>
                                                ) : (
                                                    <span className="text-xs text-gray-500">—</span>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </motion.div>
    );
}

export default ConsentsPage;
