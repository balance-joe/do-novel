# main.py
import asyncio
import httpx
import yaml
from parsel import Selector
from rich.progress import Progress

# 加载配置
def load_config(config_path="./config/www.fa4d83bf.cfd.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

async def fetch_chapter_list(url: str):
    """
    抓取章节目录页，返回小说信息和章节列表
    完全使用配置驱动，兼容 headers/cookies
    """

    headers = config.get("headers", {})
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        sel = Selector(resp.text)
        print(sel)

        # 使用配置中的规则提取小说信息
        novel_cfg = config['novel']
        title = sel.xpath(novel_cfg['title']).get(default="").strip()
        
        # 作者提取（使用配置中的分隔符）
        author_raw = sel.xpath(novel_cfg['author']).get(default="")
        author_split = novel_cfg.get('author_split', '：')
        author = author_raw.split(author_split)[-1].strip() if author_raw else ""
        
        # 更新时间提取
        update_raw = sel.xpath(novel_cfg['update_time']).get(default="")
        update_split = novel_cfg.get('update_split', '：')
        update_time = update_raw.split(update_split)[-1].strip() if update_raw else ""
        
        # 简介提取
        intro = sel.xpath(novel_cfg['intro']).get(default="").strip()

        # 使用配置中的规则提取章节列表
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

        # 查看更多章节链接
        # more_chapters = sel.xpath(chapters_cfg.get('more_url', '')).get()
        # if more_chapters:
        #     more_chapters = config['base_url'] + more_chapters

        novel_info = {
            "title": title,
            "author": author,
            "intro": intro,
            "update_time": update_time,
            "all_chapters": all_chapters,
            # "more_chapters_url": more_chapters
        }

        return novel_info

async def fetch_chapter_content(url: str) -> dict:
    """
    抓取单章节（可能多页）内容。
    """
    content_cfg = config['content']
    filters = config.get('filters', {})
    chapter_content = []
    
    headers = config.get("headers", {})
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30.0) as client:
        while url:
            resp = await client.get(url)
            resp.raise_for_status()
            sel = Selector(resp.text)

            # 章节标题（只取第一页）
            if not chapter_content:
                title_sel = sel.xpath(content_cfg['container'])
                title = title_sel.xpath(content_cfg['title']).get(default="").strip()

            # 正文段落
            content_sel = sel.xpath(content_cfg['container'])
            paragraphs = content_sel.xpath(content_cfg['text']).getall()
            for p in paragraphs:
                p = p.strip()
                if p and not any(f in p for f in filters.get('regex', [])):
                    chapter_content.append(p)

            # 查找下一页链接（分页章节）
            next_page = sel.xpath(content_cfg.get('next_page', '')).get()
            if next_page:
                url = config['base_url'] + next_page
            else:
                url = None

    return {
        "title": title,
        "content": "\n".join(chapter_content)
    }

# 示例用法
async def main():
    
    chapter_url = 'https://www.fa4d83bf.cfd/book/64959/'
    novel_info = await fetch_chapter_list(chapter_url)
    print(f"小说: {novel_info['title']}, 作者: {novel_info['author']}")
    print(novel_info)
    # # 下载第一章作为测试
    # if novel_info['all_chapters']:
    #     chapter = await fetch_chapter_content(novel_info['all_chapters'][0]['url'])
    #     print(f"章节: {chapter['title']}")
    #     print(f"内容预览: {chapter['content'][:200]}...")
    # chapter = await fetch_chapter_content('https://www.630book.cc/shu/533218/180813574.html')
    # print(f"章节: {chapter['title']}")
    # print(f"内容预览: {chapter['content'][:200]}...")

if __name__ == "__main__":
    asyncio.run(main())