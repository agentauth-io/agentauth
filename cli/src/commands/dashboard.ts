// Dashboard command
import { Command } from "commander";
import ora from "ora";
import chalk from "chalk";
import { apiRequest } from "../utils/api.js";
import { error, heading, keyValue } from "../utils/output.js";
import type { DashboardStats } from "../types.js";

export const dashboardCommand = new Command("dashboard")
    .description("Show dashboard overview")
    .option("--json", "Output in JSON format")
    .action(async (options) => {
        const spinner = ora("Fetching dashboard data...").start();

        const result = await apiRequest<DashboardStats>("/v1/dashboard/stats");

        if (!result.success || !result.data) {
            spinner.fail("Failed to fetch dashboard data");
            error(result.error || "Unknown error");
            return;
        }

        spinner.stop();
        const stats = result.data;

        if (options.json) {
            console.log(JSON.stringify(stats, null, 2));
            return;
        }

        // ASCII art header
        console.log(chalk.cyan(`
   ___                    _   ___       _   _     
  / _ \\                  | | / _ \\     | | | |    
 / /_\\ \\__ _  ___ _ __ | |/ /_\\ \\_ _| |_| |__  
 |  _  / _\` |/ _ \\ '_ \\| ||  _  | | | | __| '_ \\ 
 | | | | (_| |  __/ | | | || | | | |_| | |_| | | |
 \\_| |_/\\__, |\\___|_| |_|_|\\_| |_/\\__,_|\\__|_| |_|
         __/ |                                    
        |___/     ${chalk.gray("Dashboard Overview")}
`));

        heading("Key Metrics");
        
        // Create a visual bar for approval rate
        const approvalBar = createBar(stats.approval_rate, 100, 20);
        
        keyValue("Total Authorizations", stats.total_authorizations.toLocaleString());
        keyValue("Transaction Volume", formatCurrency(stats.transaction_volume));
        keyValue("Approval Rate", `${stats.approval_rate}% ${approvalBar}`);
        keyValue("Avg Response Time", `${stats.avg_response_time}ms`);
        
        heading("Activity");
        keyValue("Active Agents", stats.active_agents);
        keyValue("Pending Consents", stats.pending_consents);

        console.log();
        console.log(chalk.gray("Run 'agentauth agents list' or 'agentauth consents list' for details."));
    });

function createBar(value: number, max: number, width: number): string {
    const filled = Math.round((value / max) * width);
    const empty = width - filled;
    const bar = chalk.green("█".repeat(filled)) + chalk.gray("░".repeat(empty));
    return `[${bar}]`;
}

function formatCurrency(amount: number): string {
    if (amount >= 1000000) {
        return `$${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
        return `$${(amount / 1000).toFixed(1)}K`;
    }
    return `$${amount.toFixed(2)}`;
}
