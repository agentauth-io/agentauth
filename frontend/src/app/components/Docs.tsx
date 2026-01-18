import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
    Book,
    Code,
    Zap,
    Shield,
    CreditCard,
    Settings,
    Terminal,
    Copy,
    Check,
    ChevronRight,
    ExternalLink,
    Search,
    Menu,
    X,
    Play,
    FileCode,
    Key,
    Webhook,
    BarChart3,
    Users,
} from "lucide-react";

interface DocsProps {
    onBack?: () => void;
}

// Documentation sections
const DOCS_SECTIONS = [
    {
        id: "getting-started",
        title: "Getting Started",
        icon: Zap,
        items: [
            { id: "introduction", title: "Introduction" },
            { id: "quickstart", title: "Quick Start" },
            { id: "authentication", title: "Authentication" },
        ]
    },
    {
        id: "core-concepts",
        title: "Core Concepts",
        icon: Book,
        items: [
            { id: "consents", title: "Consents" },
            { id: "authorization", title: "Authorization" },
            { id: "verification", title: "Verification" },
        ]
    },
    {
        id: "api-reference",
        title: "API Reference",
        icon: Code,
        items: [
            { id: "consents-api", title: "Consents API" },
            { id: "authorize-api", title: "Authorize API" },
            { id: "verify-api", title: "Verify API" },
            { id: "limits-api", title: "Limits API" },
            { id: "rules-api", title: "Rules API" },
        ]
    },
    {
        id: "sdks",
        title: "SDKs & Integrations",
        icon: Terminal,
        items: [
            { id: "python-sdk", title: "Python SDK" },
            { id: "langchain", title: "LangChain" },
            { id: "crewai", title: "CrewAI" },
        ]
    },
    {
        id: "features",
        title: "Features",
        icon: Settings,
        items: [
            { id: "spending-limits", title: "Spending Limits" },
            { id: "merchant-rules", title: "Merchant Rules" },
            { id: "webhooks", title: "Webhooks" },
            { id: "analytics", title: "Analytics" },
        ]
    },
];

// Code examples
const CODE_EXAMPLES: Record<string, { language: string; code: string }[]> = {
    quickstart: [
        {
            language: "python",
            code: `from agentauth import AgentAuthClient

# Initialize the client
client = AgentAuthClient(api_key="your_api_key")

# Create a consent for the user
consent = client.create_consent(
    user_id="user_123",
    intent={"description": "Buy groceries under $50"},
    constraints={"max_amount": 50.0, "currency": "USD"}
)

# Use the delegation token for agent transactions
token = consent.delegation_token`
        },
        {
            language: "curl",
            code: `curl -X POST https://api.agentauth.dev/v1/consents \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "user_123",
    "intent": {"description": "Buy groceries under $50"},
    "constraints": {"max_amount": 50.0, "currency": "USD"}
  }'`
        }
    ],
    authorization: [
        {
            language: "python",
            code: `# Request authorization for a purchase
auth = client.authorize(
    delegation_token=token,
    action="payment",
    transaction={
        "amount": 25.99,
        "currency": "USD",
        "merchant_id": "grocery_store_123",
        "merchant_name": "Fresh Mart"
    }
)

if auth.decision == "ALLOW":
    print(f"Authorized! Code: {auth.authorization_code}")
elif auth.decision == "DENY":
    print(f"Denied: {auth.reason}")`
        }
    ],
    verification: [
        {
            language: "python",
            code: `# Merchant verifies the authorization code
result = client.verify(
    authorization_code="authz_abc123...",
    transaction={"amount": 25.99, "currency": "USD"},
    merchant_id="grocery_store_123"
)

if result.valid:
    print("✓ Authorization verified!")
    print(f"Transaction ID: {result.transaction_id}")
    # Process the payment...`
        }
    ],
    langchain: [
        {
            language: "python",
            code: `from agentauth.integrations.langchain import (
    AuthorizedPurchaseTool,
    CheckSpendingLimitsTool
)
from langchain.agents import AgentExecutor

# Create AgentAuth tools
purchase_tool = AuthorizedPurchaseTool(
    client=client,
    delegation_token=token
)

limits_tool = CheckSpendingLimitsTool(client=client)

# Add to your LangChain agent
agent = AgentExecutor(
    tools=[purchase_tool, limits_tool],
    # ... your agent config
)`
        }
    ],
};

// Content for each section
const DOCS_CONTENT: Record<string, { title: string; description: string; content: React.ReactNode }> = {
    introduction: {
        title: "Introduction",
        description: "Learn what AgentAuth is and how it helps secure AI agent transactions.",
        content: (
            <div className="space-y-6">
                <p className="text-gray-300 text-lg leading-relaxed">
                    AgentAuth is the authorization layer for AI agent transactions. It sits between your AI agents
                    and payment providers, ensuring every transaction is authorized by the user within defined constraints.
                </p>

                <div className="grid md:grid-cols-3 gap-4 my-8">
                    <div className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-xl">
                        <Shield className="w-8 h-8 text-purple-400 mb-3" />
                        <h4 className="text-white font-semibold mb-2">User Control</h4>
                        <p className="text-gray-400 text-sm">Users set limits and rules for what their AI agents can purchase.</p>
                    </div>
                    <div className="p-4 bg-cyan-500/10 border border-cyan-500/20 rounded-xl">
                        <Zap className="w-8 h-8 text-cyan-400 mb-3" />
                        <h4 className="text-white font-semibold mb-2">Real-time Auth</h4>
                        <p className="text-gray-400 text-sm">Authorization decisions in milliseconds, not seconds.</p>
                    </div>
                    <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
                        <CreditCard className="w-8 h-8 text-green-400 mb-3" />
                        <h4 className="text-white font-semibold mb-2">Stripe Integration</h4>
                        <p className="text-gray-400 text-sm">Native integration with Stripe for payments.</p>
                    </div>
                </div>

                <h3 className="text-xl font-semibold text-white mt-8 mb-4">How It Works</h3>
                <ol className="space-y-4">
                    <li className="flex gap-4">
                        <span className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 font-bold flex-shrink-0">1</span>
                        <div>
                            <p className="text-white font-medium">User Creates Consent</p>
                            <p className="text-gray-400 text-sm">Define spending limits, allowed merchants, and transaction rules.</p>
                        </div>
                    </li>
                    <li className="flex gap-4">
                        <span className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 font-bold flex-shrink-0">2</span>
                        <div>
                            <p className="text-white font-medium">AI Agent Requests Authorization</p>
                            <p className="text-gray-400 text-sm">Agent sends transaction details to AgentAuth for approval.</p>
                        </div>
                    </li>
                    <li className="flex gap-4">
                        <span className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 font-bold flex-shrink-0">3</span>
                        <div>
                            <p className="text-white font-medium">AgentAuth Evaluates</p>
                            <p className="text-gray-400 text-sm">Checks against spending limits, merchant rules, and category filters.</p>
                        </div>
                    </li>
                    <li className="flex gap-4">
                        <span className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 font-bold flex-shrink-0">4</span>
                        <div>
                            <p className="text-white font-medium">Merchant Verifies</p>
                            <p className="text-gray-400 text-sm">Merchant confirms authorization code before processing payment.</p>
                        </div>
                    </li>
                </ol>
            </div>
        )
    },
    quickstart: {
        title: "Quick Start",
        description: "Get up and running with AgentAuth in under 5 minutes.",
        content: (
            <div className="space-y-8">
                {/* Time to first API call badge */}
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-full">
                    <Zap className="w-4 h-4 text-green-400" />
                    <span className="text-green-400 text-sm font-medium">Time to first API call: ~5 minutes</span>
                </div>

                {/* Step 1: Install */}
                <div className="p-6 bg-white/5 border border-white/10 rounded-xl">
                    <div className="flex items-center gap-3 mb-4">
                        <span className="w-8 h-8 rounded-full bg-purple-500/30 flex items-center justify-center text-purple-400 font-bold">1</span>
                        <h3 className="text-xl font-semibold text-white">Install the SDK</h3>
                        <span className="text-gray-500 text-sm">~30 seconds</span>
                    </div>
                    <div className="bg-[#0d0d12] rounded-lg p-4 font-mono text-sm">
                        <span className="text-gray-500">$</span> <span className="text-green-400">pip install agentauth</span>
                    </div>
                </div>

                {/* Step 2: Get API Key */}
                <div className="p-6 bg-white/5 border border-white/10 rounded-xl">
                    <div className="flex items-center gap-3 mb-4">
                        <span className="w-8 h-8 rounded-full bg-purple-500/30 flex items-center justify-center text-purple-400 font-bold">2</span>
                        <h3 className="text-xl font-semibold text-white">Get Your API Key</h3>
                        <span className="text-gray-500 text-sm">~1 minute</span>
                    </div>
                    <p className="text-gray-400 mb-3">Sign up at <a href="#" className="text-purple-400 hover:underline">agentauth.in</a> to get your API key.</p>
                    <div className="bg-[#0d0d12] rounded-lg p-4 font-mono text-sm">
                        <span className="text-gray-500"># Set your environment variable</span><br />
                        <span className="text-cyan-400">export</span> <span className="text-white">AGENTAUTH_API_KEY=</span><span className="text-yellow-400">"aa_live_..."</span>
                    </div>
                </div>

                {/* Step 3: Initialize */}
                <div className="p-6 bg-white/5 border border-white/10 rounded-xl">
                    <div className="flex items-center gap-3 mb-4">
                        <span className="w-8 h-8 rounded-full bg-purple-500/30 flex items-center justify-center text-purple-400 font-bold">3</span>
                        <h3 className="text-xl font-semibold text-white">Create a Consent</h3>
                        <span className="text-gray-500 text-sm">~2 minutes</span>
                    </div>
                    <p className="text-gray-400 mb-3">The user creates a consent with spending limits:</p>
                </div>

                {/* Step 4: Authorize */}
                <div className="p-6 bg-white/5 border border-white/10 rounded-xl">
                    <div className="flex items-center gap-3 mb-4">
                        <span className="w-8 h-8 rounded-full bg-purple-500/30 flex items-center justify-center text-purple-400 font-bold">4</span>
                        <h3 className="text-xl font-semibold text-white">Authorize a Transaction</h3>
                        <span className="text-gray-500 text-sm">~1 minute</span>
                    </div>
                    <p className="text-gray-400 mb-3">Your AI agent requests authorization before each purchase:</p>
                </div>

                {/* What's Next */}
                <div className="p-6 bg-gradient-to-r from-purple-500/10 to-cyan-500/10 border border-purple-500/20 rounded-xl">
                    <h3 className="text-lg font-semibold text-white mb-3">🎉 You're ready!</h3>
                    <p className="text-gray-400 mb-4">That's it! Your AI agent can now make authorized purchases within user-defined limits.</p>
                    <div className="flex flex-wrap gap-3">
                        <a href="#demo" className="px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg text-sm hover:bg-purple-500/30 transition-colors">
                            Try the Demo →
                        </a>
                        <a href="#" className="px-4 py-2 bg-white/10 text-white rounded-lg text-sm hover:bg-white/20 transition-colors">
                            View Full API Reference
                        </a>
                    </div>
                </div>
            </div>
        )
    },
    authentication: {
        title: "Authentication",
        description: "Learn how to authenticate with the AgentAuth API.",
        content: (
            <div className="space-y-6">
                <p className="text-gray-300">
                    AgentAuth uses API keys for authentication. You can get your API keys from the
                    <a href="#portal" className="text-purple-400 hover:text-purple-300 ml-1">Developer Portal</a>.
                </p>

                <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
                    <p className="text-yellow-400 font-medium">⚠️ Keep your API keys secure</p>
                    <p className="text-gray-400 text-sm mt-1">Never expose your secret API key in client-side code or public repositories.</p>
                </div>

                <h4 className="text-lg font-semibold text-white mt-6">Using API Keys</h4>
                <p className="text-gray-400 mb-4">Include your API key in the Authorization header:</p>
                <div className="bg-[#0d0d12] rounded-xl p-4 font-mono text-sm">
                    <span className="text-gray-500">Authorization:</span> <span className="text-green-400">Bearer YOUR_API_KEY</span>
                </div>
            </div>
        )
    },
};

function CodeBlock({ code, language }: { code: string; language: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="relative group">
            <div className="absolute top-3 right-3 flex items-center gap-2">
                <span className="text-xs text-gray-500 uppercase">{language}</span>
                <button
                    onClick={handleCopy}
                    className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                >
                    {copied ? (
                        <Check className="w-4 h-4 text-green-400" />
                    ) : (
                        <Copy className="w-4 h-4 text-gray-400" />
                    )}
                </button>
            </div>
            <pre className="bg-[#0d0d12] rounded-xl p-4 overflow-x-auto">
                <code className="text-sm text-gray-300 font-mono whitespace-pre">{code}</code>
            </pre>
        </div>
    );
}

export function Docs({ onBack }: DocsProps) {
    const [activeSection, setActiveSection] = useState("introduction");
    const [searchQuery, setSearchQuery] = useState("");
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [activeCodeTab, setActiveCodeTab] = useState(0);

    const currentContent = DOCS_CONTENT[activeSection];
    const currentExamples = CODE_EXAMPLES[activeSection];

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
            {/* Top Navigation */}
            <header className="sticky top-0 z-50 bg-[#0A0A0F]/80 backdrop-blur-xl border-b border-white/5">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        <button
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            className="lg:hidden p-2 hover:bg-white/5 rounded-lg"
                        >
                            {sidebarOpen ? <X className="w-5 h-5 text-white" /> : <Menu className="w-5 h-5 text-white" />}
                        </button>
                        <a href="#" className="text-xl font-bold text-white">AgentAuth</a>
                        <span className="text-gray-500">|</span>
                        <span className="text-gray-400">Documentation</span>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="relative hidden md:block">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                            <input
                                type="text"
                                placeholder="Search docs..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-64 pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-purple-500/50 text-sm"
                            />
                            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500 bg-white/5 px-1.5 py-0.5 rounded">⌘K</kbd>
                        </div>

                        <a href="#demo" className="px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg text-sm hover:bg-purple-500/30 transition-colors">
                            Try Demo
                        </a>

                        {onBack && (
                            <button
                                onClick={onBack}
                                className="text-gray-400 hover:text-white transition-colors text-sm"
                            >
                                ← Back
                            </button>
                        )}
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto flex">
                {/* Sidebar */}
                <aside className={`
                    fixed lg:sticky top-[73px] left-0 h-[calc(100vh-73px)] w-72 
                    bg-[#0A0A0F] lg:bg-transparent border-r border-white/5 
                    overflow-y-auto transition-transform z-40
                    ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
                `}>
                    <nav className="p-6 space-y-6">
                        {DOCS_SECTIONS.map((section) => (
                            <div key={section.id}>
                                <div className="flex items-center gap-2 text-gray-400 mb-3">
                                    <section.icon className="w-4 h-4" />
                                    <span className="text-xs font-semibold uppercase tracking-wider">{section.title}</span>
                                </div>
                                <ul className="space-y-1">
                                    {section.items.map((item) => (
                                        <li key={item.id}>
                                            <button
                                                onClick={() => {
                                                    setActiveSection(item.id);
                                                    setSidebarOpen(false);
                                                }}
                                                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${activeSection === item.id
                                                    ? "bg-purple-500/20 text-purple-400 font-medium"
                                                    : "text-gray-400 hover:text-white hover:bg-white/5"
                                                    }`}
                                            >
                                                {item.title}
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </nav>
                </aside>

                {/* Main Content */}
                <main className="flex-1 min-w-0 px-6 lg:px-12 py-12">
                    <motion.div
                        key={activeSection}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        {/* Breadcrumb */}
                        <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
                            <span>Docs</span>
                            <ChevronRight className="w-4 h-4" />
                            <span className="text-gray-300">{currentContent?.title || activeSection}</span>
                        </div>

                        {/* Title */}
                        <h1 className="text-4xl font-bold text-white mb-4">
                            {currentContent?.title || activeSection}
                        </h1>

                        {currentContent?.description && (
                            <p className="text-xl text-gray-400 mb-8">
                                {currentContent.description}
                            </p>
                        )}

                        {/* Content */}
                        {currentContent?.content && (
                            <div className="prose prose-invert max-w-none">
                                {currentContent.content}
                            </div>
                        )}

                        {/* Code Examples */}
                        {currentExamples && (
                            <div className="mt-8">
                                <div className="flex gap-2 mb-4">
                                    {currentExamples.map((example, index) => (
                                        <button
                                            key={index}
                                            onClick={() => setActiveCodeTab(index)}
                                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeCodeTab === index
                                                ? "bg-purple-500/20 text-purple-400"
                                                : "text-gray-400 hover:text-white hover:bg-white/5"
                                                }`}
                                        >
                                            {example.language.toUpperCase()}
                                        </button>
                                    ))}
                                </div>
                                <CodeBlock
                                    code={currentExamples[activeCodeTab].code}
                                    language={currentExamples[activeCodeTab].language}
                                />
                            </div>
                        )}

                        {/* API Reference Format */}
                        {activeSection.includes("-api") && (
                            <div className="space-y-8 mt-8">
                                <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs font-bold rounded">POST</span>
                                        <code className="text-gray-300 font-mono">/v1/{activeSection.replace("-api", "")}</code>
                                    </div>
                                    <p className="text-gray-400 text-sm">
                                        {activeSection === "consents-api" && "Create a new user consent for AI agent transactions."}
                                        {activeSection === "authorize-api" && "Request authorization for a transaction."}
                                        {activeSection === "verify-api" && "Verify an authorization code before processing payment."}
                                        {activeSection === "limits-api" && "Get or update spending limits."}
                                        {activeSection === "rules-api" && "Manage merchant and category rules."}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Navigation */}
                        <div className="mt-16 pt-8 border-t border-white/10 flex justify-between">
                            <a href="#" className="text-gray-400 hover:text-white transition-colors">
                                ← Previous
                            </a>
                            <a href="#" className="text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1">
                                Next <ChevronRight className="w-4 h-4" />
                            </a>
                        </div>
                    </motion.div>
                </main>

                {/* Right Sidebar - Table of Contents */}
                <aside className="hidden xl:block w-64 p-6 sticky top-[73px] h-[calc(100vh-73px)]">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">On this page</h4>
                    <ul className="space-y-2 text-sm">
                        <li>
                            <a href="#" className="text-gray-400 hover:text-white transition-colors">Overview</a>
                        </li>
                        <li>
                            <a href="#" className="text-gray-400 hover:text-white transition-colors">Code Examples</a>
                        </li>
                        <li>
                            <a href="#" className="text-gray-400 hover:text-white transition-colors">Parameters</a>
                        </li>
                        <li>
                            <a href="#" className="text-gray-400 hover:text-white transition-colors">Response</a>
                        </li>
                    </ul>

                    <div className="mt-8 p-4 bg-purple-500/10 border border-purple-500/20 rounded-xl">
                        <p className="text-sm text-gray-400 mb-3">Need help?</p>
                        <a href="#" className="text-purple-400 text-sm hover:text-purple-300 flex items-center gap-1">
                            Join our Discord <ExternalLink className="w-3 h-3" />
                        </a>
                    </div>
                </aside>
            </div>
        </div>
    );
}
