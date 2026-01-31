"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect, useCallback } from "react";
import { CheckCircle2, XCircle, ArrowRight } from "lucide-react";
import { staggerContainer, staggerItem, viewportOnce } from "@/lib/animations";

/**
 * LiveDemoSection - Professional interactive demo with clean design
 */

interface Transaction {
  id: string;
  merchant: string;
  amount: number;
  status: "approved" | "denied";
  reason?: string;
}

const merchants = [
  { name: "Amazon", icon: "🛒" },
  { name: "Uber", icon: "🚗" },
  { name: "Netflix", icon: "🎬" },
  { name: "Blocked Merchant", icon: "⛔", blocked: true },
];

export function LiveDemoSection() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [dailySpent, setDailySpent] = useState(0);
  const dailyLimit = 500;

  const processTransaction = useCallback(() => {
    const merchant = merchants[Math.floor(Math.random() * merchants.length)];
    const amount = Math.round((Math.random() * 150 + 10) * 100) / 100;
    
    let status: "approved" | "denied" = "approved";
    let reason: string | undefined;

    if (merchant.blocked) {
      status = "denied";
      reason = "Blocked merchant";
    } else if (dailySpent + amount > dailyLimit) {
      status = "denied";
      reason = "Daily limit exceeded";
    } else if (amount > 200) {
      status = "denied";
      reason = "Amount exceeds $200 limit";
    }

    const newTx: Transaction = {
      id: crypto.randomUUID(),
      merchant: merchant.name,
      amount,
      status,
      reason,
    };

    setTransactions(prev => [newTx, ...prev].slice(0, 5));
    
    if (status === "approved") {
      setDailySpent(prev => prev + amount);
    }
  }, [dailySpent]);

  useEffect(() => {
    if (!isRunning) return;
    
    const interval = setInterval(processTransaction, 2000);
    return () => clearInterval(interval);
  }, [isRunning, processTransaction]);

  return (
    <section className="py-32 bg-black relative overflow-hidden" id="demo">
      <div className="max-w-[1200px] mx-auto px-6 lg:px-8">
        {/* Header */}
        <motion.div
          className="text-center mb-16"
          initial="hidden"
          whileInView="visible"
          viewport={viewportOnce}
          variants={staggerContainer(0.1)}
        >
          <motion.p
            variants={staggerItem}
            className="text-emerald-400 font-medium mb-4 tracking-wide"
          >
            Live Demo
          </motion.p>
          <motion.h2
            variants={staggerItem}
            className="text-4xl lg:text-5xl font-semibold text-white tracking-tight mb-6"
          >
            See it in action
          </motion.h2>
          <motion.p
            variants={staggerItem}
            className="text-lg text-zinc-400 max-w-xl mx-auto"
          >
            Watch real-time authorization decisions based on configurable policies.
          </motion.p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Left: Spline 3D + Controls */}
          <motion.div
            className="space-y-8"
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={viewportOnce}
            transition={{ duration: 0.6 }}
          >
            {/* Minimalistic SVG Visual */}
            <div className="relative h-[350px] rounded-3xl overflow-hidden border border-zinc-800/50 bg-zinc-950 flex items-center justify-center">
              <svg width="220" height="220" viewBox="0 0 220 220" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="110" cy="110" r="100" fill="#18181b" stroke="#10b981" strokeWidth="4" />
                <rect x="60" y="80" width="100" height="60" rx="16" fill="#27272a" stroke="#10b981" strokeWidth="2" />
                <rect x="80" y="100" width="20" height="20" rx="4" fill="#10b981" />
                <rect x="120" y="100" width="40" height="10" rx="3" fill="#334155" />
                <rect x="120" y="115" width="30" height="7" rx="2" fill="#334155" />
                <circle cx="110" cy="110" r="100" stroke="#10b981" strokeWidth="2" opacity="0.1" />
              </svg>
            </div>

            {/* Policy Display */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
              <h3 className="text-white font-semibold mb-4">Active Policy</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-zinc-500">Daily Limit</p>
                  <p className="text-white font-medium">${dailyLimit}</p>
                </div>
                <div>
                  <p className="text-zinc-500">Max Per Transaction</p>
                  <p className="text-white font-medium">$200</p>
                </div>
                <div>
                  <p className="text-zinc-500">Spent Today</p>
                  <p className="text-emerald-400 font-medium">${dailySpent.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-zinc-500">Remaining</p>
                  <p className="text-white font-medium">${(dailyLimit - dailySpent).toFixed(2)}</p>
                </div>
              </div>
              
              {/* Progress bar */}
              <div className="mt-4 h-2 bg-zinc-800 rounded-full overflow-hidden">
                <motion.div 
                  className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400"
                  initial={{ width: 0 }}
                  animate={{ width: `${(dailySpent / dailyLimit) * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>

            {/* Control Button */}
            <motion.button
              onClick={() => setIsRunning(!isRunning)}
              className={`w-full py-4 rounded-2xl font-semibold flex items-center justify-center gap-3 transition-all ${
                isRunning 
                  ? "bg-zinc-800 text-white hover:bg-zinc-700" 
                  : "bg-white text-black hover:bg-zinc-100"
              }`}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {isRunning ? (
                <>
                  <span className="w-3 h-3 bg-red-500 rounded-sm" />
                  Stop Simulation
                </>
              ) : (
                <>
                  <ArrowRight className="w-5 h-5" />
                  Start Demo
                </>
              )}
            </motion.button>
          </motion.div>

          {/* Right: Transaction Feed */}
          <motion.div
            className="bg-zinc-900/30 border border-zinc-800/50 rounded-3xl p-6"
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={viewportOnce}
            transition={{ duration: 0.6 }}
          >
            <h3 className="text-white font-semibold mb-6 flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isRunning ? "bg-emerald-400 animate-pulse" : "bg-zinc-600"}`} />
              Transaction Feed
            </h3>

            <div className="space-y-4 min-h-[400px]">
              <AnimatePresence mode="popLayout">
                {transactions.length === 0 ? (
                  <motion.div
                    key="empty"
                    className="text-center py-16 text-zinc-500"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    Click &quot;Start Demo&quot; to see live transactions
                  </motion.div>
                ) : (
                  transactions.map((tx) => (
                    <motion.div
                      key={tx.id}
                      layout
                      initial={{ opacity: 0, y: -20, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      className={`p-4 rounded-xl border ${
                        tx.status === "approved" 
                          ? "bg-emerald-500/5 border-emerald-500/20" 
                          : "bg-red-500/5 border-red-500/20"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-white">{tx.merchant}</span>
                        <span className="text-white font-semibold">${tx.amount.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className={`flex items-center gap-1.5 ${
                          tx.status === "approved" ? "text-emerald-400" : "text-red-400"
                        }`}>
                          {tx.status === "approved" ? (
                            <CheckCircle2 className="w-4 h-4" />
                          ) : (
                            <XCircle className="w-4 h-4" />
                          )}
                          {tx.status === "approved" ? "Approved" : "Denied"}
                        </span>
                        {tx.reason && (
                          <span className="text-zinc-500">{tx.reason}</span>
                        )}
                      </div>
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
