import random
import re
import logging
from urllib.parse import urlparse, urljoin, unquote,quote, urlunparse
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
import asyncio
import aiohttp
import posixpath
import hashlib, os
from lxml import html
from lxml.etree import Comment
import tldextract
from service.fetch_utils import RequestManager

logger = logging.getLogger('CrawlUrlService')

class CrawlUrlService:
    CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fa5\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf]+')

    def __init__(self, proxies=None):

        self.session = None

        # 直接指定快代理
        self.proxies = [
            # "http://q808.kdltps.com:15818",   # 只需替换成你们的隧道域名和端口
        ]
        
        self.req_mgr = RequestManager(proxies=self.proxies)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self  # 返回自身供 async with 使用

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()
        
    def get_url_data(self, url: str, main_domain: str = "henu.edu.cn") -> List[Dict]:
        """
        获取指定URL页面中的所有有效链接
        
        参数:
            url: 要抓取的URL
            main_domain: 主域名，用于链接过滤
        
        返回:
            包含有效链接(title和link)的字典列表
        """
        try:
            # 解析URL获取基础信息
            url_info = urlparse(url)
            fetch_domain = f"{url_info.scheme}://{url_info.netloc}"
            
            # 获取页面所有链接
            links = self.fetch_page_links(url)
            logger.info(f"抓取成功: {url}")
        except Exception as e:
            logger.error(f"抓取失败: {url} - {str(e)}")
            return []
        
        # 处理并过滤链接
        valid_links = []
        for item in links:
            # 处理链接项（中文编码、相对路径转换等）
            processed = self.process_link_item(item, url)
            if not processed:
                continue
                
            # 验证链接有效性
            if self.is_valid_link(processed) and self.is_valid_http_link(processed["link"], main_domain):
                valid_links.append(processed)
        
        # 去重后返回
        return self.deduplicate_by_link(valid_links)

    def fetch_page_links(self, url: str) -> List[Dict]:
        """
        获取指定URL页面中的所有链接
        """
        try:
            html = self.req_mgr.request_sync(url)  # <-- 使用 fetch_utils.py 管理请求
            if not html:
                logger.error(f"获取页面失败: {url}")
                return []

            # 解析HTML获取链接
            return self.parse_html_links(html, url)
        except Exception as e:
            logger.error(f"获取页面链接失败: {url} - {str(e)}")
            return []
        finally:
            # 安全关闭会话
            try:
                if self.req_mgr and self.req_mgr.session and not self.req_mgr.session.closed:
                    import asyncio
                    asyncio.run(self.req_mgr.session.close())
            except Exception as close_err:
                logger.warning(f"关闭 aiohttp session 时出错: {close_err}")

    
    async def async_fetch_multiple(self, urls: List[str], retry: int = 3) -> List[Dict]:
        """
        异步批量获取多个 URL 页面内容
        - 自动关闭 session
        - 内部支持 RequestManager 的复用、限速与重试
        """
        if not self.req_mgr:
            raise RuntimeError("RequestManager 未初始化")

        results = []
        try:
            async def fetch_one(url):
                html = await self.req_mgr.request_async(url, retry=retry)
                return {"url": url, "html": html}

            tasks = [fetch_one(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=False)
            return results

        except Exception as e:
            print(f"[AsyncBatch] 批量抓取异常: {e}")
            return []

        finally:
            # 🔒 保证 session 在任务结束后关闭
            try:
                await self.req_mgr.close()
            except Exception as close_err:
                print(f"[AsyncBatch] 关闭 aiohttp session 出错: {close_err}")

    async def async_fetch_single(self, url: str, retry: int = 3) -> Dict:
        """
        异步抓取单个URL内容，支持重试
        """
        result_list = await self.async_fetch_multiple([url], retry=retry)
        return result_list[0] if result_list else {'url': url, 'html': None}

    async def async_fetch_in_batches(self, urls: List[str], batch_size: int = 10, retry: int = 3, auto_close: bool = True):
        """
        分批异步抓取（防封 + 限流友好版）
        - 支持自动关闭 session
        - 每批之间随机延时，防止被封
        - 批次异常不影响整体执行
        """
        if not self.req_mgr:
            raise RuntimeError("RequestManager 未初始化")

        all_results = []

        try:
            for i in range(0, len(urls), batch_size):
                batch = urls[i:i + batch_size]

                async def fetch_one(url):
                    try:
                        html = await self.req_mgr.request_async(url, retry=retry)
                        return {"url": url, "html": html}
                    except Exception as e:
                        print(f"[AsyncBatch] 抓取失败: {url} - {e}")
                        return {"url": url, "html": None}

                # ⚙️ 批次并发执行
                batch_results = await asyncio.gather(*[fetch_one(u) for u in batch], return_exceptions=False)
                all_results.extend(batch_results)

                # 🕒 批次间延时（2~5秒）
                delay = random.uniform(2, 5)
                print(f"[AsyncBatch] 批次 {i // batch_size + 1} 完成，休眠 {delay:.2f}s...")
                await asyncio.sleep(delay)

            return all_results

        finally:
            # ✅ 任务完成后安全关闭 session
            if auto_close:
                try:
                    await self.req_mgr.close()
                except Exception as e:
                    print(f"[AsyncBatch] 关闭 session 出错: {e}")

    async def fetch_and_parse_multiple(self, urls: List[str], main_domain: str) -> List[Dict]:
        """
        批量异步抓取并解析多个URL的链接
        
        参数:
            urls: URL列表
            main_domain: 主域名用于链接过滤
            
        返回:
            包含所有有效链接的字典列表
        """
        # 1. 异步获取所有URL的HTML内容
        results = await self.async_fetch_multiple(urls)
        
        # 2. 解析每个页面的链接
        all_links = []
        for result in results:
            if not result['html']:
                continue
                
            # 解析HTML中的链接
            links = self.parse_html_links(result['html'], result['url'])
            
            # 处理每个链接项
            for link_data in links:
                processed = self.process_link_item(link_data, result['url'])
                if not processed:
                    continue
                    
                # 验证链接有效性
                if self.is_valid_http_link(processed['link'], main_domain):
                    all_links.append(processed)
        
        # 3. 去重后返回
        return self.deduplicate_by_link(all_links)


    def parse_html_links(self, html: str, base_url: str) -> List[Dict]:
        """
        解析HTML内容中的链接
        
        参数:
            html: HTML内容
            base_url: 基础URL，用于相对路径转换
        
        返回:
            包含链接(title和link)的字典列表
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, "lxml")
        links = []
        
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href", "").strip()
            
            # 先取 title 属性，没有就取文本
            title = a_tag.get("title", "").strip()
            if not title:
                title = a_tag.get_text().strip()
            
            if not title or not href:
                continue
                
            links.append({
                "link": href,
                "title": title
            })
            
        return links

    def process_link_item(self, item: Dict, base_url: str) -> Optional[Dict]:
        """
        处理链接项
        
        参数:
            item: 链接项字典
            base_url: 基础URL
            
        返回:
            处理后的链接字典或None
        """
        if not item.get('link'):
            return None
            
        # 中文URL编码处理
        link = self.CHINESE_PATTERN.sub(
            lambda m: ''.join(f'%{ord(c):02X}' for c in m.group()),
            item['link']
        )
        
        # 相对路径转绝对路径
        if not link.startswith(('http://', 'https://')):
            link = self.resolve_url(base_url, link)
        
        return {
            'link': link,
            'title': item.get('title', '').strip()
        }

    def encode_chinese_url(self, url: str) -> str:
        """
        对URL中的中文字符进行编码
        
        参数:
            url: 原始URL
        
        返回:
            编码后的URL
        """
        def encode_match(match):
            return "".join(f"%{ord(c):02X}" for c in match.group())
            
        return self.CHINESE_PATTERN.sub(encode_match, url)

    def resolve_url(self, base_url: str, relative: str) -> str:
        """
        解析相对URL为绝对URL
        
        参数:
            base_url: 基础URL
            relative: 相对路径
            
        返回:
            绝对URL
        """
        if relative.startswith(('#', '?')):
            base = base_url.split('#')[0].split('?')[0]
            return base + relative
        
        # 标准化路径处理
        base_parts = list(urlparse(base_url))
        new_path = unquote(relative)
        
        if new_path.startswith('/'):
            base_parts[2] = new_path
        else:
            base_parts[2] = posixpath.normpath(
                posixpath.join(posixpath.dirname(base_parts[2]), new_path)
            )
        
        return urlunparse(base_parts)

    def is_valid_link(self, item: Dict) -> bool:
        """
        验证链接是否有效
        
        参数:
            item: 包含链接信息的字典
        
        返回:
            链接是否有效的布尔值
        """
        if not item.get("title") or not item.get("link"):
            return False
            
        link = item["link"]
        
        # 排除无效协议
        invalid_protocols = ["#", "javascript:", "mailto:", "tel:"]
        if any(link.startswith(proto) for proto in invalid_protocols):
            return False
            
        # 解析URL路径
        parsed = urlparse(link)
        path = parsed.path
        
        # 排除根路径和索引文件
        if not path or path == "/":
            return False
            
        filename = path.split("/")[-1].lower()
        if filename in ["index.html", "main.html", "default.html"]:
            return False
            
        # 排除文件类型
        file_extensions = ["pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png", "gif", "mp3", "mp4"]
        extension = filename.split(".")[-1] if "." in filename else ""
        if extension in file_extensions:
            return False
            
        # 排除导航文本
        navigation_texts = ["首页", "主页", "上页", "下页", "下一页", "上一页", "尾页"]
        if item["title"] in navigation_texts:
            return False
            
        return True

    def is_valid_http_link(self, link: str, main_domain: str) -> bool:
        """
        验证HTTP链接是否有效且属于主域名
        
        参数:
            link: 链接URL
            main_domain: 主域名
        
        返回:
            链接是否有效的布尔值
        """
        # 检查HTTP协议
        if not link.startswith(("http://", "https://")):
            logger.info(f"非HTTP链接被过滤: {link}")
            return False
            
        # 解析主机名
        try:
            host = urlparse(link).hostname
            if not host:
                logger.info(f"无法解析域名: {link}")
                return False
                
            # 主域名验证
            if host == main_domain or host.endswith(f".{main_domain}"):
                return True
                
            logger.info(f"非主域名链接被过滤: {link} (host: {host}, expected: {main_domain})")
            return False
            
        except Exception:
            return False

    def deduplicate_by_link(self, data: List[Dict]) -> List[Dict]:
        """
        根据链接去重
        
        参数:
            data: 包含链接的字典列表
        
        返回:
            去重后的列表
        """
        seen = set()
        result = []
        
        for item in data:
            normalized = self.normalize_url(item["link"])
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(item)
                
        return result

    def normalize_url(self, url: str) -> str:
        """
        URL标准化
        
        参数:
            url: 原始URL
            
        返回:
            标准化后的URL
        """
        if not url:
            return ''
            
        # 基本清理
        url = url.lower().strip()
        url = re.sub(r'#.*$', '', url)  # 移除锚点
        url = url.rstrip('/')  # 移除末尾斜杠
        
        # 统一协议处理
        url = url.replace('http://', '').replace('https://', '')
        return url

    # 从文件加载HTML内容
    def get_html_from_file(self, url: str, base_path="../runtime/html") -> str:
        host = urlparse(url).netloc
        if not host:
            raise ValueError(f"无效的URL: {url}")

        normalized_url = self.normalize_url(url)
        file_name = hashlib.md5(normalized_url.encode("utf-8")).hexdigest() + ".html"
        file_path = os.path.join(base_path, host, file_name)
        # print("file_path:", file_path)

        if not os.path.exists(file_path):
            return ""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""
        
    def extract_clean_body(self, html_content: str) -> str:
        """
        提取HTML中的body内容，并移除干扰标签
        
        参数:
            html_content: 原始HTML字符串
            
        返回:
            清洗后的HTML字符串，只保留正文区域
        """
        # 解析HTML，忽略错误
        parser = html.HTMLParser(recover=True, encoding='utf-8')
        try:
            tree = html.fromstring(html_content, parser=parser)
        except Exception:
            return ""
        
        # 获取<body>节点
        body = tree.xpath('//body')
        if not body:
            return ""
        body = body[0]
        
        # 1. 移除<script>、<style>、<link>、<meta>、<noscript>标签
        remove_tags = ['script', 'style', 'link', 'meta', 'noscript']
        for tag in remove_tags:
            for element in body.xpath(f'.//{tag}'):
                element.getparent().remove(element)
        
        # 2. 移除注释
        for comment in body.xpath('//comment()'):
            comment.getparent().remove(comment)
        
        # 3. 移除常见的头部、尾部、导航等噪音元素
        noise_selectors = [
            '//*[contains(@class, "footer")]',
            '//*[contains(@class, "header")]',
            '//*[contains(@class, "head")]',
            '//*[contains(@class, "nav")]',
            '//*[contains(@id, "footer")]',
            '//*[contains(@id, "header")]',
            '//*[contains(@id, "nav")]'
        ]
        for selector in noise_selectors:
            for element in body.xpath(selector):
                element.getparent().remove(element)
        
        # 4. 提取body的innerHTML
        inner_html = ''
        for child in body.getchildren():
            inner_html += html.tostring(child, encoding='unicode', method='html')
        
        # 清除标签之间的多余换行和空白
        inner_html = re.sub(r'>\s*\r?\n\s*<', '><', inner_html)  # 去除标签间换行
        inner_html = re.sub(r'>\s{2,}<', '><', inner_html)       # 清除连续空格/制表符
        
        return inner_html.strip()        
    
    @staticmethod
    def get_main_domain(url: str) -> str:
        """
        提取主域名，例如：
        https://news.sina.com.cn/china/xxx → sina.com.cn
        https://sub.blog.example.co.uk → example.co.uk
        """
        extracted = tldextract.extract(url)
        if not extracted.domain or not extracted.suffix:
            return ""  # 解析失败，返回空字符串
        return f"{extracted.domain}.{extracted.suffix}"
    
    async def is_url_accessible(url: str, timeout: float = 10.0, retries: int = 2) -> bool:
        """
        判断 URL 是否可访问，自动重试
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        }
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
                    resp = await client.get(url)
                    if 200 <= resp.status_code < 400:
                        return True
            except (httpx.ConnectError, httpx.RequestError, httpx.ReadTimeout) as e:
                print(f"[Attempt {attempt+1}] URL连接异常: {url} -> {e}")
                await asyncio.sleep(0.5)
        return False

    def generate_urls(self,domain: str) -> list[str]:
        """
        根据 domain 生成尝试 URL 列表（优先 https，支持 www）
        """
        domain = domain.strip().rstrip("/")
        urls = [f"https://{domain}", f"http://{domain}"]

        if not domain.lower().startswith("www."):
            urls += [f"https://www.{domain}", f"http://www.{domain}"]

        return urls

    def get_accessible_url(self,domain: str) -> str:
        """
        遍历 URL 列表，返回第一个可访问的 URL
        """
        urls = self.generate_urls(domain)
        for url in urls:
            if self.is_url_accessible(url):
                return url
        return ''