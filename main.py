# main.py
import asyncio
from service.novel_service import NovelService

async def main():
    # 测试章节列表
    url = "https://www.53122c.cfd/book/31383/"
    novel_service = NovelService(url)
    info = await novel_service.fetch_chapter_list(url)
    # print(info)

    # # 测试正文抓取
    # url = "https://www.53122c.cfd/book/31383/1.html"
    # novel_service = NovelService(url)
    # content = await novel_service.fetch_chapter_content(url)
    # print(content)

    chapters = info['all_chapters']  # 仅测试前5章
    # print(f"准备下载小说《{info['title']}》的 {len(chapters)} 章")
    await novel_service.download_novel("官道之色戒", "低手寂寞", chapters)

if __name__ == "__main__":
    asyncio.run(main())
