import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Shield, Plus, Trash2, Store, Tag, Check, X } from "lucide-react";

const API_BASE = window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "https://agentauth-production.up.railway.app";

interface MerchantRule {
    id: string;
    merchant_pattern: string;
    action: "allow" | "block";
    description: string | null;
    is_active: boolean;
}

interface CategoryRule {
    id: string;
    category: string;
    action: "allow" | "block";
    is_active: boolean;
}

export function RulesManager() {
    const [merchantRules, setMerchantRules] = useState<MerchantRule[]>([]);
    const [categoryRules, setCategoryRules] = useState<CategoryRule[]>([]);
    const [activeTab, setActiveTab] = useState<"merchants" | "categories">("merchants");
    const [showAddModal, setShowAddModal] = useState(false);
    const [newRule, setNewRule] = useState({ pattern: "", action: "block", description: "" });

    useEffect(() => {
        fetchRules();
    }, []);

    const fetchRules = async () => {
        try {
            const [merchantRes, categoryRes] = await Promise.all([
                fetch(`${API_BASE}/v1/rules/merchants`),
                fetch(`${API_BASE}/v1/rules/categories`)
            ]);
            if (merchantRes.ok) setMerchantRules(await merchantRes.json());
            if (categoryRes.ok) setCategoryRules(await categoryRes.json());
        } catch (err) {
            console.error("Failed to fetch rules:", err);
        }
    };

    const addMerchantRule = async () => {
        try {
            const res = await fetch(`${API_BASE}/v1/rules/merchants`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    merchant_pattern: newRule.pattern,
                    action: newRule.action,
                    description: newRule.description || null,
                }),
            });
            if (res.ok) {
                await fetchRules();
                setShowAddModal(false);
                setNewRule({ pattern: "", action: "block", description: "" });
            }
        } catch (err) {
            console.error("Failed to add rule:", err);
        }
    };

    const addCategoryRule = async () => {
        try {
            const res = await fetch(`${API_BASE}/v1/rules/categories`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    category: newRule.pattern,
                    action: newRule.action,
                }),
            });
            if (res.ok) {
                await fetchRules();
                setShowAddModal(false);
                setNewRule({ pattern: "", action: "block", description: "" });
            }
        } catch (err) {
            console.error("Failed to add rule:", err);
        }
    };

    const deleteRule = async (id: string, type: "merchants" | "categories") => {
        try {
            await fetch(`${API_BASE}/v1/rules/${type}/${id}`, { method: "DELETE" });
            await fetchRules();
        } catch (err) {
            console.error("Failed to delete rule:", err);
        }
    };

    const categories = [
        "saas", "ecommerce", "travel", "entertainment", "gambling",
        "crypto", "food", "utilities", "education", "healthcare"
    ];

    return (
        <motion.div
            className="rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.03] to-transparent overflow-hidden"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
        >
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Shield className="w-5 h-5 text-purple-400" />
                        Spending Rules
                    </h2>
                    <p className="text-sm text-gray-400">Whitelist/blacklist merchants and categories</p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="px-3 py-1.5 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 text-sm flex items-center gap-1"
                >
                    <Plus className="w-4 h-4" />
                    Add Rule
                </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-white/10">
                <button
                    onClick={() => setActiveTab("merchants")}
                    className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === "merchants"
                        ? "text-purple-400 border-b-2 border-purple-400"
                        : "text-gray-500 hover:text-gray-300"
                        }`}
                >
                    <Store className="w-4 h-4 inline mr-2" />
                    Merchants ({merchantRules.length})
                </button>
                <button
                    onClick={() => setActiveTab("categories")}
                    className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === "categories"
                        ? "text-purple-400 border-b-2 border-purple-400"
                        : "text-gray-500 hover:text-gray-300"
                        }`}
                >
                    <Tag className="w-4 h-4 inline mr-2" />
                    Categories ({categoryRules.length})
                </button>
            </div>

            {/* Rules List */}
            <div className="p-4 space-y-2 max-h-64 overflow-y-auto">
                <AnimatePresence mode="wait">
                    {activeTab === "merchants" ? (
                        merchantRules.length > 0 ? (
                            merchantRules.map((rule) => (
                                <motion.div
                                    key={rule.id}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: 10 }}
                                    className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${rule.action === "allow" ? "bg-green-500/20" : "bg-red-500/20"
                                            }`}>
                                            {rule.action === "allow" ? (
                                                <Check className="w-4 h-4 text-green-400" />
                                            ) : (
                                                <X className="w-4 h-4 text-red-400" />
                                            )}
                                        </div>
                                        <div>
                                            <code className="text-cyan-400 text-sm">{rule.merchant_pattern}</code>
                                            {rule.description && (
                                                <p className="text-xs text-gray-500">{rule.description}</p>
                                            )}
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => deleteRule(rule.id, "merchants")}
                                        className="p-2 rounded-lg hover:bg-red-500/20 text-gray-500 hover:text-red-400 transition-colors"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </motion.div>
                            ))
                        ) : (
                            <p className="text-center text-gray-500 py-8">No merchant rules configured</p>
                        )
                    ) : (
                        categoryRules.length > 0 ? (
                            categoryRules.map((rule) => (
                                <motion.div
                                    key={rule.id}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: 10 }}
                                    className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${rule.action === "allow" ? "bg-green-500/20" : "bg-red-500/20"
                                            }`}>
                                            {rule.action === "allow" ? (
                                                <Check className="w-4 h-4 text-green-400" />
                                            ) : (
                                                <X className="w-4 h-4 text-red-400" />
                                            )}
                                        </div>
                                        <span className="text-white capitalize">{rule.category}</span>
                                    </div>
                                    <button
                                        onClick={() => deleteRule(rule.id, "categories")}
                                        className="p-2 rounded-lg hover:bg-red-500/20 text-gray-500 hover:text-red-400 transition-colors"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </motion.div>
                            ))
                        ) : (
                            <p className="text-center text-gray-500 py-8">No category rules configured</p>
                        )
                    )}
                </AnimatePresence>
            </div>

            {/* Add Rule Modal */}
            <AnimatePresence>
                {showAddModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
                        onClick={() => setShowAddModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-[#1a1a24] rounded-2xl p-6 w-full max-w-md border border-white/10"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <h3 className="text-lg font-semibold text-white mb-4">
                                Add {activeTab === "merchants" ? "Merchant" : "Category"} Rule
                            </h3>

                            <div className="space-y-4">
                                {activeTab === "merchants" ? (
                                    <>
                                        <div>
                                            <label className="block text-sm text-gray-400 mb-1">Merchant Pattern</label>
                                            <input
                                                type="text"
                                                value={newRule.pattern}
                                                onChange={(e) => setNewRule({ ...newRule, pattern: e.target.value })}
                                                placeholder="*.gambling.com or amazon"
                                                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm text-gray-400 mb-1">Description</label>
                                            <input
                                                type="text"
                                                value={newRule.description}
                                                onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
                                                placeholder="Optional description"
                                                className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white"
                                            />
                                        </div>
                                    </>
                                ) : (
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">Category</label>
                                        <select
                                            value={newRule.pattern}
                                            onChange={(e) => setNewRule({ ...newRule, pattern: e.target.value })}
                                            className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white"
                                        >
                                            <option value="">Select category</option>
                                            {categories.map((cat) => (
                                                <option key={cat} value={cat}>{cat}</option>
                                            ))}
                                        </select>
                                    </div>
                                )}

                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Action</label>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setNewRule({ ...newRule, action: "block" })}
                                            className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${newRule.action === "block"
                                                ? "bg-red-500/30 text-red-400 border border-red-500/50"
                                                : "bg-white/5 text-gray-400 border border-white/10"
                                                }`}
                                        >
                                            Block
                                        </button>
                                        <button
                                            onClick={() => setNewRule({ ...newRule, action: "allow" })}
                                            className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${newRule.action === "allow"
                                                ? "bg-green-500/30 text-green-400 border border-green-500/50"
                                                : "bg-white/5 text-gray-400 border border-white/10"
                                                }`}
                                        >
                                            Allow
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-2 mt-6">
                                <button
                                    onClick={() => setShowAddModal(false)}
                                    className="flex-1 py-2 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={activeTab === "merchants" ? addMerchantRule : addCategoryRule}
                                    disabled={!newRule.pattern}
                                    className="flex-1 py-2 rounded-lg bg-purple-500 text-white hover:bg-purple-600 disabled:opacity-50"
                                >
                                    Add Rule
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}
