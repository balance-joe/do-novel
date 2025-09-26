# main.py
import asyncio
import httpx
import aiofiles
from parsel import Selector
from rich.progress import Progress


CHAPTER_LIST_URL = "https://www.630book.cc/kan/1918762.html"
BASE_URL = "https://www.630book.cc"


async def fetch_chapter_list():
    """抓取章节目录页，返回小说信息和章节列表"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(CHAPTER_LIST_URL)
        resp.raise_for_status()
        sel = Selector(resp.text)

        # 小说信息
        title = sel.xpath("//div[@class='info']/div[@class='top']/h1/text()").get(default="").strip()
        author = sel.xpath("//div[@class='info']/div[@class='top']//p[contains(text(),'作')]/text()").get(default="").split('：')[-1].strip()
        update_time = sel.xpath("//div[@class='info']/div[@class='top']/p[contains(text(),'最后更新')]/text()").get(default="").split('：')[-1].strip()
        intro = sel.xpath("//div[@class='info']/div[@class='desc']/text()").get(default="").strip()

        # 全部章节列表
        all_chapters = []
        chapter_nodes = sel.xpath("//h2[contains(@class,'layout-tit')][2]/following-sibling::ul[1]/li/a")
        for a in chapter_nodes:
            chap_title = a.xpath("text()").get(default="").strip()
            href = a.xpath("@href").get(default="").strip()
            if href:
                all_chapters.append({
                    "title": chap_title,
                    "url": BASE_URL + href
                })

        # 查看更多章节链接
        more_chapters = sel.xpath("//a[contains(@class,'btn-mulu')]/@href").get()
        if more_chapters:
            more_chapters = BASE_URL + more_chapters

        novel_info = {
            "title": title,
            "author": author,
            "intro": intro,
            "update_time": update_time,
            "all_chapters": all_chapters,
            "more_chapters_url": more_chapters
        }

        print(novel_info)
        return novel_info


async def fetch_chapter_content(url: str) -> dict:
    """
    抓取单章节（可能多页）内容。
    返回 dict: {
        "title": str,
        "content": str
    }
    """
    chapter_content = []
    async with httpx.AsyncClient() as client:
        while url:
            resp = await client.get(url)
            resp.raise_for_status()
            sel = Selector(resp.text)

            # 章节标题（只取第一页）
            if not chapter_content:
                title = sel.xpath("//div[@class='word_read']/h3/text()").get()
                title = title.strip() if title else ""

            # 正文段落
            paragraphs = sel.xpath("//div[@class='word_read']/p/text()").getall()
            for p in paragraphs:
                p = p.strip()
                if p and "请勿开启浏览器" not in p:
                    chapter_content.append(p)

            # 查找下一页链接（分页章节）
            next_page = sel.xpath("//div[@class='read_btn']/a[contains(@href,'_1.html')]/@href").get()
            if next_page:
                url = BASE_URL + next_page
            else:
                url = None  # 没有下一页就退出

    return {
        "title": title,
        "content": "\n".join(chapter_content)
    }

# 示例用法
async def main():

#     chapters = await fetch_chapter_list()
#     novel_info = await fetch_chapter_list()
#     chapters = novel_info['all_chapters']
#     print(f"共发现 {len(chapters)} 章，开始下载...")
    url = "https://www.630book.cc/kan/1918762_5857837_0.html"
    chapter = await fetch_chapter_content(url)
    print("标题:", chapter["title"])
    print("内容:", chapter["content"][:500], "...")  # 只打印前500字符

if __name__ == "__main__":
    asyncio.run(main())
