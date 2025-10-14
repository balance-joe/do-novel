# main.py
import asyncio
from service.novel_service import NovelService

async def main():
    # 测试章节列表
    # url = "https://www.53122c.cfd/book/31383/"
    # novel_service = NovelService(url)
    # info = await novel_service.fetch_chapter_list()
    # print(info)

    # 测试正文抓取
    url = "https://www.53122c.cfd/book/31383/788.html"
    novel_service = NovelService(url)
    content = await novel_service.fetch_chapter_content()
    print(content)

if __name__ == "__main__":
    asyncio.run(main())
