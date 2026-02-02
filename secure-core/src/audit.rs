//! Immutable audit trail with cryptographic chaining
//!
//! Provides a tamper-evident log of all authorization decisions.

use crate::crypto::{
    Ed25519SigningKey, Ed25519VerifyingKey, Ed25519Signature,
    sha256_hash, current_timestamp, generate_id,
};
use crate::proofs::{MerkleTree, MerkleProof, AuthorizationProof};
use crate::errors::{AuditError, CryptoError};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, RwLock};

/// Audit entry type
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AuditEntryType {
    /// Authorization request
    AuthorizationRequest,
    /// Authorization decision
    AuthorizationDecision,
    /// Policy change
    PolicyChange,
    /// Key rotation
    KeyRotation,
    /// System event
    SystemEvent,
    /// Security alert
    SecurityAlert,
}

/// Single audit log entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEntry {
    /// Unique entry ID
    pub id: String,
    /// Entry type
    pub entry_type: AuditEntryType,
    /// Timestamp
    pub timestamp: u64,
    /// Sequence number in chain
    pub sequence: u64,
    /// Hash of previous entry (chain link)
    pub prev_hash: [u8; 32],
    /// Entry payload
    pub payload: AuditPayload,
    /// Entry hash (computed)
    pub hash: [u8; 32],
    /// Signature over entry
    pub signature: Option<Ed25519Signature>,
}

impl AuditEntry {
    /// Create new audit entry
    pub fn new(
        entry_type: AuditEntryType,
        sequence: u64,
        prev_hash: [u8; 32],
        payload: AuditPayload,
    ) -> Self {
        let id = generate_id("audit");
        let timestamp = current_timestamp();
        
        let mut entry = Self {
            id,
            entry_type,
            timestamp,
            sequence,
            prev_hash,
            payload,
            hash: [0u8; 32],
            signature: None,
        };
        
        entry.hash = entry.compute_hash();
        entry
    }

    /// Compute entry hash
    fn compute_hash(&self) -> [u8; 32] {
        let mut content = Vec::new();
        content.extend_from_slice(self.id.as_bytes());
        content.extend_from_slice(&self.timestamp.to_be_bytes());
        content.extend_from_slice(&self.sequence.to_be_bytes());
        content.extend_from_slice(&self.prev_hash);
        content.extend_from_slice(&serde_json::to_vec(&self.payload).unwrap_or_default());
        sha256_hash(&content)
    }

    /// Sign the entry
    pub fn sign(&mut self, signing_key: &Ed25519SigningKey) {
        let signature = signing_key.sign(&self.hash);
        self.signature = Some(signature);
    }

    /// Verify entry signature
    pub fn verify_signature(&self, verifying_key: &Ed25519VerifyingKey) -> Result<bool, CryptoError> {
        match &self.signature {
            Some(sig) => verifying_key.verify(&self.hash, sig),
            None => Ok(false),
        }
    }

    /// Verify chain link
    pub fn verify_chain(&self, prev_entry: &AuditEntry) -> bool {
        self.prev_hash == prev_entry.hash && self.sequence == prev_entry.sequence + 1
    }
}

/// Audit entry payload
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AuditPayload {
    /// Authorization request details
    AuthRequest {
        request_id: String,
        agent_id: String,
        user_id: String,
        action: String,
        resource: String,
        amount: Option<f64>,
    },
    /// Authorization decision
    AuthDecision {
        request_id: String,
        decision: String,
        policy_id: Option<String>,
        reason: String,
        token_id: Option<String>,
    },
    /// Policy change
    PolicyChange {
        policy_id: String,
        change_type: String,
        changed_by: String,
        old_hash: Option<String>,
        new_hash: String,
    },
    /// Key rotation
    KeyRotation {
        key_id: String,
        key_type: String,
        old_fingerprint: Option<String>,
        new_fingerprint: String,
    },
    /// System event
    SystemEvent {
        event_type: String,
        message: String,
        metadata: HashMap<String, String>,
    },
    /// Security alert
    SecurityAlert {
        alert_type: String,
        severity: String,
        message: String,
        source: String,
    },
}

/// Audit log with append-only semantics
pub struct AuditLog {
    entries: Vec<AuditEntry>,
    merkle_tree: MerkleTree,
    signing_key: Option<Ed25519SigningKey>,
    sequence_counter: u64,
}

impl AuditLog {
    /// Create new audit log
    pub fn new(signing_key: Option<Ed25519SigningKey>) -> Self {
        Self {
            entries: Vec::new(),
            merkle_tree: MerkleTree::new(),
            signing_key,
            sequence_counter: 0,
        }
    }

    /// Append entry to log
    pub fn append(
        &mut self,
        entry_type: AuditEntryType,
        payload: AuditPayload,
    ) -> Result<&AuditEntry, AuditError> {
        let prev_hash = self.entries
            .last()
            .map(|e| e.hash)
            .unwrap_or([0u8; 32]);
        
        self.sequence_counter += 1;
        let mut entry = AuditEntry::new(
            entry_type,
            self.sequence_counter,
            prev_hash,
            payload,
        );
        
        // Sign if we have a signing key
        if let Some(ref key) = self.signing_key {
            entry.sign(key);
        }
        
        // Add to Merkle tree
        self.merkle_tree.add(&entry.hash);
        
        self.entries.push(entry);
        Ok(self.entries.last().unwrap())
    }

    /// Log authorization request
    pub fn log_auth_request(
        &mut self,
        request_id: &str,
        agent_id: &str,
        user_id: &str,
        action: &str,
        resource: &str,
        amount: Option<f64>,
    ) -> Result<&AuditEntry, AuditError> {
        self.append(
            AuditEntryType::AuthorizationRequest,
            AuditPayload::AuthRequest {
                request_id: request_id.to_string(),
                agent_id: agent_id.to_string(),
                user_id: user_id.to_string(),
                action: action.to_string(),
                resource: resource.to_string(),
                amount,
            },
        )
    }

    /// Log authorization decision
    pub fn log_auth_decision(
        &mut self,
        request_id: &str,
        decision: &str,
        policy_id: Option<&str>,
        reason: &str,
        token_id: Option<&str>,
    ) -> Result<&AuditEntry, AuditError> {
        self.append(
            AuditEntryType::AuthorizationDecision,
            AuditPayload::AuthDecision {
                request_id: request_id.to_string(),
                decision: decision.to_string(),
                policy_id: policy_id.map(String::from),
                reason: reason.to_string(),
                token_id: token_id.map(String::from),
            },
        )
    }

    /// Log security alert
    pub fn log_security_alert(
        &mut self,
        alert_type: &str,
        severity: &str,
        message: &str,
        source: &str,
    ) -> Result<&AuditEntry, AuditError> {
        self.append(
            AuditEntryType::SecurityAlert,
            AuditPayload::SecurityAlert {
                alert_type: alert_type.to_string(),
                severity: severity.to_string(),
                message: message.to_string(),
                source: source.to_string(),
            },
        )
    }

    /// Get entry by ID
    pub fn get_entry(&self, id: &str) -> Option<&AuditEntry> {
        self.entries.iter().find(|e| e.id == id)
    }

    /// Get entry by sequence
    pub fn get_by_sequence(&self, seq: u64) -> Option<&AuditEntry> {
        self.entries.iter().find(|e| e.sequence == seq)
    }

    /// Get Merkle proof for entry
    pub fn get_merkle_proof(&self, index: usize) -> Option<MerkleProof> {
        self.merkle_tree.proof(index)
    }

    /// Get current Merkle root
    pub fn merkle_root(&self) -> Option<[u8; 32]> {
        self.merkle_tree.root_hash()
    }

    /// Verify entire chain integrity
    pub fn verify_chain(&self) -> bool {
        if self.entries.is_empty() {
            return true;
        }

        // Verify first entry has zero prev_hash
        if self.entries[0].prev_hash != [0u8; 32] {
            return false;
        }

        // Verify chain links
        for i in 1..self.entries.len() {
            if !self.entries[i].verify_chain(&self.entries[i - 1]) {
                return false;
            }
        }

        true
    }

    /// Get number of entries
    pub fn len(&self) -> usize {
        self.entries.len()
    }

    /// Check if empty
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Get latest entries
    pub fn latest(&self, count: usize) -> Vec<&AuditEntry> {
        self.entries.iter().rev().take(count).collect()
    }

    /// Search entries by request ID
    pub fn find_by_request(&self, request_id: &str) -> Vec<&AuditEntry> {
        self.entries
            .iter()
            .filter(|e| match &e.payload {
                AuditPayload::AuthRequest { request_id: id, .. } => id == request_id,
                AuditPayload::AuthDecision { request_id: id, .. } => id == request_id,
                _ => false,
            })
            .collect()
    }

    /// Export log for external verification
    pub fn export(&self) -> AuditLogExport {
        AuditLogExport {
            entries: self.entries.clone(),
            merkle_root: self.merkle_root(),
            total_entries: self.entries.len() as u64,
            exported_at: current_timestamp(),
        }
    }
}

/// Exported audit log for verification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditLogExport {
    pub entries: Vec<AuditEntry>,
    pub merkle_root: Option<[u8; 32]>,
    pub total_entries: u64,
    pub exported_at: u64,
}

impl AuditLogExport {
    /// Verify exported log integrity
    pub fn verify(&self) -> bool {
        if self.entries.is_empty() {
            return true;
        }

        // Verify chain
        if self.entries[0].prev_hash != [0u8; 32] {
            return false;
        }

        for i in 1..self.entries.len() {
            if !self.entries[i].verify_chain(&self.entries[i - 1]) {
                return false;
            }
        }

        // Rebuild Merkle tree and verify root
        if let Some(expected_root) = self.merkle_root {
            let mut tree = MerkleTree::new();
            for entry in &self.entries {
                tree.add(&entry.hash);
            }
            if tree.root_hash() != Some(expected_root) {
                return false;
            }
        }

        true
    }
}

/// Thread-safe audit log wrapper
pub struct SharedAuditLog {
    inner: Arc<RwLock<AuditLog>>,
}

impl SharedAuditLog {
    /// Create new shared audit log
    pub fn new(signing_key: Option<Ed25519SigningKey>) -> Self {
        Self {
            inner: Arc::new(RwLock::new(AuditLog::new(signing_key))),
        }
    }

    /// Append entry
    pub fn append(
        &self,
        entry_type: AuditEntryType,
        payload: AuditPayload,
    ) -> Result<String, AuditError> {
        let mut log = self.inner.write().map_err(|_| AuditError::WriteFailed)?;
        let entry = log.append(entry_type, payload)?;
        Ok(entry.id.clone())
    }

    /// Get entry
    pub fn get_entry(&self, id: &str) -> Result<Option<AuditEntry>, AuditError> {
        let log = self.inner.read().map_err(|_| AuditError::ReadFailed)?;
        Ok(log.get_entry(id).cloned())
    }

    /// Verify chain
    pub fn verify_chain(&self) -> Result<bool, AuditError> {
        let log = self.inner.read().map_err(|_| AuditError::ReadFailed)?;
        Ok(log.verify_chain())
    }

    /// Get Merkle root
    pub fn merkle_root(&self) -> Result<Option<[u8; 32]>, AuditError> {
        let log = self.inner.read().map_err(|_| AuditError::ReadFailed)?;
        Ok(log.merkle_root())
    }

    /// Export log
    pub fn export(&self) -> Result<AuditLogExport, AuditError> {
        let log = self.inner.read().map_err(|_| AuditError::ReadFailed)?;
        Ok(log.export())
    }
}

impl Clone for SharedAuditLog {
    fn clone(&self) -> Self {
        Self {
            inner: Arc::clone(&self.inner),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_audit_log_chain() {
        let signing_key = Ed25519SigningKey::generate();
        let mut log = AuditLog::new(Some(signing_key));
        
        log.log_auth_request(
            "req_1",
            "agent_1",
            "user_1",
            "purchase",
            "shop",
            Some(25.0),
        ).unwrap();
        
        log.log_auth_decision(
            "req_1",
            "approved",
            Some("pol_1"),
            "Within limits",
            Some("tok_1"),
        ).unwrap();
        
        assert_eq!(log.len(), 2);
        assert!(log.verify_chain());
    }

    #[test]
    fn test_audit_log_merkle() {
        let mut log = AuditLog::new(None);
        
        for i in 0..10 {
            log.log_auth_request(
                &format!("req_{}", i),
                "agent_1",
                "user_1",
                "read",
                "data",
                None,
            ).unwrap();
        }
        
        assert!(log.merkle_root().is_some());
        
        let proof = log.get_merkle_proof(5).unwrap();
        assert!(proof.verify());
    }

    #[test]
    fn test_audit_log_export() {
        let mut log = AuditLog::new(None);
        
        log.log_auth_request("req_1", "agent_1", "user_1", "write", "file", None).unwrap();
        log.log_auth_decision("req_1", "denied", None, "Permission denied", None).unwrap();
        
        let export = log.export();
        assert!(export.verify());
    }
}
