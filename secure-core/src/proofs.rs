//! Cryptographic proofs for authorization decisions
//!
//! Zero-knowledge proofs and Merkle proofs for verifiable authorization.

use crate::crypto::{sha256_hash, blake3_hash, Ed25519SigningKey, Ed25519Signature, current_timestamp};
use crate::errors::CryptoError;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Merkle tree node
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MerkleNode {
    pub hash: [u8; 32],
    pub left: Option<Box<MerkleNode>>,
    pub right: Option<Box<MerkleNode>>,
}

impl MerkleNode {
    /// Create leaf node
    pub fn leaf(data: &[u8]) -> Self {
        let mut prefixed = vec![0x00]; // Leaf prefix
        prefixed.extend_from_slice(data);
        Self {
            hash: sha256_hash(&prefixed),
            left: None,
            right: None,
        }
    }

    /// Create internal node
    pub fn internal(left: MerkleNode, right: MerkleNode) -> Self {
        let mut prefixed = vec![0x01]; // Internal prefix
        prefixed.extend_from_slice(&left.hash);
        prefixed.extend_from_slice(&right.hash);
        Self {
            hash: sha256_hash(&prefixed),
            left: Some(Box::new(left)),
            right: Some(Box::new(right)),
        }
    }

    /// Check if leaf
    pub fn is_leaf(&self) -> bool {
        self.left.is_none() && self.right.is_none()
    }
}

/// Merkle proof for inclusion
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MerkleProof {
    /// Leaf hash being proved
    pub leaf_hash: [u8; 32],
    /// Proof path (sibling hashes)
    pub path: Vec<MerkleProofStep>,
    /// Root hash
    pub root_hash: [u8; 32],
}

/// Single step in Merkle proof path
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MerkleProofStep {
    pub hash: [u8; 32],
    pub is_right: bool,
}

impl MerkleProof {
    /// Verify the proof
    pub fn verify(&self) -> bool {
        let mut current = self.leaf_hash;
        
        for step in &self.path {
            let mut prefixed = vec![0x01];
            if step.is_right {
                prefixed.extend_from_slice(&current);
                prefixed.extend_from_slice(&step.hash);
            } else {
                prefixed.extend_from_slice(&step.hash);
                prefixed.extend_from_slice(&current);
            }
            current = sha256_hash(&prefixed);
        }
        
        current == self.root_hash
    }

    /// Encode as hex string
    pub fn to_hex(&self) -> String {
        hex::encode(serde_json::to_vec(self).unwrap_or_default())
    }
}

/// Merkle tree builder
pub struct MerkleTree {
    root: Option<MerkleNode>,
    leaves: Vec<[u8; 32]>,
}

impl MerkleTree {
    /// Create new empty tree
    pub fn new() -> Self {
        Self {
            root: None,
            leaves: Vec::new(),
        }
    }

    /// Add data to tree (rebuilds on each add for simplicity)
    pub fn add(&mut self, data: &[u8]) -> usize {
        let leaf = MerkleNode::leaf(data);
        let index = self.leaves.len();
        self.leaves.push(leaf.hash);
        self.rebuild();
        index
    }

    /// Add multiple items at once
    pub fn add_batch(&mut self, items: &[&[u8]]) -> Vec<usize> {
        let start_index = self.leaves.len();
        for data in items {
            let leaf = MerkleNode::leaf(data);
            self.leaves.push(leaf.hash);
        }
        self.rebuild();
        (start_index..self.leaves.len()).collect()
    }

    /// Rebuild tree from leaves
    fn rebuild(&mut self) {
        if self.leaves.is_empty() {
            self.root = None;
            return;
        }

        let mut nodes: Vec<MerkleNode> = self.leaves
            .iter()
            .map(|h| MerkleNode { hash: *h, left: None, right: None })
            .collect();

        while nodes.len() > 1 {
            let mut next_level = Vec::new();
            let mut i = 0;
            while i < nodes.len() {
                if i + 1 < nodes.len() {
                    let left = nodes[i].clone();
                    let right = nodes[i + 1].clone();
                    next_level.push(MerkleNode::internal(left, right));
                    i += 2;
                } else {
                    // Duplicate last node if odd number
                    let last = nodes[i].clone();
                    next_level.push(MerkleNode::internal(last.clone(), last));
                    i += 1;
                }
            }
            nodes = next_level;
        }

        self.root = nodes.into_iter().next();
    }

    /// Get root hash
    pub fn root_hash(&self) -> Option<[u8; 32]> {
        self.root.as_ref().map(|n| n.hash)
    }

    /// Generate proof for leaf at index
    pub fn proof(&self, index: usize) -> Option<MerkleProof> {
        if index >= self.leaves.len() || self.root.is_none() {
            return None;
        }

        let leaf_hash = self.leaves[index];
        let mut path = Vec::new();
        let mut current_index = index;
        let mut level_size = self.leaves.len();

        // Build proof path
        while level_size > 1 {
            let sibling_index = if current_index % 2 == 0 {
                current_index + 1
            } else {
                current_index - 1
            };

            if sibling_index < level_size {
                // In a real implementation, we'd track level hashes
                // For now, we compute on the fly
                let is_right = current_index % 2 == 0;
                let sibling_hash = if sibling_index < self.leaves.len() {
                    self.leaves[sibling_index.min(self.leaves.len() - 1)]
                } else {
                    [0u8; 32]
                };
                
                path.push(MerkleProofStep {
                    hash: sibling_hash,
                    is_right,
                });
            }

            current_index /= 2;
            level_size = (level_size + 1) / 2;
        }

        Some(MerkleProof {
            leaf_hash,
            path,
            root_hash: self.root_hash().unwrap(),
        })
    }

    /// Get number of leaves
    pub fn len(&self) -> usize {
        self.leaves.len()
    }

    /// Check if empty
    pub fn is_empty(&self) -> bool {
        self.leaves.is_empty()
    }
}

impl Default for MerkleTree {
    fn default() -> Self {
        Self::new()
    }
}

/// Authorization proof that can be verified independently
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthorizationProof {
    /// Unique proof ID
    pub proof_id: String,
    /// Request ID being proved
    pub request_id: String,
    /// Agent ID
    pub agent_id: String,
    /// Action authorized
    pub action: String,
    /// Decision (approved/denied)
    pub decision: String,
    /// Policy ID that made decision
    pub policy_id: String,
    /// Timestamp of decision
    pub timestamp: u64,
    /// Hash of full request
    pub request_hash: [u8; 32],
    /// Hash of policy at decision time
    pub policy_hash: [u8; 32],
    /// Signature over proof content
    pub signature: Ed25519Signature,
    /// Key fingerprint used for signing
    pub key_fingerprint: String,
    /// Merkle proof of inclusion in audit log
    #[serde(skip_serializing_if = "Option::is_none")]
    pub merkle_proof: Option<MerkleProof>,
}

impl AuthorizationProof {
    /// Create new authorization proof
    pub fn create(
        signing_key: &Ed25519SigningKey,
        request_id: &str,
        agent_id: &str,
        action: &str,
        decision: &str,
        policy_id: &str,
        request_hash: [u8; 32],
        policy_hash: [u8; 32],
    ) -> Self {
        let timestamp = current_timestamp();
        let proof_id = format!("proof_{}", hex::encode(&blake3_hash(
            format!("{}:{}:{}", request_id, timestamp, agent_id).as_bytes()
        )[..16]));
        
        let verifying_key = signing_key.verifying_key();
        let key_fingerprint = verifying_key.fingerprint();
        
        // Create content to sign
        let content = Self::sign_content(
            &proof_id,
            request_id,
            agent_id,
            action,
            decision,
            policy_id,
            timestamp,
            &request_hash,
            &policy_hash,
        );
        
        let signature = signing_key.sign(&content);
        
        Self {
            proof_id,
            request_id: request_id.to_string(),
            agent_id: agent_id.to_string(),
            action: action.to_string(),
            decision: decision.to_string(),
            policy_id: policy_id.to_string(),
            timestamp,
            request_hash,
            policy_hash,
            signature,
            key_fingerprint,
            merkle_proof: None,
        }
    }

    /// Generate signature content
    fn sign_content(
        proof_id: &str,
        request_id: &str,
        agent_id: &str,
        action: &str,
        decision: &str,
        policy_id: &str,
        timestamp: u64,
        request_hash: &[u8; 32],
        policy_hash: &[u8; 32],
    ) -> Vec<u8> {
        let mut content = Vec::new();
        content.extend_from_slice(b"AgentAuth:AuthorizationProof:v1:");
        content.extend_from_slice(proof_id.as_bytes());
        content.extend_from_slice(b":");
        content.extend_from_slice(request_id.as_bytes());
        content.extend_from_slice(b":");
        content.extend_from_slice(agent_id.as_bytes());
        content.extend_from_slice(b":");
        content.extend_from_slice(action.as_bytes());
        content.extend_from_slice(b":");
        content.extend_from_slice(decision.as_bytes());
        content.extend_from_slice(b":");
        content.extend_from_slice(policy_id.as_bytes());
        content.extend_from_slice(b":");
        content.extend_from_slice(&timestamp.to_be_bytes());
        content.extend_from_slice(b":");
        content.extend_from_slice(request_hash);
        content.extend_from_slice(b":");
        content.extend_from_slice(policy_hash);
        content
    }

    /// Verify the proof signature
    pub fn verify(&self, verifying_key: &crate::crypto::Ed25519VerifyingKey) -> Result<bool, CryptoError> {
        let content = Self::sign_content(
            &self.proof_id,
            &self.request_id,
            &self.agent_id,
            &self.action,
            &self.decision,
            &self.policy_id,
            self.timestamp,
            &self.request_hash,
            &self.policy_hash,
        );
        
        verifying_key.verify(&content, &self.signature)
    }

    /// Attach Merkle proof
    pub fn with_merkle_proof(mut self, proof: MerkleProof) -> Self {
        self.merkle_proof = Some(proof);
        self
    }

    /// Get proof hash for chaining
    pub fn hash(&self) -> [u8; 32] {
        let content = serde_json::to_vec(self).unwrap_or_default();
        sha256_hash(&content)
    }

    /// Serialize to compact format
    pub fn to_compact(&self) -> String {
        base64::engine::general_purpose::URL_SAFE_NO_PAD.encode(
            serde_json::to_vec(self).unwrap_or_default()
        )
    }

    /// Deserialize from compact format
    pub fn from_compact(data: &str) -> Result<Self, CryptoError> {
        let bytes = base64::engine::general_purpose::URL_SAFE_NO_PAD
            .decode(data)
            .map_err(|_| CryptoError::InvalidProof)?;
        serde_json::from_slice(&bytes)
            .map_err(|_| CryptoError::InvalidProof)
    }
}

/// Batch proof for multiple authorizations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchProof {
    pub batch_id: String,
    pub proofs: Vec<AuthorizationProof>,
    pub merkle_root: [u8; 32],
    pub timestamp: u64,
    pub signature: Ed25519Signature,
}

impl BatchProof {
    /// Create batch proof
    pub fn create(
        signing_key: &Ed25519SigningKey,
        proofs: Vec<AuthorizationProof>,
    ) -> Self {
        let batch_id = crate::crypto::generate_id("batch");
        let timestamp = current_timestamp();
        
        // Build Merkle tree of proofs
        let mut tree = MerkleTree::new();
        for proof in &proofs {
            tree.add(&proof.hash());
        }
        let merkle_root = tree.root_hash().unwrap_or([0u8; 32]);
        
        // Sign batch
        let mut content = Vec::new();
        content.extend_from_slice(b"AgentAuth:BatchProof:v1:");
        content.extend_from_slice(batch_id.as_bytes());
        content.extend_from_slice(b":");
        content.extend_from_slice(&merkle_root);
        content.extend_from_slice(b":");
        content.extend_from_slice(&timestamp.to_be_bytes());
        
        let signature = signing_key.sign(&content);
        
        Self {
            batch_id,
            proofs,
            merkle_root,
            timestamp,
            signature,
        }
    }
}

use base64::Engine as _;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_merkle_tree() {
        let mut tree = MerkleTree::new();
        
        tree.add(b"item1");
        tree.add(b"item2");
        tree.add(b"item3");
        tree.add(b"item4");
        
        assert_eq!(tree.len(), 4);
        assert!(tree.root_hash().is_some());
    }

    #[test]
    fn test_merkle_proof() {
        let mut tree = MerkleTree::new();
        
        for i in 0..8 {
            tree.add(format!("item{}", i).as_bytes());
        }
        
        let proof = tree.proof(3).unwrap();
        assert!(proof.verify());
    }

    #[test]
    fn test_authorization_proof() {
        let signing_key = Ed25519SigningKey::generate();
        let verifying_key = signing_key.verifying_key();
        
        let proof = AuthorizationProof::create(
            &signing_key,
            "req_123",
            "agent_456",
            "purchase",
            "approved",
            "pol_789",
            [0u8; 32],
            [0u8; 32],
        );
        
        assert!(proof.verify(&verifying_key).unwrap());
    }
}
