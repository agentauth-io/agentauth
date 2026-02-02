//! Key management and hierarchical key derivation
//!
//! Implements a secure key hierarchy with automatic rotation support.
//! Designed for integration with Hardware Security Modules (HSM).

use crate::crypto::{
    Ed25519SigningKey, Ed25519VerifyingKey, SecretBytes,
    hkdf_derive, generate_id, current_timestamp, sha256_hash,
};
use crate::errors::CryptoError;
use serde::{Deserialize, Serialize};
use zeroize::{Zeroize, ZeroizeOnDrop};
use std::collections::HashMap;
use chrono::{DateTime, Utc};

/// Key purpose identifiers
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum KeyPurpose {
    /// Master root key (stored in HSM)
    MasterRoot,
    /// Signing operations (Ed25519)
    Signing,
    /// Encryption operations (ChaCha20)
    Encryption,
    /// Key derivation
    Derivation,
    /// Token generation
    TokenGeneration,
    /// API key derivation
    ApiKeyDerivation,
    /// Audit log signing
    AuditSigning,
    /// Session key agreement
    SessionKey,
}

impl KeyPurpose {
    /// Get info bytes for HKDF
    fn info_bytes(&self) -> &'static [u8] {
        match self {
            KeyPurpose::MasterRoot => b"agentauth:master:root:v1",
            KeyPurpose::Signing => b"agentauth:signing:v1",
            KeyPurpose::Encryption => b"agentauth:encryption:v1",
            KeyPurpose::Derivation => b"agentauth:derivation:v1",
            KeyPurpose::TokenGeneration => b"agentauth:token:v1",
            KeyPurpose::ApiKeyDerivation => b"agentauth:apikey:v1",
            KeyPurpose::AuditSigning => b"agentauth:audit:v1",
            KeyPurpose::SessionKey => b"agentauth:session:v1",
        }
    }
}

/// Key metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyMetadata {
    pub id: String,
    pub purpose: KeyPurpose,
    pub created_at: DateTime<Utc>,
    pub expires_at: Option<DateTime<Utc>>,
    pub version: u32,
    pub fingerprint: String,
    pub parent_id: Option<String>,
}

/// Master key that derives all other keys
#[derive(ZeroizeOnDrop)]
pub struct MasterKey {
    secret: SecretBytes,
    metadata: KeyMetadata,
    #[zeroize(skip)]
    derived_keys: HashMap<KeyPurpose, DerivedKey>,
}

impl MasterKey {
    /// Generate a new random master key
    pub fn generate() -> Self {
        let secret = SecretBytes::random(32);
        let fingerprint = hex::encode(&sha256_hash(secret.expose())[..8]);
        
        Self {
            secret,
            metadata: KeyMetadata {
                id: generate_id("mk"),
                purpose: KeyPurpose::MasterRoot,
                created_at: Utc::now(),
                expires_at: None,
                version: 1,
                fingerprint,
                parent_id: None,
            },
            derived_keys: HashMap::new(),
        }
    }

    /// Load master key from bytes (e.g., from HSM)
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, CryptoError> {
        if bytes.len() != 32 {
            return Err(CryptoError::InvalidKeyLength);
        }
        let secret = SecretBytes::from(bytes);
        let fingerprint = hex::encode(&sha256_hash(secret.expose())[..8]);
        
        Ok(Self {
            secret,
            metadata: KeyMetadata {
                id: generate_id("mk"),
                purpose: KeyPurpose::MasterRoot,
                created_at: Utc::now(),
                expires_at: None,
                version: 1,
                fingerprint,
                parent_id: None,
            },
            derived_keys: HashMap::new(),
        })
    }

    /// Get key metadata
    pub fn metadata(&self) -> &KeyMetadata {
        &self.metadata
    }

    /// Derive a key for specific purpose
    pub fn derive(&mut self, purpose: KeyPurpose) -> Result<&DerivedKey, CryptoError> {
        if !self.derived_keys.contains_key(&purpose) {
            let derived = self.derive_new(purpose)?;
            self.derived_keys.insert(purpose, derived);
        }
        Ok(self.derived_keys.get(&purpose).unwrap())
    }

    /// Internal derivation
    fn derive_new(&self, purpose: KeyPurpose) -> Result<DerivedKey, CryptoError> {
        let info = purpose.info_bytes();
        let salt = format!("{}:{}", self.metadata.id, self.metadata.version);
        
        let derived_secret = hkdf_derive(
            &self.secret,
            Some(salt.as_bytes()),
            info,
            32,
        )?;
        
        let fingerprint = hex::encode(&sha256_hash(derived_secret.expose())[..8]);
        
        Ok(DerivedKey {
            secret: derived_secret,
            metadata: KeyMetadata {
                id: generate_id("dk"),
                purpose,
                created_at: Utc::now(),
                expires_at: None,
                version: 1,
                fingerprint,
                parent_id: Some(self.metadata.id.clone()),
            },
        })
    }

    /// Rotate the master key
    pub fn rotate(&self) -> Self {
        let new_secret = SecretBytes::random(32);
        let fingerprint = hex::encode(&sha256_hash(new_secret.expose())[..8]);
        
        Self {
            secret: new_secret,
            metadata: KeyMetadata {
                id: generate_id("mk"),
                purpose: KeyPurpose::MasterRoot,
                created_at: Utc::now(),
                expires_at: None,
                version: self.metadata.version + 1,
                fingerprint,
                parent_id: Some(self.metadata.id.clone()),
            },
            derived_keys: HashMap::new(),
        }
    }
}

/// Derived key for specific purpose
#[derive(ZeroizeOnDrop)]
pub struct DerivedKey {
    secret: SecretBytes,
    #[zeroize(skip)]
    metadata: KeyMetadata,
}

impl DerivedKey {
    /// Get key metadata
    pub fn metadata(&self) -> &KeyMetadata {
        &self.metadata
    }

    /// Get raw secret bytes (use with caution)
    pub fn secret(&self) -> &SecretBytes {
        &self.secret
    }

    /// Create Ed25519 signing key from derived key
    pub fn to_signing_key(&self) -> Result<Ed25519SigningKey, CryptoError> {
        let bytes: [u8; 32] = self.secret.expose()
            .try_into()
            .map_err(|_| CryptoError::InvalidKeyLength)?;
        Ed25519SigningKey::from_bytes(&bytes)
    }

    /// Derive child key for sub-purpose
    pub fn derive_child(&self, context: &str) -> Result<SecretBytes, CryptoError> {
        hkdf_derive(
            &self.secret,
            Some(self.metadata.id.as_bytes()),
            context.as_bytes(),
            32,
        )
    }
}

/// API Key with hierarchical derivation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiKey {
    pub key: String,
    pub key_id: String,
    pub owner: String,
    pub scopes: Vec<String>,
    pub created_at: DateTime<Utc>,
    pub expires_at: Option<DateTime<Utc>>,
    pub rate_limit: u32,
}

impl ApiKey {
    /// Generate API key from derivation key
    pub fn generate(
        derivation_key: &DerivedKey,
        owner: &str,
        scopes: Vec<String>,
        rate_limit: u32,
        expires_in_days: Option<u32>,
    ) -> Result<Self, CryptoError> {
        let key_id = generate_id("ak");
        
        // Derive unique key material
        let context = format!("apikey:{}:{}", owner, key_id);
        let key_material = derivation_key.derive_child(&context)?;
        
        // Format: aa_<tier>_<hex>
        let tier = if scopes.contains(&"admin".to_string()) {
            "admin"
        } else if scopes.contains(&"write".to_string()) {
            "live"
        } else {
            "test"
        };
        
        let key = format!("aa_{}_{}", tier, hex::encode(key_material.expose()));
        
        let expires_at = expires_in_days.map(|days| {
            Utc::now() + chrono::Duration::days(days as i64)
        });
        
        Ok(Self {
            key,
            key_id,
            owner: owner.to_string(),
            scopes,
            created_at: Utc::now(),
            expires_at,
            rate_limit,
        })
    }

    /// Check if key is expired
    pub fn is_expired(&self) -> bool {
        if let Some(expires_at) = self.expires_at {
            Utc::now() > expires_at
        } else {
            false
        }
    }

    /// Check if key has scope
    pub fn has_scope(&self, scope: &str) -> bool {
        self.scopes.contains(&scope.to_string()) ||
        self.scopes.contains(&"*".to_string())
    }

    /// Extract prefix to validate format
    pub fn extract_prefix(key: &str) -> Option<(&str, &str)> {
        if !key.starts_with("aa_") {
            return None;
        }
        let parts: Vec<&str> = key.splitn(3, '_').collect();
        if parts.len() == 3 {
            Some((parts[1], parts[2]))
        } else {
            None
        }
    }
}

/// Agent identity key pair
#[derive(Serialize, Deserialize)]
pub struct AgentIdentity {
    pub agent_id: String,
    #[serde(skip)]
    signing_key: Option<Ed25519SigningKey>,
    pub verifying_key: Ed25519VerifyingKey,
    pub created_at: DateTime<Utc>,
    pub fingerprint: String,
}

impl AgentIdentity {
    /// Generate new agent identity
    pub fn generate(agent_id: &str) -> Self {
        let signing_key = Ed25519SigningKey::generate();
        let verifying_key = signing_key.verifying_key();
        let fingerprint = verifying_key.fingerprint();
        
        Self {
            agent_id: agent_id.to_string(),
            signing_key: Some(signing_key),
            verifying_key,
            created_at: Utc::now(),
            fingerprint,
        }
    }

    /// Get signing key (if available)
    pub fn signing_key(&self) -> Option<&Ed25519SigningKey> {
        self.signing_key.as_ref()
    }

    /// Create signature for agent action
    pub fn sign_action(&self, action: &str, timestamp: u64) -> Option<String> {
        let message = format!("{}:{}:{}", self.agent_id, action, timestamp);
        self.signing_key.as_ref().map(|sk| sk.sign(message.as_bytes()).to_base64())
    }

    /// Export public identity (without private key)
    pub fn public_identity(&self) -> PublicAgentIdentity {
        PublicAgentIdentity {
            agent_id: self.agent_id.clone(),
            verifying_key: self.verifying_key.clone(),
            created_at: self.created_at,
            fingerprint: self.fingerprint.clone(),
        }
    }
}

/// Public agent identity (shareable)
#[derive(Clone, Serialize, Deserialize)]
pub struct PublicAgentIdentity {
    pub agent_id: String,
    pub verifying_key: Ed25519VerifyingKey,
    pub created_at: DateTime<Utc>,
    pub fingerprint: String,
}

impl PublicAgentIdentity {
    /// Verify agent signature
    pub fn verify_signature(
        &self,
        action: &str,
        timestamp: u64,
        signature: &str,
    ) -> Result<bool, CryptoError> {
        let message = format!("{}:{}:{}", self.agent_id, action, timestamp);
        
        let sig_bytes = base64::engine::general_purpose::URL_SAFE_NO_PAD
            .decode(signature)
            .map_err(|_| CryptoError::InvalidSignature)?;
        
        let sig_arr: [u8; 64] = sig_bytes.try_into()
            .map_err(|_| CryptoError::InvalidSignature)?;
        
        let signature = crate::crypto::Ed25519Signature::from_bytes(&sig_arr);
        self.verifying_key.verify(message.as_bytes(), &signature)
    }
}

use base64::Engine as _;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_master_key_derivation() {
        let mut master = MasterKey::generate();
        
        let signing_key = master.derive(KeyPurpose::Signing).unwrap();
        let encryption_key = master.derive(KeyPurpose::Encryption).unwrap();
        
        // Keys should be different
        assert_ne!(
            signing_key.secret().expose(),
            encryption_key.secret().expose()
        );
        
        // Deriving same purpose should return same key
        let signing_key2 = master.derive(KeyPurpose::Signing).unwrap();
        assert_eq!(
            signing_key.secret().expose(),
            signing_key2.secret().expose()
        );
    }

    #[test]
    fn test_api_key_generation() {
        let mut master = MasterKey::generate();
        let derivation_key = master.derive(KeyPurpose::ApiKeyDerivation).unwrap();
        
        let api_key = ApiKey::generate(
            derivation_key,
            "test-user",
            vec!["read".to_string(), "write".to_string()],
            1000,
            Some(30),
        ).unwrap();
        
        assert!(api_key.key.starts_with("aa_live_"));
        assert!(!api_key.is_expired());
        assert!(api_key.has_scope("read"));
    }

    #[test]
    fn test_agent_identity() {
        let identity = AgentIdentity::generate("agent_123");
        
        let timestamp = current_timestamp();
        let signature = identity.sign_action("purchase", timestamp).unwrap();
        
        let public_id = identity.public_identity();
        assert!(public_id.verify_signature("purchase", timestamp, &signature).unwrap());
    }
}
