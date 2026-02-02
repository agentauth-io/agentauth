// Policies command
import { Command } from "commander";
import { input, select, number, checkbox, confirm } from "@inquirer/prompts";
import ora from "ora";
import chalk from "chalk";
import { apiRequest } from "../utils/api.js";
import { error, heading, keyValue, formatOutput, formatTable } from "../utils/output.js";
import { getConfig } from "../utils/config.js";
import type { Policy } from "../types.js";

export const policiesCommand = new Command("policies")
    .description("Manage authorization policies and rules")
    .addCommand(
        new Command("list")
            .description("List all policies")
            .option("-t, --type <type>", "Filter by type (spending_limit, merchant_rule, category_rule, time_rule)")
            .option("--format <format>", "Output format (table, json, yaml)", getConfig().defaultFormat)
            .action(async (options) => {
                const spinner = ora("Fetching policies...").start();

                const params = new URLSearchParams();
                if (options.type) params.append("type", options.type);

                const result = await apiRequest<Policy[]>(`/v1/rules?${params}`);

                if (result.success && result.data) {
                    spinner.succeed(`Found ${result.data.length} policies`);
                    
                    if (options.format === "table") {
                        console.log(formatTable(
                            result.data.map(p => ({
                                id: p.id.substring(0, 8) + "...",
                                name: p.name,
                                type: p.type,
                                enabled: p.enabled ? chalk.green("✓") : chalk.red("✗"),
                                created: new Date(p.created_at).toLocaleDateString(),
                            })),
                            ["id", "name", "type", "enabled", "created"]
                        ));
                    } else {
                        console.log(formatOutput(result.data, options.format));
                    }
                } else {
                    spinner.fail("Failed to fetch policies");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("create")
            .description("Create a new policy")
            .option("-n, --name <name>", "Policy name")
            .option("-t, --type <type>", "Policy type")
            .option("--interactive", "Interactive mode")
            .option("--json", "Output in JSON format")
            .action(async (options) => {
                let { name, type } = options;
                let policyConfig: Record<string, unknown> = {};

                if (options.interactive || !name || !type) {
                    name = await input({
                        message: "Policy name:",
                        default: name,
                        validate: (val: string) => val.length > 0 || "Name is required",
                    });

                    type = await select({
                        message: "Policy type:",
                        choices: [
                            { name: "Spending Limit - Set maximum spending amounts", value: "spending_limit" },
                            { name: "Merchant Rule - Allow or block specific merchants", value: "merchant_rule" },
                            { name: "Category Rule - Allow or block merchant categories", value: "category_rule" },
                            { name: "Time Rule - Restrict transactions by time", value: "time_rule" },
                        ],
                        default: type,
                    });

                    // Type-specific configuration
                    if (type === "spending_limit") {
                        const dailyLimit = await number({
                            message: "Daily limit ($):",
                            default: 1000,
                        });
                        const monthlyLimit = await number({
                            message: "Monthly limit ($):",
                            default: 10000,
                        });
                        const perTransactionLimit = await number({
                            message: "Per-transaction limit ($):",
                            default: 500,
                        });
                        policyConfig = { daily_limit: dailyLimit, monthly_limit: monthlyLimit, per_transaction_limit: perTransactionLimit };
                    } else if (type === "merchant_rule") {
                        const action = await select({
                            message: "Action:",
                            choices: [
                                { name: "Allow", value: "allow" },
                                { name: "Block", value: "block" },
                            ],
                        });
                        const merchants = await input({
                            message: "Merchants (comma-separated):",
                        });
                        policyConfig = {
                            action,
                            merchants: merchants.split(",").map((m: string) => m.trim()),
                        };
                    } else if (type === "category_rule") {
                        const action = await select({
                            message: "Action:",
                            choices: [
                                { name: "Allow", value: "allow" },
                                { name: "Block", value: "block" },
                            ],
                        });
                        const categories = await checkbox({
                            message: "Categories:",
                            choices: [
                                { name: "Gambling", value: "gambling" },
                                { name: "Adult", value: "adult" },
                                { name: "Crypto", value: "crypto" },
                                { name: "Travel", value: "travel" },
                                { name: "SaaS", value: "saas" },
                                { name: "E-commerce", value: "ecommerce" },
                                { name: "Cloud Services", value: "cloud_services" },
                            ],
                        });
                        policyConfig = { action, categories };
                    }
                }

                const spinner = ora("Creating policy...").start();

                const result = await apiRequest<Policy>("/v1/rules", {
                    method: "POST",
                    body: { name, type, config: policyConfig, enabled: true },
                });

                if (result.success && result.data) {
                    spinner.succeed("Policy created successfully");
                    
                    if (options.json) {
                        console.log(JSON.stringify(result.data, null, 2));
                    } else {
                        heading("Policy Details");
                        keyValue("ID", result.data.id);
                        keyValue("Name", result.data.name);
                        keyValue("Type", result.data.type);
                        keyValue("Enabled", result.data.enabled);
                    }
                } else {
                    spinner.fail("Failed to create policy");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("delete")
            .description("Delete a policy")
            .argument("<policy_id>", "Policy ID")
            .option("-f, --force", "Skip confirmation")
            .action(async (policyId, options) => {
                if (!options.force) {
                    const shouldDelete = await confirm({
                        message: `Are you sure you want to delete policy ${policyId}?`,
                        default: false,
                    });
                    if (!shouldDelete) {
                        console.log("Cancelled.");
                        return;
                    }
                }

                const spinner = ora("Deleting policy...").start();

                const result = await apiRequest(`/v1/rules/${policyId}`, {
                    method: "DELETE",
                });

                if (result.success) {
                    spinner.succeed("Policy deleted successfully");
                } else {
                    spinner.fail("Failed to delete policy");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("toggle")
            .description("Enable or disable a policy")
            .argument("<policy_id>", "Policy ID")
            .option("--enable", "Enable the policy")
            .option("--disable", "Disable the policy")
            .action(async (policyId, options) => {
                const enabled = options.enable ? true : options.disable ? false : null;
                
                if (enabled === null) {
                    error("Please specify --enable or --disable");
                    return;
                }

                const spinner = ora(`${enabled ? "Enabling" : "Disabling"} policy...`).start();

                const result = await apiRequest<Policy>(`/v1/rules/${policyId}`, {
                    method: "PATCH",
                    body: { enabled },
                });

                if (result.success) {
                    spinner.succeed(`Policy ${enabled ? "enabled" : "disabled"} successfully`);
                } else {
                    spinner.fail(`Failed to ${enabled ? "enable" : "disable"} policy`);
                    error(result.error || "Unknown error");
                }
            })
    );
