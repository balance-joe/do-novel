import os
import re
from urllib.parse import urlparse
import httpx
from parsel import Selector
import yaml

# -----------------------------
# 配置验证器
# -----------------------------
def validate_config(config: dict):
    """
    验证配置结构和必需字段
    """
    errors = []

    # 基本字段
    for field in ['name', 'base_url', 'encoding']:
        if field not in config:
            errors.append(f"缺少必需字段: {field}")

    # novel 配置检查
    if 'novel' not in config:
        errors.append("缺少 novel 配置")
    else:
        for field in ['title', 'author']:
            if field not in config['novel']:
                errors.append(f"novel 配置缺少必需字段: {field}")

    # chapters 配置检查
    if 'chapters' not in config:
        errors.append("缺少 chapters 配置")
    else:
        for field in ['item', 'url']:
            if field not in config['chapters']:
                errors.append(f"chapters 配置缺少必需字段: {field}")

    # content 配置检查
    if 'content' not in config:
        errors.append("缺少 content 配置")
    else:
        if 'text' not in config['content']:
            errors.append("content 配置缺少必需字段: text")

    if errors:
        raise ValueError("配置验证错误:\n" + "\n".join(errors))

    # 设置默认值
    config['chapters'].setdefault('pagination', False)
    config['content'].setdefault('pagination', False)

    print("✅ 配置验证通过")

# -----------------------------
# 域名提取工具
# -----------------------------
def extract_domain_from_url(url: str) -> str:
    """
    返回完整域名（含子域名）
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"URL 无效，无法提取域名: {url}")
    return hostname

def load_config(domain: str) -> dict:
    """
    根据域名加载 ./config 下的配置文件
    文件名: {domain}.yml (如 www.630book.cc.yml)
    """
    config_dir = os.path.join(os.getcwd(), "config")  # 根目录 ./config
    config_path = os.path.join(config_dir, f"{domain}.yml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


# -----------------------------
# 配置测试工具
# -----------------------------
def test_config(test_url: str) -> dict:
    """
    测试配置抓取指定 URL 的效果
    返回结果字典，包含提取成功/失败信息
    """
    results = {
        "status": "ok",
        "errors": [],
        "novel_info": {},
        "chapters": [],
        "content_preview": ""
    }
    
    try:

        # 0.获取本次域名
        domain = extract_domain_from_url(test_url)
        # 1. 验证配置
        config = load_config(domain)
        validate_config(config)

        # 2. 检查域名匹配
        config_domain = extract_domain_from_url(config.get("base_url", ""))
        if domain != config_domain:
            raise ValueError(f"测试 URL 域名 ({domain}) 与配置 base_url ({config_domain}) 不匹配")

        # 3. 请求页面
        headers = {"User-Agent": config.get("user_agent", "Mozilla/5.0")}
        resp = httpx.get(test_url, headers=headers, timeout=10)
        resp.raise_for_status()
        resp.encoding = config.get("encoding", "utf-8")
        sel = Selector(resp.text)

        # 4. 提取小说信息
        novel_cfg = config.get("novel", {})
        novel_info = {}
        for key, xpath in novel_cfg.items():
            if key.endswith("_split"):
                continue
            if xpath.startswith("regex:"):
                pattern = xpath.replace("regex:", "").strip()
                match = re.search(pattern, resp.text)
                if match:
                    novel_info[key] = match.group(1) if match.groups() else match.group(0)
                else:
                    novel_info[key] = None
            else:
                novel_info[key] = sel.xpath(xpath).get(default="").strip()
        results["novel_info"] = novel_info

        # 5. 提取章节列表（只取前 5 个预览）
        chap_cfg = config.get("chapters", {})
        if chap_cfg:
            container = sel.xpath(chap_cfg.get("container", ".")) or sel
            items = container.xpath(chap_cfg.get("item", ".")) or []
            chapters = []
            for a in items[:5]:
                chap = {
                    "title": a.xpath(chap_cfg.get("title", "text()")).get(default="").strip(),
                    "url": a.xpath(chap_cfg.get("url", "@href")).get(default="").strip(),
                }
                chapters.append(chap)
            results["chapters"] = chapters

        # 6. 提取正文（第一页前 200 字预览）
        cont_cfg = config.get("content", {})
        if cont_cfg:
            content_sel = sel.xpath(cont_cfg.get("container", ".")) or sel
            paras = content_sel.xpath(cont_cfg.get("text", "text()")).getall()
            cleaned = [p.strip() for p in paras if p.strip()]

            # 应用过滤规则
            filters = config.get("filters", {})
            for xpath in filters.get("remove_html", []):
                # 注意：这里只做提示，可在实际抓取中移除节点
                pass
            for pattern in filters.get("regex", []):
                cleaned = [re.sub(pattern, "", p) for p in cleaned]

            results["content_preview"] = "\n".join(cleaned[:10])[:200]

    except Exception as e:
        results["status"] = "error"
        results["errors"].append(str(e))

    return results
