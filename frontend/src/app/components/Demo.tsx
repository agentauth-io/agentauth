import { useState } from "react";
import { Play, Check, X, DollarSign, ShoppingCart, Coffee } from "lucide-react";
import { motion } from "motion/react";

interface Transaction {
  id: number;
  agent: string;
  action: string;
  amount: number;
  merchant: string;
  status: "pending" | "approved" | "denied";
  reason?: string;
}

const demoTransactions: Transaction[] = [
  {
    id: 1,
    agent: "Shopping Assistant",
    action: "Purchase headphones",
    amount: 79.99,
    merchant: "Amazon",
    status: "pending",
  },
  {
    id: 2,
    agent: "Travel Bot",
    action: "Book flight",
    amount: 450.00,
    merchant: "United Airlines",
    status: "pending",
  },
  {
    id: 3,
    agent: "Food Delivery Agent",
    action: "Order lunch",
    amount: 25.50,
    merchant: "DoorDash",
    status: "pending",
  },
];

export function Demo() {
  const [transactions, setTransactions] = useState<Transaction[]>(demoTransactions);
  const [isRunning, setIsRunning] = useState(false);

  const runDemo = () => {
    setIsRunning(true);
    setTransactions(demoTransactions.map(t => ({ ...t, status: "pending" as const })));

    // Simulate authorization decisions with delays
    setTimeout(() => {
      setTransactions(prev => prev.map(t => 
        t.id === 1 ? { ...t, status: "approved" as const } : t
      ));
    }, 800);

    setTimeout(() => {
      setTransactions(prev => prev.map(t => 
        t.id === 2 ? { ...t, status: "denied" as const, reason: "Exceeds $200 limit" } : t
      ));
    }, 1600);

    setTimeout(() => {
      setTransactions(prev => prev.map(t => 
        t.id === 3 ? { ...t, status: "approved" as const } : t
      ));
      setIsRunning(false);
    }, 2400);
  };

  const getIcon = (merchant: string) => {
    if (merchant === "Amazon") return <ShoppingCart className="w-5 h-5" />;
    if (merchant === "DoorDash") return <Coffee className="w-5 h-5" />;
    return <DollarSign className="w-5 h-5" />;
  };

  return (
    <section id="demo" className="relative px-6 lg:px-12 py-24 lg:py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0f0f1a] via-[#1a1a2e] to-[#0f0f1a]" />
      
      {/* Decorative elements */}
      <div className="absolute top-1/3 left-0 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/3 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl" />

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
            <Play className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-gray-400">Interactive Demo</span>
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6">
            See AgentAuth
            <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent"> in Action</span>
          </h2>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
            Watch how AgentAuth authorizes or denies AI agent transactions in real-time based on your policies.
          </p>
        </motion.div>

        {/* Demo Card */}
        <motion.div
          className="relative rounded-2xl border border-white/10 bg-white/[0.02] backdrop-blur-xl overflow-hidden"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/60" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
                <div className="w-3 h-3 rounded-full bg-green-500/60" />
              </div>
              <span className="text-sm text-gray-400 font-mono ml-2">AgentAuth Dashboard</span>
            </div>
            <button
              onClick={runDemo}
              disabled={isRunning}
              className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg text-sm font-medium hover:shadow-lg hover:shadow-purple-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isRunning ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Demo
                </>
              )}
            </button>
          </div>

          {/* Policy Display */}
          <div className="px-6 py-4 border-b border-white/10 bg-white/[0.01]">
            <p className="text-sm text-gray-400 mb-2">Active Policy:</p>
            <div className="flex flex-wrap gap-3">
              <span className="px-3 py-1.5 bg-purple-500/10 border border-purple-500/20 rounded-lg text-purple-300 text-xs font-medium">
                Max Transaction: $200
              </span>
              <span className="px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-300 text-xs font-medium">
                Daily Limit: $500
              </span>
              <span className="px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg text-green-300 text-xs font-medium">
                Approved Merchants: 150+
              </span>
            </div>
          </div>

          {/* Transactions */}
          <div className="divide-y divide-white/5">
            {transactions.map((tx, index) => (
              <motion.div
                key={tx.id}
                className="px-6 py-5 flex items-center justify-between gap-4"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-gray-400">
                    {getIcon(tx.merchant)}
                  </div>
                  <div>
                    <p className="text-white font-medium">{tx.action}</p>
                    <p className="text-sm text-gray-500">{tx.agent} → {tx.merchant}</p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <span className="text-white font-mono text-lg">
                    ${tx.amount.toFixed(2)}
                  </span>

                  {/* Status */}
                  <div className="w-28">
                    {tx.status === "pending" && (
                      <span className="flex items-center gap-2 text-gray-400 text-sm">
                        <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse" />
                        Pending
                      </span>
                    )}
                    {tx.status === "approved" && (
                      <span className="flex items-center gap-2 text-green-400 text-sm">
                        <Check className="w-4 h-4" />
                        Approved
                      </span>
                    )}
                    {tx.status === "denied" && (
                      <div>
                        <span className="flex items-center gap-2 text-red-400 text-sm">
                          <X className="w-4 h-4" />
                          Denied
                        </span>
                        {tx.reason && (
                          <p className="text-xs text-red-400/60 mt-0.5">{tx.reason}</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-white/10 bg-white/[0.01]">
            <p className="text-xs text-gray-500 text-center">
              This is a simulated demo. Real authorizations happen in under 50ms.
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
