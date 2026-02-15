"""
Network Connectivity Checker - Detects actual internet access beyond WiFi.

This module provides functionality to detect:
- Internet connectivity (not just WiFi connection)
- Captive portal / re-authentication requirements
- Network accessibility issues

Used to pause timer when re-authentication is needed.
"""

import asyncio
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class NetworkConnectivityChecker:
    """
    Detects internet connectivity beyond WiFi connection status.

    This is crucial for detecting when user needs to re-authenticate
    (e.g., corporate portal login) even though WiFi appears connected.
    """

    # Multiple connectivity check endpoints for redundancy
    CONNECTIVITY_ENDPOINTS = [
        "http://connectivitycheck.gstatic.com/generate_204",  # Google
        "http://www.msftconnect.com/connecttest.txt",        # Microsoft
        "http://captive.apple.com/hotspot-detect.html"       # Apple
    ]

    def __init__(self):
        """Initialize network checker"""
        self.client: Optional[httpx.AsyncClient] = None
        self._is_initialized = False

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, *args):
        """Async context manager exit"""
        await self.cleanup()

    async def initialize(self):
        """Initialize HTTP client for reuse"""
        if not self._is_initialized:
            self.client = httpx.AsyncClient(timeout=5.0)
            self._is_initialized = True
            logger.info("Network connectivity checker initialized")

    async def cleanup(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
            self._is_initialized = False
            logger.info("Network connectivity checker cleaned up")

    async def has_internet_access(self) -> bool:
        """
        Check if device has actual internet access (not just WiFi).

        This method tries multiple connectivity check endpoints to determine
        if the device can reach the internet. A 200/204 response indicates
        connectivity, while a 302/307 redirect indicates a captive portal
        requiring authentication.

        Returns:
            True if internet access is available, False otherwise
        """
        if not self.client:
            # Temporary client if not initialized
            async with httpx.AsyncClient(timeout=5.0) as client:
                return await self._check_with_client(client)

        return await self._check_with_client(self.client)

    async def _check_with_client(self, client: httpx.AsyncClient) -> bool:
        """
        Try multiple endpoints for reliability.

        Args:
            client: HTTP client to use for requests

        Returns:
            True if any endpoint confirms connectivity
        """
        for endpoint in self.CONNECTIVITY_ENDPOINTS:
            try:
                response = await client.get(endpoint, follow_redirects=False)

                # 204 No Content = connected (standard connectivity check response)
                # 200 OK = connected (some endpoints return content)
                if response.status_code in [200, 204]:
                    logger.debug(f"Network access confirmed via {endpoint}")
                    return True

                # 302/307 redirect = captive portal / re-auth needed
                if response.status_code in [302, 303, 307]:
                    logger.debug(f"Captive portal detected at {endpoint}")
                    return False

            except (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.RequestError
            ) as e:
                logger.debug(f"Connectivity check failed for {endpoint}: {e}")
                continue

        # All endpoints failed - no internet access
        logger.warning("No internet access detected - all endpoints failed")
        return False

    async def detect_captive_portal(self) -> bool:
        """
        Specifically detect if re-authentication (captive portal) is needed.

        Returns:
            True if captive portal detected, False otherwise
        """
        try:
            if not self.client:
                async with httpx.AsyncClient(
                    timeout=5.0,
                    follow_redirects=False
                ) as client:
                    response = await client.get(self.CONNECTIVITY_ENDPOINTS[0])
            else:
                response = await self.client.get(
                    self.CONNECTIVITY_ENDPOINTS[0],
                    follow_redirects=False
                )

            # 302/307 redirect indicates captive portal
            is_portal = response.status_code in [302, 307, 303]

            if is_portal:
                logger.info("Captive portal / re-auth required")

            return is_portal

        except Exception as e:
            logger.error(f"Captive portal detection failed: {e}")
            return False

    async def wait_for_internet_access(
        self,
        max_wait_seconds: int = 300,
        check_interval_seconds: int = 10
    ) -> bool:
        """
        Wait for internet access to become available (blocking).

        Useful for re-authentication scenarios where we want to wait
        for user to complete login before resuming timer.

        Args:
            max_wait_seconds: Maximum time to wait (default 5 minutes)
            check_interval_seconds: How often to check (default 10 seconds)

        Returns:
            True if internet access restored, False if timeout
        """
        elapsed = 0

        while elapsed < max_wait_seconds:
            has_access = await self.has_internet_access()

            if has_access:
                logger.info(f"Internet access restored after {elapsed}s")
                return True

            await asyncio.sleep(check_interval_seconds)
            elapsed += check_interval_seconds

        logger.warning(
            f"Internet access not restored after {max_wait_seconds}s timeout"
        )
        return False
