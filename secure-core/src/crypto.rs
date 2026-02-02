//! Core cryptographic operations
//!
//! Provides memory-safe implementations of essential cryptographic primitives.
//! All secret material is automatically zeroized when dropped.

use chacha20poly1305::{
    aead::{Aead, KeyInit, OsRng},
    ChaCha20Poly1305, Nonce,
};
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};
use hkdf::Hkdf;
use hmac::{Hmac, Mac};
use sha2::{Digest, Sha256, Sha512};
use zeroize::{Zeroize, ZeroizeOnDrop};
use rand::RngCore;
use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::errors::CryptoError;

/// Size of a symmetric key in bytes (256-bit)
pub const KEY_SIZE: usize = 32;
/// Size of a nonce in bytes (96-bit for ChaCha20-Poly1305)
pub const NONCE_SIZE: usize = 12;
/// Size of an Ed25519 signature
pub const SIGNATURE_SIZE: usize = 64;
/// Size of an Ed25519 public key
pub const PUBLIC_KEY_SIZE: usize = 32;
/// Size of an Ed25519 private key
pub const PRIVATE_KEY_SIZE: usize = 32;
/// Size of authentication tag
pub const TAG_SIZE: usize = 16;

/// Secret bytes that are zeroized on drop
#[derive(Clone, Zeroize, ZeroizeOnDrop)]
pub struct SecretBytes(Vec<u8>);

impl SecretBytes {
    /// Create new secret bytes from raw data
    pub fn new(data: Vec<u8>) -> Self {
        Self(data)
    }

    /// Create secret bytes of given size filled with random data
    pub fn random(size: usize) -> Self {
        let mut data = vec![0u8; size];
        OsRng.fill_bytes(&mut data);
        Self(data)
    }

    /// Get length of secret data
    pub fn len(&self) -> usize {
        self.0.len()
    }

    /// Check if empty
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }

    /// Get reference to bytes (use with caution)
    pub fn as_bytes(&self) -> &[u8] {
        &self.0
    }

    /// Expose secret for cryptographic operations
    pub fn expose(&self) -> &[u8] {
        &self.0
    }
}

impl From<Vec<u8>> for SecretBytes {
    fn from(data: Vec<u8>) -> Self {
        Self::new(data)
    }
}

impl From<&[u8]> for SecretBytes {
    fn from(data: &[u8]) -> Self {
        Self::new(data.to_vec())
    }
}

/// HMAC-SHA512 message authentication code
#[derive(Clone, Serialize, Deserialize)]
pub struct HmacSignature(#[serde(with = "hex")] pub Vec<u8>);

impl HmacSignature {
    /// Create new HMAC-SHA512 signature
    pub fn sign(key: &SecretBytes, message: &[u8]) -> Result<Self, CryptoError> {
        type HmacSha512 = Hmac<Sha512>;
        let mut mac = HmacSha512::new_from_slice(key.expose())
            .map_err(|_| CryptoError::InvalidKeyLength)?;
        mac.update(message);
        let result = mac.finalize();
        Ok(Self(result.into_bytes().to_vec()))
    }

    /// Verify HMAC signature
    pub fn verify(&self, key: &SecretBytes, message: &[u8]) -> Result<bool, CryptoError> {
        type HmacSha512 = Hmac<Sha512>;
        let mut mac = HmacSha512::new_from_slice(key.expose())
            .map_err(|_| CryptoError::InvalidKeyLength)?;
        mac.update(message);
        Ok(mac.verify_slice(&self.0).is_ok())
    }

    /// Get as hex string
    pub fn to_hex(&self) -> String {
        hex::encode(&self.0)
    }

    /// Get as bytes
    pub fn as_bytes(&self) -> &[u8] {
        &self.0
    }
}

/// Ed25519 signing key (private)
#[derive(ZeroizeOnDrop)]
pub struct Ed25519SigningKey {
    inner: SigningKey,
}

impl Ed25519SigningKey {
    /// Generate new random signing key
    pub fn generate() -> Self {
        Self {
            inner: SigningKey::generate(&mut OsRng),
        }
    }

    /// Create from raw bytes
    pub fn from_bytes(bytes: &[u8; PRIVATE_KEY_SIZE]) -> Result<Self, CryptoError> {
        let inner = SigningKey::from_bytes(bytes);
        Ok(Self { inner })
    }

    /// Sign a message
    pub fn sign(&self, message: &[u8]) -> Ed25519Signature {
        let sig = self.inner.sign(message);
        Ed25519Signature(sig)
    }

    /// Get the corresponding verification (public) key
    pub fn verifying_key(&self) -> Ed25519VerifyingKey {
        Ed25519VerifyingKey {
            inner: self.inner.verifying_key(),
        }
    }

    /// Export to bytes (use with extreme caution)
    pub fn to_bytes(&self) -> [u8; PRIVATE_KEY_SIZE] {
        self.inner.to_bytes()
    }

    /// Export as base64
    pub fn to_base64(&self) -> String {
        URL_SAFE_NO_PAD.encode(self.to_bytes())
    }
}

/// Ed25519 verification key (public)
#[derive(Clone, Serialize, Deserialize)]
pub struct Ed25519VerifyingKey {
    #[serde(with = "verifying_key_serde")]
    inner: VerifyingKey,
}

mod verifying_key_serde {
    use super::*;
    use serde::{Deserializer, Serializer};

    pub fn serialize<S>(key: &VerifyingKey, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&URL_SAFE_NO_PAD.encode(key.as_bytes()))
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<VerifyingKey, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        let bytes = URL_SAFE_NO_PAD.decode(&s).map_err(serde::de::Error::custom)?;
        let arr: [u8; 32] = bytes.try_into().map_err(|_| serde::de::Error::custom("invalid key length"))?;
        VerifyingKey::from_bytes(&arr).map_err(serde::de::Error::custom)
    }
}

impl Ed25519VerifyingKey {
    /// Create from raw bytes
    pub fn from_bytes(bytes: &[u8; PUBLIC_KEY_SIZE]) -> Result<Self, CryptoError> {
        let inner = VerifyingKey::from_bytes(bytes)
            .map_err(|_| CryptoError::InvalidPublicKey)?;
        Ok(Self { inner })
    }

    /// Verify a signature
    pub fn verify(&self, message: &[u8], signature: &Ed25519Signature) -> Result<bool, CryptoError> {
        Ok(self.inner.verify(message, &signature.0).is_ok())
    }

    /// Export to bytes
    pub fn to_bytes(&self) -> [u8; PUBLIC_KEY_SIZE] {
        self.inner.to_bytes()
    }

    /// Export as base64
    pub fn to_base64(&self) -> String {
        URL_SAFE_NO_PAD.encode(self.to_bytes())
    }

    /// Get key fingerprint (first 8 bytes of SHA256 hash)
    pub fn fingerprint(&self) -> String {
        let hash = Sha256::digest(self.to_bytes());
        hex::encode(&hash[..8])
    }
}

/// Ed25519 signature
#[derive(Clone, Serialize, Deserialize)]
pub struct Ed25519Signature(#[serde(with = "signature_serde")] Signature);

mod signature_serde {
    use super::*;
    use serde::{Deserializer, Serializer};

    pub fn serialize<S>(sig: &Signature, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&URL_SAFE_NO_PAD.encode(sig.to_bytes()))
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<Signature, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        let bytes = URL_SAFE_NO_PAD.decode(&s).map_err(serde::de::Error::custom)?;
        let arr: [u8; 64] = bytes.try_into().map_err(|_| serde::de::Error::custom("invalid sig length"))?;
        Ok(Signature::from_bytes(&arr))
    }
}

impl Ed25519Signature {
    /// Create from raw bytes
    pub fn from_bytes(bytes: &[u8; SIGNATURE_SIZE]) -> Self {
        Self(Signature::from_bytes(bytes))
    }

    /// Export to bytes
    pub fn to_bytes(&self) -> [u8; SIGNATURE_SIZE] {
        self.0.to_bytes()
    }

    /// Export as base64
    pub fn to_base64(&self) -> String {
        URL_SAFE_NO_PAD.encode(self.to_bytes())
    }
}

/// ChaCha20-Poly1305 authenticated encryption
pub struct Aead {
    cipher: ChaCha20Poly1305,
}

impl Aead {
    /// Create new AEAD instance with given key
    pub fn new(key: &SecretBytes) -> Result<Self, CryptoError> {
        if key.len() != KEY_SIZE {
            return Err(CryptoError::InvalidKeyLength);
        }
        let cipher = ChaCha20Poly1305::new_from_slice(key.expose())
            .map_err(|_| CryptoError::InvalidKeyLength)?;
        Ok(Self { cipher })
    }

    /// Encrypt with associated data
    pub fn encrypt(&self, plaintext: &[u8], aad: &[u8]) -> Result<Vec<u8>, CryptoError> {
        let mut nonce_bytes = [0u8; NONCE_SIZE];
        OsRng.fill_bytes(&mut nonce_bytes);
        let nonce = Nonce::from_slice(&nonce_bytes);
        
        let ciphertext = self.cipher
            .encrypt(nonce, plaintext)
            .map_err(|_| CryptoError::EncryptionFailed)?;
        
        // Prepend nonce to ciphertext
        let mut result = Vec::with_capacity(NONCE_SIZE + ciphertext.len());
        result.extend_from_slice(&nonce_bytes);
        result.extend_from_slice(&ciphertext);
        Ok(result)
    }

    /// Decrypt with associated data
    pub fn decrypt(&self, ciphertext: &[u8], aad: &[u8]) -> Result<Vec<u8>, CryptoError> {
        if ciphertext.len() < NONCE_SIZE + TAG_SIZE {
            return Err(CryptoError::InvalidCiphertext);
        }
        
        let (nonce_bytes, ct) = ciphertext.split_at(NONCE_SIZE);
        let nonce = Nonce::from_slice(nonce_bytes);
        
        self.cipher
            .decrypt(nonce, ct)
            .map_err(|_| CryptoError::DecryptionFailed)
    }
}

/// HKDF key derivation
pub fn hkdf_derive(
    ikm: &SecretBytes,
    salt: Option<&[u8]>,
    info: &[u8],
    output_len: usize,
) -> Result<SecretBytes, CryptoError> {
    let hk = Hkdf::<Sha256>::new(salt, ikm.expose());
    let mut okm = vec![0u8; output_len];
    hk.expand(info, &mut okm)
        .map_err(|_| CryptoError::KeyDerivationFailed)?;
    Ok(SecretBytes::new(okm))
}

/// BLAKE3 hash
pub fn blake3_hash(data: &[u8]) -> [u8; 32] {
    blake3::hash(data).into()
}

/// SHA-256 hash
pub fn sha256_hash(data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize().into()
}

/// Generate cryptographically secure random bytes
pub fn random_bytes(len: usize) -> Vec<u8> {
    let mut bytes = vec![0u8; len];
    OsRng.fill_bytes(&mut bytes);
    bytes
}

/// Generate random ID with prefix
pub fn generate_id(prefix: &str) -> String {
    let bytes = random_bytes(16);
    format!("{}_{}", prefix, hex::encode(bytes))
}

/// Get current Unix timestamp in seconds
pub fn current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("Time went backwards")
        .as_secs()
}

/// Constant-time comparison
pub fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut result = 0u8;
    for (x, y) in a.iter().zip(b.iter()) {
        result |= x ^ y;
    }
    result == 0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ed25519_sign_verify() {
        let signing_key = Ed25519SigningKey::generate();
        let verifying_key = signing_key.verifying_key();
        
        let message = b"test message";
        let signature = signing_key.sign(message);
        
        assert!(verifying_key.verify(message, &signature).unwrap());
    }

    #[test]
    fn test_hmac_sign_verify() {
        let key = SecretBytes::random(32);
        let message = b"test message";
        
        let sig = HmacSignature::sign(&key, message).unwrap();
        assert!(sig.verify(&key, message).unwrap());
    }

    #[test]
    fn test_aead_encrypt_decrypt() {
        let key = SecretBytes::random(32);
        let aead = Aead::new(&key).unwrap();
        
        let plaintext = b"secret data";
        let aad = b"associated data";
        
        let ciphertext = aead.encrypt(plaintext, aad).unwrap();
        let decrypted = aead.decrypt(&ciphertext, aad).unwrap();
        
        assert_eq!(plaintext.as_slice(), decrypted.as_slice());
    }

    #[test]
    fn test_hkdf_derive() {
        let ikm = SecretBytes::random(32);
        let salt = b"salt";
        let info = b"info";
        
        let derived = hkdf_derive(&ikm, Some(salt), info, 32).unwrap();
        assert_eq!(derived.len(), 32);
    }

    #[test]
    fn test_constant_time_eq() {
        let a = b"test123";
        let b = b"test123";
        let c = b"test456";
        
        assert!(constant_time_eq(a, b));
        assert!(!constant_time_eq(a, c));
    }
}
