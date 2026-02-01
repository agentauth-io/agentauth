import { useState } from "react";
import { motion } from "motion/react";
import {
    UserPlus,
    Crown,
    MoreVertical,
} from "lucide-react";

interface TeamPageProps {
    showToast: (message: string, type: "success" | "error" | "info") => void;
}

export function TeamPage({ showToast }: TeamPageProps) {
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState("Admin");

    const handleInvite = () => {
        if (!inviteEmail.trim() || !inviteEmail.includes("@")) {
            showToast("Please enter a valid email address", "error");
            return;
        }
        showToast(`Invitation sent to ${inviteEmail} as ${inviteRole}`, "success");
        setInviteEmail("");
    };

    return (
        <motion.div
            key="team"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Invite Section */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-6 mb-6">
                <h3 className="text-white font-medium mb-4">Invite Team Member</h3>
                <div className="flex gap-4">
                    <input
                        type="email"
                        placeholder="colleague@company.com"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        className="flex-1 px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm focus:outline-none focus:border-[#444]"
                    />
                    <select
                        value={inviteRole}
                        onChange={(e) => setInviteRole(e.target.value)}
                        className="px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm focus:outline-none"
                    >
                        <option>Admin</option>
                        <option>Developer</option>
                        <option>Viewer</option>
                    </select>
                    <button
                        onClick={handleInvite}
                        className="flex items-center gap-2 px-6 py-2.5 bg-white hover:bg-gray-200 text-black rounded-lg text-sm font-medium"
                    >
                        <UserPlus className="w-4 h-4" />
                        Send Invite
                    </button>
                </div>
            </div>

            {/* Team Members */}
            <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-[#222] bg-[#0d0d0d] text-left">
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Member</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Last Active</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider"></th>
                        </tr>
                    </thead>
                    <tbody>
                        {[
                            { name: "John Doe", email: "john@company.com", role: "Owner", status: "active", lastActive: "Now", isOwner: true },
                            { name: "Sarah Chen", email: "sarah@company.com", role: "Admin", status: "active", lastActive: "2 hr ago", isOwner: false },
                            { name: "Mike Wilson", email: "mike@company.com", role: "Developer", status: "active", lastActive: "1 day ago", isOwner: false },
                            { name: "Emily Brown", email: "emily@company.com", role: "Viewer", status: "pending", lastActive: "Invited 3 days ago", isOwner: false },
                        ].map((member, i) => (
                            <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                                <td className="py-4 px-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-9 h-9 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                                            {member.name.split(" ").map(n => n[0]).join("")}
                                        </div>
                                        <div>
                                            <div className="text-white text-sm font-medium flex items-center gap-2">
                                                {member.name}
                                                {member.isOwner && <Crown className="w-3.5 h-3.5 text-yellow-500" />}
                                            </div>
                                            <div className="text-gray-500 text-xs">{member.email}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="py-4 px-4">
                                    <span className={`px-2.5 py-1 rounded text-xs font-medium ${
                                        member.role === "Owner" ? "bg-yellow-500/10 text-yellow-500" :
                                        member.role === "Admin" ? "bg-purple-500/10 text-purple-500" :
                                        member.role === "Developer" ? "bg-cyan-500/10 text-cyan-500" :
                                        "bg-gray-500/10 text-gray-500"
                                    }`}>
                                        {member.role}
                                    </span>
                                </td>
                                <td className="py-4 px-4">
                                    <span className={`inline-flex items-center gap-1.5 text-xs ${member.status === "active" ? "text-emerald-500" : "text-yellow-500"}`}>
                                        <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                        {member.status === "active" ? "Active" : "Pending"}
                                    </span>
                                </td>
                                <td className="py-4 px-4 text-gray-500 text-sm">{member.lastActive}</td>
                                <td className="py-4 px-4">
                                    {!member.isOwner && (
                                        <button
                                            onClick={() => showToast(`Options for ${member.name}: Change Role, Remove`, "info")}
                                            className="p-2 hover:bg-white/5 rounded-lg"
                                        >
                                            <MoreVertical className="w-4 h-4 text-gray-500" />
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </motion.div>
    );
}
