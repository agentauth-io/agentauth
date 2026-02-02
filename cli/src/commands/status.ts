// Status command - Professional UI
import { Command } from "commander";
import { getConfig } from "../utils/config.js";
import { apiRequest, checkConnection } from "../utils/api.js";
import { 
    colors, 
    icons, 
    header, 
    keyValue, 
    spinner, 
    statusBadge,
    box,
    divider,
    success,
    error,
    formatCurrency,
    formatNumber,
} from "../utils/ui.js";

// Analytics summary type matching the API
interface AnalyticsSummary {
    total_authorizations: number;
    total_approved: number;
    total_denied: number;
    total_amount: string;
    approval_rate: number;
    today_authorizations: number;
    today_approved: number;
    today_denied: number;
    today_amount: string;
    month_authorizations: number;
    month_amount: string;
    top_merchants: Array<{ merchant: string; count: number }>;
    top_agents: Array<{ agent: string; count: number }>;
}

export const statusCommand = new Command("status")
    .description("Show current authentication status and API health")
    .option("--json", "Output in JSON format")
    .option("-v, --verbose", "Show detailed information")
    .action(async (options) => {
        const config = getConfig();
        
        if (options.json) {
            const status = {
                authenticated: !!config.apiKey,
                apiUrl: config.apiUrl,
                connected: false,
                stats: null as AnalyticsSummary | null,
            };

            const spin = spinner("Checking connection...").start();
            status.connected = await checkConnection();
            
            if (status.connected && config.apiKey) {
                const result = await apiRequest<AnalyticsSummary>("/v1/analytics/summary");
                if (result.success && result.data) {
                    status.stats = result.data;
                }
            }
            
            spin.stop();
            console.log(JSON.stringify(status, null, 2));
            return;
        }

        // Header with status
        console.log(header("Status"));
        
        // Connection info
        const spin = spinner("Checking connection...").start();
        const connected = await checkConnection();
        spin.stop();
        
        // Build status display
        const isAuth = !!config.apiKey;
        const maskedKey = isAuth 
            ? config.apiKey!.substring(0, 8) + "•".repeat(12) + config.apiKey!.slice(-4)
            : "Not configured";
        
        console.log(keyValue([
            ["Connection", connected ? "Connected" : "Disconnected"],
            ["API URL", config.apiUrl],
            ["API Key", maskedKey],
            ["Format", config.defaultFormat],
        ]));
        
        // Status badges
        console.log();
        console.log(`  ${connected ? statusBadge("connected") : statusBadge("disconnected")} ` +
                    `${isAuth ? statusBadge("live") : statusBadge("inactive")}`);
        
        if (!connected) {
            console.log();
            error("Cannot connect to API", `Check if ${config.apiUrl} is reachable`);
            return;
        }
        
        if (!isAuth) {
            console.log();
            console.log(`  ${colors.dim("Run")} ${colors.primary("agentauth login")} ${colors.dim("to authenticate")}`);
            return;
        }
        
        // Fetch analytics
        console.log();
        const statsSpin = spinner("Loading analytics...").start();
        const result = await apiRequest<AnalyticsSummary>("/v1/analytics/summary");
        
        if (result.success && result.data) {
            statsSpin.succeed(colors.dim("Analytics loaded"));
            
            console.log(header("Overview"));
            
            // Stats grid
            const stats = result.data;
            const totalAuth = formatNumber(stats.total_authorizations ?? 0);
            const approvalRate = `${(stats.approval_rate ?? 0).toFixed(1)}%`;
            const todayAuth = formatNumber(stats.today_authorizations ?? 0);
            const monthAmount = stats.month_amount ?? "0";
            
            console.log(
                `  ${icons.lightning} ${colors.primary(totalAuth)} ${colors.dim("total authorizations")}` +
                `    ${icons.check} ${colors.success(approvalRate)} ${colors.dim("approval rate")}`
            );
            console.log(
                `  ${icons.clock} ${colors.accent(todayAuth)} ${colors.dim("today")}` +
                `                   ${icons.money} ${colors.success(formatCurrency(parseFloat(monthAmount) || 0))} ${colors.dim("this month")}`
            );
            
            // Approval breakdown
            if (options.verbose && (stats.total_approved || stats.total_denied)) {
                console.log();
                console.log(`  ${colors.dim("Breakdown:")}`);
                console.log(`    ${colors.success("✓")} ${formatNumber(stats.total_approved ?? 0)} approved`);
                console.log(`    ${colors.error("✗")} ${formatNumber(stats.total_denied ?? 0)} denied`);
            }
            
            // Top merchants
            if (stats.top_merchants?.length > 0) {
                console.log(`\n  ${colors.dim("Top Merchants:")}`);
                stats.top_merchants.slice(0, 3).forEach((m, i) => {
                    console.log(`    ${colors.muted(`${i + 1}.`)} ${m.merchant} ${colors.dim(`(${m.count})`)}`);
                });
            }
        } else {
            statsSpin.info(colors.dim("No analytics data available"));
        }
        
        console.log(`\n${divider(50)}`);
        console.log(`  ${colors.dim("Last checked:")} ${colors.muted(new Date().toLocaleTimeString())}`);
    });
