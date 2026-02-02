//! # AgentAuth Secure Core
//! 
//! Memory-safe cryptographic primitives for the AgentAuth authorization network.
//! 
//! ## Security Properties
//! 
//! - **Memory Safety**: All secret material is zeroized after use
//! - **Constant-Time**: No timing side channels in security-critical operations
//! - **Auditability**: Designed for formal verification
//! - **HSM Ready**: Optional hardware security module integration
//! 
//! ## Algorithms
//! 
//! - **Ed25519**: Digital signatures for agent identity and authorization proofs
//! - **X25519**: Key exchange for secure channel establishment
//! - **ChaCha20-Poly1305**: Authenticated encryption for tokens
//! - **BLAKE3**: Fast cryptographic hashing
//! - **Argon2id**: Memory-hard key derivation
//! - **HKDF-SHA256**: Standard key derivation

pub mod crypto;
pub mod keys;
pub mod tokens;
pub mod proofs;
pub mod errors;
pub mod audit;

pub use crypto::*;
pub use keys::*;
pub use tokens::*;
pub use proofs::*;
pub use errors::*;
pub use audit::*;

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Security level identifier
pub const SECURITY_LEVEL: &str = "FIPS-140-2-L2-COMPATIBLE";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version() {
        assert!(!VERSION.is_empty());
    }
}
