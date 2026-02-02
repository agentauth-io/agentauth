// API client utilities
import fetch, { AbortError } from "node-fetch";
import { getApiKey, getApiUrl } from "./config.js";
import type { ApiResponse } from "../types.js";

// Request timeout in milliseconds
const REQUEST_TIMEOUT = 30000;

// User agent string
const USER_AGENT = `AgentAuth-CLI/1.0.0 (${process.platform}; Node.js ${process.version})`;

export class ApiError extends Error {
    constructor(
        message: string,
        public statusCode: number,
        public response?: unknown
    ) {
        super(message);
        this.name = "ApiError";
    }
}

export async function apiRequest<T>(
    endpoint: string,
    options: {
        method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
        body?: unknown;
        requiresAuth?: boolean;
        timeout?: number;
    } = {}
): Promise<ApiResponse<T>> {
    const { method = "GET", body, requiresAuth = true, timeout = REQUEST_TIMEOUT } = options;
    const apiKey = getApiKey();
    const apiUrl = getApiUrl();

    if (requiresAuth && !apiKey) {
        return {
            success: false,
            error: "Not authenticated. Run 'agentauth login' first.",
        };
    }

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    };

    if (apiKey) {
        headers["X-API-Key"] = apiKey;
    }

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(`${apiUrl}${endpoint}`, {
            method,
            headers,
            body: body ? JSON.stringify(body) : undefined,
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        // Handle non-JSON responses
        const contentType = response.headers.get("content-type");
        let data: T;
        
        if (contentType?.includes("application/json")) {
            data = await response.json() as T;
        } else {
            const text = await response.text();
            data = { message: text } as T;
        }

        if (!response.ok) {
            const errorDetail = (data as { detail?: string; message?: string; error?: string });
            return {
                success: false,
                error: errorDetail?.detail || errorDetail?.message || errorDetail?.error || 
                       `Request failed with status ${response.status}`,
            };
        }

        return {
            success: true,
            data,
        };
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error instanceof AbortError || (error as Error).name === "AbortError") {
            return {
                success: false,
                error: `Request timed out after ${timeout / 1000}s. Check your connection.`,
            };
        }
        
        if ((error as Error).message?.includes("ECONNREFUSED")) {
            return {
                success: false,
                error: `Cannot connect to ${apiUrl}. Is the server running?`,
            };
        }
        
        if ((error as Error).message?.includes("ENOTFOUND")) {
            return {
                success: false,
                error: `Cannot resolve ${apiUrl}. Check your internet connection.`,
            };
        }
        
        return {
            success: false,
            error: error instanceof Error ? error.message : "Unknown error occurred",
        };
    }
}

export async function checkConnection(): Promise<boolean> {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        const response = await fetch(`${getApiUrl()}/health`, {
            headers: { "User-Agent": USER_AGENT },
            signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        return response.ok;
    } catch {
        return false;
    }
}

export interface ApiHealthStatus {
    connected: boolean;
    latency?: number;
    version?: string;
    error?: string;
}

export async function checkApiHealth(): Promise<ApiHealthStatus> {
    const start = Date.now();
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        const response = await fetch(`${getApiUrl()}/health`, {
            headers: { "User-Agent": USER_AGENT },
            signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        const latency = Date.now() - start;
        
        if (response.ok) {
            const data = await response.json() as { status?: string; version?: string };
            return {
                connected: true,
                latency,
                version: data.version,
            };
        }
        
        return {
            connected: false,
            latency,
            error: `HTTP ${response.status}`,
        };
    } catch (err) {
        const error = err as Error;
        if (error.message?.includes("ECONNREFUSED")) {
            return { connected: false, error: "Server not running" };
        }
        if (error.message?.includes("ENOTFOUND")) {
            return { connected: false, error: "Cannot resolve host" };
        }
        if (error.name === "AbortError") {
            return { connected: false, error: "Connection timeout" };
        }
        return { connected: false, error: error.message || "Unknown error" };
    }
}

// Try to find an available API endpoint
const FALLBACK_URLS = [
    "http://localhost:8000",
    "https://api.agentauth.in",
];

export async function findAvailableApi(): Promise<string | null> {
    for (const url of FALLBACK_URLS) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(`${url}/health`, {
                headers: { "User-Agent": USER_AGENT },
                signal: controller.signal,
            });
            
            clearTimeout(timeoutId);
            if (response.ok) {
                return url;
            }
        } catch {
            continue;
        }
    }
    return null;
}
