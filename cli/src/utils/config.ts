// Configuration utilities
import Conf from "conf";
import type { Config } from "../types.js";

const config = new Conf<Config>({
    projectName: "agentauth",
    defaults: {
        apiUrl: "https://api.agentauth.in",
        defaultFormat: "table",
    },
});

// Environment variable support
const ENV_API_KEY = process.env.AGENTAUTH_API_KEY;
const ENV_API_URL = process.env.AGENTAUTH_API_URL;

export function getConfig(): Config {
    return {
        // Environment variables take precedence
        apiKey: ENV_API_KEY || config.get("apiKey"),
        apiUrl: ENV_API_URL || config.get("apiUrl"),
        defaultFormat: config.get("defaultFormat"),
    };
}

export function setApiKey(key: string): void {
    config.set("apiKey", key);
}

export function clearApiKey(): void {
    config.delete("apiKey");
}

export function setApiUrl(url: string): void {
    config.set("apiUrl", url);
}

export function setDefaultFormat(format: "table" | "json" | "yaml"): void {
    config.set("defaultFormat", format);
}

export function getApiKey(): string | undefined {
    return ENV_API_KEY || config.get("apiKey");
}

export function getApiUrl(): string {
    return ENV_API_URL || config.get("apiUrl") || "https://api.agentauth.in";
}

export function isAuthenticated(): boolean {
    return !!(ENV_API_KEY || config.get("apiKey"));
}

export function getConfigPath(): string {
    return config.path;
}
