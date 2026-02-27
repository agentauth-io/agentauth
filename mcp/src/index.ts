#!/usr/bin/env node
/**
 * AgentAuth MCP Server
 *
 * Exposes AgentAuth authorization tools and resources to AI agents
 * via the Model Context Protocol (stdio transport).
 *
 * Tools:
 *   - authorize       — Authorize an agent action
 *   - create_consent  — Create a user spending consent
 *   - check_budget    — Check remaining budget for a user
 *   - list_policies   — List all configured policies
 *   - evaluate_policy — Evaluate policies in the playground
 *   - create_policy   — Create a new authorization policy
 *
 * Resources:
 *   - agentauth://policies   — Current policy list
 *   - agentauth://health     — API health status
 *   - agentauth://openapi    — OpenAPI spec reference
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// ─── Config ──────────────────────────────────────────────────────────

const API_BASE = process.env.AGENTAUTH_API_URL || "https://agentauth-api.koyeb.app";
const API_KEY = process.env.AGENTAUTH_API_KEY || "";

async function apiRequest(method: string, path: string, body?: unknown): Promise<unknown> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (API_KEY) headers["X-API-Key"] = API_KEY;

    const res = await fetch(`${API_BASE}${path}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(`AgentAuth API error (${res.status}): ${(err as any).detail || res.statusText}`);
    }
    return res.json();
}

// ─── Server ──────────────────────────────────────────────────────────

const server = new McpServer({
    name: "agentauth",
    version: "0.1.0",
});

// ─── Tool: authorize ─────────────────────────────────────────────────

server.tool(
    "authorize",
    "Authorize an AI agent action (purchase, booking, etc) against configured policies. Returns allow/deny with risk score and explanation.",
    {
        agent_id: z.string().describe("Unique identifier for the AI agent"),
        user_id: z.string().describe("User who delegated authority to the agent"),
        action: z.string().describe("Action type: purchase, booking, transfer, etc"),
        amount: z.number().optional().describe("Transaction amount"),
        currency: z.string().optional().default("USD").describe("Currency (ISO 4217)"),
        merchant_id: z.string().optional().describe("Merchant ID"),
        merchant_name: z.string().optional().describe("Merchant name"),
        category: z.string().optional().describe("Category: groceries, electronics, travel, etc"),
    },
    async (params) => {
        try {
            const result = await apiRequest("POST", "/v1/authorize", params);
            return {
                content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
            };
        } catch (e: any) {
            return {
                content: [{ type: "text" as const, text: `Error: ${e.message}` }],
                isError: true,
            };
        }
    }
);

// ─── Tool: create_consent ────────────────────────────────────────────

server.tool(
    "create_consent",
    "Create a user spending consent — grants an agent permission to spend up to a limit within specified categories.",
    {
        user_id: z.string().describe("User granting consent"),
        intent: z.string().describe("What the user wants the agent to do"),
        max_amount: z.number().describe("Maximum spending limit"),
        currency: z.string().optional().default("USD"),
        allowed_merchants: z.array(z.string()).optional().describe("Restrict to these merchants"),
        allowed_categories: z.array(z.string()).optional().describe("Restrict to these categories"),
        expires_in_seconds: z.number().optional().default(3600),
    },
    async (params) => {
        try {
            const result = await apiRequest("POST", "/v1/consents", {
                ...params,
                single_use: true,
                signature: "mcp_server",
                public_key: "mcp_key",
            });
            return {
                content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
            };
        } catch (e: any) {
            return {
                content: [{ type: "text" as const, text: `Error: ${e.message}` }],
                isError: true,
            };
        }
    }
);

// ─── Tool: check_budget ──────────────────────────────────────────────

server.tool(
    "check_budget",
    "Check a user's remaining spending budget — daily/monthly spent and limits.",
    {
        user_id: z.string().describe("User to check budget for"),
    },
    async ({ user_id }) => {
        try {
            const result = await apiRequest("GET", `/v1/user/${user_id}/spending`);
            return {
                content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
            };
        } catch (e: any) {
            return {
                content: [{ type: "text" as const, text: `Error: ${e.message}` }],
                isError: true,
            };
        }
    }
);

// ─── Tool: list_policies ─────────────────────────────────────────────

server.tool(
    "list_policies",
    "List all authorization policies configured in AgentAuth.",
    {},
    async () => {
        try {
            const result = await apiRequest("GET", "/v1/policies");
            return {
                content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
            };
        } catch (e: any) {
            return {
                content: [{ type: "text" as const, text: `Error: ${e.message}` }],
                isError: true,
            };
        }
    }
);

// ─── Tool: evaluate_policy ───────────────────────────────────────────

server.tool(
    "evaluate_policy",
    "Evaluate policies against a context in the sandbox. No auth required. Returns decision (allow/deny), risk score, and trace.",
    {
        policies: z.array(z.object({
            id: z.string().optional().default("pol_1"),
            name: z.string(),
            effect: z.enum(["allow", "deny", "require_approval"]),
            priority: z.number().optional().default(0),
            description: z.string().optional().default(""),
            constraints: z.record(z.string(), z.unknown()).optional().default({}),
            rules: z.array(z.object({
                conditions: z.array(z.object({
                    attribute: z.string(),
                    operator: z.string(),
                    value: z.unknown(),
                })),
                logic: z.enum(["and", "or"]).optional().default("and"),
            })).optional().default([]),
        })).describe("Policies to evaluate"),
        context: z.record(z.string(), z.unknown()).describe("Request context: { amount, category, merchant, ... }"),
        combine_algorithm: z.enum(["deny_overrides", "allow_overrides", "first_applicable", "unanimous"])
            .optional()
            .default("deny_overrides"),
    },
    async (params) => {
        try {
            const result = await apiRequest("POST", "/v1/playground/evaluate", params);
            return {
                content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
            };
        } catch (e: any) {
            return {
                content: [{ type: "text" as const, text: `Error: ${e.message}` }],
                isError: true,
            };
        }
    }
);

// ─── Tool: create_policy ─────────────────────────────────────────────

server.tool(
    "create_policy",
    "Create a new authorization policy in AgentAuth.",
    {
        name: z.string().describe("Policy name"),
        effect: z.enum(["allow", "deny", "require_approval"]).describe("Policy effect"),
        priority: z.number().optional().default(0).describe("Higher = evaluated first"),
        description: z.string().optional().default(""),
        rules: z.array(z.object({
            conditions: z.array(z.object({
                attribute: z.string(),
                operator: z.string(),
                value: z.unknown(),
            })),
            logic: z.enum(["and", "or"]).optional().default("and"),
        })).optional().default([]),
        constraints: z.record(z.string(), z.unknown()).optional().default({}),
    },
    async (params) => {
        try {
            const result = await apiRequest("POST", "/v1/policies", params);
            return {
                content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
            };
        } catch (e: any) {
            return {
                content: [{ type: "text" as const, text: `Error: ${e.message}` }],
                isError: true,
            };
        }
    }
);

// ─── Resources ───────────────────────────────────────────────────────

server.resource(
    "policies",
    "agentauth://policies",
    async (uri) => {
        const result = await apiRequest("GET", "/v1/policies");
        return {
            contents: [{
                uri: uri.href,
                mimeType: "application/json",
                text: JSON.stringify(result, null, 2),
            }],
        };
    }
);

server.resource(
    "health",
    "agentauth://health",
    async (uri) => {
        const result = await apiRequest("GET", "/health");
        return {
            contents: [{
                uri: uri.href,
                mimeType: "application/json",
                text: JSON.stringify(result, null, 2),
            }],
        };
    }
);

server.resource(
    "openapi",
    "agentauth://openapi",
    async (uri) => ({
        contents: [{
            uri: uri.href,
            mimeType: "text/plain",
            text: "OpenAPI spec: https://raw.githubusercontent.com/agentauth-io/agentauth/main/openapi.yaml",
        }],
    })
);

// ─── Start ───────────────────────────────────────────────────────────

async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("AgentAuth MCP server running on stdio");
}

main().catch((e) => {
    console.error("Fatal:", e);
    process.exit(1);
});
