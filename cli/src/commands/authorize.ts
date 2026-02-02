// Authorize command
import { Command } from "commander";
import { input, number } from "@inquirer/prompts";
import ora from "ora";
import chalk from "chalk";
import { apiRequest } from "../utils/api.js";
import { error, heading, keyValue, formatOutput } from "../utils/output.js";
import { getConfig } from "../utils/config.js";
import type { Authorization } from "../types.js";

export const authorizeCommand = new Command("authorize")
    .description("Create or verify agent authorizations")
    .addCommand(
        new Command("create")
            .description("Request a new authorization")
            .option("-a, --agent <agent_id>", "Agent ID")
            .option("-u, --user <user_id>", "User ID")
            .option("--action <action>", "Action type (purchase, read, write, transfer)", "purchase")
            .option("-m, --amount <amount>", "Transaction amount", parseFloat)
            .option("--merchant <merchant>", "Merchant name or ID")
            .option("--category <category>", "Transaction category")
            .option("-r, --resource <resource>", "Resource identifier")
            .option("--interactive", "Interactive mode", false)
            .option("--json", "Output in JSON format")
            .action(async (options) => {
                let { agent, user, action, amount, merchant, category, resource } = options;

                if (options.interactive || (!agent || !user)) {
                    agent = await input({
                        message: "Agent ID:",
                        default: agent || "cli-agent",
                        validate: (val: string) => val.length > 0 || "Agent ID is required",
                    });

                    user = await input({
                        message: "User ID:",
                        default: user || "cli-user",
                        validate: (val: string) => val.length > 0 || "User ID is required",
                    });

                    action = await input({
                        message: "Action (purchase, read, write, transfer):",
                        default: action || "purchase",
                    });

                    amount = await number({
                        message: "Amount (0 for non-financial):",
                        default: amount || 0,
                    });

                    merchant = await input({
                        message: "Merchant (optional):",
                        default: merchant || "",
                    });
                    
                    category = await input({
                        message: "Category (optional):",
                        default: category || "",
                    });
                }

                const spinner = ora("Requesting authorization...").start();

                const result = await apiRequest<Authorization>("/v1/authorize", {
                    method: "POST",
                    body: {
                        agent_id: agent,
                        user_id: user,
                        action: action,
                        amount: amount || undefined,
                        merchant: merchant || undefined,
                        category: category || undefined,
                        resource: resource || undefined,
                    },
                });

                if (result.success && result.data) {
                    spinner.succeed("Authorization created");
                    
                    if (options.json) {
                        console.log(JSON.stringify(result.data, null, 2));
                    } else {
                        heading("Authorization Details");
                        keyValue("Request ID", result.data.request_id || result.data.id);
                        keyValue("Status", result.data.status === "approved" 
                            ? chalk.green("✓ " + result.data.status) 
                            : result.data.status === "denied"
                            ? chalk.red("✗ " + result.data.status)
                            : chalk.yellow(result.data.status));
                        keyValue("Authorized", result.data.authorized ? chalk.green("Yes") : chalk.red("No"));
                        keyValue("Reason", result.data.reason || "N/A");
                        keyValue("Policy", result.data.policy_id || "N/A");
                        if (result.data.token) {
                            keyValue("Token", result.data.token.substring(0, 30) + "...");
                        }
                        if (result.data.expires_at) {
                            const expiry = typeof result.data.expires_at === 'number' 
                                ? new Date(result.data.expires_at * 1000) 
                                : new Date(result.data.expires_at);
                            keyValue("Expires", expiry.toLocaleString());
                        }
                    }
                } else {
                    spinner.fail("Authorization failed");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("verify")
            .description("Verify an existing authorization")
            .argument("<authorization_id>", "Authorization ID to verify")
            .option("--json", "Output in JSON format")
            .action(async (authId, options) => {
                const spinner = ora("Verifying authorization...").start();

                const result = await apiRequest<Authorization>(`/v1/verify/${authId}`);

                if (result.success && result.data) {
                    spinner.succeed("Authorization verified");
                    
                    if (options.json) {
                        console.log(JSON.stringify(result.data, null, 2));
                    } else {
                        heading("Authorization Status");
                        keyValue("ID", result.data.id);
                        keyValue("Status", result.data.status === "authorized" 
                            ? chalk.green("✓ Valid") 
                            : result.data.status === "expired"
                            ? chalk.yellow("⚠ Expired")
                            : chalk.red("✗ Invalid"));
                        keyValue("Agent", result.data.agent_id);
                        keyValue("Amount", `${result.data.max_amount || result.data.amount || 0} ${result.data.currency || "USD"}`);
                        if (result.data.created_at) {
                            keyValue("Created", new Date(result.data.created_at).toLocaleString());
                        }
                    }
                } else {
                    spinner.fail("Verification failed");
                    error(result.error || "Authorization not found");
                }
            })
    )
    .addCommand(
        new Command("list")
            .description("List recent authorizations")
            .option("-l, --limit <limit>", "Number of results", "20")
            .option("-s, --status <status>", "Filter by status (authorized, denied, pending, expired)")
            .option("--format <format>", "Output format (table, json, yaml)", getConfig().defaultFormat)
            .action(async (options) => {
                const spinner = ora("Fetching authorizations...").start();

                const params = new URLSearchParams();
                params.append("limit", options.limit);
                if (options.status) params.append("status", options.status);

                const result = await apiRequest<Authorization[]>(`/v1/authorizations?${params}`);

                if (result.success && result.data) {
                    spinner.succeed(`Found ${result.data.length} authorizations`);
                    console.log(formatOutput(result.data, options.format));
                } else {
                    spinner.fail("Failed to fetch authorizations");
                    error(result.error || "Unknown error");
                }
            })
    );
