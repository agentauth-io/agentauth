'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';

const sections = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    subsections: ['Installation', 'Quick Start', 'Authentication'],
  },
  {
    id: 'core-concepts',
    title: 'Core Concepts',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    subsections: ['Agents', 'Policies', 'Transactions', 'Audit Logs'],
  },
  {
    id: 'api-reference',
    title: 'API Reference',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
      </svg>
    ),
    subsections: ['Authorization', 'Agents', 'Policies', 'Webhooks'],
  },
  {
    id: 'sdks',
    title: 'SDKs',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
    subsections: ['Python', 'JavaScript', 'Go', 'REST API'],
  },
  {
    id: 'guides',
    title: 'Guides',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
    subsections: ['Shopping Agent', 'Travel Booking', 'Payment Integration', 'Custom Policies'],
  },
];

const codeExamples = {
  installation: `# Install via pip
pip install agentauth

# Or with poetry
poetry add agentauth`,
  
  quickStart: `from agentauth import AgentAuth

# Initialize the client
client = AgentAuth(api_key="your_api_key")

# Create an agent with spending policy
agent = client.agents.create(
    name="Shopping Assistant",
    policy={
        "daily_limit": 500,
        "max_per_transaction": 200,
        "allowed_categories": ["shopping", "groceries"],
        "blocked_merchants": ["gambling_site"]
    }
)

print(f"Agent created: {agent.id}")`,

  authorization: `# Request authorization for a transaction
response = client.authorize(
    agent_id=agent.id,
    transaction={
        "amount": 49.99,
        "currency": "USD",
        "merchant_id": "amazon_123",
        "merchant_name": "Amazon",
        "category": "shopping",
        "description": "Wireless headphones"
    }
)

if response.approved:
    print("✓ Transaction approved")
    print(f"  Remaining daily limit: \${response.remaining_limit}")
else:
    print(f"✗ Denied: {response.reason}")`,

  webhook: `# Set up webhook for real-time notifications
client.webhooks.create(
    url="https://your-app.com/webhooks/agentauth",
    events=["transaction.approved", "transaction.denied", "limit.reached"]
)`,

  apiAuthorize: `POST /v1/authorize
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "agent_id": "agent_abc123",
  "transaction": {
    "amount": 49.99,
    "currency": "USD",
    "merchant_id": "merchant_xyz",
    "merchant_name": "Example Store",
    "category": "shopping",
    "metadata": {
      "order_id": "order_12345"
    }
  }
}`,

  apiResponse: `{
  "approved": true,
  "transaction_id": "txn_def456",
  "agent_id": "agent_abc123",
  "amount": 49.99,
  "currency": "USD",
  "remaining_daily_limit": 450.01,
  "policy_checks": [
    { "rule": "daily_limit", "passed": true },
    { "rule": "max_per_transaction", "passed": true },
    { "rule": "category_allowed", "passed": true }
  ],
  "timestamp": "2026-01-29T10:30:00Z"
}`,
};

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState('getting-started');
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const copyToClipboard = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const CodeBlock = ({ code, language = 'python', id }: { code: string; language?: string; id: string }) => (
    <div className="relative group">
      <div className="absolute top-3 right-3 z-10">
        <button
          onClick={() => copyToClipboard(code, id)}
          className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
        >
          {copiedCode === id ? (
            <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          )}
        </button>
      </div>
      <pre className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 overflow-x-auto">
        <code className="text-sm text-zinc-300 font-mono">{code}</code>
      </pre>
      <div className="absolute top-3 left-3 text-xs text-zinc-500 font-mono">{language}</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-xl border-b border-zinc-800/50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="text-xl font-semibold">
              AgentAuth
            </Link>
            <nav className="hidden md:flex items-center gap-6 text-sm">
              <Link href="/docs" className="text-white font-medium">Docs</Link>
              <a href="#api-reference" className="text-zinc-400 hover:text-white transition-colors">API</a>
              <a href="#guides" className="text-zinc-400 hover:text-white transition-colors">Guides</a>
              <a href="https://github.com/agentauth-io/agentauth" target="_blank" rel="noopener" className="text-zinc-400 hover:text-white transition-colors">GitHub</a>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Search docs..."
                className="w-64 px-4 py-2 pl-10 bg-zinc-900 border border-zinc-800 rounded-lg text-sm focus:outline-none focus:border-zinc-600 transition-colors"
              />
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <kbd className="absolute right-3 top-1/2 -translate-y-1/2 px-1.5 py-0.5 bg-zinc-800 rounded text-[10px] text-zinc-500">⌘K</kbd>
            </div>
          </div>
        </div>
      </header>

      <div className="flex pt-16">
        {/* Sidebar */}
        <aside className="fixed left-0 top-16 bottom-0 w-64 border-r border-zinc-800/50 overflow-y-auto bg-black/50 backdrop-blur-xl">
          <nav className="p-4 space-y-1">
            {sections.map((section) => (
              <div key={section.id}>
                <button
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left text-sm transition-colors ${
                    activeSection === section.id
                      ? 'bg-white/10 text-white'
                      : 'text-zinc-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  {section.icon}
                  {section.title}
                </button>
                <AnimatePresence>
                  {activeSection === section.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="pl-8 py-1 space-y-1">
                        {section.subsections.map((sub) => (
                          <a
                            key={sub}
                            href={`#${sub.toLowerCase().replace(/\s+/g, '-')}`}
                            className="block px-3 py-1.5 text-sm text-zinc-500 hover:text-white transition-colors"
                          >
                            {sub}
                          </a>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 ml-64 p-8 max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {/* Getting Started */}
            <section id="getting-started" className="mb-16">
              <h1 className="text-4xl font-bold mb-4">Getting Started</h1>
              <p className="text-lg text-zinc-400 mb-8">
                AgentAuth provides real-time authorization for AI agents making financial decisions. 
                Get started in minutes with our Python SDK.
              </p>

              <div className="space-y-8">
                <div id="installation">
                  <h2 className="text-2xl font-semibold mb-4">Installation</h2>
                  <p className="text-zinc-400 mb-4">
                    Install the AgentAuth SDK using pip or poetry:
                  </p>
                  <CodeBlock code={codeExamples.installation} language="bash" id="install" />
                </div>

                <div id="quick-start">
                  <h2 className="text-2xl font-semibold mb-4">Quick Start</h2>
                  <p className="text-zinc-400 mb-4">
                    Create your first agent with a spending policy:
                  </p>
                  <CodeBlock code={codeExamples.quickStart} language="python" id="quickstart" />
                </div>

                <div id="authentication">
                  <h2 className="text-2xl font-semibold mb-4">Making Your First Authorization</h2>
                  <p className="text-zinc-400 mb-4">
                    Request authorization before your agent makes any financial decision:
                  </p>
                  <CodeBlock code={codeExamples.authorization} language="python" id="auth" />
                </div>
              </div>
            </section>

            {/* Core Concepts */}
            <section id="core-concepts" className="mb-16">
              <h1 className="text-4xl font-bold mb-4">Core Concepts</h1>
              
              <div className="space-y-8">
                <div id="agents" className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                  <h2 className="text-2xl font-semibold mb-4">Agents</h2>
                  <p className="text-zinc-400">
                    An Agent represents an AI system that can make financial decisions. Each agent has:
                  </p>
                  <ul className="mt-4 space-y-2 text-zinc-400">
                    <li className="flex items-start gap-2">
                      <span className="text-emerald-400 mt-1">•</span>
                      <span><strong className="text-white">Unique ID:</strong> Identifies the agent across all transactions</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-emerald-400 mt-1">•</span>
                      <span><strong className="text-white">Policy:</strong> Rules that govern what transactions are allowed</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-emerald-400 mt-1">•</span>
                      <span><strong className="text-white">Audit Trail:</strong> Complete history of all authorization requests</span>
                    </li>
                  </ul>
                </div>

                <div id="policies" className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                  <h2 className="text-2xl font-semibold mb-4">Policies</h2>
                  <p className="text-zinc-400 mb-4">
                    Policies define the rules for agent spending. Available policy rules include:
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    {[
                      { name: 'daily_limit', desc: 'Maximum spend per 24 hours' },
                      { name: 'max_per_transaction', desc: 'Cap on individual transactions' },
                      { name: 'allowed_categories', desc: 'Whitelist of merchant categories' },
                      { name: 'blocked_merchants', desc: 'Blacklist specific merchants' },
                      { name: 'time_restrictions', desc: 'Limit to business hours' },
                      { name: 'require_approval', desc: 'Human-in-the-loop for large amounts' },
                    ].map((rule) => (
                      <div key={rule.name} className="bg-black/50 rounded-lg p-3">
                        <code className="text-emerald-400 text-sm">{rule.name}</code>
                        <p className="text-xs text-zinc-500 mt-1">{rule.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div id="transactions" className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                  <h2 className="text-2xl font-semibold mb-4">Transactions</h2>
                  <p className="text-zinc-400">
                    Every authorization request creates a transaction record with full details:
                    amount, merchant, category, approval status, policy checks, and timestamp.
                    All transactions are immutably logged for compliance.
                  </p>
                </div>
              </div>
            </section>

            {/* API Reference */}
            <section id="api-reference" className="mb-16">
              <h1 className="text-4xl font-bold mb-4">API Reference</h1>
              <p className="text-lg text-zinc-400 mb-8">
                RESTful API with sub-50ms response times for real-time authorization.
              </p>

              <div className="space-y-8">
                <div id="authorization">
                  <h2 className="text-2xl font-semibold mb-4">POST /v1/authorize</h2>
                  <p className="text-zinc-400 mb-4">
                    Request authorization for a transaction. Returns approval status in real-time.
                  </p>
                  
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium text-zinc-300 mb-2">Request</h3>
                      <CodeBlock code={codeExamples.apiAuthorize} language="http" id="api-req" />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-zinc-300 mb-2">Response</h3>
                      <CodeBlock code={codeExamples.apiResponse} language="json" id="api-res" />
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Webhooks */}
            <section id="webhooks" className="mb-16">
              <h2 className="text-2xl font-semibold mb-4">Webhooks</h2>
              <p className="text-zinc-400 mb-4">
                Receive real-time notifications for transaction events:
              </p>
              <CodeBlock code={codeExamples.webhook} language="python" id="webhook" />
            </section>

            {/* Footer */}
            <div className="border-t border-zinc-800 pt-8 mt-16">
              <div className="flex items-center justify-between text-sm text-zinc-500">
                <p>© 2026 AgentAuth. All rights reserved.</p>
                <div className="flex items-center gap-4">
                  <a href="https://github.com/agentauth-io/agentauth" className="hover:text-white transition-colors">GitHub</a>
                  <a href="mailto:support@agentauth.in" className="hover:text-white transition-colors">Support</a>
                </div>
              </div>
            </div>
          </motion.div>
        </main>
      </div>
    </div>
  );
}
