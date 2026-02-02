//! Core types for the policy engine

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Decision from policy evaluation
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum Decision {
    Allow,
    Deny,
    RequireApproval,
    RequireMfa,
    Escalate,
    RateLimit,
}

/// Priority level for rules
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "snake_case")]
pub enum Priority {
    Critical = 100,
    High = 75,
    Medium = 50,
    Low = 25,
    Default = 0,
}

impl Default for Priority {
    fn default() -> Self {
        Priority::Default
    }
}

/// Comparison operators for conditions
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum Operator {
    Equals,
    NotEquals,
    GreaterThan,
    LessThan,
    GreaterOrEqual,
    LessOrEqual,
    Contains,
    NotContains,
    StartsWith,
    EndsWith,
    Matches,      // Regex match
    In,           // Value in list
    NotIn,        // Value not in list
    Exists,
    NotExists,
    Between,
    IpInRange,    // IP address in CIDR range
    TimeInRange,  // Time within range
}

/// Value types for policy evaluation
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(untagged)]
pub enum Value {
    Null,
    Bool(bool),
    Int(i64),
    Float(f64),
    String(String),
    List(Vec<Value>),
    Object(HashMap<String, Value>),
}

impl Value {
    pub fn as_bool(&self) -> Option<bool> {
        match self {
            Value::Bool(b) => Some(*b),
            Value::Int(i) => Some(*i != 0),
            Value::String(s) => Some(!s.is_empty()),
            _ => None,
        }
    }

    pub fn as_i64(&self) -> Option<i64> {
        match self {
            Value::Int(i) => Some(*i),
            Value::Float(f) => Some(*f as i64),
            Value::String(s) => s.parse().ok(),
            _ => None,
        }
    }

    pub fn as_f64(&self) -> Option<f64> {
        match self {
            Value::Float(f) => Some(*f),
            Value::Int(i) => Some(*i as f64),
            Value::String(s) => s.parse().ok(),
            _ => None,
        }
    }

    pub fn as_str(&self) -> Option<&str> {
        match self {
            Value::String(s) => Some(s),
            _ => None,
        }
    }

    pub fn as_list(&self) -> Option<&Vec<Value>> {
        match self {
            Value::List(l) => Some(l),
            _ => None,
        }
    }

    pub fn as_object(&self) -> Option<&HashMap<String, Value>> {
        match self {
            Value::Object(o) => Some(o),
            _ => None,
        }
    }

    pub fn is_truthy(&self) -> bool {
        match self {
            Value::Null => false,
            Value::Bool(b) => *b,
            Value::Int(i) => *i != 0,
            Value::Float(f) => *f != 0.0,
            Value::String(s) => !s.is_empty(),
            Value::List(l) => !l.is_empty(),
            Value::Object(o) => !o.is_empty(),
        }
    }
}

/// Result of policy evaluation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvaluationResult {
    pub decision: Decision,
    pub matched_rules: Vec<String>,
    pub metadata: HashMap<String, Value>,
    pub evaluation_time_ms: f64,
    pub risk_score: f64,
    pub constraints: Vec<Constraint>,
    pub audit_data: AuditData,
}

impl Default for EvaluationResult {
    fn default() -> Self {
        EvaluationResult {
            decision: Decision::Deny,
            matched_rules: Vec::new(),
            metadata: HashMap::new(),
            evaluation_time_ms: 0.0,
            risk_score: 0.0,
            constraints: Vec::new(),
            audit_data: AuditData::default(),
        }
    }
}

/// Constraint applied to authorized requests
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Constraint {
    pub constraint_type: ConstraintType,
    pub value: Value,
    pub message: String,
}

/// Types of constraints
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum ConstraintType {
    MaxAmount,
    MaxTransactions,
    AllowedActions,
    AllowedResources,
    TimeWindow,
    RequiredApprovers,
    SessionTimeout,
    GeographicRestriction,
    RateLimitPerMinute,
    RateLimitPerHour,
    Custom(String),
}

/// Audit data for the evaluation
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AuditData {
    pub request_hash: String,
    pub context_hash: String,
    pub rules_evaluated: usize,
    pub timestamp: i64,
    pub trace_id: String,
}

/// Engine statistics
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EngineStats {
    pub total_rules: usize,
    pub active_rules: usize,
    pub evaluations_count: u64,
    pub average_eval_time_ms: f64,
    pub cache_hit_rate: f64,
}

/// Risk level classification
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "snake_case")]
pub enum RiskLevel {
    Critical,
    High,
    Medium,
    Low,
    None,
}

impl RiskLevel {
    pub fn from_score(score: f64) -> Self {
        match score {
            s if s >= 0.9 => RiskLevel::Critical,
            s if s >= 0.7 => RiskLevel::High,
            s if s >= 0.4 => RiskLevel::Medium,
            s if s >= 0.1 => RiskLevel::Low,
            _ => RiskLevel::None,
        }
    }

    pub fn to_score(&self) -> f64 {
        match self {
            RiskLevel::Critical => 1.0,
            RiskLevel::High => 0.8,
            RiskLevel::Medium => 0.5,
            RiskLevel::Low => 0.2,
            RiskLevel::None => 0.0,
        }
    }
}
