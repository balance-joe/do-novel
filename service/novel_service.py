# service/novel_service.py
import asyncio
from collections import defaultdict
import re
from urllib.parse import urljoin
from parsel import Selector
from service.config_service import ConfigService
from service.crawl_service import CrawlService
import os
import aiofiles
from lxml import html
from lxml.etree import XPathError, ParserError


class NovelService:
    def __init__(self, url: str):
        if url:
            self.url = url
            self.config = ConfigService().load_config(url)
            self.base_url = self.config.get("base_url", "")
        
    # 抓取章节列表页
    async def fetch_chapter_list(self, url: str):
        async with CrawlService() as crawl:
            result = await crawl.async_fetch_single(url)
            html = result.get("html", "") if result else ""

            if not html:
                return {}

            sel = Selector(html)

            # 获取章节列表
            chapters_cfg = self.config["chapters"]
            all_chapters = []
            containers = sel.xpath(chapters_cfg["container"])
            
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
            
            return all_chapters


    # 抓取小说信息页
    async def fetch_novel_info(self, url: str):
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

            return {
                "title": title,
                "author": author,
                "intro": intro,
                "update_time": update_time,
            }


    # 抓取单章正文页（含分页）
    async def fetch_chapter_content(self, url: str):
        async with CrawlService() as crawl:
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






















            
    # 异步下载整本小说（多章节合并）
    # 直接调用 fetch_chapter_content()
    async def download_novel(self, novel_name: str, author: str, chapters: list[dict]):
        
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
                merged_text.append(f"\n{title}\n\n{content}\n")
                print(f"✅ 成功下载章节：{title}")
            except Exception as e:
                print(f"❌ 抓取章节失败: {chap['title']} - {e}")
                merged_text.append(f"\n\n第{idx}章 {chap['title']}\n\n【抓取失败】\n")

        # === 写入文件 ===
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write("".join(merged_text))

        print(f"✅ 小说《{novel_name}》下载完成：{file_path}")
        return file_path



    def compress_html(self, html_content):
        """
        使用正则表达式压缩HTML，移除重复的链接
        """
        # 匹配所有容器
        container_pattern = r'(<div[^>]*>.*?</div>|<ul[^>]*>.*?</ul>|<ol[^>]*>.*?</ol>|<nav[^>]*>.*?</nav>|<section[^>]*>.*?</section>|<article[^>]*>.*?</article>)'
        
        def remove_duplicate_links(match):
            container_html = match.group(0)
            
            # 匹配容器内的所有链接
            link_pattern = r'(<a\s+[^>]*href=([\'"])(.*?)\2[^>]*>.*?</a>)'
            links = re.findall(link_pattern, container_html, re.DOTALL)
            
            # 记录每个href出现的次数和第一个出现的位置
            href_count = defaultdict(int)
            href_first_occurrence = {}
            
            for i, (full_match, quote, href) in enumerate(links):
                href_count[href] += 1
                if href not in href_first_occurrence:
                    href_first_occurrence[href] = (full_match, i)
            
            # 构建新的容器内容
            new_container = container_html
            
            # 从后往前处理，避免索引变化问题
            for href, count in sorted(href_count.items(), key=lambda x: -x[1]):
                if count > 1:
                    # 找到所有重复链接的位置
                    all_occurrences = [m.start() for m in re.finditer(re.escape(href_first_occurrence[href][0]), new_container)]
                    
                    # 保留第一个，移除其他
                    for i, pos in enumerate(all_occurrences):
                        if i > 0:  # 跳过第一个
                            # 找到链接的完整匹配
                            link_match = re.search(r'<a\s+[^>]*>.*?</a>', new_container[pos:], re.DOTALL)
                            if link_match:
                                link_text_match = re.search(r'>([^<]*)</a>', link_match.group(0))
                                if link_text_match:
                                    # 保留链接文本，但移除链接
                                    link_text = link_text_match.group(1)
                                    new_container = new_container[:pos] + link_text + new_container[pos+len(link_match.group(0)):]
            
            return new_container
        
        # 对每个容器应用去重
        compressed_html = re.sub(container_pattern, remove_duplicate_links, html_content, flags=re.DOTALL)
        
        return compressed_html
