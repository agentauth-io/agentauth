// Team Page Component

import { useState } from "react";
import { motion } from "motion/react";
import { UserPlus, Crown } from "lucide-react";
import { TeamMember } from "./types";

interface TeamPageProps {
    teamMembers: TeamMember[];
    onInviteTeamMember: (email: string, role: string) => void;
    onRemoveTeamMember: (memberId: string) => void;
}

export function TeamPage({
    teamMembers,
    onInviteTeamMember,
    onRemoveTeamMember,
}: TeamPageProps) {
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState("Admin");

    const handleInvite = () => {
        if (inviteEmail.trim() && inviteEmail.includes("@")) {
            onInviteTeamMember(inviteEmail.trim(), inviteRole);
            setInviteEmail("");
        }
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
                <div className="flex flex-col sm:flex-row gap-4">
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
                        <option value="Admin">Admin</option>
                        <option value="Developer">Developer</option>
                        <option value="Viewer">Viewer</option>
                    </select>
                    <button 
                        onClick={handleInvite}
                        disabled={!inviteEmail.trim() || !inviteEmail.includes("@")}
                        className="flex items-center justify-center gap-2 px-6 py-2.5 bg-white hover:bg-gray-200 text-black rounded-lg text-sm font-medium disabled:opacity-50"
                    >
                        <UserPlus className="w-4 h-4" />
                        Send Invite
                    </button>
                </div>
            </div>

            {/* Team Members */}
            <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden overflow-x-auto">
                <table className="w-full min-w-[600px]">
                    <thead>
                        <tr className="border-b border-[#222] bg-[#0d0d0d] text-left">
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Member</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Last Active</th>
                            <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {teamMembers.map((member) => (
                            <tr key={member.id} className="border-b border-white/5 hover:bg-white/[0.02]">
                                <td className="py-4 px-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-9 h-9 bg-gradient-to-br from-zinc-600 to-zinc-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                                            {member.avatar || member.name.split(" ").map((n: string) => n[0]).join("")}
                                        </div>
                                        <div>
                                            <div className="text-white text-sm font-medium flex items-center gap-2">
                                                {member.name}
                                                {member.role === "Owner" && <Crown className="w-3.5 h-3.5 text-yellow-500" />}
                                            </div>
                                            <div className="text-gray-500 text-xs">{member.email}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="py-4 px-4">
                                    <span className={`px-2.5 py-1 rounded text-xs font-medium ${
                                        member.role === "Owner" ? "bg-yellow-500/10 text-yellow-500" :
                                        member.role === "Admin" ? "bg-zinc-800/50 text-zinc-400" :
                                        member.role === "Developer" ? "bg-cyan-500/10 text-cyan-500" :
                                        "bg-gray-500/10 text-gray-500"
                                    }`}>
                                        {member.role}
                                    </span>
                                </td>
                                <td className="py-4 px-4">
                                    <span className={`inline-flex items-center gap-1.5 text-xs ${
                                        member.status === "active" ? "text-emerald-500" : "text-yellow-500"
                                    }`}>
                                        <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                        {member.status === "active" ? "Active" : "Pending"}
                                    </span>
                                </td>
                                <td className="py-4 px-4 text-gray-500 text-sm">{member.lastActive || "—"}</td>
                                <td className="py-4 px-4">
                                    {member.role !== "Owner" && (
                                        <button 
                                            onClick={() => onRemoveTeamMember(member.id)}
                                            className="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg text-xs"
                                        >
                                            Remove
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

export default TeamPage;
