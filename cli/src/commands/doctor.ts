// Doctor command - diagnose connection and configuration issues
import { Command } from "commander";
import { getConfig, setApiUrl } from "../utils/config.js";
import { checkApiHealth, findAvailableApi, ApiHealthStatus } from "../utils/api.js";
import { 
    colors, 
    icons, 
    header, 
    keyValue, 
    spinner, 
    statusBadge,
    success,
    error,
    warning,
    info,
    divider,
} from "../utils/ui.js";
import { confirm } from "@inquirer/prompts";

interface CheckResult {
    name: string;
    status: "pass" | "fail" | "warn";
    message: string;
    details?: string;
}

async function runChecks(): Promise<CheckResult[]> {
    const results: CheckResult[] = [];
    const config = getConfig();

    // Check 1: Configuration
    results.push({
        name: "Configuration",
        status: config.apiUrl ? "pass" : "fail",
        message: config.apiUrl ? `API URL: ${config.apiUrl}` : "No API URL configured",
    });

    // Check 2: Authentication
    results.push({
        name: "Authentication",
        status: config.apiKey ? "pass" : "warn",
        message: config.apiKey 
            ? `API Key: ${config.apiKey.substring(0, 8)}...` 
            : "Not authenticated",
        details: config.apiKey ? undefined : "Run 'agentauth login' to authenticate",
    });

    // Check 3: API Connection
    const health = await checkApiHealth();
    results.push({
        name: "API Connection",
        status: health.connected ? "pass" : "fail",
        message: health.connected 
            ? `Connected (${health.latency}ms latency)` 
            : `Connection failed`,
        details: health.error,
    });

    // Check 4: API Version (if connected)
    if (health.connected && health.version) {
        results.push({
            name: "API Version",
            status: "pass",
            message: `v${health.version}`,
        });
    }

    return results;
}

export const doctorCommand = new Command("doctor")
    .description("Diagnose connection issues and find available API endpoints")
    .option("--fix", "Attempt to fix issues automatically")
    .option("--json", "Output in JSON format")
    .action(async (options) => {
        if (options.json) {
            const results = await runChecks();
            console.log(JSON.stringify({ checks: results, timestamp: new Date().toISOString() }, null, 2));
            return;
        }

        console.log(header("Diagnostics"));
        console.log();

        const spin = spinner("Running diagnostics...").start();
        const results = await runChecks();
        spin.stop();

        // Display results
        let hasIssues = false;
        for (const check of results) {
            const icon = check.status === "pass" ? colors.success("✓") 
                       : check.status === "warn" ? colors.warning("⚠")
                       : colors.error("✗");
            
            console.log(`  ${icon} ${colors.primary(check.name)}: ${check.message}`);
            if (check.details) {
                console.log(`    ${colors.dim(check.details)}`);
            }
            
            if (check.status !== "pass") hasIssues = true;
        }

        console.log();
        console.log(divider(50));

        // If connection failed, try to find alternative
        const connectionCheck = results.find(r => r.name === "API Connection");
        if (connectionCheck?.status === "fail") {
            console.log();
            const searchSpin = spinner("Searching for available API endpoints...").start();
            const availableUrl = await findAvailableApi();
            
            if (availableUrl) {
                searchSpin.succeed(`Found available API: ${colors.success(availableUrl)}`);
                
                if (options.fix) {
                    setApiUrl(availableUrl);
                    success(`Configuration updated - API URL set to ${availableUrl}`);
                } else {
                    console.log();
                    const shouldFix = await confirm({
                        message: `Switch to ${availableUrl}?`,
                        default: true,
                    });
                    
                    if (shouldFix) {
                        setApiUrl(availableUrl);
                        success(`Configuration updated - API URL set to ${availableUrl}`);
                    }
                }
            } else {
                searchSpin.fail("No available API endpoints found");
                console.log();
                error("Cannot connect to any API. Make sure the AgentAuth server is running");
                console.log(`  ${colors.dim("Start local server:")} ${colors.muted("python -m uvicorn app.main:app")}`);
                console.log(`  ${colors.dim("Or deploy to:")} ${colors.muted("https://railway.app")}`);
            }
        } else if (!hasIssues) {
            console.log();
            success("All checks passed - AgentAuth CLI is ready to use");
        }
    });
