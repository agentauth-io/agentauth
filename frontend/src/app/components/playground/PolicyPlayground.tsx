import React, { useState, useCallback, useEffect } from 'react';
import '../../../styles/playground.css';

/* ──────────────── types ──────────────── */
interface ConditionDef {
    attribute: string;
    operator: string;
    value: any;
}
interface RuleDef {
    conditions: ConditionDef[];
    logic: string;
}
interface PolicyDef {
    id: string;
    name: string;
    effect: string;
    priority: number;
    description: string;
    constraints: Record<string, any>;
    rules: RuleDef[];
}
interface TraceEntry {
    policy_id: string;
    policy_name: string;
    effect: string;
    applies: boolean;
    explanation: string;
}
interface EvalResult {
    decision: string;
    allowed: boolean;
    explanation: string;
    risk_score: number;
    evaluation_time_ms: number;
    policies_evaluated: number;
    deciding_policy_id: string | null;
    deciding_policy_name: string | null;
    constraints: Record<string, any>;
    trace: TraceEntry[];
}

/* ──────────────── API URL ──────────────── */
const API_BASE = import.meta.env.VITE_API_URL || 'https://agentauth-api.koyeb.app';

/* ──────────────── default data ──────────────── */
const DEFAULT_POLICIES: PolicyDef[] = [
    {
        id: 'pol_budget',
        name: 'Daily Budget Limit',
        effect: 'allow',
        priority: 10,
        description: 'Allow purchases up to $200 each, within approved categories',
        constraints: { daily_limit: 500.0 },
        rules: [{
            conditions: [
                { attribute: 'amount', operator: 'lte', value: 200.0 },
                { attribute: 'category', operator: 'in', value: ['groceries', 'electronics', 'clothing', 'home'] }
            ],
            logic: 'and'
        }]
    },
    {
        id: 'pol_block_risk',
        name: 'Block Risky Categories',
        effect: 'deny',
        priority: 100,
        description: 'Block gambling, crypto, and adult categories',
        constraints: {},
        rules: [{
            conditions: [
                { attribute: 'category', operator: 'in', value: ['gambling', 'crypto', 'adult', 'alcohol'] }
            ],
            logic: 'and'
        }]
    }
];

const DEFAULT_CONTEXT = {
    agent_id: 'shopping-bot-1',
    action: 'purchase',
    amount: 45.99,
    merchant: 'Walmart',
    category: 'groceries',
    merchant_country: 'US'
};

/* ──────────────── helpers ──────────────── */
const prettyJSON = (obj: any) => JSON.stringify(obj, null, 2);

/* ──────────────── component ──────────────── */
export default function PolicyPlayground() {
    const [policiesStr, setPoliciesStr] = useState(prettyJSON(DEFAULT_POLICIES));
    const [contextStr, setContextStr] = useState(prettyJSON(DEFAULT_CONTEXT));
    const [algorithm, setAlgorithm] = useState('deny_overrides');
    const [result, setResult] = useState<EvalResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [templates, setTemplates] = useState<Record<string, any>>({});
    const [activeTemplate, setActiveTemplate] = useState<string | null>(null);

    /* fetch templates on mount */
    useEffect(() => {
        fetch(`${API_BASE}/v1/playground/templates`)
            .then(r => r.json())
            .then(data => setTemplates(data.templates || {}))
            .catch(() => { /* silently fail — templates are optional */ });
    }, []);

    /* apply template */
    const applyTemplate = useCallback((key: string) => {
        const t = templates[key];
        if (!t) return;
        setPoliciesStr(prettyJSON(t.policies));
        setContextStr(prettyJSON(t.context));
        setActiveTemplate(key);
        setResult(null);
        setError(null);
    }, [templates]);

    /* evaluate */
    const evaluate = useCallback(async () => {
        setLoading(true);
        setError(null);
        setResult(null);

        let policies: PolicyDef[];
        let context: Record<string, any>;

        try {
            policies = JSON.parse(policiesStr);
        } catch {
            setError('Invalid JSON in Policies panel');
            setLoading(false);
            return;
        }
        try {
            context = JSON.parse(contextStr);
        } catch {
            setError('Invalid JSON in Context panel');
            setLoading(false);
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/v1/playground/evaluate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    policies,
                    context,
                    combine_algorithm: algorithm,
                }),
            });
            if (!res.ok) {
                const body = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(body.detail || `HTTP ${res.status}`);
            }
            const data: EvalResult = await res.json();
            setResult(data);
        } catch (e: any) {
            setError(e.message || 'Evaluation failed');
        } finally {
            setLoading(false);
        }
    }, [policiesStr, contextStr, algorithm]);

    const templateKeys = Object.keys(templates);

    return (
        <div className="pg-shell">
            {/* Header */}
            <div className="pg-header">
                <div>
                    <h1>◈ Policy Playground</h1>
                    <div className="pg-subtitle">Interactive policy evaluator — real PolicyEngine, zero auth</div>
                </div>
                <a href="/dashboard" className="pg-back">← NUCLEUS</a>
            </div>

            {/* Template selector */}
            {templateKeys.length > 0 && (
                <div className="pg-templates">
                    <label>Templates</label>
                    {templateKeys.map(k => (
                        <button
                            key={k}
                            className={`pg-tmpl-btn ${activeTemplate === k ? 'active' : ''}`}
                            onClick={() => applyTemplate(k)}
                        >
                            {templates[k].name}
                        </button>
                    ))}
                </div>
            )}

            {/* Split panels */}
            <div className="pg-panels">
                {/* Policies Editor */}
                <div className="pg-panel">
                    <div className="pg-panel-header">
                        <h3>Policies</h3>
                        <span className="pg-badge">JSON</span>
                    </div>
                    <textarea
                        className="pg-editor"
                        value={policiesStr}
                        onChange={e => { setPoliciesStr(e.target.value); setActiveTemplate(null); }}
                        spellCheck={false}
                    />
                </div>

                {/* Context Editor */}
                <div className="pg-panel">
                    <div className="pg-panel-header">
                        <h3>Request Context</h3>
                        <span className="pg-badge">JSON</span>
                    </div>
                    <textarea
                        className="pg-editor"
                        value={contextStr}
                        onChange={e => { setContextStr(e.target.value); setActiveTemplate(null); }}
                        spellCheck={false}
                    />
                </div>
            </div>

            {/* Action bar */}
            <div className="pg-action-bar">
                <button className="pg-evaluate-btn" onClick={evaluate} disabled={loading}>
                    {loading ? '⟳ Evaluating…' : '▶ Evaluate'}
                </button>
                <select className="pg-algo-select" value={algorithm} onChange={e => setAlgorithm(e.target.value)}>
                    <option value="deny_overrides">Deny Overrides</option>
                    <option value="allow_overrides">Allow Overrides</option>
                    <option value="first_applicable">First Applicable</option>
                    <option value="unanimous">Unanimous</option>
                </select>
            </div>

            {/* Error */}
            {error && <div className="pg-error">⚠ {error}</div>}

            {/* Result */}
            {result ? (
                <div className="pg-result">
                    <div className="pg-result-header">
                        <span className={`pg-decision-badge ${result.decision}`}>
                            {result.decision === 'allow' ? '✓ ALLOW' :
                                result.decision === 'deny' ? '✗ DENY' :
                                    '⏳ REQUIRE APPROVAL'}
                        </span>
                        <div className="pg-result-meta">
                            <div className="meta-item">
                                <div className="meta-label">Risk Score</div>
                                <div className="meta-value">{(result.risk_score * 100).toFixed(0)}%</div>
                            </div>
                            <div className="meta-item">
                                <div className="meta-label">Eval Time</div>
                                <div className="meta-value">{result.evaluation_time_ms.toFixed(2)}ms</div>
                            </div>
                            <div className="meta-item">
                                <div className="meta-label">Policies</div>
                                <div className="meta-value">{result.policies_evaluated}</div>
                            </div>
                            {result.deciding_policy_name && (
                                <div className="meta-item">
                                    <div className="meta-label">Deciding Policy</div>
                                    <div className="meta-value">{result.deciding_policy_name}</div>
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="pg-result-body">
                        <div className="pg-explanation">{result.explanation}</div>

                        {/* Trace */}
                        {result.trace.length > 0 && (
                            <>
                                <div className="pg-trace-title">Evaluation Trace</div>
                                <ul className="pg-trace-list">
                                    {result.trace.map((t, i) => (
                                        <li key={i} className="pg-trace-item">
                                            <span className={`trace-indicator ${t.applies ? 'matched' : 'unmatched'}`} />
                                            <span className="trace-name">{t.policy_name}</span>
                                            <span className={`trace-effect ${t.effect}`}>{t.effect.toUpperCase()}</span>
                                            <span className="trace-explanation">{t.explanation}</span>
                                        </li>
                                    ))}
                                </ul>
                            </>
                        )}
                    </div>
                </div>
            ) : !error && (
                <div className="pg-result">
                    <div className="pg-empty">
                        <div className="pg-empty-icon">◈</div>
                        <p>Write policies, define context, click Evaluate</p>
                    </div>
                </div>
            )}
        </div>
    );
}
