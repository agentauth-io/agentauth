// Agents command
import { Command } from "commander";
import { input, confirm } from "@inquirer/prompts";
import ora from "ora";
import chalk from "chalk";
import { apiRequest } from "../utils/api.js";
import { error, heading, keyValue, formatOutput, formatTable } from "../utils/output.js";
import { getConfig } from "../utils/config.js";
import type { Agent } from "../types.js";

export const agentsCommand = new Command("agents")
    .description("Manage registered agents")
    .addCommand(
        new Command("list")
            .description("List all registered agents")
            .option("-s, --status <status>", "Filter by status (active, inactive, suspended)")
            .option("--format <format>", "Output format (table, json, yaml)", getConfig().defaultFormat)
            .action(async (options) => {
                const spinner = ora("Fetching agents...").start();

                const params = new URLSearchParams();
                if (options.status) params.append("status", options.status);

                const result = await apiRequest<Agent[]>(`/v1/agents?${params}`);

                if (result.success && result.data) {
                    spinner.succeed(`Found ${result.data.length} agents`);
                    
                    if (options.format === "table") {
                        console.log(formatTable(
                            result.data.map(a => ({
                                id: a.id.substring(0, 8) + "...",
                                name: a.name,
                                status: a.status === "active" ? chalk.green("active") : chalk.gray(a.status),
                                transactions: a.transactions.toLocaleString(),
                                volume: a.volume,
                                approval_rate: `${a.approval_rate}%`,
                            })),
                            ["id", "name", "status", "transactions", "volume", "approval_rate"]
                        ));
                    } else {
                        console.log(formatOutput(result.data, options.format));
                    }
                } else {
                    spinner.fail("Failed to fetch agents");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("register")
            .description("Register a new agent")
            .option("-n, --name <name>", "Agent name")
            .option("--interactive", "Interactive mode")
            .option("--json", "Output in JSON format")
            .action(async (options) => {
                let { name } = options;

                if (options.interactive || !name) {
                    name = await input({
                        message: "Agent name:",
                        default: name,
                        validate: (val: string) => {
                            if (val.length < 3) return "Name must be at least 3 characters";
                            if (!/^[a-z0-9-]+$/.test(val)) return "Name can only contain lowercase letters, numbers, and hyphens";
                            return true;
                        },
                    });
                }

                const spinner = ora("Registering agent...").start();

                const result = await apiRequest<Agent>("/v1/agents", {
                    method: "POST",
                    body: { name },
                });

                if (result.success && result.data) {
                    spinner.succeed("Agent registered successfully");
                    
                    if (options.json) {
                        console.log(JSON.stringify(result.data, null, 2));
                    } else {
                        heading("Agent Details");
                        keyValue("Agent ID", result.data.id);
                        keyValue("Name", result.data.name);
                        keyValue("Status", chalk.green(result.data.status));
                        keyValue("Created", new Date(result.data.created_at).toLocaleString());
                    }
                } else {
                    spinner.fail("Failed to register agent");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("get")
            .description("Get agent details")
            .argument("<agent_id>", "Agent ID")
            .option("--json", "Output in JSON format")
            .action(async (agentId, options) => {
                const spinner = ora("Fetching agent...").start();

                const result = await apiRequest<Agent>(`/v1/agents/${agentId}`);

                if (result.success && result.data) {
                    spinner.succeed("Agent found");
                    
                    if (options.json) {
                        console.log(JSON.stringify(result.data, null, 2));
                    } else {
                        heading(`Agent: ${result.data.name}`);
                        keyValue("ID", result.data.id);
                        keyValue("Status", result.data.status === "active" 
                            ? chalk.green(result.data.status)
                            : chalk.gray(result.data.status));
                        keyValue("Created", new Date(result.data.created_at).toLocaleString());
                        keyValue("Last Active", result.data.last_active 
                            ? new Date(result.data.last_active).toLocaleString()
                            : "Never");
                        keyValue("Transactions", result.data.transactions.toLocaleString());
                        keyValue("Volume", result.data.volume);
                        keyValue("Approval Rate", `${result.data.approval_rate}%`);
                    }
                } else {
                    spinner.fail("Agent not found");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("delete")
            .description("Delete an agent")
            .argument("<agent_id>", "Agent ID")
            .option("-f, --force", "Skip confirmation")
            .action(async (agentId, options) => {
                if (!options.force) {
                    const shouldDelete = await confirm({
                        message: `Are you sure you want to delete agent ${agentId}?`,
                        default: false,
                    });
                    if (!shouldDelete) {
                        console.log("Cancelled.");
                        return;
                    }
                }

                const spinner = ora("Deleting agent...").start();

                const result = await apiRequest(`/v1/agents/${agentId}`, {
                    method: "DELETE",
                });

                if (result.success) {
                    spinner.succeed("Agent deleted successfully");
                } else {
                    spinner.fail("Failed to delete agent");
                    error(result.error || "Unknown error");
                }
            })
    );
