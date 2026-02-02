import { useState } from "react";
import { 
  ArrowLeft, Book, Code, Terminal, Shield, Key, Zap, ChevronRight, 
  Lock, Eye, Clock, CheckCircle, XCircle, AlertTriangle, Cpu,
  Wallet, Globe, FileCode, GitBranch, Layers, ArrowRight
} from "lucide-react";
import { motion } from "motion/react";

interface DocsProps {
  onBack: () => void;
}

type TabId = "overview" | "authorization" | "sdk" | "cli" | "security" | "api";

interface Tab {
  id: TabId;
  label: string;
  icon: React.ReactNode;
}

const tabs: Tab[] = [
  { id: "overview", label: "Overview", icon: <Book className="w-4 h-4" /> },
  { id: "authorization", label: "How It Works", icon: <Shield className="w-4 h-4" /> },
  { id: "sdk", label: "SDK", icon: <Code className="w-4 h-4" /> },
  { id: "cli", label: "CLI", icon: <Terminal className="w-4 h-4" /> },
  { id: "security", label: "Security", icon: <Lock className="w-4 h-4" /> },
  { id: "api", label: "API Reference", icon: <Zap className="w-4 h-4" /> },
];

export function Docs({ onBack }: DocsProps) {
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-black/80 backdrop-blur-xl px-6 lg:px-12 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-gray-500 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <div className="h-6 w-px bg-white/10" />
            <div className="flex items-center gap-2">
              <Book className="w-5 h-5 text-gray-400" />
              <span className="text-white font-semibold">Documentation</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-gray-600 hidden md:block">v0.2.0</span>
            <a
              href="https://github.com/agentauth-io/agentauth"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-gray-500 hover:text-white transition-colors flex items-center gap-1"
            >
              <GitBranch className="w-4 h-4" />
              GitHub
            </a>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 lg:px-12 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <nav className="lg:w-56 flex-shrink-0">
            <div className="lg:sticky lg:top-24 space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-all ${
                    activeTab === tab.id
                      ? "bg-white/5 text-white border border-white/10"
                      : "text-gray-500 hover:text-white hover:bg-white/5"
                  }`}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>
          </nav>

          {/* Content */}
          <main className="flex-1 min-w-0">
            {activeTab === "overview" && <OverviewSection />}
            {activeTab === "authorization" && <AuthorizationSection />}
            {activeTab === "sdk" && <SDKSection />}
            {activeTab === "cli" && <CLISection />}
            {activeTab === "security" && <SecuritySection />}
            {activeTab === "api" && <APISection />}
          </main>
        </div>
      </div>
    </div>
  );
}

function OverviewSection() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
        What is AgentAuth?
      </h1>
      <p className="text-xl text-gray-500 mb-8 leading-relaxed">
        AgentAuth is the authorization layer for AI agent commerce. We provide the infrastructure 
        that lets AI agents make real purchases on behalf of humans—safely, with limits, and with 
        cryptographic proof of consent.
      </p>

      {/* The Problem */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-gray-400" />
          The Problem
        </h2>
        <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
          <p className="text-gray-500 leading-relaxed mb-4">
            AI agents are becoming capable of autonomous actions—booking flights, ordering groceries, 
            purchasing software licenses. But there's no standardized way to:
          </p>
          <ul className="space-y-3 text-gray-500">
            <li className="flex items-start gap-3">
              <XCircle className="w-5 h-5 text-gray-600 mt-0.5 flex-shrink-0" />
              <span>Prove that a human actually authorized a purchase made by an AI</span>
            </li>
            <li className="flex items-start gap-3">
              <XCircle className="w-5 h-5 text-gray-600 mt-0.5 flex-shrink-0" />
              <span>Set and enforce spending limits that AI agents can't bypass</span>
            </li>
            <li className="flex items-start gap-3">
              <XCircle className="w-5 h-5 text-gray-600 mt-0.5 flex-shrink-0" />
              <span>Audit what your AI agents are doing with your money</span>
            </li>
            <li className="flex items-start gap-3">
              <XCircle className="w-5 h-5 text-gray-600 mt-0.5 flex-shrink-0" />
              <span>Handle chargebacks when an AI makes a disputed purchase</span>
            </li>
          </ul>
        </div>
      </div>

      {/* The Solution */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-white" />
          The Solution
        </h2>
        <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
          <p className="text-gray-400 leading-relaxed mb-6">
            AgentAuth sits between your AI agents and payment providers. Every transaction 
            goes through our authorization engine, which:
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
                <Shield className="w-4 h-4 text-gray-400" />
              </div>
              <div>
                <p className="text-white font-medium">Validates Consent</p>
                <p className="text-sm text-gray-600">Checks if the user approved this type of purchase</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
                <Wallet className="w-4 h-4 text-gray-400" />
              </div>
              <div>
                <p className="text-white font-medium">Enforces Limits</p>
                <p className="text-sm text-gray-600">Per-transaction, daily, weekly, monthly caps</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
                <Key className="w-4 h-4 text-gray-400" />
              </div>
              <div>
                <p className="text-white font-medium">Signs Cryptographically</p>
                <p className="text-sm text-gray-600">Ed25519 proof of human authorization</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
                <Eye className="w-4 h-4 text-gray-400" />
              </div>
              <div>
                <p className="text-white font-medium">Logs Everything</p>
                <p className="text-sm text-gray-600">Immutable audit trail for compliance</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Use Cases */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Layers className="w-5 h-5 text-gray-400" />
          Use Cases
        </h2>
        <div className="grid gap-4">
          <div className="p-5 rounded-xl border border-white/5 bg-white/[0.02]">
            <h3 className="text-white font-medium mb-2">E-commerce AI Assistants</h3>
            <p className="text-gray-500 text-sm">
              Let users say "buy me noise-canceling headphones under $100" and have their AI 
              assistant actually complete the purchase—with proof the human approved it.
            </p>
          </div>
          <div className="p-5 rounded-xl border border-white/5 bg-white/[0.02]">
            <h3 className="text-white font-medium mb-2">Travel Booking Agents</h3>
            <p className="text-gray-500 text-sm">
              AI agents that book flights, hotels, and rental cars within user-defined budgets. 
              Every booking is cryptographically linked to user consent.
            </p>
          </div>
          <div className="p-5 rounded-xl border border-white/5 bg-white/[0.02]">
            <h3 className="text-white font-medium mb-2">Corporate Expense Automation</h3>
            <p className="text-gray-500 text-sm">
              Automate recurring purchases (SaaS subscriptions, office supplies) with 
              policy-based controls. Finance teams get full visibility and can set department-level limits.
            </p>
          </div>
          <div className="p-5 rounded-xl border border-white/5 bg-white/[0.02]">
            <h3 className="text-white font-medium mb-2">Autonomous Agent Networks</h3>
            <p className="text-gray-500 text-sm">
              Multi-agent systems where agents can request budget allocations from each other, 
              with hierarchical consent chains and spending controls.
            </p>
          </div>
        </div>
      </div>

      {/* Quick Start */}
      <div className="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
        <h3 className="text-lg font-bold text-white mb-3">Ready to get started?</h3>
        <p className="text-gray-500 mb-4">
          Integration takes less than 10 minutes. Install our SDK, create a consent, and start authorizing.
        </p>
        <div className="flex flex-wrap gap-3">
          <a href="#sdk" className="inline-flex items-center gap-2 px-4 py-2 bg-white text-black rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">
            View SDK Docs <ArrowRight className="w-4 h-4" />
          </a>
          <a href="/#waitlist" className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 text-white rounded-lg text-sm font-medium hover:bg-white/10 transition-colors">
            Join Waitlist
          </a>
        </div>
      </div>
    </motion.div>
  );
}

function AuthorizationSection() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
        How Authorization Works
      </h1>
      <p className="text-xl text-gray-500 mb-8 leading-relaxed">
        A deep dive into how AgentAuth validates, approves, and signs AI agent transactions.
      </p>

      {/* The Flow */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-6">The Authorization Flow</h2>
        
        <div className="relative">
          {/* Timeline */}
          <div className="absolute left-[19px] top-8 bottom-8 w-0.5 bg-gradient-to-b from-white/30 via-white/20 to-white/10" />
          
          <div className="space-y-8">
            {/* Step 1 */}
            <div className="flex gap-6">
              <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center flex-shrink-0 z-10">
                <span className="text-black font-bold text-sm">1</span>
              </div>
              <div className="flex-1 p-5 rounded-xl border border-white/10 bg-white/[0.02]">
                <h3 className="text-white font-semibold mb-2">User Creates Consent</h3>
                <p className="text-gray-500 text-sm mb-3">
                  The user (human) defines what their AI agent is allowed to do. This includes:
                </p>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Spending limits (per-transaction, daily, monthly)</li>
                  <li>• Allowed merchants or categories</li>
                  <li>• Time restrictions (business hours only, etc.)</li>
                  <li>• Expiration date</li>
                </ul>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex gap-6">
              <div className="w-10 h-10 rounded-full bg-white/80 flex items-center justify-center flex-shrink-0 z-10">
                <span className="text-black font-bold text-sm">2</span>
              </div>
              <div className="flex-1 p-5 rounded-xl border border-white/10 bg-white/[0.02]">
                <h3 className="text-white font-semibold mb-2">Agent Requests Authorization</h3>
                <p className="text-gray-500 text-sm mb-3">
                  When the AI agent wants to make a purchase, it sends an authorization request to AgentAuth:
                </p>
                <pre className="p-3 rounded-lg bg-black/50 text-xs text-gray-400 font-mono overflow-x-auto">
{`POST /v1/authorize
{
  "agent_id": "agent_shopping_123",
  "amount": 49.99,
  "currency": "USD",
  "merchant": "amazon.com",
  "description": "Sony WH-1000XM5 Headphones"
}`}
                </pre>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex gap-6">
              <div className="w-10 h-10 rounded-full bg-white/60 flex items-center justify-center flex-shrink-0 z-10">
                <span className="text-black font-bold text-sm">3</span>
              </div>
              <div className="flex-1 p-5 rounded-xl border border-white/10 bg-white/[0.02]">
                <h3 className="text-white font-semibold mb-2">Policy Evaluation</h3>
                <p className="text-gray-500 text-sm mb-3">
                  Our authorization engine evaluates the request against all active consents and policies:
                </p>
                <div className="grid gap-2 text-sm">
                  <div className="flex items-center gap-2 text-gray-500">
                    <CheckCircle className="w-4 h-4 text-white" />
                    Is there a valid consent for this agent?
                  </div>
                  <div className="flex items-center gap-2 text-gray-500">
                    <CheckCircle className="w-4 h-4 text-white" />
                    Is the amount within the per-transaction limit?
                  </div>
                  <div className="flex items-center gap-2 text-gray-500">
                    <CheckCircle className="w-4 h-4 text-white" />
                    Has the daily/monthly limit been reached?
                  </div>
                  <div className="flex items-center gap-2 text-gray-500">
                    <CheckCircle className="w-4 h-4 text-white" />
                    Is the merchant on the allowed list?
                  </div>
                  <div className="flex items-center gap-2 text-gray-500">
                    <CheckCircle className="w-4 h-4 text-white" />
                    Is the request within the allowed time window?
                  </div>
                </div>
              </div>
            </div>

            {/* Step 4 */}
            <div className="flex gap-6">
              <div className="w-10 h-10 rounded-full bg-white/40 flex items-center justify-center flex-shrink-0 z-10">
                <span className="text-black font-bold text-sm">4</span>
              </div>
              <div className="flex-1 p-5 rounded-xl border border-white/10 bg-white/[0.02]">
                <h3 className="text-white font-semibold mb-2">Cryptographic Signing</h3>
                <p className="text-gray-500 text-sm mb-3">
                  If approved, AgentAuth generates a cryptographic proof using Ed25519 signatures:
                </p>
                <pre className="p-3 rounded-lg bg-black/50 text-xs text-gray-400 font-mono overflow-x-auto">
{`{
  "approved": true,
  "auth_code": "aa_auth_7f3k9...",
  "signature": "ed25519:3Jh8x...",
  "consent_id": "consent_abc123",
  "expires_at": "2026-02-02T15:30:00Z"
}`}
                </pre>
                <p className="text-gray-600 text-xs mt-2">
                  This signature cryptographically proves the human consent chain.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Decision Factors */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-gray-400" />
          Decision Factors
        </h2>
        <p className="text-gray-500 mb-6">
          Our authorization engine considers multiple factors when making a decision. The exact 
          algorithms and risk scoring models are proprietary, but here's what we evaluate:
        </p>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02]">
            <h4 className="text-white font-medium mb-2">Consent Validity</h4>
            <p className="text-gray-600 text-sm">
              Active consent must exist, not be expired, and match the agent making the request.
            </p>
          </div>
          <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02]">
            <h4 className="text-white font-medium mb-2">Spending Limits</h4>
            <p className="text-gray-600 text-sm">
              Real-time tracking of all limit types with atomic enforcement to prevent overruns.
            </p>
          </div>
          <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02]">
            <h4 className="text-white font-medium mb-2">Merchant Rules</h4>
            <p className="text-gray-600 text-sm">
              Allowlist/blocklist matching with category inheritance and wildcard support.
            </p>
          </div>
          <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02]">
            <h4 className="text-white font-medium mb-2">Temporal Controls</h4>
            <p className="text-gray-600 text-sm">
              Time-of-day restrictions, cooldown periods, and velocity checks.
            </p>
          </div>
          <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02]">
            <h4 className="text-white font-medium mb-2">Risk Scoring</h4>
            <p className="text-gray-600 text-sm">
              Proprietary risk model that flags anomalous patterns for additional review.
            </p>
          </div>
          <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02]">
            <h4 className="text-white font-medium mb-2">Chain of Custody</h4>
            <p className="text-gray-600 text-sm">
              Full trace from human consent through agent delegation to final transaction.
            </p>
          </div>
        </div>
      </div>

      {/* Response Types */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Response Types</h2>
        <div className="space-y-4">
          <div className="p-4 rounded-xl border border-white/20 bg-white/[0.02]">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-5 h-5 text-white" />
              <span className="text-white font-semibold">APPROVED</span>
            </div>
            <p className="text-gray-500 text-sm">
              Transaction passes all checks. Includes auth code and signature for the merchant.
            </p>
          </div>
          <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02]">
            <div className="flex items-center gap-2 mb-2">
              <XCircle className="w-5 h-5 text-gray-500" />
              <span className="text-gray-400 font-semibold">DENIED</span>
            </div>
            <p className="text-gray-500 text-sm">
              Transaction blocked. Response includes reason code (e.g., LIMIT_EXCEEDED, MERCHANT_BLOCKED).
            </p>
          </div>
          <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02]">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-5 h-5 text-gray-500" />
              <span className="text-gray-400 font-semibold">PENDING_REVIEW</span>
            </div>
            <p className="text-gray-500 text-sm">
              Transaction requires human approval (high-risk or exceeds soft limits). User notified.
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function SDKSection() {
  const codeExamples = {
    install: `npm install @agentauth/sdk`,
    python: `pip install agentauth`,
    initialize: `import { AgentAuth } from '@agentauth/sdk';

const client = new AgentAuth({
  apiKey: process.env.AGENTAUTH_API_KEY,
  environment: 'production' // or 'sandbox'
});`,
    createConsent: `// Create a consent for your AI shopping agent
const consent = await client.consents.create({
  userId: "user_abc123",
  agentId: "agent_shopping_456",
  name: "Shopping Assistant Consent",
  limits: {
    maxTransaction: 100.00,
    dailyLimit: 500.00,
    monthlyLimit: 2000.00
  },
  rules: {
    allowedMerchants: ["amazon.com", "bestbuy.com", "walmart.com"],
    blockedCategories: ["gambling", "adult"],
    timeRestrictions: {
      allowedDays: ["monday", "tuesday", "wednesday", "thursday", "friday"],
      allowedHours: { start: 9, end: 18 }
    }
  },
  expiresIn: "90d"
});`,
    authorize: `// When your AI agent wants to make a purchase
const auth = await client.authorize({
  consentId: consent.id,
  agentId: "agent_shopping_456",
  transaction: {
    amount: 79.99,
    currency: "USD",
    merchant: "amazon.com",
    category: "electronics",
    description: "Wireless Bluetooth Headphones"
  }
});

if (auth.approved) {
  await processPayment({
    amount: 79.99,
    authCode: auth.authCode,
    signature: auth.signature
  });
}`,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
        SDK Documentation
      </h1>
      <p className="text-xl text-gray-500 mb-8 leading-relaxed">
        Official client libraries for integrating AgentAuth into your applications.
      </p>

      {/* Installation */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4">Installation</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="rounded-xl border border-white/10 bg-white/[0.02] overflow-hidden">
            <div className="px-4 py-2 border-b border-white/10 flex items-center gap-2">
              <FileCode className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-500">JavaScript / TypeScript</span>
            </div>
            <pre className="p-4 text-sm text-gray-400 font-mono">
              <code>{codeExamples.install}</code>
            </pre>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.02] overflow-hidden">
            <div className="px-4 py-2 border-b border-white/10 flex items-center gap-2">
              <FileCode className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-500">Python</span>
            </div>
            <pre className="p-4 text-sm text-gray-400 font-mono">
              <code>{codeExamples.python}</code>
            </pre>
          </div>
        </div>
        <p className="text-gray-600 text-sm mt-3">
          Go, Rust, and Ruby SDKs coming soon. Use our REST API directly in the meantime.
        </p>
      </div>

      {/* Initialize */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4">Initialize the Client</h2>
        <CodeBlock code={codeExamples.initialize} filename="setup.ts" />
      </div>

      {/* Create Consent */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4">Create a Consent</h2>
        <p className="text-gray-500 mb-4">
          Consents define what your AI agents are allowed to purchase.
        </p>
        <CodeBlock code={codeExamples.createConsent} filename="create-consent.ts" />
      </div>

      {/* Authorize */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4">Authorize a Transaction</h2>
        <p className="text-gray-500 mb-4">
          When your AI agent wants to make a purchase, request authorization first.
        </p>
        <CodeBlock code={codeExamples.authorize} filename="authorize.ts" />
      </div>

      {/* Framework Integrations */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Framework Integrations</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02] text-center">
            <p className="text-white font-medium">LangChain</p>
            <p className="text-gray-600 text-xs mt-1">AgentAuth tool available</p>
          </div>
          <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02] text-center">
            <p className="text-white font-medium">LlamaIndex</p>
            <p className="text-gray-600 text-xs mt-1">Native integration</p>
          </div>
          <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02] text-center">
            <p className="text-white font-medium">AutoGPT</p>
            <p className="text-gray-600 text-xs mt-1">Plugin available</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function CLISection() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-gray-400 text-xs font-medium mb-4">
        <Clock className="w-3 h-3" />
        Coming Soon
      </div>
      
      <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
        AgentAuth CLI
      </h1>
      <p className="text-xl text-gray-500 mb-8 leading-relaxed">
        A powerful command-line interface for managing consents, testing authorizations, 
        and debugging your AgentAuth integration.
      </p>

      {/* Preview */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4">Preview</h2>
        <div className="rounded-xl border border-white/10 bg-black/50 overflow-hidden">
          <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-500">Terminal</span>
          </div>
          <pre className="p-4 text-sm font-mono overflow-x-auto">
            <code className="text-gray-400">
              <span className="text-white">$</span> agentauth login{"\n"}
              <span className="text-gray-500">✓ Authenticated as team@company.com</span>{"\n\n"}
              <span className="text-white">$</span> agentauth consents list{"\n"}
              <span className="text-gray-600">┌────────────────────┬──────────────────┬──────────┬─────────────┐</span>{"\n"}
              <span className="text-gray-600">│ ID                 │ Name             │ Status   │ Spent/Limit │</span>{"\n"}
              <span className="text-gray-600">├────────────────────┼──────────────────┼──────────┼─────────────┤</span>{"\n"}
              <span className="text-gray-600">│ consent_abc123     │ Shopping Bot     │</span> <span className="text-white">active</span>   <span className="text-gray-600">│ $145/$500   │</span>{"\n"}
              <span className="text-gray-600">│ consent_def456     │ Travel Agent     │</span> <span className="text-white">active</span>   <span className="text-gray-600">│ $0/$2000    │</span>{"\n"}
              <span className="text-gray-600">│ consent_ghi789     │ Food Delivery    │</span> <span className="text-gray-500">expired</span>  <span className="text-gray-600">│ $89/$100    │</span>{"\n"}
              <span className="text-gray-600">└────────────────────┴──────────────────┴──────────┴─────────────┘</span>
            </code>
          </pre>
        </div>
      </div>

      {/* Planned Commands */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4">Planned Commands</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {["agentauth login", "agentauth consents", "agentauth test", "agentauth logs", "agentauth verify", "agentauth init"].map((cmd) => (
            <div key={cmd} className="p-4 rounded-xl border border-white/10 bg-white/[0.02]">
              <span className="text-white font-mono text-sm">{cmd}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Get Notified */}
      <div className="p-6 rounded-2xl border border-white/10 bg-white/[0.02] text-center">
        <h3 className="text-lg font-bold text-white mb-3">Get Notified</h3>
        <p className="text-gray-500 mb-4">
          Join our waitlist to be the first to try the AgentAuth CLI.
        </p>
        <a
          href="/#waitlist"
          className="inline-flex items-center gap-2 px-6 py-3 bg-white text-black rounded-xl font-semibold hover:bg-gray-200 transition-all"
        >
          Join Waitlist
        </a>
      </div>
    </motion.div>
  );
}

function SecuritySection() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
        Security Architecture
      </h1>
      <p className="text-xl text-gray-500 mb-8 leading-relaxed">
        How AgentAuth protects your data and ensures the integrity of every authorization.
      </p>

      {/* Cryptography */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Key className="w-5 h-5 text-gray-400" />
          Cryptographic Foundation
        </h2>
        <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-white font-medium mb-2">Ed25519 Signatures</h3>
              <p className="text-gray-500 text-sm">
                Every authorization is signed with Ed25519, providing non-repudiable proof 
                of consent. Fast verification and resistant to known attacks.
              </p>
            </div>
            <div>
              <h3 className="text-white font-medium mb-2">X25519 Key Exchange</h3>
              <p className="text-gray-500 text-sm">
                Secure communication using X25519 Diffie-Hellman key exchange 
                for encrypted channels.
              </p>
            </div>
            <div>
              <h3 className="text-white font-medium mb-2">AES-256-GCM Encryption</h3>
              <p className="text-gray-500 text-sm">
                All sensitive data at rest encrypted using AES-256-GCM with 
                per-record keys from HSM.
              </p>
            </div>
            <div>
              <h3 className="text-white font-medium mb-2">SHA-256 Hashing</h3>
              <p className="text-gray-500 text-sm">
                Transaction data hashed before signing for integrity 
                and efficient storage.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Infrastructure */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Globe className="w-5 h-5 text-gray-400" />
          Infrastructure Security
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          {[
            { label: "SOC2 Type II", desc: "Annual security audit" },
            { label: "TLS 1.3 Everywhere", desc: "All traffic encrypted" },
            { label: "HSM Key Storage", desc: "Hardware security modules" },
            { label: "Multi-Region", desc: "Replicated across zones" },
          ].map((item) => (
            <div key={item.label} className="p-4 rounded-xl border border-white/10 bg-white/[0.02]">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-4 h-4 text-white" />
                <span className="text-white font-medium">{item.label}</span>
              </div>
              <p className="text-gray-600 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Disclosure */}
      <div className="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
        <h3 className="text-lg font-bold text-white mb-3">Responsible Disclosure</h3>
        <p className="text-gray-500 mb-4">
          Found a security vulnerability? Report to our security team.
        </p>
        <a
          href="mailto:security@agentauth.in"
          className="inline-flex items-center gap-2 text-white hover:text-gray-300 transition-colors"
        >
          security@agentauth.in <ChevronRight className="w-4 h-4" />
        </a>
      </div>
    </motion.div>
  );
}

function APISection() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
        API Reference
      </h1>
      <p className="text-xl text-gray-500 mb-8 leading-relaxed">
        Complete REST API documentation for direct integration.
      </p>

      {/* Base URL */}
      <div className="mb-8">
        <h2 className="text-lg font-bold text-white mb-3">Base URL</h2>
        <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02] font-mono text-sm">
          <span className="text-gray-500">Production:</span>{" "}
          <span className="text-white">https://api.agentauth.in/v1</span>
        </div>
      </div>

      {/* Authentication */}
      <div className="mb-8">
        <h2 className="text-lg font-bold text-white mb-3">Authentication</h2>
        <div className="p-4 rounded-xl border border-white/10 bg-white/[0.02] font-mono text-sm overflow-x-auto">
          <span className="text-gray-500">Authorization: Bearer</span>{" "}
          <span className="text-white">aa_live_xxxxxxxxxxxxxxxx</span>
        </div>
      </div>

      {/* Endpoints */}
      <div className="mb-8">
        <h2 className="text-lg font-bold text-white mb-4">Core Endpoints</h2>
        <div className="space-y-3">
          <EndpointCard method="POST" path="/consents" description="Create a new consent" />
          <EndpointCard method="GET" path="/consents" description="List all consents" />
          <EndpointCard method="GET" path="/consents/:id" description="Get consent details" />
          <EndpointCard method="DELETE" path="/consents/:id" description="Revoke a consent" />
          <EndpointCard method="POST" path="/authorize" description="Request authorization" />
          <EndpointCard method="POST" path="/verify" description="Verify an authorization" />
          <EndpointCard method="GET" path="/audit" description="Query audit logs" />
        </div>
      </div>

      {/* OpenAPI */}
      <div className="p-6 rounded-2xl border border-white/10 bg-white/[0.02]">
        <h3 className="text-lg font-bold text-white mb-3">Interactive API Explorer</h3>
        <p className="text-gray-500 mb-4">
          Try out API endpoints directly with our OpenAPI documentation.
        </p>
        <a
          href="https://characteristic-inessa-agentauth-0a540dd6.koyeb.app/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-6 py-3 bg-white text-black rounded-xl font-semibold hover:bg-gray-200 transition-all"
        >
          <Code className="w-5 h-5" />
          Open API Explorer
          <ChevronRight className="w-4 h-4" />
        </a>
      </div>
    </motion.div>
  );
}

// Helper Components
function CodeBlock({ code, filename }: { code: string; filename: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] overflow-hidden">
      <div className="px-4 py-2 border-b border-white/10 flex items-center justify-between">
        <span className="text-sm text-gray-500 font-mono">{filename}</span>
        <Code className="w-4 h-4 text-gray-600" />
      </div>
      <pre className="p-4 text-sm text-gray-400 font-mono overflow-x-auto">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function EndpointCard({ method, path, description }: { method: string; path: string; description: string }) {
  return (
    <div className="flex items-center gap-4 p-3 rounded-lg border border-white/5 bg-white/[0.01] hover:bg-white/[0.03] transition-colors">
      <span className="px-2 py-1 rounded text-xs font-mono font-bold bg-white/5 text-white border border-white/10">
        {method}
      </span>
      <span className="font-mono text-sm text-gray-400">{path}</span>
      <span className="text-sm text-gray-600 ml-auto hidden md:block">{description}</span>
    </div>
  );
}
