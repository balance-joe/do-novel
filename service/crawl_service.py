# service/crawl_service.py
import posixpath
import re
from urllib.parse import urlparse, unquote, urlunparse
from typing import List, Dict
import asyncio
from lxml import html
from lxml.etree import Comment
from service.fetch_utils import RequestManager

class CrawlService:
    def __init__(self, proxies=None, max_concurrent=5):
        self.req_mgr = RequestManager(proxies=proxies, max_concurrent=max_concurrent)

    async def async_fetch_multiple(self, urls: List[str], retry: int = 3) -> List[Dict]:
        """
        异步批量获取多个 URL 页面内容（自动容错）
        """
        try:
            async with self.req_mgr:
                results = await self.req_mgr.request_batch(urls, retry=retry)
            return results
        except Exception as e:
            print(f"[AsyncBatch] 批量抓取异常: {e}")
            return []

    async def async_fetch_single(self, url: str, retry: int = 3) -> Dict:
        """
        异步抓取单个 URL 内容
        """
        results = await self.async_fetch_multiple([url], retry=retry)
        return results[0] if results else {"url": url, "html": None}

    def resolve_url(self, base_url: str, relative: str) -> str:
        """
        解析相对URL为绝对URL，兼容各种奇葩路径
        """
        try:
            if not base_url or not relative:
                return relative or base_url
            if relative.startswith(("http://", "https://")):
                return relative
            if relative.startswith(("#", "?")):
                base = base_url.split("#")[0].split("?")[0]
                return base + relative

            base_parts = list(urlparse(base_url))
            new_path = unquote(relative)
            if new_path.startswith("/"):
                base_parts[2] = new_path
            else:
                base_parts[2] = posixpath.normpath(
                    posixpath.join(posixpath.dirname(base_parts[2]), new_path)
                )
            return urlunparse(base_parts)
        except Exception as e:
            print(f"[resolve_url] 解析失败: {base_url} + {relative} ({e})")
            return relative

    def extract_clean_body(self, html_content: str) -> str:
        """
        提取HTML中的body内容，并清除干扰元素
        """
        if not html_content:
            return ""
        try:
            parser = html.HTMLParser(recover=True, encoding="utf-8")
            tree = html.fromstring(html_content, parser=parser)
            body = tree.xpath("//body")
            if not body:
                return ""
            body = body[0]
        except Exception:
            return ""

        # 清除噪音元素
        for tag in ["script", "style", "link", "meta", "noscript","input"]:
            for e in body.xpath(f".//{tag}"):
                if e.getparent() is not None:
                    e.getparent().remove(e)
        for comment in body.xpath("//comment()"):
            if comment.getparent() is not None:
                comment.getparent().remove(comment)

        for selector in [
            '//*[contains(@class, "footer")]',
            '//*[contains(@class, "header")]',
            '//*[contains(@class, "nav")]',
            '//*[contains(@id, "footer")]',
            '//*[contains(@id, "header")]',
            '//*[contains(@id, "nav")]',
        ]:
            for e in body.xpath(selector):
                if e.getparent() is not None:
                    e.getparent().remove(e)

        # 提取 innerHTML
        content = "".join(
            html.tostring(child, encoding="unicode", method="html")
            for child in body.getchildren()
        )

        # 精简空白字符
        content = re.sub(r">\s*\n\s*<", "><", content)
        content = re.sub(r">\s{2,}<", "><", content)
        return content.strip()
    
    
    async def __aenter__(self):
        await self.req_mgr._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.req_mgr.close()
