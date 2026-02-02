//! WebAssembly Policy Engine for AgentAuth
//! 
//! This module provides a secure, portable policy evaluation engine
//! that runs in any WebAssembly runtime (browsers, Node.js, edge workers, etc.)

mod engine;
mod rules;
mod context;
mod types;
mod builtins;

pub use engine::PolicyEngine;
pub use rules::{Rule, RuleSet, Condition, Action};
pub use context::EvaluationContext;
pub use types::*;
pub use builtins::BuiltinFunctions;

use wasm_bindgen::prelude::*;

// Panic hook for better error messages
#[wasm_bindgen(start)]
pub fn init() {
    console_error_panic_hook::set_once();
}

/// Initialize the policy engine with a set of rules
#[wasm_bindgen]
pub fn create_engine(rules_json: &str) -> Result<PolicyEngineHandle, JsValue> {
    let engine = PolicyEngine::from_json(rules_json)
        .map_err(|e| JsValue::from_str(&e.to_string()))?;
    
    Ok(PolicyEngineHandle { engine })
}

/// WebAssembly handle to the policy engine
#[wasm_bindgen]
pub struct PolicyEngineHandle {
    engine: PolicyEngine,
}

#[wasm_bindgen]
impl PolicyEngineHandle {
    /// Evaluate a request against the policy rules
    pub fn evaluate(&self, context_json: &str) -> Result<JsValue, JsValue> {
        let context: EvaluationContext = serde_json::from_str(context_json)
            .map_err(|e| JsValue::from_str(&format!("Invalid context: {}", e)))?;
        
        let result = self.engine.evaluate(&context);
        
        serde_wasm_bindgen::to_value(&result)
            .map_err(|e| JsValue::from_str(&e.to_string()))
    }

    /// Add a new rule to the engine
    pub fn add_rule(&mut self, rule_json: &str) -> Result<(), JsValue> {
        let rule: Rule = serde_json::from_str(rule_json)
            .map_err(|e| JsValue::from_str(&format!("Invalid rule: {}", e)))?;
        
        self.engine.add_rule(rule);
        Ok(())
    }

    /// Remove a rule by ID
    pub fn remove_rule(&mut self, rule_id: &str) -> bool {
        self.engine.remove_rule(rule_id)
    }

    /// Get all rule IDs
    pub fn list_rules(&self) -> JsValue {
        let ids = self.engine.list_rule_ids();
        serde_wasm_bindgen::to_value(&ids).unwrap()
    }

    /// Export all rules as JSON
    pub fn export_rules(&self) -> String {
        self.engine.to_json()
    }

    /// Validate a rule without adding it
    pub fn validate_rule(&self, rule_json: &str) -> Result<bool, JsValue> {
        let rule: Rule = serde_json::from_str(rule_json)
            .map_err(|e| JsValue::from_str(&format!("Invalid rule: {}", e)))?;
        
        Ok(self.engine.validate_rule(&rule))
    }

    /// Get engine statistics
    pub fn get_stats(&self) -> JsValue {
        serde_wasm_bindgen::to_value(&self.engine.stats()).unwrap()
    }
}

// Re-export for convenience
pub mod prelude {
    pub use super::{
        PolicyEngine,
        PolicyEngineHandle,
        EvaluationContext,
        Rule,
        RuleSet,
        Condition,
        Action,
        create_engine,
    };
}
