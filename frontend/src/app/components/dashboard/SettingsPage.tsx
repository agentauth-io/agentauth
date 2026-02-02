// Settings Page Component

import { motion } from "motion/react";
import { NotificationSettings } from "./types";

interface SettingsPageProps {
    orgName: string;
    orgUrl: string;
    editingOrgName: boolean;
    editingOrgUrl: boolean;
    notifications: NotificationSettings;
    onOrgNameChange: (value: string) => void;
    onOrgUrlChange: (value: string) => void;
    onSetEditingOrgName: (editing: boolean) => void;
    onSetEditingOrgUrl: (editing: boolean) => void;
    onSaveOrgName: () => void;
    onSaveOrgUrl: () => void;
    onToggleNotification: (key: keyof NotificationSettings) => void;
    onDeleteOrganization: () => void;
}

interface ToggleSwitchProps {
    enabled: boolean;
    onToggle: () => void;
}

function ToggleSwitch({ enabled, onToggle }: ToggleSwitchProps) {
    return (
        <button 
            onClick={onToggle}
            className={`w-11 h-6 rounded-full transition-colors ${enabled ? "bg-emerald-500" : "bg-[#333]"}`}
        >
            <div className={`w-5 h-5 bg-white rounded-full transition-transform ${enabled ? "translate-x-5" : "translate-x-0.5"}`} />
        </button>
    );
}

export function SettingsPage({
    orgName,
    orgUrl,
    editingOrgName,
    editingOrgUrl,
    notifications,
    onOrgNameChange,
    onOrgUrlChange,
    onSetEditingOrgName,
    onSetEditingOrgUrl,
    onSaveOrgName,
    onSaveOrgUrl,
    onToggleNotification,
    onDeleteOrganization,
}: SettingsPageProps) {
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
                    <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                            <p className="text-white text-sm">Organization Name</p>
                            <p className="text-gray-500 text-xs mt-0.5">Your company or project name</p>
                        </div>
                        <div className="flex items-center gap-3">
                            {editingOrgName ? (
                                <>
                                    <input
                                        type="text"
                                        value={orgName}
                                        onChange={(e) => onOrgNameChange(e.target.value)}
                                        className="px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm focus:outline-none focus:border-[#555]"
                                    />
                                    <button 
                                        onClick={onSaveOrgName}
                                        className="px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 border border-emerald-500/20 rounded-lg text-xs"
                                    >
                                        Save
                                    </button>
                                </>
                            ) : (
                                <>
                                    <span className="text-gray-400 text-sm">{orgName}</span>
                                    <button 
                                        onClick={() => onSetEditingOrgName(true)}
                                        className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs text-white"
                                    >
                                        Edit
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                    <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                            <p className="text-white text-sm">Organization URL</p>
                            <p className="text-gray-500 text-xs mt-0.5">Your unique AgentAuth URL</p>
                        </div>
                        <div className="flex items-center gap-3">
                            {editingOrgUrl ? (
                                <>
                                    <input
                                        type="text"
                                        value={orgUrl}
                                        onChange={(e) => onOrgUrlChange(e.target.value)}
                                        className="px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-cyan-400 text-sm focus:outline-none focus:border-[#555]"
                                    />
                                    <button 
                                        onClick={onSaveOrgUrl}
                                        className="px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 border border-emerald-500/20 rounded-lg text-xs"
                                    >
                                        Save
                                    </button>
                                </>
                            ) : (
                                <>
                                    <code className="text-cyan-400 text-sm">{orgUrl}</code>
                                    <button 
                                        onClick={() => onSetEditingOrgUrl(true)}
                                        className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs text-white"
                                    >
                                        Edit
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                    <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
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
                    <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                            <p className="text-white text-sm">Default Daily Limit</p>
                            <p className="text-gray-500 text-xs mt-0.5">Maximum spending per agent per day</p>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-gray-400">$</span>
                            <input type="number" defaultValue="1000" className="w-24 px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm text-right focus:outline-none" />
                        </div>
                    </div>
                    <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                            <p className="text-white text-sm">Default Monthly Limit</p>
                            <p className="text-gray-500 text-xs mt-0.5">Maximum spending per agent per month</p>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-gray-400">$</span>
                            <input type="number" defaultValue="10000" className="w-24 px-3 py-1.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm text-right focus:outline-none" />
                        </div>
                    </div>
                    <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
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
                    <div className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-white text-sm">Transaction Alerts</p>
                            <p className="text-gray-500 text-xs mt-0.5">Get notified for denied transactions</p>
                        </div>
                        <ToggleSwitch 
                            enabled={notifications.transactionAlerts} 
                            onToggle={() => onToggleNotification("transactionAlerts")} 
                        />
                    </div>
                    <div className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-white text-sm">Consent Requests</p>
                            <p className="text-gray-500 text-xs mt-0.5">Notify when agents request new permissions</p>
                        </div>
                        <ToggleSwitch 
                            enabled={notifications.consentRequests} 
                            onToggle={() => onToggleNotification("consentRequests")} 
                        />
                    </div>
                    <div className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-white text-sm">Weekly Reports</p>
                            <p className="text-gray-500 text-xs mt-0.5">Receive weekly analytics summary</p>
                        </div>
                        <ToggleSwitch 
                            enabled={notifications.weeklyReports} 
                            onToggle={() => onToggleNotification("weeklyReports")} 
                        />
                    </div>
                    <div className="p-4 flex items-center justify-between">
                        <div>
                            <p className="text-white text-sm">Security Alerts</p>
                            <p className="text-gray-500 text-xs mt-0.5">Important security notifications</p>
                        </div>
                        <ToggleSwitch 
                            enabled={notifications.securityAlerts} 
                            onToggle={() => onToggleNotification("securityAlerts")} 
                        />
                    </div>
                </div>
            </div>

            {/* Danger Zone */}
            <div>
                <h3 className="text-red-500 font-medium mb-4">Danger Zone</h3>
                <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div>
                            <p className="text-white text-sm">Delete Organization</p>
                            <p className="text-gray-500 text-xs mt-0.5">Permanently delete your organization and all data</p>
                        </div>
                        <button 
                            onClick={onDeleteOrganization}
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

export default SettingsPage;
