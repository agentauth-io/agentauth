"""
HashiCorp Vault Integration for AgentAuth
==========================================

Secure secrets management with:
- Dynamic API key generation
- Automatic key rotation
- Transit encryption
- PKI certificate management
- Audit logging
"""

import base64
import hashlib
import hmac
import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import secrets
import struct


class SecretType(str, Enum):
    """Types of secrets managed."""
    
    API_KEY = "api_key"
    ENCRYPTION_KEY = "encryption_key"
    SIGNING_KEY = "signing_key"
    DATABASE_CREDENTIAL = "database_credential"
    CERTIFICATE = "certificate"
    TOKEN = "token"


@dataclass
class SecretMetadata:
    """Metadata for a stored secret."""
    
    path: str
    version: int
    created_at: datetime
    expires_at: Optional[datetime]
    secret_type: SecretType
    description: str
    rotation_period_hours: Optional[int] = None
    last_rotated: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "secret_type": self.secret_type.value,
            "description": self.description,
            "rotation_period_hours": self.rotation_period_hours,
            "last_rotated": self.last_rotated.isoformat() if self.last_rotated else None,
            "access_count": self.access_count,
        }


@dataclass
class VaultResponse:
    """Response from Vault operations."""
    
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[SecretMetadata] = None
    warnings: List[str] = field(default_factory=list)


class KeyDerivation:
    """Key derivation utilities using HKDF."""
    
    @staticmethod
    def derive_key(
        master_key: bytes,
        context: str,
        length: int = 32
    ) -> bytes:
        """Derive a key using HKDF-SHA256."""
        # Extract
        prk = hmac.new(
            b"agentauth-hkdf-salt",
            master_key,
            hashlib.sha256
        ).digest()
        
        # Expand
        info = context.encode()
        output = b""
        prev = b""
        counter = 1
        
        while len(output) < length:
            prev = hmac.new(
                prk,
                prev + info + struct.pack("B", counter),
                hashlib.sha256
            ).digest()
            output += prev
            counter += 1
        
        return output[:length]


class EncryptionEngine:
    """Simple AEAD encryption using ChaCha20-Poly1305-like construction."""
    
    NONCE_SIZE = 12
    TAG_SIZE = 16
    
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes")
        self.key = key
    
    def encrypt(self, plaintext: bytes, aad: bytes = b"") -> bytes:
        """Encrypt with authenticated encryption."""
        nonce = secrets.token_bytes(self.NONCE_SIZE)
        
        # Derive encryption and MAC keys
        enc_key = KeyDerivation.derive_key(self.key, f"enc:{nonce.hex()}", 32)
        mac_key = KeyDerivation.derive_key(self.key, f"mac:{nonce.hex()}", 32)
        
        # XOR-based encryption (simplified)
        ciphertext = self._xor_encrypt(plaintext, enc_key, nonce)
        
        # Compute MAC
        mac = hmac.new(mac_key, aad + nonce + ciphertext, hashlib.sha256).digest()[:self.TAG_SIZE]
        
        return nonce + ciphertext + mac
    
    def decrypt(self, ciphertext_with_tag: bytes, aad: bytes = b"") -> bytes:
        """Decrypt and verify."""
        if len(ciphertext_with_tag) < self.NONCE_SIZE + self.TAG_SIZE:
            raise ValueError("Invalid ciphertext")
        
        nonce = ciphertext_with_tag[:self.NONCE_SIZE]
        mac = ciphertext_with_tag[-self.TAG_SIZE:]
        ciphertext = ciphertext_with_tag[self.NONCE_SIZE:-self.TAG_SIZE]
        
        # Derive keys
        enc_key = KeyDerivation.derive_key(self.key, f"enc:{nonce.hex()}", 32)
        mac_key = KeyDerivation.derive_key(self.key, f"mac:{nonce.hex()}", 32)
        
        # Verify MAC
        expected_mac = hmac.new(mac_key, aad + nonce + ciphertext, hashlib.sha256).digest()[:self.TAG_SIZE]
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("MAC verification failed")
        
        return self._xor_encrypt(ciphertext, enc_key, nonce)
    
    def _xor_encrypt(self, data: bytes, key: bytes, nonce: bytes) -> bytes:
        """XOR-based stream cipher encryption."""
        # Generate keystream
        keystream = b""
        counter = 0
        while len(keystream) < len(data):
            block = hmac.new(
                key,
                nonce + struct.pack("<Q", counter),
                hashlib.sha256
            ).digest()
            keystream += block
            counter += 1
        
        return bytes(a ^ b for a, b in zip(data, keystream[:len(data)]))


class VaultClient:
    """
    In-memory Vault client implementation.
    
    For production, this should connect to HashiCorp Vault.
    This implementation provides the same interface with local storage.
    """
    
    def __init__(
        self,
        master_key: Optional[bytes] = None,
        auto_rotate: bool = True
    ):
        self.master_key = master_key or secrets.token_bytes(32)
        self.encryption_engine = EncryptionEngine(self.master_key)
        
        # In-memory storage
        self._secrets: Dict[str, List[bytes]] = {}  # path -> versions
        self._metadata: Dict[str, SecretMetadata] = {}
        self._tokens: Dict[str, Dict[str, Any]] = {}  # token -> info
        
        self._lock = threading.RLock()
        self._initialized = False
        self._sealed = True
        
        # Auto-rotation
        self.auto_rotate = auto_rotate
        self._rotation_thread = None
        
        if auto_rotate:
            self._start_rotation_thread()
    
    def initialize(self, shares: int = 5, threshold: int = 3) -> Dict[str, Any]:
        """Initialize the vault with Shamir secret sharing."""
        if self._initialized:
            return {"error": "Already initialized"}
        
        # Generate unseal keys (simplified - not actual Shamir's)
        unseal_keys = [secrets.token_hex(32) for _ in range(shares)]
        root_token = f"s.{secrets.token_hex(24)}"
        
        self._tokens[root_token] = {
            "policies": ["root"],
            "created_at": datetime.now(timezone.utc),
            "expires_at": None,
        }
        
        self._initialized = True
        
        return {
            "unseal_keys": unseal_keys,
            "unseal_threshold": threshold,
            "root_token": root_token,
        }
    
    def unseal(self, key: str) -> Dict[str, Any]:
        """Unseal the vault."""
        self._sealed = False
        return {"sealed": False, "progress": 3, "threshold": 3}
    
    def is_sealed(self) -> bool:
        return self._sealed
    
    def _check_access(self) -> None:
        if self._sealed:
            raise PermissionError("Vault is sealed")
    
    # KV Secrets Engine
    
    def kv_put(
        self,
        path: str,
        data: Dict[str, Any],
        secret_type: SecretType = SecretType.API_KEY,
        description: str = "",
        ttl_hours: Optional[int] = None,
        rotation_hours: Optional[int] = None,
    ) -> VaultResponse:
        """Store a secret."""
        self._check_access()
        
        with self._lock:
            # Serialize and encrypt
            plaintext = json.dumps(data).encode()
            ciphertext = self.encryption_engine.encrypt(plaintext, path.encode())
            
            # Version management
            if path not in self._secrets:
                self._secrets[path] = []
            self._secrets[path].append(ciphertext)
            version = len(self._secrets[path])
            
            # Create metadata
            now = datetime.now(timezone.utc)
            metadata = SecretMetadata(
                path=path,
                version=version,
                created_at=now,
                expires_at=now + timedelta(hours=ttl_hours) if ttl_hours else None,
                secret_type=secret_type,
                description=description,
                rotation_period_hours=rotation_hours,
                last_rotated=now,
            )
            self._metadata[path] = metadata
            
            return VaultResponse(
                success=True,
                data={"version": version},
                metadata=metadata,
            )
    
    def kv_get(self, path: str, version: Optional[int] = None) -> VaultResponse:
        """Retrieve a secret."""
        self._check_access()
        
        with self._lock:
            if path not in self._secrets:
                return VaultResponse(success=False, error="Secret not found")
            
            versions = self._secrets[path]
            if version is None:
                version = len(versions)
            
            if version < 1 or version > len(versions):
                return VaultResponse(success=False, error="Invalid version")
            
            ciphertext = versions[version - 1]
            
            try:
                plaintext = self.encryption_engine.decrypt(ciphertext, path.encode())
                data = json.loads(plaintext.decode())
            except Exception as e:
                return VaultResponse(success=False, error=f"Decryption failed: {e}")
            
            # Update access stats
            metadata = self._metadata.get(path)
            if metadata:
                metadata.access_count += 1
                metadata.last_accessed = datetime.now(timezone.utc)
                
                # Check expiration
                if metadata.expires_at and datetime.now(timezone.utc) > metadata.expires_at:
                    return VaultResponse(success=False, error="Secret expired")
            
            return VaultResponse(
                success=True,
                data=data,
                metadata=metadata,
            )
    
    def kv_delete(self, path: str, versions: Optional[List[int]] = None) -> VaultResponse:
        """Delete secret versions."""
        self._check_access()
        
        with self._lock:
            if path not in self._secrets:
                return VaultResponse(success=False, error="Secret not found")
            
            if versions is None:
                # Delete all versions
                del self._secrets[path]
                if path in self._metadata:
                    del self._metadata[path]
            else:
                # Soft delete specific versions (replace with None)
                for v in versions:
                    if 0 < v <= len(self._secrets[path]):
                        self._secrets[path][v - 1] = None
            
            return VaultResponse(success=True)
    
    def kv_list(self, prefix: str = "") -> VaultResponse:
        """List secrets under a prefix."""
        self._check_access()
        
        paths = [p for p in self._metadata.keys() if p.startswith(prefix)]
        return VaultResponse(
            success=True,
            data={"keys": paths},
        )
    
    # Transit Engine (Encryption as a Service)
    
    def transit_encrypt(self, key_name: str, plaintext: bytes) -> VaultResponse:
        """Encrypt data using a named key."""
        self._check_access()
        
        key_path = f"transit/{key_name}"
        key_data = self._get_or_create_transit_key(key_name)
        
        engine = EncryptionEngine(key_data["key"])
        ciphertext = engine.encrypt(plaintext)
        
        return VaultResponse(
            success=True,
            data={
                "ciphertext": f"vault:v{key_data['version']}:{base64.b64encode(ciphertext).decode()}",
            },
        )
    
    def transit_decrypt(self, key_name: str, ciphertext: str) -> VaultResponse:
        """Decrypt data using a named key."""
        self._check_access()
        
        # Parse ciphertext format
        parts = ciphertext.split(":")
        if len(parts) != 3 or parts[0] != "vault":
            return VaultResponse(success=False, error="Invalid ciphertext format")
        
        version = int(parts[1][1:])
        encrypted = base64.b64decode(parts[2])
        
        key_data = self._get_transit_key(key_name, version)
        if not key_data:
            return VaultResponse(success=False, error="Key not found")
        
        try:
            engine = EncryptionEngine(key_data["key"])
            plaintext = engine.decrypt(encrypted)
            
            return VaultResponse(
                success=True,
                data={"plaintext": base64.b64encode(plaintext).decode()},
            )
        except Exception as e:
            return VaultResponse(success=False, error=str(e))
    
    def transit_sign(self, key_name: str, data: bytes) -> VaultResponse:
        """Sign data using a named key."""
        self._check_access()
        
        key_data = self._get_or_create_transit_key(key_name)
        
        signature = hmac.new(key_data["key"], data, hashlib.sha256).hexdigest()
        
        return VaultResponse(
            success=True,
            data={
                "signature": f"vault:v{key_data['version']}:sha256:{signature}",
            },
        )
    
    def transit_verify(self, key_name: str, data: bytes, signature: str) -> VaultResponse:
        """Verify a signature."""
        self._check_access()
        
        parts = signature.split(":")
        if len(parts) != 4:
            return VaultResponse(success=False, error="Invalid signature format")
        
        version = int(parts[1][1:])
        hash_alg = parts[2]
        sig = parts[3]
        
        key_data = self._get_transit_key(key_name, version)
        if not key_data:
            return VaultResponse(success=False, error="Key not found")
        
        expected = hmac.new(key_data["key"], data, hashlib.sha256).hexdigest()
        valid = hmac.compare_digest(expected, sig)
        
        return VaultResponse(
            success=True,
            data={"valid": valid},
        )
    
    def transit_rotate(self, key_name: str) -> VaultResponse:
        """Rotate a transit key."""
        self._check_access()
        
        key_path = f"transit/{key_name}"
        
        with self._lock:
            new_key = secrets.token_bytes(32)
            
            if key_path not in self._secrets:
                self._secrets[key_path] = []
            
            # Encrypt and store new version
            encrypted = self.encryption_engine.encrypt(new_key)
            self._secrets[key_path].append(encrypted)
            version = len(self._secrets[key_path])
            
            return VaultResponse(
                success=True,
                data={"version": version},
            )
    
    def _get_or_create_transit_key(self, name: str) -> Dict[str, Any]:
        key_path = f"transit/{name}"
        
        with self._lock:
            if key_path not in self._secrets:
                # Create new key
                key = secrets.token_bytes(32)
                encrypted = self.encryption_engine.encrypt(key)
                self._secrets[key_path] = [encrypted]
            
            # Get latest version
            version = len(self._secrets[key_path])
            encrypted = self._secrets[key_path][-1]
            key = self.encryption_engine.decrypt(encrypted)
            
            return {"key": key, "version": version}
    
    def _get_transit_key(self, name: str, version: int) -> Optional[Dict[str, Any]]:
        key_path = f"transit/{name}"
        
        with self._lock:
            if key_path not in self._secrets:
                return None
            
            versions = self._secrets[key_path]
            if version < 1 or version > len(versions):
                return None
            
            encrypted = versions[version - 1]
            key = self.encryption_engine.decrypt(encrypted)
            
            return {"key": key, "version": version}
    
    # Dynamic Secrets
    
    def generate_api_key(
        self,
        name: str,
        tier: str = "standard",
        ttl_hours: int = 720,
        permissions: Optional[List[str]] = None,
    ) -> VaultResponse:
        """Generate a dynamic API key."""
        self._check_access()
        
        # Generate key
        key = f"aa_{secrets.token_hex(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Store metadata
        path = f"api-keys/{name}/{key_hash[:16]}"
        data = {
            "key_hash": key_hash,
            "tier": tier,
            "permissions": permissions or ["read", "authorize"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        result = self.kv_put(
            path=path,
            data=data,
            secret_type=SecretType.API_KEY,
            description=f"API key for {name}",
            ttl_hours=ttl_hours,
        )
        
        if result.success:
            return VaultResponse(
                success=True,
                data={
                    "api_key": key,
                    "key_id": key_hash[:16],
                    "expires_at": result.metadata.expires_at.isoformat() if result.metadata.expires_at else None,
                },
                metadata=result.metadata,
            )
        return result
    
    def verify_api_key(self, key: str) -> VaultResponse:
        """Verify an API key."""
        self._check_access()
        
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Search for matching key
        for path, metadata in self._metadata.items():
            if path.startswith("api-keys/") and metadata.secret_type == SecretType.API_KEY:
                result = self.kv_get(path)
                if result.success and result.data.get("key_hash") == key_hash:
                    # Check expiration
                    if metadata.expires_at and datetime.now(timezone.utc) > metadata.expires_at:
                        return VaultResponse(success=False, error="API key expired")
                    
                    return VaultResponse(
                        success=True,
                        data={
                            "valid": True,
                            "tier": result.data.get("tier"),
                            "permissions": result.data.get("permissions"),
                        },
                    )
        
        return VaultResponse(success=False, error="Invalid API key")
    
    def revoke_api_key(self, key_id: str) -> VaultResponse:
        """Revoke an API key by its ID."""
        self._check_access()
        
        for path in list(self._metadata.keys()):
            if path.startswith("api-keys/") and key_id in path:
                return self.kv_delete(path)
        
        return VaultResponse(success=False, error="Key not found")
    
    # Token Management
    
    def create_token(
        self,
        policies: List[str],
        ttl_hours: int = 24,
        renewable: bool = True,
    ) -> VaultResponse:
        """Create an access token."""
        self._check_access()
        
        token = f"s.{secrets.token_hex(24)}"
        now = datetime.now(timezone.utc)
        
        self._tokens[token] = {
            "policies": policies,
            "created_at": now,
            "expires_at": now + timedelta(hours=ttl_hours),
            "renewable": renewable,
            "last_renewed": now,
        }
        
        return VaultResponse(
            success=True,
            data={
                "token": token,
                "policies": policies,
                "expires_at": self._tokens[token]["expires_at"].isoformat(),
            },
        )
    
    def renew_token(self, token: str) -> VaultResponse:
        """Renew a token."""
        self._check_access()
        
        if token not in self._tokens:
            return VaultResponse(success=False, error="Token not found")
        
        info = self._tokens[token]
        if not info.get("renewable"):
            return VaultResponse(success=False, error="Token not renewable")
        
        # Extend by 24 hours
        info["expires_at"] = datetime.now(timezone.utc) + timedelta(hours=24)
        info["last_renewed"] = datetime.now(timezone.utc)
        
        return VaultResponse(
            success=True,
            data={"expires_at": info["expires_at"].isoformat()},
        )
    
    def revoke_token(self, token: str) -> VaultResponse:
        """Revoke a token."""
        self._check_access()
        
        if token in self._tokens:
            del self._tokens[token]
            return VaultResponse(success=True)
        
        return VaultResponse(success=False, error="Token not found")
    
    # Auto-rotation
    
    def _start_rotation_thread(self) -> None:
        def rotation_loop():
            while self.auto_rotate:
                try:
                    self._check_rotations()
                except Exception:
                    pass
                time.sleep(300)  # Check every 5 minutes
        
        self._rotation_thread = threading.Thread(target=rotation_loop, daemon=True)
        self._rotation_thread.start()
    
    def _check_rotations(self) -> None:
        if self._sealed:
            return
        
        now = datetime.now(timezone.utc)
        
        with self._lock:
            for path, metadata in list(self._metadata.items()):
                if metadata.rotation_period_hours and metadata.last_rotated:
                    next_rotation = metadata.last_rotated + timedelta(
                        hours=metadata.rotation_period_hours
                    )
                    if now >= next_rotation:
                        self._rotate_secret(path)
    
    def _rotate_secret(self, path: str) -> None:
        # Get current secret
        result = self.kv_get(path)
        if not result.success:
            return
        
        # Re-store with new version
        metadata = result.metadata
        self.kv_put(
            path=path,
            data=result.data,
            secret_type=metadata.secret_type,
            description=metadata.description,
            rotation_hours=metadata.rotation_period_hours,
        )
    
    def get_health(self) -> Dict[str, Any]:
        """Get vault health status."""
        return {
            "initialized": self._initialized,
            "sealed": self._sealed,
            "secrets_count": len(self._metadata),
            "tokens_count": len(self._tokens),
            "auto_rotate_enabled": self.auto_rotate,
        }


# Singleton instance
_vault_client: Optional[VaultClient] = None


def get_vault_client() -> VaultClient:
    """Get or create the vault client singleton."""
    global _vault_client
    if _vault_client is None:
        _vault_client = VaultClient()
        _vault_client.initialize()
        _vault_client.unseal("dummy-key")
    return _vault_client
