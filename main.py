# main.py
import asyncio
import sys
from service.novel_service import NovelService

# ✅ Windows 下切换事件循环策略，解决 ProactorEventLoop 异常
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    # 测试章节列表
    url = "https://www.53122c.cfd/book/55146/"
    novel_service = NovelService(url)
    info = await novel_service.fetch_chapter_list(url)
    # print(info)

    # 测试正文抓取
    url = "https://www.53122c.cfd/book/55146/2.html"
    novel_service = NovelService(url)
    content = await novel_service.fetch_chapter_content(url)
    print(content)

    chapters = info['all_chapters']  # 仅测试前5章
    # print(f"准备下载小说《{info['title']}》的 {len(chapters)} 章")
    await novel_service.download_novel("蛊真人", "", chapters)

if __name__ == "__main__":
    asyncio.run(main())
    
    