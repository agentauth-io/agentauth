import React, { useState, useCallback, useRef } from 'react';
import '../../../styles/budget-demo.css';

/* ─── Transaction Data ───────────────────────────────────────────── */

interface ShoppingItem {
    item: string;
    amount: number;
    merchant: string;
    category: string;
    country: string;
    icon: string;
}

interface TxResult {
    item: ShoppingItem;
    decision: string;
    risk_score: number;
    eval_ms: number;
    policy_name: string;
    explanation: string;
}

const SHOPPING_LIST: ShoppingItem[] = [
    { item: 'Organic Bananas', amount: 4.99, merchant: 'Whole Foods', category: 'groceries', country: 'US', icon: '🍌' },
    { item: 'Running Shoes', amount: 129.99, merchant: 'Nike', category: 'clothing', country: 'US', icon: '👟' },
    { item: 'iPhone 16 Pro', amount: 1199.00, merchant: 'Apple', category: 'electronics', country: 'US', icon: '📱' },
    { item: 'Lottery Tickets', amount: 50.00, merchant: 'StateLotto', category: 'gambling', country: 'US', icon: '🎰' },
    { item: 'Espresso Machine', amount: 349.00, merchant: 'Breville UK', category: 'home', country: 'GB', icon: '☕' },
    { item: 'Protein Bars (12pk)', amount: 24.99, merchant: 'Amazon', category: 'groceries', country: 'US', icon: '💪' },
    { item: 'Crypto Trading Course', amount: 499.00, merchant: 'SketchyCo', category: 'crypto', country: 'KY', icon: '🪙' },
];

const POLICIES = [
    {
        id: 'pol_budget', name: 'Daily Budget Limit', effect: 'allow', priority: 10,
        description: 'Allow purchases up to $200, approved categories only',
        constraints: { daily_limit: 500.0 },
        rules: [{
            conditions: [
                { attribute: 'amount', operator: 'lte', value: 200.0 },
                { attribute: 'category', operator: 'in', value: ['groceries', 'electronics', 'clothing', 'home', 'health'] },
            ], logic: 'and'
        }],
    },
    {
        id: 'pol_block', name: 'Block Risky Categories', effect: 'deny', priority: 100,
        description: 'Block gambling, crypto, and adult',
        constraints: {},
        rules: [{
            conditions: [
                { attribute: 'category', operator: 'in', value: ['gambling', 'crypto', 'adult'] },
            ], logic: 'and'
        }],
    },
    {
        id: 'pol_geo', name: 'Geo-Restrict to US', effect: 'deny', priority: 90,
        description: 'Only US merchants allowed',
        constraints: {},
        rules: [{
            conditions: [
                { attribute: 'merchant_country', operator: 'not_in', value: ['US'] },
            ], logic: 'and'
        }],
    },
    {
        id: 'pol_high', name: 'High Value Review', effect: 'require_approval', priority: 50,
        description: 'Items over $500 need human approval',
        constraints: {},
        rules: [{
            conditions: [
                { attribute: 'amount', operator: 'gt', value: 500.0 },
            ], logic: 'and'
        }],
    },
];

const API_BASE = import.meta.env.VITE_API_URL || 'https://agentauth-api.koyeb.app';
const DAILY_BUDGET = 500;

/* ─── Component ──────────────────────────────────────────────────── */

export default function BudgetDemo() {
    const [results, setResults] = useState<TxResult[]>([]);
    const [pending, setPending] = useState<number | null>(null);
    const [running, setRunning] = useState(false);
    const [speed, setSpeed] = useState(1200);
    const cancelRef = useRef(false);

    const totalSpent = results
        .filter(r => r.decision === 'allow')
        .reduce((s, r) => s + r.item.amount, 0);

    const pctUsed = Math.min((totalSpent / DAILY_BUDGET) * 100, 100);
    const allowed = results.filter(r => r.decision === 'allow').length;
    const denied = results.filter(r => r.decision === 'deny').length;
    const approvals = results.filter(r => r.decision === 'require_approval').length;

    const reset = useCallback(() => {
        cancelRef.current = true;
        setResults([]);
        setPending(null);
        setRunning(false);
        setTimeout(() => { cancelRef.current = false; }, 100);
    }, []);

    const run = useCallback(async () => {
        cancelRef.current = false;
        setResults([]);
        setPending(null);
        setRunning(true);

        for (let i = 0; i < SHOPPING_LIST.length; i++) {
            if (cancelRef.current) break;
            const item = SHOPPING_LIST[i];
            setPending(i);

            // Wait to show "evaluating" state
            await new Promise(r => setTimeout(r, speed * 0.4));
            if (cancelRef.current) break;

            try {
                const res = await fetch(`${API_BASE}/v1/playground/evaluate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        policies: POLICIES,
                        context: {
                            agent_id: 'shopping-agent-v1',
                            action: 'purchase',
                            amount: item.amount,
                            merchant: item.merchant,
                            category: item.category,
                            merchant_country: item.country,
                        },
                        combine_algorithm: 'deny_overrides',
                    }),
                });
                const data = await res.json();

                if (cancelRef.current) break;
                setResults(prev => [...prev, {
                    item,
                    decision: data.decision || 'deny',
                    risk_score: data.risk_score || 0,
                    eval_ms: data.evaluation_time_ms || 0,
                    policy_name: data.deciding_policy_name || 'N/A',
                    explanation: data.explanation || '',
                }]);
            } catch {
                if (cancelRef.current) break;
                setResults(prev => [...prev, {
                    item,
                    decision: 'deny',
                    risk_score: 1,
                    eval_ms: 0,
                    policy_name: 'Error',
                    explanation: 'Backend unreachable — using deny-by-default',
                }]);
            }

            setPending(null);
            await new Promise(r => setTimeout(r, speed * 0.6));
        }

        setRunning(false);
        setPending(null);
    }, [speed]);

    const budgetClass = pctUsed > 80 ? 'critical' : pctUsed > 50 ? 'warn' : '';

    return (
        <div className="bd-shell">
            <a href="/" className="bd-back">← HOME</a>

            <div className="bd-header">
                <h1>◈ AI Agent Budget Demo</h1>
                <div className="bd-tagline">Watch an AI shopping agent attempt 7 purchases through AgentAuth&apos;s policy engine</div>
            </div>

            {/* Budget Bar */}
            <div className="bd-budget-wrap">
                <div className="bd-budget-label">
                    <span>Daily Budget</span>
                    <span>${totalSpent.toFixed(2)} / ${DAILY_BUDGET.toFixed(2)}</span>
                </div>
                <div className="bd-budget-bar">
                    <div
                        className={`bd-budget-fill ${budgetClass}`}
                        style={{ width: `${pctUsed}%` }}
                    />
                </div>
            </div>

            {/* Controls */}
            <div className="bd-controls">
                <button className="bd-run-btn" onClick={run} disabled={running}>
                    {running ? '⟳ Running…' : '▶ Run Demo'}
                </button>
                <button className="bd-reset-btn" onClick={reset}>Reset</button>
                <select
                    className="bd-speed"
                    value={speed}
                    onChange={e => setSpeed(Number(e.target.value))}
                    disabled={running}
                >
                    <option value={2000}>Slow</option>
                    <option value={1200}>Normal</option>
                    <option value={600}>Fast</option>
                </select>
            </div>

            {/* Transaction Feed */}
            <div className="bd-feed">
                {/* Pending item */}
                {pending !== null && (
                    <div className="bd-tx pending">
                        <div className="bd-tx-icon">{SHOPPING_LIST[pending].icon}</div>
                        <div className="bd-tx-info">
                            <div className="bd-tx-name">{SHOPPING_LIST[pending].item}</div>
                            <div className="bd-tx-detail">
                                {SHOPPING_LIST[pending].merchant} · {SHOPPING_LIST[pending].category} · {SHOPPING_LIST[pending].country}
                            </div>
                        </div>
                        <div className="bd-tx-amount" style={{ color: '#a0a0a8' }}>
                            ${SHOPPING_LIST[pending].amount.toFixed(2)}
                        </div>
                        <div className="bd-tx-badge evaluating">EVALUATING</div>
                    </div>
                )}

                {/* Completed items (newest first) */}
                {[...results].reverse().map((r, i) => (
                    <div key={`${r.item.item}-${i}`} className="bd-tx">
                        <div className="bd-tx-icon">{r.item.icon}</div>
                        <div className="bd-tx-info">
                            <div className="bd-tx-name">{r.item.item}</div>
                            <div className="bd-tx-detail">
                                {r.item.merchant} · {r.item.category} · {r.item.country}
                                {r.eval_ms > 0 && ` · ${r.eval_ms.toFixed(1)}ms`}
                            </div>
                            {r.explanation && (
                                <div className="bd-tx-reason">→ {r.explanation} ({r.policy_name})</div>
                            )}
                        </div>
                        <div className="bd-tx-amount" style={{
                            color: r.decision === 'allow' ? '#00ff88' :
                                r.decision === 'deny' ? '#ff4444' : '#ffbe00'
                        }}>
                            ${r.item.amount.toFixed(2)}
                        </div>
                        <div className={`bd-tx-badge ${r.decision}`}>
                            {r.decision === 'allow' ? '✓ ALLOWED' :
                                r.decision === 'deny' ? '✗ DENIED' : '⏳ REVIEW'}
                        </div>
                    </div>
                ))}
            </div>

            {/* Stats */}
            {results.length > 0 && (
                <div className="bd-stats">
                    <div className="bd-stat">
                        <div className="bd-stat-value green">{allowed}</div>
                        <div className="bd-stat-label">Allowed</div>
                    </div>
                    <div className="bd-stat">
                        <div className="bd-stat-value red">{denied}</div>
                        <div className="bd-stat-label">Denied</div>
                    </div>
                    <div className="bd-stat">
                        <div className="bd-stat-value yellow">{approvals}</div>
                        <div className="bd-stat-label">Review</div>
                    </div>
                    <div className="bd-stat">
                        <div className="bd-stat-value cyan">${totalSpent.toFixed(2)}</div>
                        <div className="bd-stat-label">Total Spent</div>
                    </div>
                </div>
            )}
        </div>
    );
}
