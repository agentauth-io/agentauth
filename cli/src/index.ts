#!/usr/bin/env node
/**
 * AgentAuth CLI - Professional Command Line Interface
 * Authorization Infrastructure for AI Agents
 */
import "dotenv/config";
import { Command } from "commander";
import chalk from "chalk";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import {
    loginCommand,
    logoutCommand,
    statusCommand,
    authorizeCommand,
    agentsCommand,
    policiesCommand,
    consentsCommand,
    logsCommand,
    keysCommand,
    testCommand,
    dashboardCommand,
    doctorCommand,
    agentCommand,
} from "./commands/index.js";
import { setDefaultFormat, setApiUrl, getConfig } from "./utils/config.js";
import { 
    banner, 
    colors, 
    icons, 
    header, 
    keyValue, 
    commandHelp,
    success,
    hint,
    divider,
} from "./utils/ui.js";

// Get package.json for version
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

let version = "0.1.0";
try {
    const pkg = JSON.parse(readFileSync(join(__dirname, "..", "package.json"), "utf-8"));
    version = pkg.version;
} catch {
    // Use default version
}

const program = new Command();

// Custom help formatting
const formatHelp = () => {
    const config = getConfig();
    const isAuthenticated = !!config.apiKey;
    const isEnvAuth = !!process.env.AGENTAUTH_API_KEY;
    
    console.log(banner());
    
    // Status bar
    let statusLine: string;
    if (isAuthenticated) {
        const authSource = isEnvAuth ? colors.muted("(env)") : "";
        statusLine = `${icons.active} ${colors.success("Authenticated")} ${authSource} ${colors.dim("│")} ${colors.dim(config.apiUrl)}`;
    } else {
        statusLine = `${icons.inactive} ${colors.muted("Not authenticated")} ${colors.dim("│ Run")} ${colors.primary("agentauth login")} ${colors.dim("to get started")}`;
    }
    
    console.log(`  ${statusLine}\n`);
    console.log(divider(60));
    
    // Commands section
    console.log(header("Commands"));
    
    console.log(colors.dim("  Authentication"));
    console.log(commandHelp([
        { name: "login", description: "Authenticate with your API key" },
        { name: "logout", description: "Clear stored credentials" },
        { name: "status", description: "Check connection and account status" },
    ]));
    
    console.log(`\n${colors.dim("  Agent Management")}`);
    console.log(commandHelp([
        { name: "agents", description: "Manage registered AI agents" },
        { name: "agent", description: "Run interactive AI shopping agent" },
        { name: "authorize", description: "Create and verify authorizations" },
        { name: "consents", description: "View and manage user consents" },
        { name: "policies", description: "Configure spending policies and rules" },
    ]));
    
    console.log(`\n${colors.dim("  Monitoring")}`);
    console.log(commandHelp([
        { name: "logs", description: "View real-time audit logs" },
        { name: "dashboard", description: "Open the web dashboard" },
        { name: "test", description: "Run integration diagnostics" },
    ]));
    
    console.log(`\n${colors.dim("  Configuration")}`);
    console.log(commandHelp([
        { name: "config", description: "View or modify CLI settings" },
        { name: "keys", description: "Manage API keys" },
        { name: "doctor", description: "Diagnose connection issues" },
    ]));
    
    // Quick start
    console.log(header("Quick Start"));
    console.log(colors.dim("  # Authenticate with your API key"));
    console.log(`  ${colors.accent("$")} agentauth login\n`);
    console.log(colors.dim("  # Check your connection status"));
    console.log(`  ${colors.accent("$")} agentauth status\n`);
    console.log(colors.dim("  # List active consents"));
    console.log(`  ${colors.accent("$")} agentauth consents list\n`);
    
    // Footer
    console.log(divider(60));
    console.log(`\n  ${colors.dim("Documentation:")} ${colors.accent("https://docs.agentauth.in")}`);
    console.log(`  ${colors.dim("Support:")}       ${colors.accent("support@agentauth.in")}`);
    console.log(`  ${colors.dim("Version:")}       ${colors.muted(version)}\n`);
};

program
    .name("agentauth")
    .description("Authorization Infrastructure for AI Agents")
    .version(version, "-v, --version", "Show version number")
    .option("-q, --quiet", "Suppress banner and decorative output")
    .option("--api-url <url>", "Override API URL")
    .option("--format <format>", "Output format (table, json, yaml)")
    .option("--no-color", "Disable colored output")
    .helpOption("-h, --help", "Show help")
    .addHelpCommand("help [command]", "Show help for a command")
    .configureHelp({
        sortSubcommands: false,
        sortOptions: false,
    })
    .hook("preAction", (thisCommand) => {
        const opts = thisCommand.opts();
        if (opts.apiUrl) {
            setApiUrl(opts.apiUrl);
        }
        if (opts.format) {
            setDefaultFormat(opts.format as "table" | "json" | "yaml");
        }
        if (opts.noColor) {
            chalk.level = 0;
        }
    });

// Override the default help
program.helpInformation = () => "";
program.on("--help", formatHelp);

// Add all commands
program.addCommand(loginCommand);
program.addCommand(logoutCommand);
program.addCommand(statusCommand);
program.addCommand(authorizeCommand);
program.addCommand(agentsCommand);
program.addCommand(policiesCommand);
program.addCommand(consentsCommand);
program.addCommand(logsCommand);
program.addCommand(keysCommand);
program.addCommand(testCommand);
program.addCommand(dashboardCommand);
program.addCommand(doctorCommand);
program.addCommand(agentCommand);

// Config command for managing CLI settings
program
    .command("config")
    .description("View or modify CLI configuration")
    .option("--api-url <url>", "Set API URL")
    .option("--format <format>", "Set default output format")
    .option("--show", "Show current configuration")
    .option("--reset", "Reset to default configuration")
    .action(async (options) => {
        const config = getConfig();
        
        if (options.reset) {
            setApiUrl("https://api.agentauth.in");
            setDefaultFormat("table");
            success("Configuration reset to defaults");
            return;
        }
        
        if (options.apiUrl) {
            setApiUrl(options.apiUrl);
            success(`API URL set to ${options.apiUrl}`);
        }
        
        if (options.format) {
            setDefaultFormat(options.format);
            success(`Output format set to ${options.format}`);
        }
        
        if (options.show || (!options.apiUrl && !options.format && !options.reset)) {
            console.log(header("Configuration"));
            console.log(keyValue([
                ["API URL", config.apiUrl],
                ["Output Format", config.defaultFormat],
                ["Authenticated", !!config.apiKey],
            ]));
            
            if (config.apiKey) {
                const masked = config.apiKey.substring(0, 8) + "•".repeat(20) + config.apiKey.slice(-4);
                console.log(`\n${colors.dim("  API Key")}       ${colors.muted(masked)}`);
            }
            
            console.log(`\n${divider(40)}`);
            hint("Use --api-url or --format to change settings");
        }
    });

// Parse arguments
const args = process.argv;

// Custom handling for no arguments or help
if (args.length <= 2) {
    formatHelp();
    process.exit(0);
}

// Handle --help flag
if (args.includes("--help") || args.includes("-h")) {
    if (args.length === 3) {
        formatHelp();
        process.exit(0);
    }
}

program.parse();
