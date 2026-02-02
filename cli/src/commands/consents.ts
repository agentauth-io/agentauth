// Consents command - Professional UI
import { Command } from "commander";
import { confirm } from "@inquirer/prompts";
import { apiRequest } from "../utils/api.js";
import { getConfig } from "../utils/config.js";
import type { Consent } from "../types.js";
import {
    colors,
    icons,
    header,
    keyValue,
    spinner,
    table,
    statusBadge,
    success,
    error,
    hint,
    formatDate,
    truncate,
} from "../utils/ui.js";

// API response wrapper
interface ConsentsListResponse {
    consents: Consent[];
    total: number;
    limit: number;
    offset: number;
}

export const consentsCommand = new Command("consents")
    .description("Manage agent consents")
    .addCommand(
        new Command("list")
            .description("List all consents")
            .option("-s, --status <status>", "Filter by status (pending, approved, denied, revoked)")
            .option("--active-only", "Show only active consents")
            .option("-l, --limit <n>", "Number of results", "20")
            .option("--format <format>", "Output format (table, json)", getConfig().defaultFormat)
            .action(async (options) => {
                const spin = spinner("Fetching consents...").start();

                const params = new URLSearchParams();
                params.append("limit", options.limit);
                if (options.status) params.append("status", options.status);
                if (options.activeOnly) params.append("is_active", "true");

                const result = await apiRequest<ConsentsListResponse>(`/v1/consents?${params}`);

                if (result.success && result.data) {
                    const consents = result.data.consents || [];
                    spin.succeed(colors.dim(`Found ${consents.length} consent${consents.length !== 1 ? "s" : ""}`));
                    
                    if (consents.length === 0) {
                        console.log();
                        console.log(`  ${colors.muted("No consents found")}`);
                        hint("Create a consent with your first authorization request");
                        return;
                    }
                    
                    if (options.format === "json") {
                        console.log(JSON.stringify(consents, null, 2));
                        return;
                    }
                    
                    console.log(header("Active Consents"));
                    
                    // Professional table
                    console.log(table(
                        consents.map(c => ({
                            id: truncate(c.consent_id || "", 12),
                            user: truncate(c.user_id || "", 14),
                            intent: truncate(c.intent_description || "N/A", 28),
                            status: c.is_active ? colors.success("Active") : colors.muted("Inactive"),
                            created: formatDate(c.created_at),
                        })),
                        [
                            { key: "id", header: "ID", width: 12 },
                            { key: "user", header: "User", width: 14 },
                            { key: "intent", header: "Intent", width: 28 },
                            { key: "status", header: "Status", width: 10 },
                            { key: "created", header: "Created", width: 12 },
                        ]
                    ));
                    
                    if (result.data.total > consents.length) {
                        console.log(`\n  ${colors.dim(`Showing ${consents.length} of ${result.data.total} total`)}`);
                    }
                } else {
                    spin.fail("Failed to fetch consents");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("approve")
            .description("Approve a pending consent")
            .argument("<consent_id>", "Consent ID")
            .action(async (consentId) => {
                const spin = spinner("Approving consent...").start();

                const result = await apiRequest<Consent>(`/v1/consents/${consentId}/approve`, {
                    method: "POST",
                });

                if (result.success) {
                    spin.succeed("Consent approved");
                    success(`Consent ${truncate(consentId, 12)} has been approved`);
                } else {
                    spin.fail("Failed to approve consent");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("deny")
            .description("Deny a pending consent")
            .argument("<consent_id>", "Consent ID")
            .option("-r, --reason <reason>", "Reason for denial")
            .action(async (consentId, options) => {
                const spin = spinner("Denying consent...").start();

                const result = await apiRequest<Consent>(`/v1/consents/${consentId}/deny`, {
                    method: "POST",
                    body: { reason: options.reason },
                });

                if (result.success) {
                    spin.succeed("Consent denied");
                } else {
                    spin.fail("Failed to deny consent");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("revoke")
            .description("Revoke an active consent")
            .argument("<consent_id>", "Consent ID")
            .option("-f, --force", "Skip confirmation")
            .action(async (consentId, options) => {
                if (!options.force) {
                    const shouldRevoke = await confirm({
                        message: `Revoke consent ${truncate(consentId, 16)}?`,
                        default: false,
                    });
                    if (!shouldRevoke) {
                        console.log(colors.dim("  Cancelled."));
                        return;
                    }
                }

                const spin = spinner("Revoking consent...").start();

                const result = await apiRequest(`/v1/consents/${consentId}/revoke`, {
                    method: "POST",
                });

                if (result.success) {
                    spin.succeed("Consent revoked");
                    success("The consent has been revoked and is no longer valid");
                } else {
                    spin.fail("Failed to revoke consent");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("get")
            .description("Get consent details")
            .argument("<consent_id>", "Consent ID")
            .option("--json", "Output in JSON format")
            .action(async (consentId, options) => {
                const spin = spinner("Fetching consent...").start();

                const result = await apiRequest<Consent>(`/v1/consents/${consentId}`);

                if (result.success && result.data) {
                    spin.succeed(colors.dim("Consent found"));
                    
                    if (options.json) {
                        console.log(JSON.stringify(result.data, null, 2));
                    } else {
                        const c = result.data;
                        console.log(header("Consent Details"));
                        console.log(keyValue([
                            ["Consent ID", c.consent_id],
                            ["User ID", c.user_id || "N/A"],
                            ["Agent ID", c.agent_id || "N/A"],
                            ["Intent", c.intent_description],
                            ["Active", c.is_active],
                        ]));
                        
                        console.log(`\n  ${c.status ? statusBadge(c.status) : statusBadge(c.is_active ? "active" : "inactive")}`);
                        
                        if (c.constraints) {
                            console.log(header("Constraints", "🔒"));
                            console.log(keyValue([
                                ["Max Amount", `$${c.constraints.max_amount || 0} ${c.constraints.currency || "USD"}`],
                            ]));
                            if (c.constraints.allowed_merchants?.length) {
                                console.log(`  ${colors.dim("Allowed Merchants:")} ${c.constraints.allowed_merchants.join(", ")}`);
                            }
                            if (c.constraints.blocked_categories?.length) {
                                console.log(`  ${colors.dim("Blocked Categories:")} ${c.constraints.blocked_categories.join(", ")}`);
                            }
                        }
                        
                        console.log(header("Timestamps", "📅"));
                        console.log(keyValue([
                            ["Created", formatDate(c.created_at)],
                            ...(c.expires_at ? [["Expires", formatDate(c.expires_at)] as [string, string]] : []),
                        ]));
                    }
                } else {
                    spin.fail("Consent not found");
                    error(result.error || "Unknown error");
                }
            })
    );
