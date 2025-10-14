# service/novel_service.py
import asyncio
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

            chapters_cfg = self.config["chapters"]
            all_chapters = []
            container = sel.xpath(chapters_cfg["container"])
            for a in container.xpath(chapters_cfg["item"]):
                chap_title = a.xpath(chapters_cfg["title"]).get(default="").strip()
                href = a.xpath(chapters_cfg["url"]).get(default="").strip()
                if href:
                    all_chapters.append({
                        "title": chap_title,
                        "url": self.base_url + href
                    })

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

            while url:
                result = await crawl.async_fetch_single(url)
                html = result.get("html", "") if result else ""
                if not html:
                    break

                sel = Selector(html)
                if not title:
                    title_sel = sel.xpath(content_cfg["container"])
                    title = title_sel.xpath(content_cfg["title"]).get(default="").strip()

                content_sel = sel.xpath(content_cfg["container"])
                paragraphs = content_sel.xpath(content_cfg["text"]).getall()
                for p in paragraphs:
                    p = p.strip()
                    if p and not any(f in p for f in filters.get("regex", [])):
                        chapter_content.append(p)

                next_page = sel.xpath(content_cfg.get("next_page", "")).get()
                url = self.base_url + next_page if next_page else None

            return {
                "title": title,
                "content": "\n".join(chapter_content)
            }
