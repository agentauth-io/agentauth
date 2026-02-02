import { motion } from "motion/react";
import { Code, Settings, Zap, CheckCircle } from "lucide-react";

const steps = [
  {
    number: "01",
    icon: Code,
    title: "Connect Your Agent",
    description: "Integrate our SDK with your AI agent in minutes. Simple REST API or Python SDK.",
    code: `import { AgentAuth } from 'agentauth';
const auth = new AgentAuth(apiKey);`,
  },
  {
    number: "02",
    icon: Settings,
    title: "Set Spending Rules",
    description: "Define budgets, merchant allowlists, and transaction limits through our dashboard.",
    code: `auth.setLimits({
  daily: 500,
  perTransaction: 100
});`,
  },
  {
    number: "03",
    icon: Zap,
    title: "Agent Makes Purchase",
    description: "Your agent requests authorization. We validate against your rules in real-time.",
    code: `const result = await auth.authorize({
  amount: 49.99,
  merchant: "amazon.com"
});`,
  },
  {
    number: "04",
    icon: CheckCircle,
    title: "Transaction Complete",
    description: "Payment is processed securely. You get instant webhooks and detailed audit logs.",
    code: `// Webhook: transaction.completed
{
  "status": "approved",
  "proofId": "prf_abc123"
}`,
  },
];

export function HowItWorks() {
  return (
    <section className="relative px-6 lg:px-12 py-24 lg:py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0f0f1a] to-[#1a1a2e]" />
      
      {/* Decorative gradient */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-b from-purple-600/10 to-transparent blur-3xl" />

      <div className="relative z-10 max-w-6xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center max-w-3xl mx-auto mb-16 lg:mb-20"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-6">
            <span className="text-sm text-gray-400">Simple Integration</span>
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6">
            Get Started in
            <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent"> Minutes</span>
          </h2>
          <p className="text-lg text-gray-400 leading-relaxed">
            Four simple steps to empower your AI agents with secure payment authorization.
          </p>
        </motion.div>

        {/* Steps */}
        <div className="space-y-6">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              className="relative"
              initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              <div className={`flex flex-col lg:flex-row items-start gap-8 p-8 rounded-2xl bg-white/[0.02] border border-white/[0.05] hover:border-white/10 transition-colors ${
                index % 2 === 1 ? 'lg:flex-row-reverse' : ''
              }`}>
                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-white/10 flex items-center justify-center">
                      <step.icon className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                      <span className="text-purple-400 text-sm font-mono">{step.number}</span>
                      <h3 className="text-xl font-semibold text-white">{step.title}</h3>
                    </div>
                  </div>
                  <p className="text-gray-400 leading-relaxed mb-4">
                    {step.description}
                  </p>
                </div>

                {/* Code Block */}
                <div className="flex-1 w-full">
                  <div className="rounded-xl bg-[#0a0a0f] border border-white/5 p-4 font-mono text-sm overflow-x-auto">
                    <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/5">
                      <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
                      <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
                      <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
                    </div>
                    <pre className="text-gray-400">
                      <code>{step.code}</code>
                    </pre>
                  </div>
                </div>
              </div>

              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute left-1/2 -bottom-3 w-px h-6 bg-gradient-to-b from-purple-500/50 to-transparent" />
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
