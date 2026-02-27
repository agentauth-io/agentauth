import { useState, useEffect, useRef, useCallback } from "react";

interface FeedItem {
    id: number;
    method: "POST" | "GET" | "DELETE";
    path: string;
    result: string;
    resultClass: string;
    latency: number;
    time: string;
}

// Simulated API activity entries
const ACTIVITY_POOL: Omit<FeedItem, "id" | "time">[] = [
    { method: "POST", path: "/v1/authorize", result: "ALLOW", resultClass: "allow", latency: 12 },
    { method: "POST", path: "/v1/authorize", result: "DENY", resultClass: "deny", latency: 8 },
    { method: "POST", path: "/v1/consents", result: "CREATED", resultClass: "ok", latency: 45 },
    { method: "GET", path: "/v1/consents", result: "3 active", resultClass: "ok", latency: 23 },
    { method: "GET", path: "/v1/dashboard/stats", result: "OK", resultClass: "ok", latency: 31 },
    { method: "POST", path: "/v1/authorize", result: "ALLOW", resultClass: "allow", latency: 9 },
    { method: "GET", path: "/v1/agents", result: "2 agents", resultClass: "ok", latency: 18 },
    { method: "POST", path: "/v1/authorize", result: "ALLOW", resultClass: "allow", latency: 14 },
    { method: "DELETE", path: "/v1/admin/api-keys/ak_x7", result: "REVOKED", resultClass: "deny", latency: 38 },
    { method: "GET", path: "/v1/dashboard/analytics", result: "OK", resultClass: "ok", latency: 67 },
    { method: "POST", path: "/v1/authorize", result: "STEP_UP", resultClass: "deny", latency: 11 },
    { method: "POST", path: "/v1/consents", result: "CREATED", resultClass: "ok", latency: 52 },
    { method: "GET", path: "/v1/health", result: "HEALTHY", resultClass: "allow", latency: 3 },
    { method: "POST", path: "/v1/authorize", result: "ALLOW", resultClass: "allow", latency: 7 },
];

interface DashboardStats {
    total_authorizations: number;
    transaction_volume: number;
    approval_rate: number;
    active_consents: number;
    daily_requests: number[];
}

interface DashboardOverviewProps {
    apiUrl: string;
    token: string;
    apiKey: string;
}

export function DashboardOverview({ apiUrl, token, apiKey }: DashboardOverviewProps) {
    const [stats, setStats] = useState<DashboardStats>({
        total_authorizations: 0,
        transaction_volume: 0,
        approval_rate: 0,
        active_consents: 0,
        daily_requests: [0, 0, 0, 0, 0, 0, 0],
    });
    const [feed, setFeed] = useState<FeedItem[]>([]);
    const feedRef = useRef<HTMLDivElement>(null);
    const idRef = useRef(0);

    // Fetch real stats
    useEffect(() => {
        const fetchStats = async () => {
            try {
                const res = await fetch(`${apiUrl}/v1/dashboard`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "X-API-Key": apiKey,
                    },
                });
                if (res.ok) {
                    const data = await res.json();
                    setStats(data);
                }
            } catch {
                // Use defaults
            }
        };
        fetchStats();
        const interval = setInterval(fetchStats, 30000);
        return () => clearInterval(interval);
    }, [apiUrl, token, apiKey]);

    // Animate live feed
    const addFeedItem = useCallback(() => {
        const entry = ACTIVITY_POOL[Math.floor(Math.random() * ACTIVITY_POOL.length)];
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}:${now.getSeconds().toString().padStart(2, "0")}`;
        const item: FeedItem = {
            ...entry,
            id: idRef.current++,
            latency: entry.latency + Math.floor(Math.random() * 10) - 5,
            time: timeStr,
        };
        setFeed((prev) => [item, ...prev].slice(0, 30));
    }, []);

    useEffect(() => {
        // Initial burst
        for (let i = 0; i < 6; i++) {
            setTimeout(addFeedItem, i * 200);
        }
        const interval = setInterval(addFeedItem, 2000 + Math.random() * 3000);
        return () => clearInterval(interval);
    }, [addFeedItem]);

    const maxDaily = Math.max(...stats.daily_requests, 1);
    const dayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

    return (
        <>
            {/* Stat Cards */}
            <div className="nuc-stats-grid">
                <StatCard
                    label="Total Authorizations"
                    value={stats.total_authorizations.toLocaleString()}
                    change="+12%"
                    up
                />
                <StatCard
                    label="Transaction Volume"
                    value={`$${stats.transaction_volume.toLocaleString()}`}
                    change="+8.3%"
                    up
                />
                <StatCard
                    label="Approval Rate"
                    value={`${stats.approval_rate}%`}
                    change="+2.1%"
                    up
                />
                <StatCard
                    label="Active Consents"
                    value={stats.active_consents.toLocaleString()}
                    change=""
                />
            </div>

            {/* Charts + Feed */}
            <div className="nuc-chart-row">
                {/* Bar Chart */}
                <div className="nuc-chart-card">
                    <div className="nuc-chart-title">Daily Requests (7d)</div>
                    <div className="nuc-bar-chart">
                        {stats.daily_requests.map((val, i) => (
                            <div
                                key={i}
                                className="nuc-bar"
                                style={{ height: `${Math.max((val / maxDaily) * 100, 4)}%` }}
                                title={`${val} requests`}
                            />
                        ))}
                    </div>
                    <div className="nuc-bar-labels">
                        {dayLabels.map((d) => (
                            <span key={d}>{d}</span>
                        ))}
                    </div>
                </div>

                {/* Live Activity Feed */}
                <div className="nuc-chart-card">
                    <div className="nuc-chart-title" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span className="nuc-pulse healthy" style={{ width: 6, height: 6 }} /> Live API Activity
                    </div>
                    <div className="nuc-feed" ref={feedRef}>
                        {feed.map((item) => (
                            <div key={item.id} className="nuc-feed-item">
                                <span className={`nuc-feed-method ${item.method}`}>{item.method}</span>
                                <span className="nuc-feed-path">{item.path}</span>
                                <span className={`nuc-feed-result ${item.resultClass}`}>{item.result}</span>
                                <span className="nuc-feed-latency">{item.latency}ms</span>
                                <span className="nuc-feed-time">{item.time}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </>
    );
}

function StatCard({ label, value, change, up }: { label: string; value: string; change: string; up?: boolean }) {
    return (
        <div className="nuc-stat-card">
            <div className="nuc-stat-label">{label}</div>
            <div className="nuc-stat-value">{value}</div>
            {change && (
                <div className={`nuc-stat-change ${up ? "up" : "down"}`}>
                    {up ? "↑" : "↓"} {change}
                </div>
            )}
        </div>
    );
}
