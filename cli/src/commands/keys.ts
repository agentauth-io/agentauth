// Keys command
import { Command } from "commander";
import { input, select, confirm } from "@inquirer/prompts";
import ora from "ora";
import chalk from "chalk";
import { apiRequest } from "../utils/api.js";
import { error, heading, keyValue, formatOutput, formatTable, warning } from "../utils/output.js";
import { getConfig } from "../utils/config.js";
import type { ApiKey } from "../types.js";

export const keysCommand = new Command("keys")
    .description("Manage API keys")
    .addCommand(
        new Command("list")
            .description("List all API keys")
            .option("--format <format>", "Output format (table, json, yaml)", getConfig().defaultFormat)
            .action(async (options) => {
                const spinner = ora("Fetching API keys...").start();

                const result = await apiRequest<ApiKey[]>("/v1/keys");

                if (result.success && result.data) {
                    spinner.succeed(`Found ${result.data.length} API keys`);
                    
                    if (options.format === "table") {
                        console.log(formatTable(
                            result.data.map(k => ({
                                name: k.name,
                                type: k.type === "live" ? chalk.green("live") : chalk.gray("test"),
                                key: k.key.substring(0, 8) + "..." + k.key.substring(k.key.length - 4),
                                created: new Date(k.created_at).toLocaleDateString(),
                                last_used: k.last_used ? new Date(k.last_used).toLocaleDateString() : "Never",
                            })),
                            ["name", "type", "key", "created", "last_used"]
                        ));
                    } else {
                        console.log(formatOutput(result.data, options.format));
                    }
                } else {
                    spinner.fail("Failed to fetch API keys");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("create")
            .description("Create a new API key")
            .option("-n, --name <name>", "Key name")
            .option("-t, --type <type>", "Key type (live or test)", "live")
            .option("--interactive", "Interactive mode")
            .action(async (options) => {
                let { name, type } = options;

                if (options.interactive || !name) {
                    name = await input({
                        message: "Key name:",
                        default: name || "My API Key",
                        validate: (val: string) => val.length > 0 || "Name is required",
                    });

                    type = await select({
                        message: "Key type:",
                        choices: [
                            { name: "Live - For production use", value: "live" },
                            { name: "Test - For development and testing", value: "test" },
                        ],
                        default: type,
                    });
                }

                const spinner = ora("Creating API key...").start();

                const result = await apiRequest<ApiKey>("/v1/keys", {
                    method: "POST",
                    body: { name, type },
                });

                if (result.success && result.data) {
                    spinner.succeed("API key created successfully");
                    
                    heading("New API Key");
                    keyValue("Name", result.data.name);
                    keyValue("Type", result.data.type === "live" ? chalk.green("live") : chalk.gray("test"));
                    
                    console.log();
                    warning("Save this key now - you won't be able to see it again!");
                    console.log();
                    console.log(chalk.bgBlack.white.bold(`  ${result.data.key}  `));
                    console.log();
                } else {
                    spinner.fail("Failed to create API key");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("delete")
            .description("Delete an API key")
            .argument("<key_id>", "API key ID")
            .option("-f, --force", "Skip confirmation")
            .action(async (keyId, options) => {
                if (!options.force) {
                    const shouldDelete = await confirm({
                        message: `Are you sure you want to delete API key ${keyId}? This cannot be undone.`,
                        default: false,
                    });
                    if (!shouldDelete) {
                        console.log("Cancelled.");
                        return;
                    }
                }

                const spinner = ora("Deleting API key...").start();

                const result = await apiRequest(`/v1/keys/${keyId}`, {
                    method: "DELETE",
                });

                if (result.success) {
                    spinner.succeed("API key deleted successfully");
                } else {
                    spinner.fail("Failed to delete API key");
                    error(result.error || "Unknown error");
                }
            })
    )
    .addCommand(
        new Command("rotate")
            .description("Rotate an API key (creates new key, keeps name)")
            .argument("<key_id>", "API key ID to rotate")
            .option("-f, --force", "Skip confirmation")
            .action(async (keyId, options) => {
                if (!options.force) {
                    const shouldRotate = await confirm({
                        message: `This will invalidate the current key and create a new one. Continue?`,
                        default: false,
                    });
                    if (!shouldRotate) {
                        console.log("Cancelled.");
                        return;
                    }
                }

                const spinner = ora("Rotating API key...").start();

                const result = await apiRequest<ApiKey>(`/v1/keys/${keyId}/rotate`, {
                    method: "POST",
                });

                if (result.success && result.data) {
                    spinner.succeed("API key rotated successfully");
                    
                    console.log();
                    warning("Save this new key now - you won't be able to see it again!");
                    console.log();
                    console.log(chalk.bgBlack.white.bold(`  ${result.data.key}  `));
                    console.log();
                } else {
                    spinner.fail("Failed to rotate API key");
                    error(result.error || "Unknown error");
                }
            })
    );
