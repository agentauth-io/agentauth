// Logs command
import { Command } from "commander";
import ora from "ora";
import chalk from "chalk";
import { apiRequest } from "../utils/api.js";
import { error, formatOutput, formatTable } from "../utils/output.js";
import { getConfig } from "../utils/config.js";
import type { LogEntry } from "../types.js";

const typeColors: Record<string, (text: string) => string> = {
    authorization: chalk.green,
    consent: chalk.cyan,
    config: chalk.magenta,
    security: chalk.yellow,
    api: chalk.blue,
};

export const logsCommand = new Command("logs")
    .description("View audit logs")
    .option("-t, --type <type>", "Filter by type (authorization, consent, config, security, api)")
    .option("-l, --limit <limit>", "Number of results", "50")
    .option("--since <date>", "Show logs since date (ISO format or relative like '1h', '1d', '1w')")
    .option("--follow", "Follow log output in real-time (experimental)")
    .option("--format <format>", "Output format (table, json, yaml)", getConfig().defaultFormat)
    .action(async (options) => {
        const spinner = ora("Fetching logs...").start();

        const params = new URLSearchParams();
        params.append("limit", options.limit);
        if (options.type) params.append("type", options.type);
        if (options.since) params.append("since", options.since);

        const result = await apiRequest<LogEntry[]>(`/v1/analytics/logs?${params}`);

        if (result.success && result.data) {
            spinner.succeed(`Found ${result.data.length} log entries`);
            
            if (options.format === "table") {
                console.log(formatTable(
                    result.data.map(log => {
                        const colorFn = typeColors[log.type] || chalk.white;
                        return {
                            time: new Date(log.timestamp).toLocaleString(),
                            type: colorFn(log.type),
                            action: log.action,
                            details: log.details.substring(0, 50) + (log.details.length > 50 ? "..." : ""),
                        };
                    }),
                    ["time", "type", "action", "details"]
                ));
            } else {
                console.log(formatOutput(result.data, options.format));
            }

            if (options.follow) {
                console.log(chalk.gray("\nFollowing logs... (Ctrl+C to stop)"));
                // In a real implementation, this would use WebSocket or polling
                // For now, just show a message
                console.log(chalk.yellow("Note: Real-time log following is not yet implemented."));
            }
        } else {
            spinner.fail("Failed to fetch logs");
            error(result.error || "Unknown error");
        }
    });
