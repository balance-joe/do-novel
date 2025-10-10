import asyncio

from service.crawl_url_service import CrawlUrlService


if __name__ == "__main__":
    crawl = CrawlUrlService()
    res = asyncio.run(crawl.async_fetch_single('https://www.1bda200708.cfd/book/61808/'))
    print(res)
