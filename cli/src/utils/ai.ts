/**
 * AI Provider - Real LLM integration for AgentAuth CLI
 * Supports: Ollama (local), OpenAI, Anthropic, Groq
 */
import fetch from "node-fetch";

export type AIProvider = "ollama" | "openai" | "anthropic" | "groq" | "simulation";

export interface AIConfig {
    provider: AIProvider;
    model?: string;
    apiKey?: string;
    baseUrl?: string;
}

export interface PurchaseAnalysis {
    decision: "buy" | "skip" | "defer";
    confidence: number;
    reasoning: string;
    alternatives?: string[];
}

interface ChatMessage {
    role: "system" | "user" | "assistant";
    content: string;
}

// Default models for each provider
const DEFAULT_MODELS: Record<AIProvider, string> = {
    ollama: "llama3.2",
    openai: "gpt-4o-mini",
    anthropic: "claude-3-haiku-20240307",
    groq: "llama-3.1-8b-instant",
    simulation: "rule-based",
};

// Get config from environment
export function getAIConfig(): AIConfig {
    const provider = (process.env.AGENTAUTH_AI_PROVIDER || "simulation") as AIProvider;
    
    return {
        provider,
        model: process.env.AGENTAUTH_AI_MODEL || DEFAULT_MODELS[provider],
        apiKey: process.env.OPENAI_API_KEY || 
                process.env.ANTHROPIC_API_KEY || 
                process.env.GROQ_API_KEY,
        baseUrl: process.env.OLLAMA_HOST || "http://localhost:11434",
    };
}

// System prompt for purchase analysis
const SYSTEM_PROMPT = `You are an AI shopping assistant helping users make smart purchasing decisions.

Analyze each purchase request and respond with a JSON object:
{
    "decision": "buy" or "skip" or "defer",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation (1-2 sentences)"
}

Consider:
- User's budget constraints
- Value for money
- Whether it's in a preferred category
- Past spending patterns

Be concise. Respond ONLY with the JSON object, no other text.`;

// Call Ollama (local)
async function callOllama(
    prompt: string,
    config: AIConfig
): Promise<string> {
    const response = await fetch(`${config.baseUrl}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            model: config.model || "llama3.2",
            prompt: prompt,
            system: SYSTEM_PROMPT,
            stream: false,
        }),
    });
    
    if (!response.ok) {
        throw new Error(`Ollama error: ${response.status}`);
    }
    
    const data = await response.json() as { response: string };
    return data.response;
}

// Call OpenAI
async function callOpenAI(
    prompt: string,
    config: AIConfig
): Promise<string> {
    const messages: ChatMessage[] = [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: prompt },
    ];
    
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${config.apiKey}`,
        },
        body: JSON.stringify({
            model: config.model || "gpt-4o-mini",
            messages,
            temperature: 0.3,
            max_tokens: 200,
        }),
    });
    
    if (!response.ok) {
        const err = await response.text();
        throw new Error(`OpenAI error: ${response.status} - ${err}`);
    }
    
    const data = await response.json() as { 
        choices: Array<{ message: { content: string } }> 
    };
    return data.choices[0].message.content;
}

// Call Anthropic
async function callAnthropic(
    prompt: string,
    config: AIConfig
): Promise<string> {
    const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": config.apiKey!,
            "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify({
            model: config.model || "claude-3-haiku-20240307",
            max_tokens: 200,
            system: SYSTEM_PROMPT,
            messages: [{ role: "user", content: prompt }],
        }),
    });
    
    if (!response.ok) {
        const err = await response.text();
        throw new Error(`Anthropic error: ${response.status} - ${err}`);
    }
    
    const data = await response.json() as { 
        content: Array<{ text: string }> 
    };
    return data.content[0].text;
}

// Call Groq
async function callGroq(
    prompt: string,
    config: AIConfig
): Promise<string> {
    const messages: ChatMessage[] = [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: prompt },
    ];
    
    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${config.apiKey}`,
        },
        body: JSON.stringify({
            model: config.model || "llama-3.1-8b-instant",
            messages,
            temperature: 0.3,
            max_tokens: 200,
        }),
    });
    
    if (!response.ok) {
        const err = await response.text();
        throw new Error(`Groq error: ${response.status} - ${err}`);
    }
    
    const data = await response.json() as { 
        choices: Array<{ message: { content: string } }> 
    };
    return data.choices[0].message.content;
}

// Main AI call function
export async function callAI(
    prompt: string,
    config?: AIConfig
): Promise<string> {
    const cfg = config || getAIConfig();
    
    switch (cfg.provider) {
        case "ollama":
            return callOllama(prompt, cfg);
        case "openai":
            if (!cfg.apiKey) throw new Error("OPENAI_API_KEY not set");
            return callOpenAI(prompt, cfg);
        case "anthropic":
            if (!cfg.apiKey) throw new Error("ANTHROPIC_API_KEY not set");
            return callAnthropic(prompt, cfg);
        case "groq":
            if (!cfg.apiKey) throw new Error("GROQ_API_KEY not set");
            return callGroq(prompt, cfg);
        default:
            throw new Error("Simulation mode - use rule-based logic");
    }
}

// Analyze a purchase using AI
export async function analyzeWithAI(
    item: string,
    merchant: string,
    amount: number,
    category: string,
    context: {
        budget: number;
        spent: number;
        maxSinglePurchase: number;
        preferredCategories: string[];
        transactionCount: number;
    }
): Promise<PurchaseAnalysis> {
    const prompt = `Analyze this purchase:

Item: ${item}
Merchant: ${merchant}
Price: $${amount.toFixed(2)}
Category: ${category}

User Context:
- Daily budget: $${context.budget.toFixed(2)}
- Already spent: $${context.spent.toFixed(2)}
- Remaining: $${(context.budget - context.spent).toFixed(2)}
- Per-transaction limit: $${context.maxSinglePurchase.toFixed(2)}
- Preferred categories: ${context.preferredCategories.join(", ")}
- Transactions today: ${context.transactionCount}

Should the user buy this item?`;

    try {
        const response = await callAI(prompt);
        
        // Parse JSON from response
        const jsonMatch = response.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            const parsed = JSON.parse(jsonMatch[0]);
            return {
                decision: parsed.decision || "skip",
                confidence: parsed.confidence || 0.5,
                reasoning: parsed.reasoning || "AI analysis",
                alternatives: parsed.alternatives,
            };
        }
        
        // Fallback parsing
        const decision = response.toLowerCase().includes("buy") ? "buy" : "skip";
        return {
            decision,
            confidence: 0.6,
            reasoning: response.slice(0, 100),
        };
    } catch (error) {
        // Return error indicator - caller should fall back to rule-based
        throw error;
    }
}

// Check if AI is available
export async function checkAIAvailability(): Promise<{
    available: boolean;
    provider: AIProvider;
    model: string;
    error?: string;
}> {
    const config = getAIConfig();
    
    if (config.provider === "simulation") {
        return {
            available: true,
            provider: "simulation",
            model: "rule-based",
        };
    }
    
    try {
        // Quick test call
        if (config.provider === "ollama") {
            const response = await fetch(`${config.baseUrl}/api/tags`, {
                method: "GET",
                signal: AbortSignal.timeout(3000),
            });
            if (!response.ok) throw new Error("Ollama not responding");
        } else {
            // For cloud providers, just check if API key exists
            if (!config.apiKey) {
                throw new Error(`${config.provider.toUpperCase()}_API_KEY not set`);
            }
        }
        
        return {
            available: true,
            provider: config.provider,
            model: config.model || DEFAULT_MODELS[config.provider],
        };
    } catch (error) {
        return {
            available: false,
            provider: config.provider,
            model: config.model || DEFAULT_MODELS[config.provider],
            error: error instanceof Error ? error.message : "Unknown error",
        };
    }
}
