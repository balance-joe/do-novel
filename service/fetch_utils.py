# fetch_utils_async.py
import random
import asyncio
from typing import Optional, List, Dict
import aiohttp
import async_timeout

class RequestManager:
    """
    异步请求管理器
    - 支持 session 复用
    - 批量并发请求
    - 自动轮换 UA、可选代理
    - 重试 + 随机延时
    """
    DEFAULT_TIMEOUT = 10
    DEFAULT_RETRY = 3
    MAX_CONCURRENT = 5  # 最大并发数

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/118.0.5993.117 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Edge/120.0.1000.0",
    ]

    def __init__(self, proxies: Optional[List[str]] = None):
        self.proxies = proxies or []
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

    def build_headers(self, url: str) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": url,
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
        }

    def get_proxy_str(self) -> Optional[str]:
        return random.choice(self.proxies) if self.proxies else None

    async def _fetch_one(self, url: str, retry: int) -> Optional[str]:
        headers = self.build_headers(url)
        proxy = self.get_proxy_str()

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
            await asyncio.sleep(random.uniform(0.5, 1.5))
        return None

    async def request_async(self, url: str, retry: int = None) -> Optional[str]:
        retry = self.DEFAULT_RETRY if retry is None else retry
        # 确保 session 已创建
        if not self._session:
            self._session = aiohttp.ClientSession()
        return await self._fetch_one(url, retry)

    async def request_batch(self, urls: List[str], retry: int = None) -> List[Dict]:
        """
        批量异步抓取
        """
        retry = self.DEFAULT_RETRY if retry is None else retry
        if not self._session:
            self._session = aiohttp.ClientSession()

        tasks = [self._fetch_one(url, retry) for url in urls]
        results = await asyncio.gather(*tasks)
        return [{"url": url, "html": html} for url, html in zip(urls, results)]

    async def close(self):
        """关闭 session"""
        if self._session:
            await self._session.close()
            self._session = None

    def handle_encoding_bytes(self, content: bytes) -> str:
        """统一处理 bytes 编码"""
        for enc in ("utf-8", "gbk", "gb2312"):
            try:
                return content.decode(enc)
            except UnicodeDecodeError:
                continue
        return content.decode("utf-8", errors="ignore")
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def __del__(self):
        if self._session and not self._session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._session.close())
            except Exception:
                pass