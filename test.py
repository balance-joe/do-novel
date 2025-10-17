# from service.crawl_service import CrawlService


# if __name__ == "__main__":
    
    
#     #读取 ./doc/chapter.html
#     html = open("./doc/chapter.html", "r", encoding="utf-8").read()
#     # print(html)
    
#     # crawl_service = CrawlService()
#     # clear_html = crawl_service.extract_clean_body(html)  # 示例小说详情页 URL
#     # print(clear_html)
#     # print(len(clear_html))
    
from parsel import Selector
from urllib.parse import urljoin

def extract_chapters(html, base_url, chapters_cfg):
    sel = Selector(text=html)
    all_chapters = []

    containers = sel.xpath(chapters_cfg["container"])
    print(f"找到 {len(containers)} 个章节容器")

    for container in containers:
        items = container.xpath(chapters_cfg["item"])
        print(f"容器内找到 {len(items)} 个章节链接")

        for a in items:
            title_parts = a.xpath(chapters_cfg["title"]).getall()
            chap_title = "".join(title_parts).strip()
            href = a.xpath(chapters_cfg["url"]).get(default="").strip()
            if not href:
                continue

            all_chapters.append({
                "title": chap_title,
                "url": urljoin(base_url, href)
            })

    return all_chapters


if __name__ == "__main__":
    html = open("./doc/chapter.html", "r", encoding="utf-8").read()
    chapters_cfg = {
        'container': "//div[contains(@class, 'section-box')]//ul[contains(@class, 'section-list')]",
        'item': './/li/a',
        'title': 'text() | @title',
        'url': '@href',
        'pagination': True
    }

    result = extract_chapters(html, "https://baidu.com/book/1/", chapters_cfg)
    print(f"共提取章节数: {len(result)}")
    for ch in result:
        print(ch)
