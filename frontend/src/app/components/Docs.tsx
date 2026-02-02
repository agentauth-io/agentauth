import { ArrowLeft, Book, Code, Terminal, Shield, Key, Zap, ChevronRight } from "lucide-react";
import { motion } from "motion/react";

interface DocsProps {
  onBack: () => void;
}

const codeExamples = {
  install: `npm install @agentauth/sdk`,
  initialize: `import { AgentAuth } from '@agentauth/sdk';

const auth = new AgentAuth({
  apiKey: process.env.AGENTAUTH_API_KEY
});`,
  authorize: `// Request authorization for an AI agent transaction
const result = await auth.authorize({
  agentId: "agent_shopping_123",
  amount: 49.99,
  merchant: "amazon.com",
  category: "electronics"
});

if (result.approved) {
  // Proceed with purchase
  console.log("Transaction approved:", result.authCode);
} else {
  console.log("Denied:", result.reason);
}`,
  consent: `// Create a consent with spending limits
const consent = await auth.createConsent({
  userId: "user_abc",
  agentId: "agent_shopping_123",
  limits: {
    maxTransaction: 100,
    dailyLimit: 500,
    monthlyLimit: 2000
  },
  allowedMerchants: ["amazon.com", "walmart.com"],
  expiresIn: "30d"
});`
};

export function Docs({ onBack }: DocsProps) {
  return (
    <div className="min-h-screen bg-[#0f0f1a]">
      {/* Header */}
      <header className="border-b border-white/5 px-6 lg:px-12 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <div className="h-6 w-px bg-white/10" />
            <div className="flex items-center gap-2">
              <Book className="w-5 h-5 text-purple-400" />
              <span className="text-white font-semibold">Documentation</span>
            </div>
          </div>
          <a
            href="https://github.com/agentauth-io/agentauth"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            View on GitHub →
          </a>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 lg:px-12 py-16">
        {/* Title */}
        <motion.div
          className="mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Getting Started
          </h1>
          <p className="text-xl text-gray-400">
            Integrate AgentAuth into your AI application in minutes.
          </p>
        </motion.div>

        {/* Quick Start */}
        <motion.section
          className="mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <Terminal className="w-6 h-6 text-purple-400" />
            Quick Start
          </h2>

          <div className="space-y-6">
            {/* Step 1 */}
            <div className="rounded-xl border border-white/10 bg-white/[0.02] overflow-hidden">
              <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
                <span className="text-sm text-gray-400">1. Install the SDK</span>
                <Code className="w-4 h-4 text-gray-500" />
              </div>
              <pre className="p-4 text-sm text-gray-300 font-mono overflow-x-auto">
                <code>{codeExamples.install}</code>
              </pre>
            </div>

            {/* Step 2 */}
            <div className="rounded-xl border border-white/10 bg-white/[0.02] overflow-hidden">
              <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
                <span className="text-sm text-gray-400">2. Initialize the client</span>
                <Code className="w-4 h-4 text-gray-500" />
              </div>
              <pre className="p-4 text-sm text-gray-300 font-mono overflow-x-auto">
                <code>{codeExamples.initialize}</code>
              </pre>
            </div>

            {/* Step 3 */}
            <div className="rounded-xl border border-white/10 bg-white/[0.02] overflow-hidden">
              <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
                <span className="text-sm text-gray-400">3. Authorize a transaction</span>
                <Code className="w-4 h-4 text-gray-500" />
              </div>
              <pre className="p-4 text-sm text-gray-300 font-mono overflow-x-auto">
                <code>{codeExamples.authorize}</code>
              </pre>
            </div>
          </div>
        </motion.section>

        {/* Core Concepts */}
        <motion.section
          className="mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <Shield className="w-6 h-6 text-purple-400" />
            Core Concepts
          </h2>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
              <h3 className="text-lg font-semibold text-white mb-2">Consents</h3>
              <p className="text-gray-400 text-sm mb-4">
                User-approved permissions that define what an AI agent can do. Includes spending limits, merchant restrictions, and time bounds.
              </p>
              <a href="#consents" className="text-purple-400 text-sm flex items-center gap-1 hover:text-purple-300">
                Learn more <ChevronRight className="w-4 h-4" />
              </a>
            </div>

            <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
              <h3 className="text-lg font-semibold text-white mb-2">Authorizations</h3>
              <p className="text-gray-400 text-sm mb-4">
                Real-time decisions on whether a specific transaction should be allowed based on active consents and policies.
              </p>
              <a href="#authorizations" className="text-purple-400 text-sm flex items-center gap-1 hover:text-purple-300">
                Learn more <ChevronRight className="w-4 h-4" />
              </a>
            </div>

            <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
              <h3 className="text-lg font-semibold text-white mb-2">Cryptographic Proofs</h3>
              <p className="text-gray-400 text-sm mb-4">
                Ed25519 signatures that prove a human authorized a transaction. Useful for chargebacks and disputes.
              </p>
              <a href="#proofs" className="text-purple-400 text-sm flex items-center gap-1 hover:text-purple-300">
                Learn more <ChevronRight className="w-4 h-4" />
              </a>
            </div>

            <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
              <h3 className="text-lg font-semibold text-white mb-2">Audit Logs</h3>
              <p className="text-gray-400 text-sm mb-4">
                Immutable records of all agent actions. Full transparency for compliance and debugging.
              </p>
              <a href="#audit" className="text-purple-400 text-sm flex items-center gap-1 hover:text-purple-300">
                Learn more <ChevronRight className="w-4 h-4" />
              </a>
            </div>
          </div>
        </motion.section>

        {/* Creating Consents */}
        <motion.section
          id="consents"
          className="mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <Key className="w-6 h-6 text-purple-400" />
            Creating Consents
          </h2>

          <p className="text-gray-400 mb-6">
            Before an AI agent can make purchases, the user must create a consent that defines the agent's permissions:
          </p>

          <div className="rounded-xl border border-white/10 bg-white/[0.02] overflow-hidden">
            <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
              <span className="text-sm text-gray-400">consent.ts</span>
              <Code className="w-4 h-4 text-gray-500" />
            </div>
            <pre className="p-4 text-sm text-gray-300 font-mono overflow-x-auto">
              <code>{codeExamples.consent}</code>
            </pre>
          </div>
        </motion.section>

        {/* API Reference Link */}
        <motion.section
          className="mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <Zap className="w-6 h-6 text-purple-400" />
            API Reference
          </h2>

          <p className="text-gray-400 mb-6">
            For the complete API documentation with all endpoints, request/response schemas, and authentication details:
          </p>

          <a
            href="https://characteristic-inessa-agentauth-0a540dd6.koyeb.app/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-3 px-6 py-4 rounded-xl border border-purple-500/30 bg-purple-500/10 text-purple-300 hover:bg-purple-500/20 transition-colors"
          >
            <Code className="w-5 h-5" />
            <div>
              <div className="font-semibold">OpenAPI Documentation</div>
              <div className="text-sm text-purple-400/70">Interactive API explorer</div>
            </div>
            <ChevronRight className="w-5 h-5 ml-2" />
          </a>
        </motion.section>

        {/* Support */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <div className="p-8 rounded-2xl border border-white/10 bg-gradient-to-br from-purple-500/10 to-blue-500/10 text-center">
            <h3 className="text-xl font-bold text-white mb-3">Need Help?</h3>
            <p className="text-gray-400 mb-6">
              Join the waitlist to get early access and priority support.
            </p>
            <a
              href="/#waitlist"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-purple-500/25 transition-all"
            >
              Join Waitlist
            </a>
          </div>
        </motion.section>
      </div>
    </div>
  );
}
