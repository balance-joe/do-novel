# main.py
import asyncio
import sys
from service.novel_service import NovelService

# ✅ Windows 下切换事件循环策略，解决 ProactorEventLoop 异常
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    # 测试章节列表
    #另一个站点
    # url = "https://www.bqg116.com/html/9236/5273283.html"
    
    url = "https://www.53122c.cfd/book/31383/"
    novel_service = NovelService(url)
    info = await novel_service.fetch_chapter_list()
    print(info)

    # 测试正文抓取
    # url = "https://www.53122c.cfd/book/31383/788.html"
    # novel_service = NovelService(url)
    # content = await novel_service.fetch_chapter_content()
    # print(content)

if __name__ == "__main__":
    asyncio.run(main())
    
    