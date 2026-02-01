import { useState } from "react";
import { motion } from "motion/react";

interface SettingsPageProps {
    showToast: (message: string, type: "success" | "error" | "info") => void;
}

export function SettingsPage({ showToast }: SettingsPageProps) {
    const [notifications, setNotifications] = useState<Record<number, boolean>>({ 0: true, 1: true, 2: false, 3: true });

    const handleToggleNotification = (index: number) => {
        setNotifications(prev => ({ ...prev, [index]: !prev[index] }));
        showToast("Notification setting updated", "success");
    };

    const handleEditSetting = (field: string) => {
        const newValue = prompt(`Enter new ${field}:`);
        if (newValue) {
            showToast(`${field} updated to "${newValue}"`, "success");
        }
    };

    const handleDeleteOrg = () => {
        const confirmText = prompt('Type "DELETE" to confirm organization deletion:');
        if (confirmText === "DELETE") {
            showToast("Organization deletion requested. You will receive a confirmation email.", "info");
        } else if (confirmText !== null) {
            showToast("Deletion cancelled - text did not match", "error");
        }
    };

    return (
        <motion.div
            key="settings"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Account Settings */}
            <div className="mb-8">
                <h3 className="text-white font-medium mb-4">Account Settings</h3>
                <div className="bg-[#111] border border-[#222] rounded-xl divide-y divide-[#222]">
                    <div className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-white text-sm">Organization Name</p>
                            <p className="text-gray-500 text-xs mt-0.5">Your company or project name</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <span className="text-gray-400 text-sm">Acme Corporation</span>
                            <button
                                onClick={() => handleEditSetting("Organization Name")}
                                className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs"
                            >
                                Edit
                            </button>
                        </div>
                    </div>
                    <div className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-white text-sm">Organization URL</p>
                            <p className="text-gray-500 text-xs mt-0.5">Your unique AgentAuth URL</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <code className="text-cyan-400 text-sm">acme.agentauth.in</code>
                            <button
                                onClick={() => handleEditSetting("Organization URL")}
                                className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs"
                            >
                                Edit
                            </button>
                        </div>
                    </div>
                    <div className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-white text-sm">Timezone</p>
                            <p className="text-gray-500 text-xs mt-0.5">Used for reports and analytics</p>
                        </div>
                        <select className="px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-sm text-white focus:outline-none">
                            <option>UTC</option>
                            <option>America/New_York</option>
                            <option>America/Los_Angeles</option>
                            <option>Europe/London</option>
                            <option>Asia/Tokyo</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Authorization Settings */}
            <div className="mb-8">
                <h3 className="text-white font-medium mb-4">Authorization Settings</h3>
                <div className="bg-[#111] border border-[#222] rounded-xl divide-y divide-[#222]">
                    <div className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-white text-sm">Default Daily Limit</p>
                            <p className="text-gray-500 text-xs mt-0.5">Maximum spending per agent per day</p>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-gray-400">$</span>
                            <input type="number" defaultValue="1000" className="w-24 px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm text-right focus:outline-none" />
                        </div>
                    </div>
                    <div className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-white text-sm">Default Monthly Limit</p>
                            <p className="text-gray-500 text-xs mt-0.5">Maximum spending per agent per month</p>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-gray-400">$</span>
                            <input type="number" defaultValue="10000" className="w-24 px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm text-right focus:outline-none" />
                        </div>
                    </div>
                    <div className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-white text-sm">Require Approval Above</p>
                            <p className="text-gray-500 text-xs mt-0.5">Transactions above this amount need manual approval</p>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-gray-400">$</span>
                            <input type="number" defaultValue="500" className="w-24 px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm text-right focus:outline-none" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Notifications */}
            <div className="mb-8">
                <h3 className="text-white font-medium mb-4">Notifications</h3>
                <div className="bg-[#111] border border-[#222] rounded-xl divide-y divide-[#222]">
                    {[
                        { title: "Transaction Alerts", desc: "Get notified for denied transactions" },
                        { title: "Consent Requests", desc: "Notify when agents request new permissions" },
                        { title: "Weekly Reports", desc: "Receive weekly analytics summary" },
                        { title: "Security Alerts", desc: "Important security notifications" },
                    ].map((setting, i) => (
                        <div key={i} className="p-4 flex items-center justify-between">
                            <div>
                                <p className="text-white text-sm">{setting.title}</p>
                                <p className="text-gray-500 text-xs mt-0.5">{setting.desc}</p>
                            </div>
                            <button
                                onClick={() => handleToggleNotification(i)}
                                className={`w-11 h-6 rounded-full transition-colors ${notifications[i] ? "bg-emerald-500" : "bg-[#333]"}`}
                            >
                                <div className={`w-5 h-5 bg-white rounded-full transition-transform ${notifications[i] ? "translate-x-5" : "translate-x-0.5"}`} />
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Danger Zone */}
            <div>
                <h3 className="text-red-500 font-medium mb-4">Danger Zone</h3>
                <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-white text-sm">Delete Organization</p>
                            <p className="text-gray-500 text-xs mt-0.5">Permanently delete your organization and all data</p>
                        </div>
                        <button
                            onClick={handleDeleteOrg}
                            className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 rounded-lg text-sm"
                        >
                            Delete Organization
                        </button>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
