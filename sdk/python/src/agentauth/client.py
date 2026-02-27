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

SDK_VERSION = "0.3.0"
_USER_AGENT = f"agentauth-python/{SDK_VERSION}"


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
        allowed_merchants: Optional[List[str]] = None,
        allowed_categories: Optional[List[str]] = None,
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

    def list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List consents with pagination."""
        return self._client._request(
            "GET", "/v1/consents", params={"limit": limit, "offset": offset}
        )

    def get(self, consent_id: str) -> Dict[str, Any]:
        """Get consent details by ID."""
        return self._client._request("GET", f"/v1/consents/{consent_id}")

    def revoke(self, consent_id: str) -> bool:
        """Revoke a consent."""
        self._client._request("DELETE", f"/v1/consents/{consent_id}")
        return True


class AgentsAPI:
    """Agents API wrapper."""

    def __init__(self, client: "AgentAuth"):
        self._client = client

    def list(self) -> Dict[str, Any]:
        """List all registered agents."""
        return self._client._request("GET", "/v1/agents")

    def create(self, name: str, description: Optional[str] = None, permissions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Register a new agent."""
        data: Dict[str, Any] = {"name": name}
        if description:
            data["description"] = description
        if permissions:
            data["permissions"] = permissions
        return self._client._request("POST", "/v1/agents", json=data)

    def get(self, agent_id: str) -> Dict[str, Any]:
        """Get agent details."""
        return self._client._request("GET", f"/v1/agents/{agent_id}")

    def delete(self, agent_id: str) -> Dict[str, Any]:
        """Delete an agent."""
        return self._client._request("DELETE", f"/v1/agents/{agent_id}")


class LimitsAPI:
    """Limits API wrapper."""

    def __init__(self, client: "AgentAuth"):
        self._client = client

    def get(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get spending limits."""
        params = {"user_id": user_id} if user_id else {}
        return self._client._request("GET", "/v1/limits", params=params)

    def set(
        self,
        user_id: str,
        daily_limit: Optional[float] = None,
        monthly_limit: Optional[float] = None,
        per_transaction_limit: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Set spending limits."""
        data: Dict[str, Any] = {"user_id": user_id}
        if daily_limit is not None:
            data["daily_limit"] = daily_limit
        if monthly_limit is not None:
            data["monthly_limit"] = monthly_limit
        if per_transaction_limit is not None:
            data["per_transaction_limit"] = per_transaction_limit
        return self._client._request("POST", "/v1/limits", json=data)

    def usage(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get usage stats."""
        params = {"user_id": user_id} if user_id else {}
        return self._client._request("GET", "/v1/limits/usage", params=params)


class WebhooksAPI:
    """Webhooks API wrapper."""

    def __init__(self, client: "AgentAuth"):
        self._client = client

    def list(self) -> Dict[str, Any]:
        """List configured webhooks."""
        return self._client._request("GET", "/v1/webhooks")

    def create(self, url: str, events: List[str], secret: Optional[str] = None) -> Dict[str, Any]:
        """Register a new webhook."""
        data: Dict[str, Any] = {"url": url, "events": events}
        if secret:
            data["secret"] = secret
        return self._client._request("POST", "/v1/webhooks", json=data)

    def delete(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook."""
        return self._client._request("DELETE", f"/v1/webhooks/{webhook_id}")


class AnalyticsAPI:
    """Analytics API wrapper."""

    def __init__(self, client: "AgentAuth"):
        self._client = client

    def summary(self, period: str = "7d") -> Dict[str, Any]:
        """Get analytics summary."""
        return self._client._request("GET", "/v1/analytics", params={"period": period})


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
        self.agents = AgentsAPI(self)
        self.limits = LimitsAPI(self)
        self.webhooks = WebhooksAPI(self)
        self.analytics = AnalyticsAPI(self)

        # Retry configuration
        self.max_retries = 3
        self.base_delay = 0.5  # seconds
        self.max_delay = 4.0   # seconds

        # Setup HTTP client
        headers = {
            "Content-Type": "application/json",
            "User-Agent": _USER_AGENT,
        }
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
        allowed_merchants: Optional[List[str]] = None,
        allowed_categories: Optional[List[str]] = None,
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

    async def list(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """List consents with pagination (async)."""
        return await self._client._request(
            "GET", "/v1/consents", params={"limit": limit, "offset": offset}
        )

    async def get(self, consent_id: str) -> Dict[str, Any]:
        """Get consent details by ID (async)."""
        return await self._client._request("GET", f"/v1/consents/{consent_id}")

    async def revoke(self, consent_id: str) -> bool:
        """Revoke a consent (async)."""
        await self._client._request("DELETE", f"/v1/consents/{consent_id}")
        return True


class AsyncAgentsAPI:
    """Async Agents API wrapper."""

    def __init__(self, client: "AsyncAgentAuth"):
        self._client = client

    async def list(self) -> Dict[str, Any]:
        return await self._client._request("GET", "/v1/agents")

    async def create(self, name: str, description: Optional[str] = None, permissions: Optional[List[str]] = None) -> Dict[str, Any]:
        data: Dict[str, Any] = {"name": name}
        if description:
            data["description"] = description
        if permissions:
            data["permissions"] = permissions
        return await self._client._request("POST", "/v1/agents", json=data)

    async def get(self, agent_id: str) -> Dict[str, Any]:
        return await self._client._request("GET", f"/v1/agents/{agent_id}")

    async def delete(self, agent_id: str) -> Dict[str, Any]:
        return await self._client._request("DELETE", f"/v1/agents/{agent_id}")


class AsyncLimitsAPI:
    """Async Limits API wrapper."""

    def __init__(self, client: "AsyncAgentAuth"):
        self._client = client

    async def get(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        params = {"user_id": user_id} if user_id else {}
        return await self._client._request("GET", "/v1/limits", params=params)

    async def usage(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        params = {"user_id": user_id} if user_id else {}
        return await self._client._request("GET", "/v1/limits/usage", params=params)


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
        self.agents = AsyncAgentsAPI(self)
        self.limits = AsyncLimitsAPI(self)

        # Retry configuration
        self.max_retries = 3
        self.base_delay = 0.5  # seconds
        self.max_delay = 4.0   # seconds

        headers = {
            "Content-Type": "application/json",
            "User-Agent": _USER_AGENT,
        }
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
