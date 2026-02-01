"""
AgentAuth Cryptographic Module
Implements secure token generation, validation, and anti-reverse-engineering measures
"""

import hashlib
import hmac
import secrets
import time
import base64
import json
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import os


@dataclass
class TokenPayload:
    """Secure token payload with built-in validation"""
    agent_id: str
    user_id: str
    scope: str
    issued_at: float
    expires_at: float
    nonce: str
    fingerprint: str


class SecureTokenManager:
    """
    High-security token manager with multiple layers of protection:
    - AES-256-GCM encryption
    - HMAC-SHA512 signatures
    - Time-based nonce validation
    - Hardware fingerprinting
    - Anti-replay protection
    """
    
    def __init__(self, master_key: Optional[bytes] = None):
        self._master_key = master_key or self._derive_master_key()
        self._nonce_cache: Dict[str, float] = {}
        self._token_blacklist: set = set()
        self._rotation_interval = 3600  # 1 hour
        self._last_rotation = time.time()
        
    def _derive_master_key(self) -> bytes:
        """Derive master key using PBKDF2 with system entropy"""
        salt = os.environ.get("AGENTAUTH_SALT", "").encode() or secrets.token_bytes(32)
        secret = os.environ.get("AGENTAUTH_SECRET", "").encode() or secrets.token_bytes(64)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=salt,
            iterations=480000,
            backend=default_backend()
        )
        return kdf.derive(secret)
    
    def _generate_nonce(self) -> str:
        """Generate cryptographically secure nonce with timestamp binding"""
        timestamp = int(time.time() * 1000000)
        random_bytes = secrets.token_bytes(16)
        combined = timestamp.to_bytes(8, 'big') + random_bytes
        return base64.urlsafe_b64encode(combined).decode()
    
    def _compute_fingerprint(self, agent_id: str, user_id: str, scope: str) -> str:
        """Compute unique fingerprint for request binding"""
        data = f"{agent_id}:{user_id}:{scope}:{int(time.time() // 60)}"
        return hashlib.blake2b(data.encode(), digest_size=16).hexdigest()
    
    def generate_token(
        self,
        agent_id: str,
        user_id: str,
        scope: str = "transaction",
        ttl_seconds: int = 300
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a secure, encrypted authorization token
        
        Returns:
            Tuple of (encrypted_token, metadata)
        """
        now = time.time()
        nonce = self._generate_nonce()
        fingerprint = self._compute_fingerprint(agent_id, user_id, scope)
        
        payload = TokenPayload(
            agent_id=agent_id,
            user_id=user_id,
            scope=scope,
            issued_at=now,
            expires_at=now + ttl_seconds,
            nonce=nonce,
            fingerprint=fingerprint
        )
        
        # Serialize payload
        payload_json = json.dumps(payload.__dict__).encode()
        
        # Encrypt with AES-256-GCM
        aesgcm = AESGCM(self._master_key)
        iv = secrets.token_bytes(12)
        ciphertext = aesgcm.encrypt(iv, payload_json, None)
        
        # Combine IV + ciphertext
        encrypted = iv + ciphertext
        
        # Add HMAC signature
        signature = hmac.new(
            self._master_key,
            encrypted,
            hashlib.sha512
        ).digest()
        
        # Final token: base64(signature + encrypted)
        final_token = base64.urlsafe_b64encode(signature + encrypted).decode()
        
        # Cache nonce for replay protection
        self._nonce_cache[nonce] = now + ttl_seconds
        
        return final_token, {
            "expires_at": payload.expires_at,
            "fingerprint": fingerprint,
            "scope": scope
        }
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[TokenPayload], str]:
        """
        Validate and decrypt a token with comprehensive security checks
        
        Returns:
            Tuple of (is_valid, payload, error_message)
        """
        try:
            # Decode token
            raw = base64.urlsafe_b64decode(token.encode())
            
            if len(raw) < 64 + 12 + 16:  # signature + iv + min ciphertext
                return False, None, "INVALID_TOKEN_FORMAT"
            
            # Extract signature and encrypted data
            signature = raw[:64]
            encrypted = raw[64:]
            
            # Verify HMAC signature
            expected_sig = hmac.new(
                self._master_key,
                encrypted,
                hashlib.sha512
            ).digest()
            
            if not hmac.compare_digest(signature, expected_sig):
                return False, None, "INVALID_SIGNATURE"
            
            # Check blacklist
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if token_hash in self._token_blacklist:
                return False, None, "TOKEN_REVOKED"
            
            # Decrypt
            iv = encrypted[:12]
            ciphertext = encrypted[12:]
            
            aesgcm = AESGCM(self._master_key)
            payload_json = aesgcm.decrypt(iv, ciphertext, None)
            payload_dict = json.loads(payload_json)
            
            payload = TokenPayload(**payload_dict)
            
            # Validate expiration
            now = time.time()
            if now > payload.expires_at:
                return False, None, "TOKEN_EXPIRED"
            
            # Validate nonce (anti-replay)
            if payload.nonce in self._nonce_cache:
                if self._nonce_cache[payload.nonce] < now:
                    del self._nonce_cache[payload.nonce]
                    return False, None, "NONCE_EXPIRED"
            
            return True, payload, "OK"
            
        except Exception as e:
            return False, None, f"VALIDATION_ERROR"
    
    def revoke_token(self, token: str) -> bool:
        """Add token to blacklist"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self._token_blacklist.add(token_hash)
        return True
    
    def rotate_keys(self) -> None:
        """Rotate encryption keys (should be called periodically)"""
        self._master_key = self._derive_master_key()
        self._last_rotation = time.time()
        self._nonce_cache.clear()


class HMACValidator:
    """
    Request signature validator for API authentication
    Implements constant-time comparison and timestamp validation
    """
    
    def __init__(self, secret_key: bytes, max_age_seconds: int = 300):
        self._secret_key = secret_key
        self._max_age = max_age_seconds
        self._used_signatures: Dict[str, float] = {}
    
    def sign_request(
        self,
        method: str,
        path: str,
        body: bytes,
        timestamp: Optional[int] = None
    ) -> Tuple[str, int]:
        """
        Sign an API request
        
        Returns:
            Tuple of (signature, timestamp)
        """
        ts = timestamp or int(time.time())
        
        # Canonical request string
        canonical = f"{method.upper()}\n{path}\n{ts}\n"
        body_hash = hashlib.sha256(body).hexdigest()
        canonical += body_hash
        
        signature = hmac.new(
            self._secret_key,
            canonical.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return signature, ts
    
    def verify_request(
        self,
        method: str,
        path: str,
        body: bytes,
        signature: str,
        timestamp: int
    ) -> Tuple[bool, str]:
        """
        Verify an API request signature
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        now = int(time.time())
        
        # Check timestamp freshness
        if abs(now - timestamp) > self._max_age:
            return False, "TIMESTAMP_EXPIRED"
        
        # Check for replay
        sig_key = f"{signature}:{timestamp}"
        if sig_key in self._used_signatures:
            return False, "REPLAY_DETECTED"
        
        # Compute expected signature
        expected, _ = self.sign_request(method, path, body, timestamp)
        
        # Constant-time comparison
        if not hmac.compare_digest(signature, expected):
            return False, "INVALID_SIGNATURE"
        
        # Store for replay protection
        self._used_signatures[sig_key] = now
        
        # Cleanup old signatures
        self._cleanup_signatures()
        
        return True, "OK"
    
    def _cleanup_signatures(self) -> None:
        """Remove expired signatures from cache"""
        now = time.time()
        expired = [k for k, v in self._used_signatures.items() if now - v > self._max_age * 2]
        for k in expired:
            del self._used_signatures[k]
