import { motion } from "motion/react";

const steps = [
  {
    number: "01",
    title: "Create Consent",
    description: "User defines what their AI agent can purchase—limits, merchants, time windows.",
    code: `const consent = await agentauth.createConsent({
  agentId: "agent_shopping_123",
  limits: { maxTransaction: 100, dailyLimit: 500 },
  allowedMerchants: ["amazon.com", "bestbuy.com"]
});`,
  },
  {
    number: "02",
    title: "Agent Requests Authorization",
    description: "When the AI agent wants to make a purchase, it requests authorization.",
    code: `const auth = await agentauth.authorize({
  consentId: consent.id,
  amount: 79.99,
  merchant: "amazon.com",
  description: "Wireless headphones"
});`,
  },
  {
    number: "03",
    title: "Policy Evaluation",
    description: "AgentAuth validates the request against all active policies in under 50ms.",
    code: `// AgentAuth checks:
// ✓ Valid consent exists
// ✓ Amount within limits
// ✓ Merchant allowed
// ✓ Daily limit not exceeded
// → Returns APPROVED or DENIED`,
  },
  {
    number: "04",
    title: "Cryptographic Proof",
    description: "Approved transactions receive a signed proof that merchants can verify.",
    code: `if (auth.approved) {
  // Use auth.signature for payment
  await processPayment({
    amount: 79.99,
    authCode: auth.authCode,
    signature: auth.signature  // Ed25519 proof
  });
}`,
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="relative px-6 lg:px-12 py-24 lg:py-32 overflow-hidden bg-black">
      <div className="relative z-10 max-w-5xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-6">
            <span className="text-sm text-gray-400">How It Works</span>
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6">
            Four Steps to Secure
            <br />
            <span className="text-gray-500">AI Agent Commerce</span>
          </h2>
        </motion.div>

        {/* Steps */}
        <div className="space-y-12">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              className="grid lg:grid-cols-2 gap-8 items-center"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              {/* Content - alternating sides */}
              <div className={index % 2 === 1 ? "lg:order-2" : ""}>
                <div className="flex items-center gap-4 mb-4">
                  <span className="text-4xl font-bold text-white/10 font-mono">
                    {step.number}
                  </span>
                  <h3 className="text-xl font-semibold text-white">
                    {step.title}
                  </h3>
                </div>
                <p className="text-gray-500 leading-relaxed">
                  {step.description}
                </p>
              </div>

              {/* Code Block */}
              <div className={index % 2 === 1 ? "lg:order-1" : ""}>
                <div className="rounded-xl border border-white/10 bg-white/[0.02] overflow-hidden">
                  <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2">
                    <div className="flex items-center gap-1.5">
                      <div className="w-3 h-3 rounded-full bg-white/10" />
                      <div className="w-3 h-3 rounded-full bg-white/10" />
                      <div className="w-3 h-3 rounded-full bg-white/10" />
                    </div>
                    <span className="text-xs text-gray-600 font-mono ml-2">step-{step.number}.ts</span>
                  </div>
                  <pre className="p-4 text-sm text-gray-400 font-mono overflow-x-auto">
                    <code>{step.code}</code>
                  </pre>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
