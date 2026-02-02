//! Policy evaluation engine

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

use crate::context::EvaluationContext;
use crate::rules::{Rule, RuleSet};
use crate::types::{
    AuditData, Decision, EngineStats, EvaluationResult, RiskLevel, Value,
};
use sha2::{Digest, Sha256};

/// The core policy evaluation engine
pub struct PolicyEngine {
    rules: RuleSet,
    stats: EngineState,
}

struct EngineState {
    evaluations: AtomicU64,
    total_time_ns: AtomicU64,
}

impl Default for EngineState {
    fn default() -> Self {
        EngineState {
            evaluations: AtomicU64::new(0),
            total_time_ns: AtomicU64::new(0),
        }
    }
}

impl PolicyEngine {
    /// Create a new policy engine with no rules
    pub fn new() -> Self {
        PolicyEngine {
            rules: RuleSet::new(),
            stats: EngineState::default(),
        }
    }

    /// Create from a RuleSet
    pub fn from_ruleset(rules: RuleSet) -> Self {
        PolicyEngine {
            rules,
            stats: EngineState::default(),
        }
    }

    /// Create from JSON string
    pub fn from_json(json: &str) -> Result<Self, serde_json::Error> {
        let rules: RuleSet = serde_json::from_str(json)?;
        Ok(Self::from_ruleset(rules))
    }

    /// Export rules as JSON
    pub fn to_json(&self) -> String {
        serde_json::to_string_pretty(&self.rules).unwrap_or_default()
    }

    /// Add a rule to the engine
    pub fn add_rule(&mut self, rule: Rule) {
        self.rules.add_rule(rule);
    }

    /// Remove a rule by ID
    pub fn remove_rule(&mut self, id: &str) -> bool {
        self.rules.remove_rule(id)
    }

    /// List all rule IDs
    pub fn list_rule_ids(&self) -> Vec<String> {
        self.rules.rules.iter().map(|r| r.id.clone()).collect()
    }

    /// Validate a rule
    pub fn validate_rule(&self, rule: &Rule) -> bool {
        // Check for valid ID
        if rule.id.is_empty() {
            return false;
        }
        
        // Check for duplicate ID
        if self.rules.rules.iter().any(|r| r.id == rule.id) {
            return false;
        }
        
        // Check for at least one condition
        if rule.conditions.is_empty() {
            return false;
        }
        
        true
    }

    /// Get engine statistics
    pub fn stats(&self) -> EngineStats {
        let evaluations = self.stats.evaluations.load(Ordering::Relaxed);
        let total_time_ns = self.stats.total_time_ns.load(Ordering::Relaxed);
        
        EngineStats {
            total_rules: self.rules.rules.len(),
            active_rules: self.rules.rules.iter().filter(|r| r.enabled).count(),
            evaluations_count: evaluations,
            average_eval_time_ms: if evaluations > 0 {
                (total_time_ns as f64 / evaluations as f64) / 1_000_000.0
            } else {
                0.0
            },
            cache_hit_rate: 0.0, // TODO: Implement caching
        }
    }

    /// Evaluate a context against all rules
    pub fn evaluate(&self, ctx: &EvaluationContext) -> EvaluationResult {
        let start = web_sys::window()
            .and_then(|w| w.performance())
            .map(|p| p.now())
            .unwrap_or(0.0);

        let mut result = EvaluationResult::default();
        let mut risk_score: f64 = 0.0;
        let mut matched_rules: Vec<String> = Vec::new();
        let mut final_decision = self.rules.default_decision.clone().unwrap_or(Decision::Deny);

        // Evaluate rules in priority order
        for rule in &self.rules.rules {
            if !rule.enabled {
                continue;
            }

            if rule.matches(ctx) {
                matched_rules.push(rule.id.clone());
                risk_score += rule.action.risk_adjustment;
                
                // Apply constraints
                result.constraints.extend(rule.action.constraints.clone());
                
                // Merge metadata
                for (key, value) in &rule.action.metadata {
                    result.metadata.insert(key.clone(), value.clone());
                }

                // Update decision
                final_decision = rule.action.decision.clone();

                // Check if this rule is terminal
                if rule.action.terminal {
                    break;
                }
            }
        }

        // Calculate final risk score
        result.risk_score = risk_score.clamp(0.0, 1.0);

        // Apply risk-based decision modification
        if result.risk_score >= 0.9 && !matches!(final_decision, Decision::Deny) {
            result.metadata.insert(
                "risk_override".to_string(),
                Value::String("high_risk_override".to_string()),
            );
            final_decision = Decision::Deny;
        } else if result.risk_score >= 0.7 && matches!(final_decision, Decision::Allow) {
            final_decision = Decision::RequireApproval;
        }

        result.decision = final_decision;
        result.matched_rules = matched_rules;

        // Generate audit data
        result.audit_data = AuditData {
            request_hash: self.hash_request(&ctx.request.id),
            context_hash: self.hash_context(ctx),
            rules_evaluated: self.rules.rules.iter().filter(|r| r.enabled).count(),
            timestamp: chrono::Utc::now().timestamp_millis(),
            trace_id: ctx.request.id.clone(),
        };

        // Calculate evaluation time
        let end = web_sys::window()
            .and_then(|w| w.performance())
            .map(|p| p.now())
            .unwrap_or(0.0);
        result.evaluation_time_ms = end - start;

        // Update stats
        self.stats.evaluations.fetch_add(1, Ordering::Relaxed);
        self.stats.total_time_ns.fetch_add(
            (result.evaluation_time_ms * 1_000_000.0) as u64,
            Ordering::Relaxed,
        );

        result
    }

    /// Evaluate with risk assessment
    pub fn evaluate_with_risk(&self, ctx: &EvaluationContext) -> EvaluationResult {
        let mut result = self.evaluate(ctx);
        
        // Calculate base risk factors
        let mut risk_factors: Vec<(String, f64)> = Vec::new();

        // Amount-based risk
        if let Some(amount) = ctx.request.amount {
            let amount_risk = match amount {
                a if a >= 10000.0 => 0.8,
                a if a >= 5000.0 => 0.6,
                a if a >= 1000.0 => 0.4,
                a if a >= 100.0 => 0.2,
                _ => 0.0,
            };
            if amount_risk > 0.0 {
                risk_factors.push(("high_amount".to_string(), amount_risk));
            }
        }

        // Velocity risk
        if ctx.history.requests_last_hour > 100 {
            risk_factors.push(("high_velocity".to_string(), 0.5));
        }

        // Trust score risk
        if ctx.agent.trust_score < 0.5 {
            risk_factors.push(("low_trust".to_string(), 0.5 - ctx.agent.trust_score));
        }

        // Failed attempts risk
        if ctx.history.failed_attempts > 3 {
            risk_factors.push(("failed_attempts".to_string(), 0.3));
        }

        // Geographic anomaly
        if ctx.history.anomaly_flags.contains(&"geo_anomaly".to_string()) {
            risk_factors.push(("geo_anomaly".to_string(), 0.4));
        }

        // Off-hours risk
        if !ctx.environment.is_business_hours {
            risk_factors.push(("off_hours".to_string(), 0.1));
        }

        // Calculate combined risk
        let total_risk: f64 = risk_factors.iter().map(|(_, r)| r).sum();
        result.risk_score = (result.risk_score + total_risk / 2.0).clamp(0.0, 1.0);

        // Add risk factors to metadata
        result.metadata.insert(
            "risk_factors".to_string(),
            Value::List(
                risk_factors
                    .iter()
                    .map(|(name, score)| {
                        Value::Object(
                            [
                                ("factor".to_string(), Value::String(name.clone())),
                                ("score".to_string(), Value::Float(*score)),
                            ]
                            .into_iter()
                            .collect(),
                        )
                    })
                    .collect(),
            ),
        );

        result.metadata.insert(
            "risk_level".to_string(),
            Value::String(format!("{:?}", RiskLevel::from_score(result.risk_score))),
        );

        result
    }

    fn hash_request(&self, request_id: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(request_id.as_bytes());
        hex::encode(hasher.finalize())
    }

    fn hash_context(&self, ctx: &EvaluationContext) -> String {
        let mut hasher = Sha256::new();
        hasher.update(ctx.request.id.as_bytes());
        hasher.update(ctx.agent.id.as_bytes());
        hasher.update(ctx.resource.id.as_bytes());
        hasher.update(ctx.request.action.as_bytes());
        hex::encode(hasher.finalize())
    }
}

impl Default for PolicyEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rules::{Condition, Action, ConditionLogic};
    use crate::types::Operator;

    fn create_test_context() -> EvaluationContext {
        EvaluationContext {
            request: crate::context::RequestContext {
                id: "req-123".to_string(),
                action: "purchase".to_string(),
                timestamp: chrono::Utc::now().timestamp_millis(),
                params: HashMap::new(),
                amount: Some(100.0),
                currency: Some("USD".to_string()),
                merchant: Some("Amazon".to_string()),
                category: Some("electronics".to_string()),
                signature: None,
            },
            agent: crate::context::AgentContext {
                id: "agent-1".to_string(),
                agent_type: "ai".to_string(),
                roles: vec!["shopper".to_string()],
                groups: vec![],
                trust_score: 0.8,
                verified: true,
                tier: Some("standard".to_string()),
                metadata: HashMap::new(),
            },
            resource: crate::context::ResourceContext::default(),
            environment: crate::context::EnvironmentContext::default(),
            history: crate::context::HistoryContext::default(),
            attributes: HashMap::new(),
        }
    }

    #[test]
    fn test_simple_evaluation() {
        let mut engine = PolicyEngine::new();
        
        engine.add_rule(Rule {
            id: "allow-small-purchases".to_string(),
            name: "Allow Small Purchases".to_string(),
            description: "Allow purchases under $500".to_string(),
            enabled: true,
            priority: crate::types::Priority::Medium,
            conditions: vec![
                Condition {
                    field: "request.amount".to_string(),
                    operator: Operator::LessThan,
                    value: Value::Float(500.0),
                    negate: false,
                    nested: None,
                },
            ],
            condition_logic: ConditionLogic::All,
            action: Action {
                decision: Decision::Allow,
                risk_adjustment: 0.0,
                constraints: vec![],
                metadata: HashMap::new(),
                audit_message: None,
                terminal: false,
            },
            tags: vec![],
            created_at: 0,
            updated_at: 0,
        });

        let ctx = create_test_context();
        let result = engine.evaluate(&ctx);
        
        assert_eq!(result.decision, Decision::Allow);
        assert!(result.matched_rules.contains(&"allow-small-purchases".to_string()));
    }
}
