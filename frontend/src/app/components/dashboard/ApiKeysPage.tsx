import { useState } from "react";
import { motion } from "motion/react";
import {
    Key,
    Plus,
    AlertTriangle,
    Copy,
    Eye,
    Trash2,
} from "lucide-react";

interface ApiKeysPageProps {
    showToast: (message: string, type: "success" | "error" | "info") => void;
    copyToClipboard: (text: string) => void;
}

export function ApiKeysPage({ showToast, copyToClipboard }: ApiKeysPageProps) {
    const [newKeyName, setNewKeyName] = useState("");
    const [newKeyType, setNewKeyType] = useState<"live" | "test">("live");

    const handleCreateKey = () => {
        if (!newKeyName.trim()) {
            showToast("Please enter a key name", "error");
            return;
        }
        showToast(`API key "${newKeyName}" created successfully!`, "success");
        setNewKeyName("");
    };

    const handleDeleteKey = (name: string) => {
        if (confirm(`Are you sure you want to delete the key "${name}"? This cannot be undone.`)) {
            showToast(`API key "${name}" deleted`, "info");
        }
    };

    return (
        <motion.div
            key="apikeys"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Info Banner */}
            <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-4 mb-6 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-cyan-500 mt-0.5" />
                <div>
                    <p className="text-white text-sm font-medium">Keep your API keys secure</p>
                    <p className="text-gray-400 text-sm mt-0.5">Never share your API keys in public repositories or client-side code. Use environment variables instead.</p>
                </div>
            </div>

            {/* Create Key Section */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-6 mb-6">
                <h3 className="text-white font-medium mb-4">Create New API Key</h3>
                <div className="flex gap-4">
                    <input
                        type="text"
                        placeholder="Key name (e.g., Production, Staging)"
                        value={newKeyName}
                        onChange={(e) => setNewKeyName(e.target.value)}
                        className="flex-1 px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm focus:outline-none focus:border-[#444]"
                    />
                    <select
                        value={newKeyType}
                        onChange={(e) => setNewKeyType(e.target.value as "live" | "test")}
                        className="px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm focus:outline-none"
                    >
                        <option value="live">Live Key</option>
                        <option value="test">Test Key</option>
                    </select>
                    <button
                        onClick={handleCreateKey}
                        className="flex items-center gap-2 px-6 py-2.5 bg-white hover:bg-gray-200 text-black rounded-lg text-sm font-medium"
                    >
                        <Plus className="w-4 h-4" />
                        Create Key
                    </button>
                </div>
            </div>

            {/* Keys List */}
            <div className="space-y-3">
                {[
                    { name: "Production Key", key: "aa_live_sk_1a2b3c4d5e6f7g8h9i0j", created: "Jan 15, 2026", lastUsed: "2 min ago", isLive: true },
                    { name: "Staging Key", key: "aa_live_sk_2b3c4d5e6f7g8h9i0j1k", created: "Jan 12, 2026", lastUsed: "1 hr ago", isLive: true },
                    { name: "Test Key", key: "aa_test_sk_3c4d5e6f7g8h9i0j1k2l", created: "Jan 10, 2026", lastUsed: "3 days ago", isLive: false },
                    { name: "Development Key", key: "aa_test_sk_4d5e6f7g8h9i0j1k2l3m", created: "Jan 8, 2026", lastUsed: "1 week ago", isLive: false },
                ].map((apiKey, i) => (
                    <div key={i} className="bg-[#111] border border-[#222] rounded-xl p-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${apiKey.isLive ? "bg-emerald-500/10" : "bg-gray-500/10"}`}>
                                    <Key className={`w-5 h-5 ${apiKey.isLive ? "text-emerald-500" : "text-gray-500"}`} />
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-white font-medium">{apiKey.name}</span>
                                        <span className={`px-2 py-0.5 rounded text-xs ${apiKey.isLive ? "bg-emerald-500/10 text-emerald-500" : "bg-gray-500/10 text-gray-500"}`}>
                                            {apiKey.isLive ? "Live" : "Test"}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3 mt-1">
                                        <code className="text-sm text-gray-500 bg-white/5 px-2 py-0.5 rounded">
                                            {apiKey.key.substring(0, 12)}...{apiKey.key.substring(apiKey.key.length - 4)}
                                        </code>
                                        <span className="text-xs text-gray-500">Created {apiKey.created}</span>
                                        <span className="text-xs text-gray-500">• Last used {apiKey.lastUsed}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => copyToClipboard(apiKey.key)}
                                    className="p-2.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg"
                                    title="Copy key"
                                >
                                    <Copy className="w-4 h-4 text-gray-400" />
                                </button>
                                <button
                                    onClick={() => showToast(`Full key: ${apiKey.key}`, "info")}
                                    className="p-2.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg"
                                    title="Reveal key"
                                >
                                    <Eye className="w-4 h-4 text-gray-400" />
                                </button>
                                <button
                                    onClick={() => handleDeleteKey(apiKey.name)}
                                    className="p-2.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-lg"
                                    title="Delete key"
                                >
                                    <Trash2 className="w-4 h-4 text-red-500" />
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </motion.div>
    );
}
