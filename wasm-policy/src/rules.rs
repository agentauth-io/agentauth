//! Rule definitions for the policy engine

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use crate::types::{Decision, Operator, Priority, Value, Constraint, ConstraintType};
use crate::context::EvaluationContext;

/// A policy rule
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Rule {
    /// Unique rule identifier
    pub id: String,
    
    /// Human-readable name
    pub name: String,
    
    /// Description of what this rule does
    #[serde(default)]
    pub description: String,
    
    /// Whether the rule is enabled
    #[serde(default = "default_true")]
    pub enabled: bool,
    
    /// Rule priority
    #[serde(default)]
    pub priority: Priority,
    
    /// Conditions that must be met
    pub conditions: Vec<Condition>,
    
    /// How conditions are combined (all = AND, any = OR)
    #[serde(default = "default_all")]
    pub condition_logic: ConditionLogic,
    
    /// Action to take when conditions match
    pub action: Action,
    
    /// Rule tags for organization
    #[serde(default)]
    pub tags: Vec<String>,
    
    /// Creation timestamp
    #[serde(default)]
    pub created_at: i64,
    
    /// Last modification timestamp
    #[serde(default)]
    pub updated_at: i64,
}

fn default_true() -> bool { true }
fn default_all() -> ConditionLogic { ConditionLogic::All }

/// Logic for combining conditions
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum ConditionLogic {
    All,    // AND
    Any,    // OR
    None,   // NOR (none should match)
}

/// A condition to evaluate
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Condition {
    /// Path to the value in the context
    pub field: String,
    
    /// Comparison operator
    pub operator: Operator,
    
    /// Value to compare against
    pub value: Value,
    
    /// Optional negation
    #[serde(default)]
    pub negate: bool,
    
    /// Nested conditions for complex logic
    #[serde(default)]
    pub nested: Option<Box<NestedCondition>>,
}

/// Nested conditions for complex logic
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NestedCondition {
    pub logic: ConditionLogic,
    pub conditions: Vec<Condition>,
}

/// Action to take when conditions match
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Action {
    /// The decision to make
    pub decision: Decision,
    
    /// Risk score adjustment (-1.0 to 1.0)
    #[serde(default)]
    pub risk_adjustment: f64,
    
    /// Constraints to apply
    #[serde(default)]
    pub constraints: Vec<Constraint>,
    
    /// Metadata to include in result
    #[serde(default)]
    pub metadata: HashMap<String, Value>,
    
    /// Message for audit log
    #[serde(default)]
    pub audit_message: Option<String>,
    
    /// Whether to stop evaluating further rules
    #[serde(default)]
    pub terminal: bool,
}

/// A collection of rules
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct RuleSet {
    pub rules: Vec<Rule>,
    #[serde(default)]
    pub default_decision: Option<Decision>,
    #[serde(default)]
    pub version: String,
}

impl Condition {
    /// Evaluate this condition against a context
    pub fn evaluate(&self, ctx: &EvaluationContext) -> bool {
        let result = if let Some(ref nested) = self.nested {
            Self::evaluate_nested(nested, ctx)
        } else {
            self.evaluate_simple(ctx)
        };
        
        if self.negate { !result } else { result }
    }

    fn evaluate_simple(&self, ctx: &EvaluationContext) -> bool {
        let field_value = match ctx.get(&self.field) {
            Some(v) => v,
            None => {
                // Handle Exists/NotExists operators
                return matches!(self.operator, Operator::NotExists);
            }
        };

        match &self.operator {
            Operator::Exists => true, // We already checked it exists
            Operator::NotExists => false, // We already checked it exists
            
            Operator::Equals => self.compare_equals(&field_value, &self.value),
            Operator::NotEquals => !self.compare_equals(&field_value, &self.value),
            
            Operator::GreaterThan => self.compare_numeric(&field_value, &self.value, |a, b| a > b),
            Operator::LessThan => self.compare_numeric(&field_value, &self.value, |a, b| a < b),
            Operator::GreaterOrEqual => self.compare_numeric(&field_value, &self.value, |a, b| a >= b),
            Operator::LessOrEqual => self.compare_numeric(&field_value, &self.value, |a, b| a <= b),
            
            Operator::Contains => self.check_contains(&field_value, &self.value),
            Operator::NotContains => !self.check_contains(&field_value, &self.value),
            
            Operator::StartsWith => self.check_starts_with(&field_value, &self.value),
            Operator::EndsWith => self.check_ends_with(&field_value, &self.value),
            
            Operator::Matches => self.check_regex(&field_value, &self.value),
            
            Operator::In => self.check_in(&field_value, &self.value),
            Operator::NotIn => !self.check_in(&field_value, &self.value),
            
            Operator::Between => self.check_between(&field_value, &self.value),
            
            Operator::IpInRange => self.check_ip_in_range(&field_value, &self.value),
            Operator::TimeInRange => self.check_time_in_range(&field_value, &self.value),
        }
    }

    fn evaluate_nested(nested: &NestedCondition, ctx: &EvaluationContext) -> bool {
        match nested.logic {
            ConditionLogic::All => nested.conditions.iter().all(|c| c.evaluate(ctx)),
            ConditionLogic::Any => nested.conditions.iter().any(|c| c.evaluate(ctx)),
            ConditionLogic::None => !nested.conditions.iter().any(|c| c.evaluate(ctx)),
        }
    }

    fn compare_equals(&self, field: &Value, target: &Value) -> bool {
        match (field, target) {
            (Value::String(a), Value::String(b)) => a.to_lowercase() == b.to_lowercase(),
            (Value::Int(a), Value::Int(b)) => a == b,
            (Value::Float(a), Value::Float(b)) => (a - b).abs() < f64::EPSILON,
            (Value::Int(a), Value::Float(b)) | (Value::Float(b), Value::Int(a)) => {
                ((*a as f64) - b).abs() < f64::EPSILON
            }
            (Value::Bool(a), Value::Bool(b)) => a == b,
            (Value::Null, Value::Null) => true,
            _ => false,
        }
    }

    fn compare_numeric<F>(&self, field: &Value, target: &Value, cmp: F) -> bool
    where
        F: Fn(f64, f64) -> bool,
    {
        let a = match field.as_f64() {
            Some(v) => v,
            None => return false,
        };
        let b = match target.as_f64() {
            Some(v) => v,
            None => return false,
        };
        cmp(a, b)
    }

    fn check_contains(&self, field: &Value, target: &Value) -> bool {
        match (field, target) {
            (Value::String(haystack), Value::String(needle)) => {
                haystack.to_lowercase().contains(&needle.to_lowercase())
            }
            (Value::List(list), target) => list.iter().any(|v| self.compare_equals(v, target)),
            _ => false,
        }
    }

    fn check_starts_with(&self, field: &Value, target: &Value) -> bool {
        match (field.as_str(), target.as_str()) {
            (Some(s), Some(prefix)) => s.to_lowercase().starts_with(&prefix.to_lowercase()),
            _ => false,
        }
    }

    fn check_ends_with(&self, field: &Value, target: &Value) -> bool {
        match (field.as_str(), target.as_str()) {
            (Some(s), Some(suffix)) => s.to_lowercase().ends_with(&suffix.to_lowercase()),
            _ => false,
        }
    }

    fn check_regex(&self, field: &Value, pattern: &Value) -> bool {
        match (field.as_str(), pattern.as_str()) {
            (Some(s), Some(p)) => {
                regex::Regex::new(p)
                    .map(|re| re.is_match(s))
                    .unwrap_or(false)
            }
            _ => false,
        }
    }

    fn check_in(&self, field: &Value, list: &Value) -> bool {
        match list {
            Value::List(items) => items.iter().any(|item| self.compare_equals(field, item)),
            _ => false,
        }
    }

    fn check_between(&self, field: &Value, range: &Value) -> bool {
        let val = match field.as_f64() {
            Some(v) => v,
            None => return false,
        };
        
        match range {
            Value::List(bounds) if bounds.len() >= 2 => {
                let min = bounds[0].as_f64().unwrap_or(f64::MIN);
                let max = bounds[1].as_f64().unwrap_or(f64::MAX);
                val >= min && val <= max
            }
            _ => false,
        }
    }

    fn check_ip_in_range(&self, ip: &Value, cidr: &Value) -> bool {
        let ip_str = match ip.as_str() {
            Some(s) => s,
            None => return false,
        };
        let cidr_str = match cidr.as_str() {
            Some(s) => s,
            None => return false,
        };
        
        // Parse CIDR notation (e.g., "192.168.1.0/24")
        let parts: Vec<&str> = cidr_str.split('/').collect();
        if parts.len() != 2 {
            return false;
        }
        
        let network_ip = parts[0];
        let prefix_len: u32 = match parts[1].parse() {
            Ok(v) => v,
            Err(_) => return false,
        };
        
        // Simple IPv4 check
        let ip_octets: Vec<u8> = ip_str
            .split('.')
            .filter_map(|s| s.parse().ok())
            .collect();
        let network_octets: Vec<u8> = network_ip
            .split('.')
            .filter_map(|s| s.parse().ok())
            .collect();
        
        if ip_octets.len() != 4 || network_octets.len() != 4 {
            return false;
        }
        
        let ip_num = u32::from_be_bytes([ip_octets[0], ip_octets[1], ip_octets[2], ip_octets[3]]);
        let network_num = u32::from_be_bytes([network_octets[0], network_octets[1], network_octets[2], network_octets[3]]);
        let mask = if prefix_len == 0 { 0 } else { !0u32 << (32 - prefix_len) };
        
        (ip_num & mask) == (network_num & mask)
    }

    fn check_time_in_range(&self, time: &Value, range: &Value) -> bool {
        // Expects time as hour (0-23) and range as [start_hour, end_hour]
        let hour = match time.as_i64() {
            Some(h) => h,
            None => return false,
        };
        
        match range {
            Value::List(bounds) if bounds.len() >= 2 => {
                let start = bounds[0].as_i64().unwrap_or(0);
                let end = bounds[1].as_i64().unwrap_or(23);
                
                if start <= end {
                    hour >= start && hour <= end
                } else {
                    // Handle overnight ranges (e.g., 22-6)
                    hour >= start || hour <= end
                }
            }
            _ => false,
        }
    }
}

impl Rule {
    /// Check if this rule applies to the given context
    pub fn matches(&self, ctx: &EvaluationContext) -> bool {
        if !self.enabled {
            return false;
        }

        match self.condition_logic {
            ConditionLogic::All => self.conditions.iter().all(|c| c.evaluate(ctx)),
            ConditionLogic::Any => self.conditions.iter().any(|c| c.evaluate(ctx)),
            ConditionLogic::None => !self.conditions.iter().any(|c| c.evaluate(ctx)),
        }
    }
}

impl RuleSet {
    pub fn new() -> Self {
        RuleSet::default()
    }

    pub fn with_rules(rules: Vec<Rule>) -> Self {
        RuleSet {
            rules,
            default_decision: Some(Decision::Deny),
            version: "1.0".to_string(),
        }
    }

    pub fn add_rule(&mut self, rule: Rule) {
        self.rules.push(rule);
        self.sort_by_priority();
    }

    pub fn remove_rule(&mut self, id: &str) -> bool {
        let initial_len = self.rules.len();
        self.rules.retain(|r| r.id != id);
        self.rules.len() < initial_len
    }

    pub fn sort_by_priority(&mut self) {
        self.rules.sort_by(|a, b| b.priority.cmp(&a.priority));
    }

    pub fn get_rule(&self, id: &str) -> Option<&Rule> {
        self.rules.iter().find(|r| r.id == id)
    }
}

/// Builder for creating rules
pub struct RuleBuilder {
    rule: Rule,
}

impl RuleBuilder {
    pub fn new(id: &str, name: &str) -> Self {
        RuleBuilder {
            rule: Rule {
                id: id.to_string(),
                name: name.to_string(),
                description: String::new(),
                enabled: true,
                priority: Priority::default(),
                conditions: Vec::new(),
                condition_logic: ConditionLogic::All,
                action: Action {
                    decision: Decision::Deny,
                    risk_adjustment: 0.0,
                    constraints: Vec::new(),
                    metadata: HashMap::new(),
                    audit_message: None,
                    terminal: false,
                },
                tags: Vec::new(),
                created_at: chrono::Utc::now().timestamp_millis(),
                updated_at: chrono::Utc::now().timestamp_millis(),
            },
        }
    }

    pub fn description(mut self, desc: &str) -> Self {
        self.rule.description = desc.to_string();
        self
    }

    pub fn priority(mut self, priority: Priority) -> Self {
        self.rule.priority = priority;
        self
    }

    pub fn condition(mut self, condition: Condition) -> Self {
        self.rule.conditions.push(condition);
        self
    }

    pub fn when(self, field: &str, op: Operator, value: Value) -> Self {
        self.condition(Condition {
            field: field.to_string(),
            operator: op,
            value,
            negate: false,
            nested: None,
        })
    }

    pub fn logic(mut self, logic: ConditionLogic) -> Self {
        self.rule.condition_logic = logic;
        self
    }

    pub fn decision(mut self, decision: Decision) -> Self {
        self.rule.action.decision = decision;
        self
    }

    pub fn risk_adjustment(mut self, adjustment: f64) -> Self {
        self.rule.action.risk_adjustment = adjustment;
        self
    }

    pub fn constraint(mut self, constraint: Constraint) -> Self {
        self.rule.action.constraints.push(constraint);
        self
    }

    pub fn max_amount(self, amount: f64) -> Self {
        self.constraint(Constraint {
            constraint_type: ConstraintType::MaxAmount,
            value: Value::Float(amount),
            message: format!("Maximum amount: ${:.2}", amount),
        })
    }

    pub fn terminal(mut self) -> Self {
        self.rule.action.terminal = true;
        self
    }

    pub fn tag(mut self, tag: &str) -> Self {
        self.rule.tags.push(tag.to_string());
        self
    }

    pub fn build(self) -> Rule {
        self.rule
    }
}
