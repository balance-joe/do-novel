# service/novel_service.py
import asyncio
from urllib.parse import urljoin
from parsel import Selector
from service.config_service import ConfigService
from service.crawl_service import CrawlService


class NovelService:
    def __init__(self, url: str):
        self.url = url
        self.config = ConfigService().load_config(url)
        
        self.base_url = self.config.get("base_url", "")

    async def fetch_chapter_list(self):
        """抓取章节列表页"""
        async with CrawlService() as crawl:
            result = await crawl.async_fetch_single(self.url)
            html = result.get("html", "") if result else ""
            if not html:
                return {}

            sel = Selector(html)
            novel_cfg = self.config["novel"]

            title = sel.xpath(novel_cfg["title"]).get(default="").strip()
            author_raw = sel.xpath(novel_cfg["author"]).get(default="")
            author_split = novel_cfg.get("author_split", "：")
            author = author_raw.split(author_split)[-1].strip() if author_raw else ""

            intro = sel.xpath(novel_cfg["intro"]).get(default="").strip()
            update_raw = sel.xpath(novel_cfg["update_time"]).get(default="")
            update_split = novel_cfg.get("update_split", "：")
            update_time = update_raw.split(update_split)[-1].strip()

            # 获取章节列表
            chapters_cfg = self.config["chapters"]
            all_chapters = []
            containers = sel.xpath(chapters_cfg["container"])
            if not containers:
                # fallback 自动容错
                containers = sel.xpath("//div[contains(@class, 'chapter') or contains(@id, 'chapter') or contains(@class, 'section')]")
            
            for container in containers:
                items = container.xpath(chapters_cfg["item"])
                for a in items:
                    title_parts = a.xpath(chapters_cfg["title"]).getall()
                    chap_title = "".join(title_parts).strip()
                    if not chap_title:
                        continue

                    href = a.xpath(chapters_cfg["url"]).get(default="").strip()
                    if not href:
                        continue

                    # ✅ 使用 urljoin，防止路径拼接错误
                    full_url = urljoin(self.base_url, href)

                    all_chapters.append({
                        "title": chap_title,
                        "url": full_url
                    })
        

            # 去重（防止分页重复）
            unique_chapters = []
            seen_urls = set()
            for ch in all_chapters:
                if ch["url"] not in seen_urls:
                    unique_chapters.append(ch)
                    seen_urls.add(ch["url"])
            all_chapters = unique_chapters
            
            #获取章节结束
            
            return {
                "title": title,
                "author": author,
                "intro": intro,
                "update_time": update_time,
                "all_chapters": all_chapters,
            }

    async def fetch_chapter_content(self):
        """抓取单章正文页（含分页）"""
        async with CrawlService() as crawl:
            url = self.url
            content_cfg = self.config["content"]
            filters = self.config.get("filters", {})
            chapter_content = []
            title = ""
            base_chapter_id = url.split("/")[-1].split(".")[0]  # 当前章节编码

            while url:
                result = await crawl.async_fetch_single(url)
                html = result.get("html", "") if result else ""
                if not html:
                    break

                sel = Selector(html)

                # 提取标题，只做一次
                if not title:
                    title_sel = sel.xpath(content_cfg["container"])
                    title = title_sel.xpath(content_cfg["title"]).get(default="").strip()

                # 提取正文
                content_sel = sel.xpath(content_cfg["container"])
                paragraphs = content_sel.xpath(content_cfg["text"]).getall()
                for p in paragraphs:
                    p = p.strip()
                    if p and not any(f in p for f in filters.get("regex", [])):
                        chapter_content.append(p)

                # 获取下一页
                next_page = sel.xpath(content_cfg.get("next_page", "")).get()
                if next_page and base_chapter_id in next_page:
                    url = urljoin(self.base_url, next_page)
                else:
                    url = None  # 本章分页结束

                print(f"当前章节抓取: {url}，下一页: {next_page}")

            return {
                "title": title,
                "content": "\n".join(chapter_content)
            }
