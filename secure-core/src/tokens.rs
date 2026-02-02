//! Authorization tokens with cryptographic proofs
//!
//! Tokens are cryptographically signed artifacts that prove an authorization decision.
//! They are designed to be compact, verifiable, and tamper-proof.

use crate::crypto::{
    Ed25519SigningKey, Ed25519VerifyingKey, Ed25519Signature,
    SecretBytes, Aead, sha256_hash, current_timestamp, generate_id,
};
use crate::keys::KeyMetadata;
use crate::errors::CryptoError;
use serde::{Deserialize, Serialize};
use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use std::collections::HashMap;

/// Token type identifier
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TokenType {
    /// One-time authorization token
    OneTime,
    /// Time-limited token
    TimeLimited,
    /// Amount-limited token
    AmountLimited,
    /// Scoped access token
    Scoped,
    /// Delegated authorization
    Delegated,
}

/// Token status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TokenStatus {
    Active,
    Used,
    Expired,
    Revoked,
}

/// Authorization token claims
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenClaims {
    /// Token ID
    pub jti: String,
    /// Issuer (AgentAuth instance ID)
    pub iss: String,
    /// Subject (agent ID)
    pub sub: String,
    /// Audience (resource/service)
    pub aud: String,
    /// Issued at (Unix timestamp)
    pub iat: u64,
    /// Expires at (Unix timestamp)
    pub exp: u64,
    /// Not before (Unix timestamp)
    pub nbf: u64,
    /// Authorization scope
    pub scope: String,
    /// Authorized action
    pub action: String,
    /// Authorized amount (if applicable)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub amount: Option<f64>,
    /// Maximum amount (if applicable)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_amount: Option<f64>,
    /// User ID
    pub user_id: String,
    /// Request ID that generated this token
    pub request_id: String,
    /// Policy ID that authorized this
    pub policy_id: String,
    /// Custom constraints
    #[serde(default)]
    pub constraints: HashMap<String, serde_json::Value>,
    /// Token type
    pub token_type: TokenType,
    /// Fingerprint of signing key
    pub key_fingerprint: String,
}

impl TokenClaims {
    /// Check if token is expired
    pub fn is_expired(&self) -> bool {
        current_timestamp() > self.exp
    }

    /// Check if token is valid (within time window)
    pub fn is_valid_time(&self) -> bool {
        let now = current_timestamp();
        now >= self.nbf && now <= self.exp
    }

    /// Get remaining validity in seconds
    pub fn time_remaining(&self) -> i64 {
        self.exp as i64 - current_timestamp() as i64
    }

    /// Serialize to canonical JSON for signing
    pub fn to_canonical(&self) -> Result<Vec<u8>, CryptoError> {
        serde_json::to_vec(self)
            .map_err(|_| CryptoError::SerializationError)
    }
}

/// Complete authorization token (claims + signature)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthorizationToken {
    pub claims: TokenClaims,
    pub signature: Ed25519Signature,
}

impl AuthorizationToken {
    /// Create and sign a new token
    pub fn create(
        signing_key: &Ed25519SigningKey,
        claims: TokenClaims,
    ) -> Result<Self, CryptoError> {
        let canonical = claims.to_canonical()?;
        let signature = signing_key.sign(&canonical);
        
        Ok(Self { claims, signature })
    }

    /// Verify token signature
    pub fn verify(&self, verifying_key: &Ed25519VerifyingKey) -> Result<bool, CryptoError> {
        let canonical = self.claims.to_canonical()?;
        verifying_key.verify(&canonical, &self.signature)
    }

    /// Encode to compact string format
    pub fn encode(&self) -> Result<String, CryptoError> {
        let json = serde_json::to_vec(self)
            .map_err(|_| CryptoError::SerializationError)?;
        Ok(URL_SAFE_NO_PAD.encode(&json))
    }

    /// Decode from compact string format
    pub fn decode(encoded: &str) -> Result<Self, CryptoError> {
        let json = URL_SAFE_NO_PAD.decode(encoded)
            .map_err(|_| CryptoError::InvalidToken)?;
        serde_json::from_slice(&json)
            .map_err(|_| CryptoError::InvalidToken)
    }

    /// Get token hash for audit purposes
    pub fn hash(&self) -> String {
        let canonical = self.claims.to_canonical().unwrap_or_default();
        hex::encode(sha256_hash(&canonical))
    }
}

/// Token generator with configuration
pub struct TokenGenerator {
    signing_key: Ed25519SigningKey,
    verifying_key: Ed25519VerifyingKey,
    issuer: String,
    default_ttl_seconds: u64,
    key_fingerprint: String,
}

impl TokenGenerator {
    /// Create new token generator
    pub fn new(signing_key: Ed25519SigningKey, issuer: &str, default_ttl: u64) -> Self {
        let verifying_key = signing_key.verifying_key();
        let key_fingerprint = verifying_key.fingerprint();
        
        Self {
            signing_key,
            verifying_key,
            issuer: issuer.to_string(),
            default_ttl_seconds: default_ttl,
            key_fingerprint,
        }
    }

    /// Generate authorization token
    pub fn generate(
        &self,
        agent_id: &str,
        user_id: &str,
        action: &str,
        resource: &str,
        request_id: &str,
        policy_id: &str,
        amount: Option<f64>,
        token_type: TokenType,
        ttl_seconds: Option<u64>,
        constraints: HashMap<String, serde_json::Value>,
    ) -> Result<AuthorizationToken, CryptoError> {
        let now = current_timestamp();
        let ttl = ttl_seconds.unwrap_or(self.default_ttl_seconds);
        
        let claims = TokenClaims {
            jti: generate_id("tok"),
            iss: self.issuer.clone(),
            sub: agent_id.to_string(),
            aud: resource.to_string(),
            iat: now,
            exp: now + ttl,
            nbf: now,
            scope: format!("{}:{}", action, resource),
            action: action.to_string(),
            amount,
            max_amount: amount,
            user_id: user_id.to_string(),
            request_id: request_id.to_string(),
            policy_id: policy_id.to_string(),
            constraints,
            token_type,
            key_fingerprint: self.key_fingerprint.clone(),
        };
        
        AuthorizationToken::create(&self.signing_key, claims)
    }

    /// Get verifying key for token verification
    pub fn verifying_key(&self) -> &Ed25519VerifyingKey {
        &self.verifying_key
    }

    /// Get issuer
    pub fn issuer(&self) -> &str {
        &self.issuer
    }
}

/// Token verifier
pub struct TokenVerifier {
    verifying_key: Ed25519VerifyingKey,
    expected_issuer: String,
    clock_skew_seconds: u64,
}

impl TokenVerifier {
    /// Create new verifier
    pub fn new(verifying_key: Ed25519VerifyingKey, issuer: &str, clock_skew: u64) -> Self {
        Self {
            verifying_key,
            expected_issuer: issuer.to_string(),
            clock_skew_seconds: clock_skew,
        }
    }

    /// Verify token is valid
    pub fn verify(&self, token: &AuthorizationToken) -> Result<TokenVerificationResult, CryptoError> {
        let mut result = TokenVerificationResult::default();
        
        // Check signature
        result.signature_valid = token.verify(&self.verifying_key)?;
        if !result.signature_valid {
            result.errors.push("Invalid signature".to_string());
        }
        
        // Check issuer
        result.issuer_valid = token.claims.iss == self.expected_issuer;
        if !result.issuer_valid {
            result.errors.push(format!(
                "Invalid issuer: expected {}, got {}",
                self.expected_issuer, token.claims.iss
            ));
        }
        
        // Check time validity
        let now = current_timestamp();
        let exp_with_skew = token.claims.exp + self.clock_skew_seconds;
        let nbf_with_skew = token.claims.nbf.saturating_sub(self.clock_skew_seconds);
        
        result.not_expired = now <= exp_with_skew;
        if !result.not_expired {
            result.errors.push("Token expired".to_string());
        }
        
        result.not_before_valid = now >= nbf_with_skew;
        if !result.not_before_valid {
            result.errors.push("Token not yet valid".to_string());
        }
        
        result.valid = result.signature_valid 
            && result.issuer_valid 
            && result.not_expired 
            && result.not_before_valid;
        
        Ok(result)
    }
}

/// Token verification result
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TokenVerificationResult {
    pub valid: bool,
    pub signature_valid: bool,
    pub issuer_valid: bool,
    pub not_expired: bool,
    pub not_before_valid: bool,
    pub errors: Vec<String>,
}

/// Encrypted token wrapper for additional security
pub struct EncryptedToken {
    ciphertext: Vec<u8>,
    key_id: String,
}

impl EncryptedToken {
    /// Encrypt a token
    pub fn encrypt(
        token: &AuthorizationToken,
        encryption_key: &SecretBytes,
        key_id: &str,
    ) -> Result<Self, CryptoError> {
        let plaintext = token.encode()?;
        let aead = Aead::new(encryption_key)?;
        let ciphertext = aead.encrypt(plaintext.as_bytes(), key_id.as_bytes())?;
        
        Ok(Self {
            ciphertext,
            key_id: key_id.to_string(),
        })
    }

    /// Decrypt to get token
    pub fn decrypt(
        &self,
        encryption_key: &SecretBytes,
    ) -> Result<AuthorizationToken, CryptoError> {
        let aead = Aead::new(encryption_key)?;
        let plaintext = aead.decrypt(&self.ciphertext, self.key_id.as_bytes())?;
        let encoded = String::from_utf8(plaintext)
            .map_err(|_| CryptoError::InvalidToken)?;
        AuthorizationToken::decode(&encoded)
    }

    /// Encode to string
    pub fn encode(&self) -> String {
        format!(
            "{}:{}",
            self.key_id,
            URL_SAFE_NO_PAD.encode(&self.ciphertext)
        )
    }

    /// Decode from string
    pub fn decode(encoded: &str) -> Result<Self, CryptoError> {
        let parts: Vec<&str> = encoded.splitn(2, ':').collect();
        if parts.len() != 2 {
            return Err(CryptoError::InvalidToken);
        }
        
        let ciphertext = URL_SAFE_NO_PAD.decode(parts[1])
            .map_err(|_| CryptoError::InvalidToken)?;
        
        Ok(Self {
            ciphertext,
            key_id: parts[0].to_string(),
        })
    }
}

/// Token revocation entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenRevocation {
    pub token_id: String,
    pub revoked_at: u64,
    pub reason: String,
    pub revoked_by: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_token_create_and_verify() {
        let signing_key = Ed25519SigningKey::generate();
        let generator = TokenGenerator::new(signing_key, "test-issuer", 3600);
        
        let token = generator.generate(
            "agent_123",
            "user_456",
            "purchase",
            "shopping-service",
            "req_789",
            "pol_abc",
            Some(25.0),
            TokenType::OneTime,
            None,
            HashMap::new(),
        ).unwrap();
        
        let verifier = TokenVerifier::new(
            generator.verifying_key().clone(),
            "test-issuer",
            30,
        );
        
        let result = verifier.verify(&token).unwrap();
        assert!(result.valid);
        assert!(result.signature_valid);
    }

    #[test]
    fn test_token_encode_decode() {
        let signing_key = Ed25519SigningKey::generate();
        let generator = TokenGenerator::new(signing_key, "test-issuer", 3600);
        
        let token = generator.generate(
            "agent_123",
            "user_456",
            "read",
            "data-service",
            "req_789",
            "pol_abc",
            None,
            TokenType::TimeLimited,
            Some(60),
            HashMap::new(),
        ).unwrap();
        
        let encoded = token.encode().unwrap();
        let decoded = AuthorizationToken::decode(&encoded).unwrap();
        
        assert_eq!(token.claims.jti, decoded.claims.jti);
        assert_eq!(token.claims.action, decoded.claims.action);
    }

    #[test]
    fn test_encrypted_token() {
        let signing_key = Ed25519SigningKey::generate();
        let generator = TokenGenerator::new(signing_key, "test-issuer", 3600);
        let encryption_key = SecretBytes::random(32);
        
        let token = generator.generate(
            "agent_123",
            "user_456",
            "write",
            "secure-service",
            "req_789",
            "pol_abc",
            None,
            TokenType::Scoped,
            None,
            HashMap::new(),
        ).unwrap();
        
        let encrypted = EncryptedToken::encrypt(&token, &encryption_key, "key_123").unwrap();
        let encoded = encrypted.encode();
        
        let decoded_encrypted = EncryptedToken::decode(&encoded).unwrap();
        let decrypted = decoded_encrypted.decrypt(&encryption_key).unwrap();
        
        assert_eq!(token.claims.jti, decrypted.claims.jti);
    }
}
