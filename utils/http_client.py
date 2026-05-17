import asyncio
import random
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from config.settings import Settings

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, rate: float = 1.0):
        self.rate = rate
        self.last_request_time = {}

    async def wait(self, domain: str):
        """Wait if necessary to maintain rate limit."""
        if domain not in self.last_request_time:
            self.last_request_time[domain] = datetime.now()
            return

        elapsed = (datetime.now() - self.last_request_time[domain]).total_seconds()
        min_interval = 1.0 / self.rate

        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

        self.last_request_time[domain] = datetime.now()


class HTTPClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.rate_limiter = RateLimiter(settings.rate_limit_per_domain)
        self.timeout = httpx.Timeout(settings.request_timeout)
        self.proxies = None

    def _get_user_agent(self) -> str:
        """Get random user agent."""
        return random.choice(self.settings.user_agent_list)

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers."""
        return {
            "User-Agent": self._get_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[httpx.Response]:
        """GET request with retries and rate limiting."""
        headers = {**self._get_headers(), **(headers or {})}

        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        for attempt in range(self.settings.max_retries):
            try:
                await self.rate_limiter.wait(domain)

                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    proxies=self.proxies,
                ) as client:
                    response = await client.get(
                        url,
                        headers=headers,
                        params=params,
                        **kwargs
                    )

                    if response.status_code == 429:
                        wait_time = 2 ** (attempt + 1)
                        logger.warning(f"Rate limited on {domain}, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status_code in [403, 404]:
                        logger.warning(f"HTTP {response.status_code} for {url}")
                        return None

                    response.raise_for_status()
                    return response

            except httpx.TimeoutException:
                logger.warning(f"Timeout on {url} (attempt {attempt + 1})")
                if attempt < self.settings.max_retries - 1:
                    await asyncio.sleep(2 ** (attempt + 1))

            except httpx.HTTPError as e:
                logger.error(f"HTTP error on {url}: {str(e)}")
                if attempt < self.settings.max_retries - 1:
                    await asyncio.sleep(2 ** (attempt + 1))

        logger.error(f"Failed to fetch {url} after {self.settings.max_retries} retries")
        return None

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Optional[httpx.Response]:
        """POST request with retries."""
        headers = {**self._get_headers(), **(headers or {})}

        for attempt in range(self.settings.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        data=data,
                        json=json,
                        headers=headers,
                        **kwargs
                    )
                    response.raise_for_status()
                    return response

            except Exception as e:
                logger.error(f"POST request error: {str(e)}")
                if attempt < self.settings.max_retries - 1:
                    await asyncio.sleep(2 ** (attempt + 1))

        return None

    def set_proxy(self, proxy_url: str):
        """Set proxy for requests."""
        self.proxies = proxy_url
