import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { DollarSign, TrendingUp, AlertTriangle, Save, RefreshCw } from "lucide-react";

const API_BASE = window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "https://agentauth-production.up.railway.app";

interface SpendingLimitsData {
    daily_limit: string;
    monthly_limit: string;
    per_transaction_limit: string;
    require_approval_above: string | null;
    is_active: boolean;
}

interface UsageData {
    daily_spent: string;
    monthly_spent: string;
    daily_transaction_count: number;
    monthly_transaction_count: number;
    daily_limit: string;
    monthly_limit: string;
    daily_remaining: string;
    monthly_remaining: string;
}

export function SpendingLimitsCard() {
    const [limits, setLimits] = useState<SpendingLimitsData | null>(null);
    const [usage, setUsage] = useState<UsageData | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [editValues, setEditValues] = useState({
        daily_limit: "",
        monthly_limit: "",
        per_transaction_limit: "",
        require_approval_above: "",
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [limitsRes, usageRes] = await Promise.all([
                fetch(`${API_BASE}/v1/limits`),
                fetch(`${API_BASE}/v1/limits/usage`)
            ]);
            if (limitsRes.ok) {
                const data = await limitsRes.json();
                setLimits(data);
                setEditValues({
                    daily_limit: data.daily_limit,
                    monthly_limit: data.monthly_limit,
                    per_transaction_limit: data.per_transaction_limit,
                    require_approval_above: data.require_approval_above || "",
                });
            }
            if (usageRes.ok) {
                setUsage(await usageRes.json());
            }
        } catch (err) {
            console.error("Failed to fetch limits:", err);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const res = await fetch(`${API_BASE}/v1/limits`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    daily_limit: parseFloat(editValues.daily_limit),
                    monthly_limit: parseFloat(editValues.monthly_limit),
                    per_transaction_limit: parseFloat(editValues.per_transaction_limit),
                    require_approval_above: editValues.require_approval_above
                        ? parseFloat(editValues.require_approval_above)
                        : null,
                }),
            });
            if (res.ok) {
                await fetchData();
                setIsEditing(false);
            }
        } catch (err) {
            console.error("Failed to save limits:", err);
        } finally {
            setIsSaving(false);
        }
    };

    const dailyPercent = usage
        ? (parseFloat(usage.daily_spent) / parseFloat(usage.daily_limit)) * 100
        : 0;
    const monthlyPercent = usage
        ? (parseFloat(usage.monthly_spent) / parseFloat(usage.monthly_limit)) * 100
        : 0;

    return (
        <motion.div
            className="rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.03] to-transparent overflow-hidden"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
        >
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                        <DollarSign className="w-5 h-5 text-green-400" />
                        Spending Limits
                    </h2>
                    <p className="text-sm text-gray-400">Control your AI agent's spending</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={fetchData}
                        className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                    >
                        <RefreshCw className="w-4 h-4 text-gray-400" />
                    </button>
                    {isEditing ? (
                        <>
                            <button
                                onClick={() => setIsEditing(false)}
                                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 text-sm"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="px-3 py-1.5 rounded-lg bg-green-500/20 hover:bg-green-500/30 text-green-400 text-sm flex items-center gap-1"
                            >
                                <Save className="w-4 h-4" />
                                {isSaving ? "Saving..." : "Save"}
                            </button>
                        </>
                    ) : (
                        <button
                            onClick={() => setIsEditing(true)}
                            className="px-3 py-1.5 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 text-sm"
                        >
                            Edit Limits
                        </button>
                    )}
                </div>
            </div>

            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Daily Budget */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400 text-sm">Daily Budget</span>
                        {isEditing ? (
                            <input
                                type="number"
                                value={editValues.daily_limit}
                                onChange={(e) => setEditValues({ ...editValues, daily_limit: e.target.value })}
                                className="w-24 px-2 py-1 rounded bg-white/5 border border-white/10 text-white text-right text-sm"
                            />
                        ) : (
                            <span className="text-white font-medium">${limits?.daily_limit || "0"}</span>
                        )}
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                            className={`h-full ${dailyPercent > 80 ? "bg-red-500" : dailyPercent > 50 ? "bg-yellow-500" : "bg-green-500"}`}
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.min(dailyPercent, 100)}%` }}
                            transition={{ duration: 0.5 }}
                        />
                    </div>
                    <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Spent: ${usage?.daily_spent || "0"}</span>
                        <span className="text-gray-500">Remaining: ${usage?.daily_remaining || "0"}</span>
                    </div>
                </div>

                {/* Monthly Budget */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400 text-sm">Monthly Budget</span>
                        {isEditing ? (
                            <input
                                type="number"
                                value={editValues.monthly_limit}
                                onChange={(e) => setEditValues({ ...editValues, monthly_limit: e.target.value })}
                                className="w-24 px-2 py-1 rounded bg-white/5 border border-white/10 text-white text-right text-sm"
                            />
                        ) : (
                            <span className="text-white font-medium">${limits?.monthly_limit || "0"}</span>
                        )}
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                            className={`h-full ${monthlyPercent > 80 ? "bg-red-500" : monthlyPercent > 50 ? "bg-yellow-500" : "bg-cyan-500"}`}
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.min(monthlyPercent, 100)}%` }}
                            transition={{ duration: 0.5 }}
                        />
                    </div>
                    <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Spent: ${usage?.monthly_spent || "0"}</span>
                        <span className="text-gray-500">Remaining: ${usage?.monthly_remaining || "0"}</span>
                    </div>
                </div>

                {/* Per-Transaction & Approval Threshold */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5">
                    <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-500" />
                        <span className="text-gray-400 text-sm">Per-Transaction Limit</span>
                    </div>
                    {isEditing ? (
                        <input
                            type="number"
                            value={editValues.per_transaction_limit}
                            onChange={(e) => setEditValues({ ...editValues, per_transaction_limit: e.target.value })}
                            className="w-20 px-2 py-1 rounded bg-white/5 border border-white/10 text-white text-right text-sm"
                        />
                    ) : (
                        <span className="text-white font-medium">${limits?.per_transaction_limit || "0"}</span>
                    )}
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-purple-500" />
                        <span className="text-gray-400 text-sm">Approval Required Above</span>
                    </div>
                    {isEditing ? (
                        <input
                            type="number"
                            value={editValues.require_approval_above}
                            onChange={(e) => setEditValues({ ...editValues, require_approval_above: e.target.value })}
                            className="w-20 px-2 py-1 rounded bg-white/5 border border-white/10 text-white text-right text-sm"
                            placeholder="None"
                        />
                    ) : (
                        <span className="text-white font-medium">
                            {limits?.require_approval_above ? `$${limits.require_approval_above}` : "None"}
                        </span>
                    )}
                </div>
            </div>

            {/* Transaction Count */}
            <div className="px-6 pb-6 flex gap-4">
                <div className="flex-1 p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-center">
                    <p className="text-2xl font-bold text-cyan-400">{usage?.daily_transaction_count || 0}</p>
                    <p className="text-xs text-gray-400">Transactions Today</p>
                </div>
                <div className="flex-1 p-3 rounded-lg bg-purple-500/10 border border-purple-500/20 text-center">
                    <p className="text-2xl font-bold text-purple-400">{usage?.monthly_transaction_count || 0}</p>
                    <p className="text-xs text-gray-400">This Month</p>
                </div>
            </div>
        </motion.div>
    );
}
