import { useEffect, useState } from "react";

interface ModuleInfo {
    name: string;
    description: string;
    status: "healthy" | "warning" | "error";
    version: string;
    endpoint: string;
    latency?: number;
}

interface DashboardModulesProps {
    apiUrl: string;
    token: string;
    apiKey: string;
}

const MODULE_DEFS: Omit<ModuleInfo, "status" | "latency">[] = [
    { name: "Authorization Engine", description: "Real-time authorization decisions for agent actions. Validates delegation tokens, checks spending limits, and enforces policy rules.", version: "1.0.4", endpoint: "/v1/authorize" },
    { name: "Consent Manager", description: "Creates and manages user consent grants. Handles spending limits, allowed merchants, and time-bound delegation tokens.", version: "1.0.4", endpoint: "/v1/consents" },
    { name: "Agent Registry", description: "Manages AI agent registrations, capabilities, and trust levels. Tracks agent activity and metadata.", version: "1.0.4", endpoint: "/v1/agents" },
    { name: "Dashboard API", description: "Aggregate statistics, transaction logs, and analytics charts for monitoring and observability.", version: "1.0.4", endpoint: "/v1/dashboard" },
    { name: "Admin Auth", description: "Secure admin portal access via JWT tokens. Manages API key lifecycle, rotation, and revocation.", version: "1.0.4", endpoint: "/v1/admin" },
    { name: "Policy Engine", description: "Configurable rules engine for agent behavior constraints. Supports spending limits, merchant whitelists, and time restrictions.", version: "1.0.4", endpoint: "/v1/policies" },
];

export function DashboardModules({ apiUrl, token, apiKey }: DashboardModulesProps) {
    const [modules, setModules] = useState<ModuleInfo[]>(
        MODULE_DEFS.map((m) => ({ ...m, status: "healthy" as const, latency: undefined }))
    );

    useEffect(() => {
        const checkHealth = async () => {
            const results = await Promise.all(
                MODULE_DEFS.map(async (mod): Promise<ModuleInfo> => {
                    const start = performance.now();
                    try {
                        const res = await fetch(`${apiUrl}${mod.endpoint}`, {
                            method: "HEAD",
                            headers: {
                                Authorization: `Bearer ${token}`,
                                "X-API-Key": apiKey,
                            },
                        });
                        const latency = Math.round(performance.now() - start);
                        return {
                            ...mod,
                            status: res.ok || res.status === 405 || res.status === 422 ? "healthy" : res.status >= 500 ? "error" : "warning",
                            latency,
                        };
                    } catch {
                        return { ...mod, status: "error", latency: undefined };
                    }
                })
            );
            setModules(results);
        };

        checkHealth();
        const interval = setInterval(checkHealth, 30000);
        return () => clearInterval(interval);
    }, [apiUrl, token, apiKey]);

    const healthyCount = modules.filter((m) => m.status === "healthy").length;

    return (
        <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <div style={{ fontFamily: "var(--nuc-font-mono)", fontSize: "0.7rem", color: "var(--nuc-text-dim)" }}>
                    {healthyCount}/{modules.length} modules operational
                </div>
                <div className={`nuc-badge ${healthyCount === modules.length ? "active" : "revoked"}`}>
                    {healthyCount === modules.length ? "All Systems Operational" : "Degraded"}
                </div>
            </div>

            <div className="nuc-modules-grid">
                {modules.map((mod) => (
                    <div key={mod.name} className="nuc-module-card">
                        <div className="nuc-module-header">
                            <div className="nuc-module-name">{mod.name}</div>
                            <div className={`nuc-module-status ${mod.status}`}>
                                <span className={`nuc-pulse ${mod.status}`} />
                                {mod.status.toUpperCase()}
                            </div>
                        </div>
                        <div className="nuc-module-desc">{mod.description}</div>
                        <div className="nuc-module-meta">
                            <span>v{mod.version}</span>
                            <span>{mod.endpoint}</span>
                            {mod.latency !== undefined && <span>{mod.latency}ms</span>}
                        </div>
                    </div>
                ))}
            </div>
        </>
    );
}
