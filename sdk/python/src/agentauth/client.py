"""
AgentAuth SDK Client

Sync and async clients for the AgentAuth API.
"""
from typing import Optional, Dict, Any, List
import httpx

from agentauth.models import (
    Consent,
    Authorization,
    Verification,
    Transaction,
    ConsentConstraints,
)
from agentauth.exceptions import (
    AgentAuthError,
    AuthorizationDenied,
    InvalidToken,
    VerificationFailed,
    APIError,
    RateLimitExceeded,
)


class ConsentsAPI:
    """Consents API wrapper."""
    
    def __init__(self, client: "AgentAuth"):
        self._client = client
    
    def create(
        self,
        user_id: str,
        intent: str,
        max_amount: float,
        currency: str = "USD",
        allowed_merchants: Optional[list[str]] = None,
        allowed_categories: Optional[list[str]] = None,
        expires_in_seconds: int = 3600,
        single_use: bool = True,
        signature: str = "sdk_generated",
        public_key: str = "sdk_key",
    ) -> Consent:
        """
        Create a new user consent.
        
        Args:
            user_id: Unique identifier for the user
            intent: Description of what the user wants to authorize
            max_amount: Maximum spending limit
            currency: Currency code (USD, EUR, etc.)
            allowed_merchants: List of allowed merchant IDs
            allowed_categories: List of allowed MCCs
            expires_in_seconds: Consent validity duration
            single_use: Whether consent is single-use
            signature: User's signature
            public_key: User's public key
            
        Returns:
            Consent object with delegation_token
        """
        data = {
            "user_id": user_id,
            "intent": {"description": intent},
            "constraints": {
                "max_amount": max_amount,
                "currency": currency,
                "allowed_merchants": allowed_merchants,
                "allowed_categories": allowed_categories,
            },
            "options": {
                "expires_in_seconds": expires_in_seconds,
                "single_use": single_use,
            },
            "signature": signature,
            "public_key": public_key,
        }
        
        response = self._client._request("POST", "/v1/consents", json=data)
        return Consent(**response)
    
    def get(self, consent_id: str) -> Dict[str, Any]:
        """Get consent details by ID."""
        return self._client._request("GET", f"/v1/consents/{consent_id}")
    
    def revoke(self, consent_id: str) -> bool:
        """Revoke a consent."""
        self._client._request("DELETE", f"/v1/consents/{consent_id}")
        return True


class AgentAuth:
    """
    AgentAuth SDK Client.
    
    The main entry point for interacting with the AgentAuth API.
    
    Example:
        ```python
        from agentauth import AgentAuth
        
        client = AgentAuth(api_key="aa_live_xxx")
        
        # Create consent
        consent = client.consents.create(
            user_id="user_123",
            intent="Buy flight under $500",
            max_amount=500,
            currency="USD"
        )
        
        # Authorize
        auth = client.authorize(
            token=consent.delegation_token,
            amount=347,
            currency="USD",
            merchant_id="delta"
        )
        
        if auth.allowed:
            print(f"Authorized: {auth.authorization_code}")
        ```
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
    ):
        """
        Initialize the AgentAuth client.
        
        Args:
            api_key: API key for authentication (optional for local dev)
            base_url: Base URL for the AgentAuth API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        # Initialize API wrappers
        self.consents = ConsentsAPI(self)
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 0.5  # seconds
        self.max_delay = 4.0   # seconds
        
        # Setup HTTP client
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self._http = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )
    
    def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API with retry logic.
        
        Implements exponential backoff for transient failures and rate limits.
        """
        import time
        import random
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self._http.request(method, path, **kwargs)
                
                # Rate limit - retry with backoff
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and attempt < self.max_retries:
                        time.sleep(int(retry_after))
                        continue
                    raise RateLimitExceeded(retry_after=int(retry_after) if retry_after else None)
                
                # Server errors - retry with exponential backoff  
                if response.status_code >= 500 and attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (2 ** attempt) + random.uniform(0, 0.1),
                        self.max_delay
                    )
                    time.sleep(delay)
                    continue
                
                if response.status_code == 204:
                    return {}
                
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    raise APIError(
                        status_code=response.status_code,
                        message=error_data.get("detail", "Unknown error")
                    )
                
                return response.json()
                
            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (2 ** attempt) + random.uniform(0, 0.1),
                        self.max_delay
                    )
                    time.sleep(delay)
                    continue
                raise AgentAuthError(f"Request failed after {self.max_retries + 1} attempts: {str(e)}")
        
        if last_exception:
            raise AgentAuthError(f"Request failed: {str(last_exception)}")
    
    def authorize(
        self,
        token: str,
        amount: float,
        currency: str = "USD",
        merchant_id: Optional[str] = None,
        merchant_name: Optional[str] = None,
        merchant_category: Optional[str] = None,
        action: str = "payment",
        raise_on_deny: bool = False,
    ) -> Authorization:
        """
        Request authorization for a transaction.
        
        Args:
            token: Delegation token from consent
            amount: Transaction amount
            currency: Transaction currency
            merchant_id: Merchant identifier
            merchant_name: Merchant display name
            merchant_category: Merchant category code (MCC)
            action: Type of action (default: "payment")
            raise_on_deny: Raise AuthorizationDenied if denied
            
        Returns:
            Authorization object with decision
            
        Raises:
            AuthorizationDenied: If raise_on_deny=True and authorization denied
            InvalidToken: If the token is invalid or expired
        """
        data = {
            "delegation_token": token,
            "action": action,
            "transaction": {
                "amount": amount,
                "currency": currency,
                "merchant_id": merchant_id,
                "merchant_name": merchant_name,
                "merchant_category": merchant_category,
            },
        }
        
        response = self._request("POST", "/v1/authorize", json=data)
        auth = Authorization(**response)
        
        if raise_on_deny and auth.denied:
            raise AuthorizationDenied(
                reason=auth.reason,
                message=auth.message
            )
        
        return auth
    
    def verify(
        self,
        authorization_code: str,
        amount: float,
        currency: str = "USD",
        merchant_id: Optional[str] = None,
        raise_on_invalid: bool = False,
    ) -> Verification:
        """
        Verify an authorization code.
        
        Args:
            authorization_code: The authorization code to verify
            amount: Transaction amount
            currency: Transaction currency
            merchant_id: Merchant identifier
            raise_on_invalid: Raise VerificationFailed if invalid
            
        Returns:
            Verification object with consent proof
            
        Raises:
            VerificationFailed: If raise_on_invalid=True and verification fails
        """
        data = {
            "authorization_code": authorization_code,
            "transaction": {
                "amount": amount,
                "currency": currency,
            },
            "merchant_id": merchant_id,
        }
        
        response = self._request("POST", "/v1/verify", json=data)
        verification = Verification(**response)
        
        if raise_on_invalid and not verification.valid:
            raise VerificationFailed(verification.error or "Unknown error")
        
        return verification
    
    # ==========================================================================
    # Billing API Methods
    # ==========================================================================
    
    def get_billing_plans(self) -> List[Dict[str, Any]]:
        """
        Get available billing plans.
        
        Returns:
            List of available billing plans with pricing and limits
        """
        return self._request("GET", "/v1/billing/plans")
    
    def get_billing_usage(self) -> Dict[str, Any]:
        """
        Get current billing usage for authenticated organization.
        
        Returns:
            Current usage statistics including request counts and limits
        """
        return self._request("GET", "/v1/billing/usage")
    
    def create_checkout_session(
        self,
        plan: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for upgrading to a paid plan.
        
        Args:
            plan: Plan ID to upgrade to ('startup', 'growth', 'enterprise')
            success_url: URL to redirect to after successful payment
            cancel_url: URL to redirect to if checkout is cancelled
            
        Returns:
            Dict with 'checkout_url' for redirecting user to Stripe
        """
        data = {
            "plan": plan,
            "success_url": success_url,
            "cancel_url": cancel_url
        }
        return self._request("POST", "/v1/billing/checkout", json=data)
    
    def get_billing_portal_url(self, return_url: str) -> Dict[str, Any]:
        """
        Get a URL to the Stripe customer billing portal.
        
        Args:
            return_url: URL to return to after visiting the portal
            
        Returns:
            Dict with 'portal_url' for redirecting user to billing portal
        """
        return self._request(
            "POST", 
            "/v1/billing/portal",
            json={"return_url": return_url}
        )
    
    def close(self):
        """Close the HTTP client."""
        self._http.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class AsyncConsentsAPI:
    """Async Consents API wrapper."""
    
    def __init__(self, client: "AsyncAgentAuth"):
        self._client = client
    
    async def create(
        self,
        user_id: str,
        intent: str,
        max_amount: float,
        currency: str = "USD",
        allowed_merchants: Optional[list[str]] = None,
        allowed_categories: Optional[list[str]] = None,
        expires_in_seconds: int = 3600,
        single_use: bool = True,
        signature: str = "sdk_generated",
        public_key: str = "sdk_key",
    ) -> Consent:
        """Create a new user consent (async)."""
        data = {
            "user_id": user_id,
            "intent": {"description": intent},
            "constraints": {
                "max_amount": max_amount,
                "currency": currency,
                "allowed_merchants": allowed_merchants,
                "allowed_categories": allowed_categories,
            },
            "options": {
                "expires_in_seconds": expires_in_seconds,
                "single_use": single_use,
            },
            "signature": signature,
            "public_key": public_key,
        }
        
        response = await self._client._request("POST", "/v1/consents", json=data)
        return Consent(**response)


class AsyncAgentAuth:
    """
    Async AgentAuth SDK Client.
    
    Example:
        ```python
        from agentauth import AsyncAgentAuth
        
        async with AsyncAgentAuth(api_key="aa_live_xxx") as client:
            consent = await client.consents.create(
                user_id="user_123",
                intent="Buy flight",
                max_amount=500,
                currency="USD"
            )
        ```
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        self.consents = AsyncConsentsAPI(self)
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 0.5  # seconds
        self.max_delay = 4.0   # seconds
        
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an async HTTP request to the API with retry logic.
        
        Implements exponential backoff for transient failures and rate limits.
        """
        import asyncio
        import random
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._http.request(method, path, **kwargs)
                
                # Rate limit - retry with backoff
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and attempt < self.max_retries:
                        await asyncio.sleep(int(retry_after))
                        continue
                    raise RateLimitExceeded(retry_after=int(retry_after) if retry_after else None)
                
                # Server errors - retry with exponential backoff
                if response.status_code >= 500 and attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (2 ** attempt) + random.uniform(0, 0.1),
                        self.max_delay
                    )
                    await asyncio.sleep(delay)
                    continue
                
                if response.status_code == 204:
                    return {}
                
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    raise APIError(
                        status_code=response.status_code,
                        message=error_data.get("detail", "Unknown error")
                    )
                
                return response.json()
                
            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (2 ** attempt) + random.uniform(0, 0.1),
                        self.max_delay
                    )
                    await asyncio.sleep(delay)
                    continue
                raise AgentAuthError(f"Request failed after {self.max_retries + 1} attempts: {str(e)}")
        
        if last_exception:
            raise AgentAuthError(f"Request failed: {str(last_exception)}")
    
    async def authorize(
        self,
        token: str,
        amount: float,
        currency: str = "USD",
        merchant_id: Optional[str] = None,
        merchant_name: Optional[str] = None,
        action: str = "payment",
        raise_on_deny: bool = False,
    ) -> Authorization:
        """Request authorization for a transaction (async)."""
        data = {
            "delegation_token": token,
            "action": action,
            "transaction": {
                "amount": amount,
                "currency": currency,
                "merchant_id": merchant_id,
                "merchant_name": merchant_name,
            },
        }
        
        response = await self._request("POST", "/v1/authorize", json=data)
        auth = Authorization(**response)
        
        if raise_on_deny and auth.denied:
            raise AuthorizationDenied(reason=auth.reason, message=auth.message)
        
        return auth
    
    async def verify(
        self,
        authorization_code: str,
        amount: float,
        currency: str = "USD",
        merchant_id: Optional[str] = None,
        raise_on_invalid: bool = False,
    ) -> Verification:
        """Verify an authorization code (async)."""
        data = {
            "authorization_code": authorization_code,
            "transaction": {"amount": amount, "currency": currency},
            "merchant_id": merchant_id,
        }
        
        response = await self._request("POST", "/v1/verify", json=data)
        verification = Verification(**response)
        
        if raise_on_invalid and not verification.valid:
            raise VerificationFailed(verification.error or "Unknown error")
        
        return verification
    
    # ==========================================================================
    # Billing API Methods
    # ==========================================================================
    
    async def get_billing_plans(self) -> List[Dict[str, Any]]:
        """
        Get available billing plans.
        
        Returns:
            List of available billing plans with pricing and limits
        """
        return await self._request("GET", "/v1/billing/plans")
    
    async def get_billing_usage(self) -> Dict[str, Any]:
        """
        Get current billing usage for authenticated organization.
        
        Returns:
            Current usage statistics including request counts and limits
        """
        return await self._request("GET", "/v1/billing/usage")
    
    async def create_checkout_session(
        self,
        plan: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for upgrading to a paid plan.
        
        Args:
            plan: Plan ID to upgrade to ('startup', 'growth', 'enterprise')
            success_url: URL to redirect to after successful payment
            cancel_url: URL to redirect to if checkout is cancelled
            
        Returns:
            Dict with 'checkout_url' for redirecting user to Stripe
        """
        data = {
            "plan": plan,
            "success_url": success_url,
            "cancel_url": cancel_url
        }
        return await self._request("POST", "/v1/billing/checkout", json=data)
    
    async def get_billing_portal_url(self, return_url: str) -> Dict[str, Any]:
        """
        Get a URL to the Stripe customer billing portal.
        
        Args:
            return_url: URL to return to after visiting the portal
            
        Returns:
            Dict with 'portal_url' for redirecting user to billing portal
        """
        return await self._request(
            "POST", 
            "/v1/billing/portal",
            json={"return_url": return_url}
        )
    
    async def close(self):
        """Close the async HTTP client."""
        await self._http.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
