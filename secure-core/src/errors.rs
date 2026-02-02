//! Error types for cryptographic operations

use thiserror::Error;

/// Cryptographic operation errors
#[derive(Debug, Error)]
pub enum CryptoError {
    #[error("Invalid key length")]
    InvalidKeyLength,

    #[error("Invalid public key")]
    InvalidPublicKey,

    #[error("Invalid private key")]
    InvalidPrivateKey,

    #[error("Invalid signature")]
    InvalidSignature,

    #[error("Signature verification failed")]
    VerificationFailed,

    #[error("Encryption failed")]
    EncryptionFailed,

    #[error("Decryption failed")]
    DecryptionFailed,

    #[error("Invalid ciphertext")]
    InvalidCiphertext,

    #[error("Key derivation failed")]
    KeyDerivationFailed,

    #[error("Invalid token")]
    InvalidToken,

    #[error("Token expired")]
    TokenExpired,

    #[error("Token not yet valid")]
    TokenNotYetValid,

    #[error("Invalid proof")]
    InvalidProof,

    #[error("Merkle proof verification failed")]
    MerkleVerificationFailed,

    #[error("Serialization error")]
    SerializationError,

    #[error("Deserialization error")]
    DeserializationError,

    #[error("Random number generation failed")]
    RngError,

    #[error("HSM operation failed: {0}")]
    HsmError(String),

    #[error("Key not found: {0}")]
    KeyNotFound(String),

    #[error("Operation not permitted")]
    NotPermitted,

    #[error("Internal error: {0}")]
    Internal(String),
}

/// Audit-specific errors
#[derive(Debug, Error)]
pub enum AuditError {
    #[error("Failed to write audit entry")]
    WriteFailed,

    #[error("Failed to read audit entry")]
    ReadFailed,

    #[error("Entry not found: {0}")]
    EntryNotFound(String),

    #[error("Chain verification failed")]
    ChainVerificationFailed,

    #[error("Storage error: {0}")]
    StorageError(String),

    #[error("Crypto error: {0}")]
    CryptoError(#[from] CryptoError),
}

/// Key management errors
#[derive(Debug, Error)]
pub enum KeyError {
    #[error("Key generation failed")]
    GenerationFailed,

    #[error("Key rotation failed")]
    RotationFailed,

    #[error("Key expired")]
    KeyExpired,

    #[error("Key revoked")]
    KeyRevoked,

    #[error("Invalid key format")]
    InvalidFormat,

    #[error("Key storage error: {0}")]
    StorageError(String),

    #[error("Crypto error: {0}")]
    CryptoError(#[from] CryptoError),
}
