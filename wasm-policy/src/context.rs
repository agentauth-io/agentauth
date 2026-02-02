//! Evaluation context for policy decisions

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use crate::types::Value;

/// The context in which a policy is evaluated
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvaluationContext {
    /// Request-specific data
    pub request: RequestContext,
    
    /// Agent/identity making the request
    pub agent: AgentContext,
    
    /// Resource being accessed
    pub resource: ResourceContext,
    
    /// Environmental factors
    pub environment: EnvironmentContext,
    
    /// Historical data for risk assessment
    #[serde(default)]
    pub history: HistoryContext,
    
    /// Additional custom attributes
    #[serde(default)]
    pub attributes: HashMap<String, Value>,
}

/// Request-specific context
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RequestContext {
    /// Unique request identifier
    pub id: String,
    
    /// The action being requested
    pub action: String,
    
    /// Request timestamp (Unix millis)
    pub timestamp: i64,
    
    /// Request parameters
    #[serde(default)]
    pub params: HashMap<String, Value>,
    
    /// Monetary amount (if applicable)
    #[serde(default)]
    pub amount: Option<f64>,
    
    /// Currency code
    #[serde(default)]
    pub currency: Option<String>,
    
    /// Target merchant/vendor
    #[serde(default)]
    pub merchant: Option<String>,
    
    /// Category of transaction
    #[serde(default)]
    pub category: Option<String>,
    
    /// Request signature for verification
    #[serde(default)]
    pub signature: Option<String>,
}

/// Agent/identity context
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentContext {
    /// Agent identifier
    pub id: String,
    
    /// Agent type (human, ai, service, etc.)
    pub agent_type: String,
    
    /// Roles assigned to the agent
    #[serde(default)]
    pub roles: Vec<String>,
    
    /// Groups the agent belongs to
    #[serde(default)]
    pub groups: Vec<String>,
    
    /// Trust score (0.0 - 1.0)
    #[serde(default)]
    pub trust_score: f64,
    
    /// Whether the agent has been verified
    #[serde(default)]
    pub verified: bool,
    
    /// Permission tier
    #[serde(default)]
    pub tier: Option<String>,
    
    /// Agent metadata
    #[serde(default)]
    pub metadata: HashMap<String, Value>,
}

/// Resource context
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceContext {
    /// Resource identifier
    pub id: String,
    
    /// Resource type (account, file, api, etc.)
    pub resource_type: String,
    
    /// Owner of the resource
    #[serde(default)]
    pub owner: Option<String>,
    
    /// Sensitivity level
    #[serde(default)]
    pub sensitivity: String,
    
    /// Resource tags
    #[serde(default)]
    pub tags: Vec<String>,
    
    /// Resource attributes
    #[serde(default)]
    pub attributes: HashMap<String, Value>,
}

impl Default for ResourceContext {
    fn default() -> Self {
        ResourceContext {
            id: String::new(),
            resource_type: String::new(),
            owner: None,
            sensitivity: "normal".to_string(),
            tags: Vec::new(),
            attributes: HashMap::new(),
        }
    }
}

/// Environment context
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvironmentContext {
    /// Client IP address
    #[serde(default)]
    pub ip_address: Option<String>,
    
    /// Geographic location
    #[serde(default)]
    pub geo: Option<GeoLocation>,
    
    /// Device information
    #[serde(default)]
    pub device: Option<DeviceInfo>,
    
    /// Current time (ISO 8601)
    #[serde(default)]
    pub current_time: Option<String>,
    
    /// Day of week (0-6, Sunday = 0)
    #[serde(default)]
    pub day_of_week: Option<u8>,
    
    /// Hour of day (0-23)
    #[serde(default)]
    pub hour_of_day: Option<u8>,
    
    /// Whether this is during business hours
    #[serde(default)]
    pub is_business_hours: bool,
    
    /// Network type
    #[serde(default)]
    pub network_type: Option<String>,
    
    /// TLS version
    #[serde(default)]
    pub tls_version: Option<String>,
    
    /// Session information
    #[serde(default)]
    pub session: Option<SessionInfo>,
}

impl Default for EnvironmentContext {
    fn default() -> Self {
        EnvironmentContext {
            ip_address: None,
            geo: None,
            device: None,
            current_time: None,
            day_of_week: None,
            hour_of_day: None,
            is_business_hours: false,
            network_type: None,
            tls_version: None,
            session: None,
        }
    }
}

/// Geographic location
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeoLocation {
    pub country: String,
    #[serde(default)]
    pub region: Option<String>,
    #[serde(default)]
    pub city: Option<String>,
    #[serde(default)]
    pub latitude: Option<f64>,
    #[serde(default)]
    pub longitude: Option<f64>,
    #[serde(default)]
    pub timezone: Option<String>,
}

/// Device information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeviceInfo {
    #[serde(default)]
    pub id: Option<String>,
    #[serde(default)]
    pub device_type: Option<String>,
    #[serde(default)]
    pub os: Option<String>,
    #[serde(default)]
    pub browser: Option<String>,
    #[serde(default)]
    pub trusted: bool,
    #[serde(default)]
    pub fingerprint: Option<String>,
}

/// Session information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionInfo {
    pub id: String,
    pub created_at: i64,
    #[serde(default)]
    pub last_activity: Option<i64>,
    #[serde(default)]
    pub mfa_verified: bool,
    #[serde(default)]
    pub auth_method: Option<String>,
}

/// Historical context for risk assessment
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct HistoryContext {
    /// Number of requests in last hour
    #[serde(default)]
    pub requests_last_hour: u64,
    
    /// Number of requests in last day
    #[serde(default)]
    pub requests_last_day: u64,
    
    /// Amount spent in last hour
    #[serde(default)]
    pub amount_last_hour: f64,
    
    /// Amount spent in last day
    #[serde(default)]
    pub amount_last_day: f64,
    
    /// Amount spent in last month
    #[serde(default)]
    pub amount_last_month: f64,
    
    /// Number of failed attempts
    #[serde(default)]
    pub failed_attempts: u64,
    
    /// Last failed attempt timestamp
    #[serde(default)]
    pub last_failed_at: Option<i64>,
    
    /// Unusual activity flags
    #[serde(default)]
    pub anomaly_flags: Vec<String>,
    
    /// Previous authorization IDs
    #[serde(default)]
    pub previous_authorizations: Vec<String>,
}

impl EvaluationContext {
    /// Get a value from the context by path (e.g., "request.amount")
    pub fn get(&self, path: &str) -> Option<Value> {
        let parts: Vec<&str> = path.split('.').collect();
        if parts.is_empty() {
            return None;
        }

        match parts[0] {
            "request" => self.get_request_value(&parts[1..]),
            "agent" => self.get_agent_value(&parts[1..]),
            "resource" => self.get_resource_value(&parts[1..]),
            "environment" => self.get_environment_value(&parts[1..]),
            "history" => self.get_history_value(&parts[1..]),
            "attributes" => {
                if parts.len() > 1 {
                    self.attributes.get(parts[1]).cloned()
                } else {
                    None
                }
            }
            _ => None,
        }
    }

    fn get_request_value(&self, parts: &[&str]) -> Option<Value> {
        if parts.is_empty() {
            return None;
        }
        match parts[0] {
            "id" => Some(Value::String(self.request.id.clone())),
            "action" => Some(Value::String(self.request.action.clone())),
            "timestamp" => Some(Value::Int(self.request.timestamp)),
            "amount" => self.request.amount.map(Value::Float),
            "currency" => self.request.currency.clone().map(Value::String),
            "merchant" => self.request.merchant.clone().map(Value::String),
            "category" => self.request.category.clone().map(Value::String),
            "params" => {
                if parts.len() > 1 {
                    self.request.params.get(parts[1]).cloned()
                } else {
                    Some(Value::Object(self.request.params.clone()))
                }
            }
            _ => None,
        }
    }

    fn get_agent_value(&self, parts: &[&str]) -> Option<Value> {
        if parts.is_empty() {
            return None;
        }
        match parts[0] {
            "id" => Some(Value::String(self.agent.id.clone())),
            "agent_type" | "type" => Some(Value::String(self.agent.agent_type.clone())),
            "roles" => Some(Value::List(
                self.agent.roles.iter().map(|r| Value::String(r.clone())).collect()
            )),
            "groups" => Some(Value::List(
                self.agent.groups.iter().map(|g| Value::String(g.clone())).collect()
            )),
            "trust_score" => Some(Value::Float(self.agent.trust_score)),
            "verified" => Some(Value::Bool(self.agent.verified)),
            "tier" => self.agent.tier.clone().map(Value::String),
            _ => None,
        }
    }

    fn get_resource_value(&self, parts: &[&str]) -> Option<Value> {
        if parts.is_empty() {
            return None;
        }
        match parts[0] {
            "id" => Some(Value::String(self.resource.id.clone())),
            "resource_type" | "type" => Some(Value::String(self.resource.resource_type.clone())),
            "owner" => self.resource.owner.clone().map(Value::String),
            "sensitivity" => Some(Value::String(self.resource.sensitivity.clone())),
            "tags" => Some(Value::List(
                self.resource.tags.iter().map(|t| Value::String(t.clone())).collect()
            )),
            _ => None,
        }
    }

    fn get_environment_value(&self, parts: &[&str]) -> Option<Value> {
        if parts.is_empty() {
            return None;
        }
        match parts[0] {
            "ip_address" => self.environment.ip_address.clone().map(Value::String),
            "is_business_hours" => Some(Value::Bool(self.environment.is_business_hours)),
            "hour_of_day" => self.environment.hour_of_day.map(|h| Value::Int(h as i64)),
            "day_of_week" => self.environment.day_of_week.map(|d| Value::Int(d as i64)),
            "geo" => {
                if let Some(ref geo) = self.environment.geo {
                    if parts.len() > 1 {
                        match parts[1] {
                            "country" => Some(Value::String(geo.country.clone())),
                            "region" => geo.region.clone().map(Value::String),
                            "city" => geo.city.clone().map(Value::String),
                            _ => None,
                        }
                    } else {
                        None
                    }
                } else {
                    None
                }
            }
            _ => None,
        }
    }

    fn get_history_value(&self, parts: &[&str]) -> Option<Value> {
        if parts.is_empty() {
            return None;
        }
        match parts[0] {
            "requests_last_hour" => Some(Value::Int(self.history.requests_last_hour as i64)),
            "requests_last_day" => Some(Value::Int(self.history.requests_last_day as i64)),
            "amount_last_hour" => Some(Value::Float(self.history.amount_last_hour)),
            "amount_last_day" => Some(Value::Float(self.history.amount_last_day)),
            "amount_last_month" => Some(Value::Float(self.history.amount_last_month)),
            "failed_attempts" => Some(Value::Int(self.history.failed_attempts as i64)),
            _ => None,
        }
    }
}
