# main.py
import asyncio
import yaml
from parsel import Selector
from service.crawl_url_service import CrawlUrlService  # ✅ 引入你的封装

# 读取配置
def load_config(config_path="./config/www.1bda200708.cfd.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

# -------------------------------
# 抓取章节目录页
# -------------------------------
async def fetch_chapter_list(url: str):
    async with CrawlUrlService() as crawl:  # ✅ 统一session
        result = await crawl.async_fetch_single(url)
        html = result["html"] if result and "html" in result else ""

        if not html:
            print(f"获取失败: {url}")
            return {}

        sel = Selector(html)

        novel_cfg = config['novel']
        title = sel.xpath(novel_cfg['title']).get(default="").strip()

        author_raw = sel.xpath(novel_cfg['author']).get(default="")
        author_split = novel_cfg.get('author_split', '：')
        author = author_raw.split(author_split)[-1].strip() if author_raw else ""

        update_raw = sel.xpath(novel_cfg['update_time']).get(default="")
        update_split = novel_cfg.get('update_split', '：')
        update_time = update_raw.split(update_split)[-1].strip() if update_raw else ""

        intro = sel.xpath(novel_cfg['intro']).get(default="").strip()

        chapters_cfg = config['chapters']
        all_chapters = []
        container = sel.xpath(chapters_cfg['container'])
        for a in container.xpath(chapters_cfg['item']):
            chap_title = a.xpath(chapters_cfg['title']).get(default="").strip()
            href = a.xpath(chapters_cfg['url']).get(default="").strip()
            if href:
                all_chapters.append({
                    "title": chap_title,
                    "url": config['base_url'] + href
                })

        novel_info = {
            "title": title,
            "author": author,
            "intro": intro,
            "update_time": update_time,
            "all_chapters": all_chapters,
        }

        return novel_info

# -------------------------------
# 抓取章节内容页（支持分页）
# -------------------------------
async def fetch_chapter_content(url: str):
    content_cfg = config['content']
    filters = config.get('filters', {})

    async with CrawlUrlService() as crawl:  # ✅ 同样复用
        chapter_content = []
        title = ""

        while url:
            result = await crawl.async_fetch_single(url)
            
            html = result["html"] if result and "html" in result else ""
            
            if not html:
                break
            
            sel = Selector(html)

            if not title:
                title_sel = sel.xpath(content_cfg['container'])
                title = title_sel.xpath(content_cfg['title']).get(default="").strip()

            content_sel = sel.xpath(content_cfg['container'])
            paragraphs = content_sel.xpath(content_cfg['text']).getall()
            for p in paragraphs:
                p = p.strip()
                if p and not any(f in p for f in filters.get('regex', [])):
                    chapter_content.append(p)

            next_page = sel.xpath(content_cfg.get('next_page', '')).get()
            url = config['base_url'] + next_page if next_page else None

        return {
            "title": title,
            "content": "\n".join(chapter_content)
        }

# -------------------------------
# 主程序入口
# -------------------------------
async def main():
    # chapter_url = 'https://www.1bda200708.cfd/book/31383/'
    # novel_info = await fetch_chapter_list(chapter_url)
    # print(f"小说: {novel_info['title']}, 作者: {novel_info['author']}")
    # print(f"共 {len(novel_info['all_chapters'])} 章")
    # print(novel_info)

    chapter_url = 'https://www.1bda200708.cfd/book/31383/788.html'
    content = await fetch_chapter_content(chapter_url)
    print(content)
    
    # # 可选：抓取第一章内容测试
    # if novel_info['all_chapters']:
    #     first = novel_info['all_chapters'][0]
    #     chapter = await fetch_chapter_content(first['url'])
    #     print(f"章节: {chapter['title']}")
    #     print(f"内容预览:\n{chapter['content'][:200]}...")

if __name__ == "__main__":
    asyncio.run(main())
