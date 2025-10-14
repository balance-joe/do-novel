# fetch_utils.py
import random
import asyncio
from typing import Optional, List, Dict
import aiohttp
import async_timeout

class RequestManager:
    """
    异步请求管理器（改进版）
    - session 生命周期完全统一
    - 支持并发控制、代理轮换、UA 伪装
    - 支持单任务异常容错
    """
    DEFAULT_TIMEOUT = 10
    DEFAULT_RETRY = 3

    def __init__(self, proxies: Optional[List[str]] = None, max_concurrent: int = 5):
        self.proxies = proxies or []
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def _ensure_session(self):
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()

    def build_headers(self, url: str) -> Dict[str, str]:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Edge/121.0.1000.0",
        ]
        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Referer": url,
        }

    async def _fetch_one(self, url: str, retry: int) -> Optional[str]:
        await self._ensure_session()
        headers = self.build_headers(url)
        proxy = random.choice(self.proxies) if self.proxies else None

        for attempt in range(1, retry + 1):
            try:
                async with self._semaphore:
                    async with async_timeout.timeout(self.DEFAULT_TIMEOUT):
                        async with self._session.get(url, headers=headers, proxy=proxy) as resp:
                            resp.raise_for_status()
                            content = await resp.read()
                            return self.handle_encoding_bytes(content)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"[Async] 请求失败 {attempt}/{retry}: {url} - {e}")
                await asyncio.sleep(random.uniform(0.5, 1.2))
            except Exception as e:
                print(f"[Async] 未知异常 {url}: {e}")
                break
        return None

    async def request_async(self, url: str, retry: Optional[int] = None) -> Optional[str]:
        retry = retry or self.DEFAULT_RETRY
        return await self._fetch_one(url, retry)

    async def request_batch(self, urls: List[str], retry: Optional[int] = None) -> List[Dict]:
        retry = retry or self.DEFAULT_RETRY
        await self._ensure_session()

        async def safe_fetch(url):
            html = await self._fetch_one(url, retry)
            return {"url": url, "html": html}

        results = await asyncio.gather(*(safe_fetch(u) for u in urls), return_exceptions=False)
        return results

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def handle_encoding_bytes(self, content: bytes) -> str:
        for enc in ("utf-8", "gbk", "gb2312"):
            try:
                return content.decode(enc)
            except UnicodeDecodeError:
                continue
        return content.decode("utf-8", errors="ignore")

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()