// Login command - Professional UI
import { Command } from "commander";
import { confirm, password } from "@inquirer/prompts";
import { setApiKey, setApiUrl, getApiUrl } from "../utils/config.js";
import { checkConnection } from "../utils/api.js";
import { 
    colors, 
    icons, 
    spinner, 
    header,
    success, 
    error, 
    info, 
    hint,
    divider,
    box,
} from "../utils/ui.js";

export const loginCommand = new Command("login")
    .description("Authenticate with AgentAuth API")
    .option("-k, --api-key <key>", "API key to use")
    .option("-u, --api-url <url>", "API URL (default: https://api.agentauth.in)")
    .action(async (options) => {
        console.log(header("Authentication"));
        
        let apiKey = options.apiKey;
        const apiUrl = options.apiUrl;

        if (apiUrl) {
            setApiUrl(apiUrl);
            console.log(`  ${colors.dim("API URL:")} ${colors.accent(apiUrl)}\n`);
        }

        if (!apiKey) {
            console.log(`  ${colors.dim("Enter your API key to authenticate.")}`);
            console.log(`  ${colors.dim("Get your key at")} ${colors.accent("https://app.agentauth.in/keys")}\n`);
            
            apiKey = await password({
                message: colors.primary("API Key"),
                mask: "•",
                validate: (val: string) => {
                    if (val.length === 0) return "API key is required";
                    if (!val.startsWith("aa_")) return "API key should start with 'aa_'";
                    return true;
                },
            });
        }

        console.log();
        const spin = spinner("Connecting to AgentAuth...").start();

        // Set the API key
        setApiKey(apiKey);

        const connected = await checkConnection();
        if (!connected) {
            spin.fail("Connection failed");
            error("Could not connect to AgentAuth API", `Make sure ${getApiUrl()} is reachable`);
            setApiKey("");
            return;
        }

        // API key format validation
        if (!apiKey.startsWith("aa_")) {
            spin.warn("Connected with non-standard key format");
            console.log(`  ${colors.warning("⚠")} ${colors.dim("Expected key format: aa_live_... or aa_test_...")}`);
        } else {
            spin.succeed("Connected successfully");
        }

        // Success display
        console.log();
        const keyType = apiKey.includes("_live_") ? "live" : apiKey.includes("_test_") ? "test" : "unknown";
        const maskedKey = apiKey.substring(0, 8) + "•".repeat(16) + apiKey.slice(-4);
        
        console.log(box([
            `${icons.check} ${colors.success("Authentication successful")}`,
            "",
            `${colors.dim("Key:")}  ${colors.muted(maskedKey)}`,
            `${colors.dim("Type:")} ${keyType === "live" ? colors.success("Live") : colors.warning("Test")}`,
            `${colors.dim("URL:")}  ${colors.muted(getApiUrl())}`,
        ], { title: "Authenticated", width: 50 }));
        
        console.log();
        hint("Run 'agentauth status' to verify your connection");
    });

export const logoutCommand = new Command("logout")
    .description("Clear stored API credentials")
    .option("-f, --force", "Skip confirmation prompt")
    .action(async (options) => {
        console.log(header("Logout"));
        
        if (!options.force) {
            const shouldLogout = await confirm({
                message: "Are you sure you want to logout?",
                default: false,
            });

            if (!shouldLogout) {
                info("Logout cancelled");
                return;
            }
        }

        setApiKey("");
        success("Logged out successfully");
        console.log(`  ${colors.dim("API credentials have been cleared.")}`);
    });
