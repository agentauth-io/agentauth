// Agent command - Interactive AI Shopping Agent for AgentAuth
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
    warning,
    info,
    table,
    formatCurrency,
} from "../utils/ui.js";
import { analyzeWithAI, checkAIAvailability, getAIConfig, AIProvider } from "../utils/ai.js";
import { input, select, confirm } from "@inquirer/prompts";

// Agent session state
interface AgentSession {
    agentId: string;
    userId: string;
    budget: number;
    spent: number;
    transactions: Transaction[];
    preferences: {
        maxSinglePurchase: number;
        blockedCategories: string[];
        preferredCategories: string[];
    };
    ai: {
        provider: AIProvider;
        model: string;
        useRealAI: boolean;
    };
}

interface Transaction {
    id: string;
    merchant: string;
    amount: number;
    item: string;
    status: "approved" | "denied" | "pending";
    reason?: string;
    timestamp: Date;
}

interface AuthorizationResponse {
    authorized: boolean;
    authorization_id?: string;
    token?: string;
    risk_score?: number;
    reason?: string;
    details?: Record<string, unknown>;
}

// Product catalog for demo
const DEMO_PRODUCTS = [
    { merchant: "Amazon", item: "Wireless Headphones Pro", amount: 79.99, category: "electronics" },
    { merchant: "Apple Store", item: "AirPods Pro 2", amount: 249.00, category: "electronics" },
    { merchant: "Uber", item: "Ride to Airport", amount: 34.50, category: "transportation" },
    { merchant: "Netflix", item: "Monthly Subscription", amount: 15.99, category: "entertainment" },
    { merchant: "Whole Foods", item: "Weekly Groceries", amount: 142.87, category: "groceries" },
    { merchant: "Best Buy", item: "4K Gaming Monitor", amount: 399.99, category: "electronics" },
    { merchant: "Spotify", item: "Premium Annual", amount: 99.00, category: "entertainment" },
    { merchant: "Instacart", item: "Grocery Delivery", amount: 67.32, category: "groceries" },
    { merchant: "Steam", item: "Cyberpunk 2077", amount: 59.99, category: "gaming" },
    { merchant: "DoorDash", item: "Dinner Delivery", amount: 28.45, category: "food" },
];

// AI decision logic - uses real AI or falls back to rules
async function aiAnalyzePurchase(
    product: typeof DEMO_PRODUCTS[0],
    session: AgentSession
): Promise<{ decision: "buy" | "skip"; reasoning: string; confidence: number }> {
    const remainingBudget = session.budget - session.spent;
    
    // Hard constraints - always check these first
    if (product.amount > remainingBudget) {
        return {
            decision: "skip",
            reasoning: `Would exceed remaining budget of ${formatCurrency(remainingBudget)}`,
            confidence: 0.95,
        };
    }
    
    if (product.amount > session.preferences.maxSinglePurchase) {
        return {
            decision: "skip",
            reasoning: `Exceeds per-transaction limit of ${formatCurrency(session.preferences.maxSinglePurchase)}`,
            confidence: 0.9,
        };
    }
    
    if (session.preferences.blockedCategories.includes(product.category)) {
        return {
            decision: "skip",
            reasoning: `Category '${product.category}' is blocked by user preferences`,
            confidence: 0.95,
        };
    }
    
    // Try real AI if enabled
    if (session.ai.useRealAI) {
        try {
            const result = await analyzeWithAI(
                product.item,
                product.merchant,
                product.amount,
                product.category,
                {
                    budget: session.budget,
                    spent: session.spent,
                    maxSinglePurchase: session.preferences.maxSinglePurchase,
                    preferredCategories: session.preferences.preferredCategories,
                    transactionCount: session.transactions.length,
                }
            );
            return {
                decision: result.decision === "defer" ? "skip" : result.decision,
                reasoning: result.reasoning,
                confidence: result.confidence,
            };
        } catch {
            // Fall through to rule-based
        }
    }
    
    // Rule-based fallback
    const isPreferred = session.preferences.preferredCategories.includes(product.category);
    
    // Value-based decision
    if (product.amount < 50) {
        return {
            decision: "buy",
            reasoning: "Small purchase within budget - good value",
            confidence: 0.85,
        };
    }
    
    if (product.amount < 100 && isPreferred) {
        return {
            decision: "buy",
            reasoning: `Good value in preferred category (${product.category})`,
            confidence: 0.8,
        };
    }
    
    if (product.amount < 200) {
        return {
            decision: "buy",
            reasoning: "Moderate purchase - proceed with standard authorization",
            confidence: 0.7,
        };
    }
    
    return {
        decision: Math.random() > 0.4 ? "buy" : "skip",
        reasoning: "Large purchase - recommending careful consideration",
        confidence: 0.55,
    };
}

// Request authorization from backend
async function requestAuthorization(
    product: typeof DEMO_PRODUCTS[0],
    session: AgentSession
): Promise<AuthorizationResponse> {
    const result = await apiRequest<AuthorizationResponse>("/v1/authorize", {
        method: "POST",
        body: {
            agent_id: session.agentId,
            user_id: session.userId,
            action: "payment",
            merchant: product.merchant,
            amount: product.amount,
            currency: "USD",
            category: product.category,
            metadata: {
                item: product.item,
                source: "cli_agent",
            },
        },
    });
    
    if (result.success && result.data) {
        return result.data;
    }
    
    // Fallback simulation if API fails
    return simulateAuthorization(product, session);
}

// Simulate authorization for demo
function simulateAuthorization(
    product: typeof DEMO_PRODUCTS[0],
    session: AgentSession
): AuthorizationResponse {
    // Check constraints
    if (product.amount > session.preferences.maxSinglePurchase) {
        return {
            authorized: false,
            reason: `Exceeds limit of ${formatCurrency(session.preferences.maxSinglePurchase)}`,
            risk_score: 0.8,
        };
    }
    
    if (session.spent + product.amount > session.budget) {
        return {
            authorized: false,
            reason: `Would exceed daily budget of ${formatCurrency(session.budget)}`,
            risk_score: 0.7,
        };
    }
    
    // Calculate risk
    let riskScore = 0.1;
    if (product.amount > 100) riskScore += 0.1;
    if (product.amount > 200) riskScore += 0.15;
    if (session.transactions.length > 5) riskScore += 0.05;
    
    return {
        authorized: true,
        authorization_id: `auth_${Date.now().toString(36)}`,
        token: `aa_tx_${Math.random().toString(36).substring(2, 18)}`,
        risk_score: Math.min(riskScore, 1),
        reason: "Authorized by AgentAuth",
    };
}

export const agentCommand = new Command("agent")
    .description("Run an interactive AI shopping agent demo")
    .option("--budget <amount>", "Daily budget in USD", "500")
    .option("--limit <amount>", "Max single purchase", "200")
    .option("--auto", "Run automatic shopping session")
    .option("--ai <provider>", "AI provider: ollama, openai, anthropic, groq", "")
    .action(async (options) => {
        const config = getConfig();
        
        // Check connection
        const connected = await checkConnection();
        if (!connected) {
            warning("Backend not connected - running in simulation mode");
        }
        
        // Check AI availability
        const aiStatus = await checkAIAvailability();
        const aiConfig = getAIConfig();
        
        // Override provider if specified
        let useRealAI = aiStatus.available && aiStatus.provider !== "simulation";
        let aiProvider = aiStatus.provider;
        let aiModel = aiStatus.model;
        
        if (options.ai) {
            aiProvider = options.ai as AIProvider;
            useRealAI = true;
        }
        
        console.log(box(
            `${colors.gradient("AgentAuth AI Shopping Agent")}\n\n` +
            `${colors.dim("An AI agent that can make purchases on your behalf,")}\n` +
            `${colors.dim("with AgentAuth providing authorization and controls.")}`,
            { padding: 1 }
        ));
        
        // Initialize session
        const session: AgentSession = {
            agentId: `agent_${Date.now().toString(36)}`,
            userId: config.apiKey ? `user_${config.apiKey.substring(0, 8)}` : "demo_user",
            budget: parseFloat(options.budget),
            spent: 0,
            transactions: [],
            preferences: {
                maxSinglePurchase: parseFloat(options.limit),
                blockedCategories: ["gambling", "adult"],
                preferredCategories: ["groceries", "electronics", "entertainment"],
            },
            ai: {
                provider: aiProvider,
                model: aiModel,
                useRealAI,
            },
        };
        
        console.log(header("Session Started"));
        console.log(keyValue([
            ["Agent ID", session.agentId],
            ["User ID", session.userId],
            ["Daily Budget", formatCurrency(session.budget)],
            ["Per-Transaction Limit", formatCurrency(session.preferences.maxSinglePurchase)],
            ["Backend", connected ? "Live (API Connected)" : "Simulation"],
            ["AI Provider", useRealAI ? `${aiProvider} (${aiModel})` : "Rule-based"],
        ]));
        
        if (!useRealAI && aiStatus.error) {
            console.log(colors.dim(`  AI unavailable: ${aiStatus.error}`));
        }
        
        if (options.auto) {
            // Automatic shopping session
            await runAutoSession(session, connected);
        } else {
            // Interactive mode
            await runInteractiveSession(session, connected);
        }
    });

async function runInteractiveSession(session: AgentSession, connected: boolean) {
    let running = true;
    
    while (running) {
        console.log(`\n${divider(50)}`);
        console.log(`  ${colors.dim("Budget:")} ${colors.success(formatCurrency(session.budget - session.spent))} remaining`);
        console.log(`  ${colors.dim("Transactions:")} ${session.transactions.length} completed`);
        console.log();
        
        const action = await select({
            message: "What would you like to do?",
            choices: [
                { name: "[1] Browse products and buy", value: "browse" },
                { name: "[2] Command the agent (natural language)", value: "command" },
                { name: "[3] View transaction history", value: "history" },
                { name: "[4] Adjust preferences", value: "settings" },
                { name: "[0] Exit", value: "exit" },
            ],
        });
        
        switch (action) {
            case "browse":
                await browseAndBuy(session, connected);
                break;
            case "command":
                await processCommand(session, connected);
                break;
            case "history":
                showHistory(session);
                break;
            case "settings":
                await adjustSettings(session);
                break;
            case "exit":
                running = false;
                break;
        }
    }
    
    // Final summary
    showSummary(session);
}

async function browseAndBuy(session: AgentSession, connected: boolean) {
    const productChoices = DEMO_PRODUCTS.map((p, i) => ({
        name: `${p.item} (${p.merchant}) - ${formatCurrency(p.amount)}`,
        value: i,
    }));
    productChoices.push({ name: "← Back", value: -1 });
    
    const selection = await select({
        message: "Select a product:",
        choices: productChoices,
    });
    
    if (selection === -1) return;
    
    const product = DEMO_PRODUCTS[selection];
    await executePurchase(product, session, connected);
}

async function processCommand(session: AgentSession, connected: boolean) {
    const command = await input({
        message: "Tell the agent what to buy:",
        default: "Buy me some headphones under $100",
    });
    
    console.log();
    const spin = spinner("AI Agent processing your request...").start();
    await new Promise(r => setTimeout(r, 1000));
    spin.stop();
    
    // Parse command (simple keyword matching for demo)
    const lowerCmd = command.toLowerCase();
    let matchedProducts = DEMO_PRODUCTS.filter(p => {
        const terms = [p.item.toLowerCase(), p.category, p.merchant.toLowerCase()];
        return terms.some(t => lowerCmd.includes(t.split(" ")[0])) ||
               lowerCmd.includes("anything") ||
               lowerCmd.includes("something");
    });
    
    // Check for price constraints
    const priceMatch = lowerCmd.match(/under \$?(\d+)/);
    if (priceMatch) {
        const maxPrice = parseFloat(priceMatch[1]);
        matchedProducts = matchedProducts.filter(p => p.amount <= maxPrice);
    }
    
    if (matchedProducts.length === 0) {
        info(`I couldn't find products matching "${command}". Try browsing instead.`);
        return;
    }
    
    // Pick best match (or first one)
    const product = matchedProducts[0];
    console.log(`\n${icons.lightning} ${colors.primary("Agent:")} I found ${colors.accent(product.item)} ` +
                `from ${product.merchant} for ${formatCurrency(product.amount)}`);
    
    const shouldBuy = await confirm({
        message: "Proceed with purchase?",
        default: true,
    });
    
    if (shouldBuy) {
        await executePurchase(product, session, connected);
    }
}

async function executePurchase(
    product: typeof DEMO_PRODUCTS[0],
    session: AgentSession,
    connected: boolean
) {
    console.log();
    console.log(box(
        `${colors.primary("Purchase Request")}\n\n` +
        `${colors.dim("Item:")} ${product.item}\n` +
        `${colors.dim("Merchant:")} ${product.merchant}\n` +
        `${colors.dim("Amount:")} ${formatCurrency(product.amount)}\n` +
        `${colors.dim("Category:")} ${product.category}`,
        { padding: 1 }
    ));
    
    // Step 1: AI Analysis
    const analysisSpin = spinner("AI analyzing purchase decision...").start();
    const analysis = await aiAnalyzePurchase(product, session);
    analysisSpin.stop();
    
    console.log(`\n${icons.lightning} ${colors.primary("AI Decision:")} ${analysis.decision.toUpperCase()}`);
    console.log(`  ${colors.dim("Confidence:")} ${(analysis.confidence * 100).toFixed(0)}%`);
    console.log(`  ${colors.dim("Reasoning:")} ${analysis.reasoning}`);
    
    if (analysis.decision === "skip") {
        warning("AI recommends skipping this purchase");
        
        const override = await confirm({
            message: "Override AI decision and proceed anyway?",
            default: false,
        });
        
        if (!override) {
            session.transactions.push({
                id: `tx_${Date.now().toString(36)}`,
                merchant: product.merchant,
                amount: product.amount,
                item: product.item,
                status: "denied",
                reason: `AI recommendation: ${analysis.reasoning}`,
                timestamp: new Date(),
            });
            return;
        }
    }
    
    // Step 2: AgentAuth Authorization
    console.log();
    const authSpin = spinner("Requesting AgentAuth authorization...").start();
    await new Promise(r => setTimeout(r, 600));
    const authResult = await requestAuthorization(product, session);
    authSpin.stop();
    
    if (!authResult.authorized) {
        console.log(`\n${statusBadge("denied")} ${colors.error("Authorization Denied")}`);
        console.log(`  ${colors.dim("Reason:")} ${authResult.reason}`);
        if (authResult.risk_score !== undefined) {
            console.log(`  ${colors.dim("Risk Score:")} ${(authResult.risk_score * 100).toFixed(0)}%`);
        }
        
        session.transactions.push({
            id: `tx_${Date.now().toString(36)}`,
            merchant: product.merchant,
            amount: product.amount,
            item: product.item,
            status: "denied",
            reason: authResult.reason,
            timestamp: new Date(),
        });
        return;
    }
    
    // Step 3: Execute Transaction
    console.log(`\n${statusBadge("approved")} ${colors.success("Authorization Approved")}`);
    if (authResult.risk_score !== undefined) {
        console.log(`  ${colors.dim("Risk Score:")} ${(authResult.risk_score * 100).toFixed(0)}%`);
    }
    console.log(`  ${colors.dim("Token:")} ${authResult.token?.substring(0, 20)}...`);
    
    const execSpin = spinner("Processing payment...").start();
    await new Promise(r => setTimeout(r, 500));
    execSpin.succeed(colors.success("Payment completed!"));
    
    // Update session
    session.spent += product.amount;
    session.transactions.push({
        id: authResult.authorization_id || `tx_${Date.now().toString(36)}`,
        merchant: product.merchant,
        amount: product.amount,
        item: product.item,
        status: "approved",
        timestamp: new Date(),
    });
    
    success(`Purchased ${product.item} for ${formatCurrency(product.amount)}`);
    console.log(`  ${colors.dim("Remaining budget:")} ${formatCurrency(session.budget - session.spent)}`);
}

function showHistory(session: AgentSession) {
    console.log(header("Transaction History"));
    
    if (session.transactions.length === 0) {
        console.log(colors.dim("  No transactions yet"));
        return;
    }
    
    const data = session.transactions.map(tx => ({
        status: tx.status === "approved" ? colors.success("✓") : colors.error("✗"),
        item: tx.item.substring(0, 25),
        merchant: tx.merchant,
        amount: formatCurrency(tx.amount),
    }));
    
    console.log(table(data, [
        { key: "status", header: "", width: 2 },
        { key: "item", header: "Item", width: 25 },
        { key: "merchant", header: "Merchant", width: 15 },
        { key: "amount", header: "Amount", width: 10, align: "right" },
    ]));
}

async function adjustSettings(session: AgentSession) {
    const setting = await select({
        message: "Which setting to adjust?",
        choices: [
            { name: `Daily Budget (currently ${formatCurrency(session.budget)})`, value: "budget" },
            { name: `Per-Transaction Limit (currently ${formatCurrency(session.preferences.maxSinglePurchase)})`, value: "limit" },
            { name: "← Back", value: "back" },
        ],
    });
    
    if (setting === "back") return;
    
    const newValue = await input({
        message: `Enter new ${setting === "budget" ? "budget" : "limit"}:`,
        default: setting === "budget" 
            ? session.budget.toString() 
            : session.preferences.maxSinglePurchase.toString(),
    });
    
    const parsed = parseFloat(newValue);
    if (!isNaN(parsed)) {
        if (setting === "budget") {
            session.budget = parsed;
        } else {
            session.preferences.maxSinglePurchase = parsed;
        }
        success(`Updated ${setting} to ${formatCurrency(parsed)}`);
    }
}

async function runAutoSession(session: AgentSession, connected: boolean) {
    console.log(header("Automatic Shopping Session"));
    console.log(colors.dim("  The AI agent will process the entire catalog...\n"));
    
    for (const product of DEMO_PRODUCTS) {
        if (session.spent >= session.budget) {
            warning("Budget exhausted - stopping session");
            break;
        }
        
        await executePurchase(product, session, connected);
        await new Promise(r => setTimeout(r, 500));
    }
    
    showSummary(session);
}

function showSummary(session: AgentSession) {
    const approved = session.transactions.filter(t => t.status === "approved").length;
    const denied = session.transactions.filter(t => t.status === "denied").length;
    
    console.log(header("Session Summary"));
    console.log(keyValue([
        ["Total Transactions", session.transactions.length.toString()],
        ["Approved", approved.toString()],
        ["Denied", denied.toString()],
        ["Total Spent", formatCurrency(session.spent)],
        ["Budget Remaining", formatCurrency(session.budget - session.spent)],
    ]));
    
    console.log(`\n${colors.dim("Thank you for using AgentAuth AI Agent!")}\n`);
}
