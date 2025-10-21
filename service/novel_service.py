# service/novel_service.py
import asyncio
from parsel import Selector
from service.config_service import ConfigService
from service.crawl_service import CrawlService
import os
import aiofiles

class NovelService:
    def __init__(self, url: str):
        if(url) :
            self.url = url
            self.config = ConfigService().load_config(url)
            self.base_url = self.config.get("base_url", "")
        
    async def fetch_chapter_list(self, url: str):
        """抓取章节列表页"""
        async with CrawlService() as crawl:
            result = await crawl.async_fetch_single(url)
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

    async def fetch_chapter_content(self, url: str):
        """抓取单章正文页（含分页）"""
        async with CrawlService() as crawl:
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
            

    async def download_novel(self, novel_name: str, author: str, chapters: list[dict]):
        """
        异步下载整本小说（多章节合并）
        直接调用 fetch_chapter_content()
        """
        os.makedirs("./output", exist_ok=True)
        file_path = f"./output/{novel_name}_{author}.txt"

        print(f"📘 开始下载小说《{novel_name}》（共 {len(chapters)} 章）...")

        merged_text = [f"《{novel_name}》 —— 作者：{author}\n\n"]

        # 串行抓取（不并发，更安全）
        for idx, chap in enumerate(chapters, start=1):
            print(f"⏬ 下载章节：{chap['title']} - {chap['url']}")
            try:
                data = await self.fetch_chapter_content(chap["url"])
                title = data.get("title") or chap["title"]
                content = data.get("content", "").replace("\\n", "\n").replace("\r", "").strip()
                merged_text.append(f"\n\n第{idx}章 {title}\n\n{content}\n")
                print(f"✅ 成功下载章节：{title}")
            except Exception as e:
                print(f"❌ 抓取章节失败: {chap['title']} - {e}")
                merged_text.append(f"\n\n第{idx}章 {chap['title']}\n\n【抓取失败】\n")

        # === 写入文件 ===
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write("".join(merged_text))

        print(f"✅ 小说《{novel_name}》下载完成：{file_path}")
        return file_path