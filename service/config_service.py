# service/config_service.py
import os
import yaml
from urllib.parse import urlparse

class ConfigService:
    def __init__(self, config_dir="./config"):
        self.config_dir = config_dir

    def get_config_path(self, url: str) -> str:
        """根据 URL 获取配置文件路径（支持 .yaml/.yml）"""
        domain = urlparse(url).netloc
        for ext in (".yaml", ".yml"):
            candidate = os.path.join(self.config_dir, f"{domain}{ext}")
            if os.path.exists(candidate):
                return candidate

        default_path = os.path.join(self.config_dir, "default.yaml")
        print(f"[⚠] 未找到 {domain} 的配置，使用默认配置 {default_path}")
        return default_path

    def extract_domain_from_url(self, url: str) -> str:
        """返回完整域名"""
        parsed = urlparse(url)
        if not parsed.hostname:
            raise ValueError(f"URL 无效: {url}")
        return parsed.hostname

    def load_config(self, url: str) -> dict:
        """加载配置"""
        config_path = self.get_config_path(url)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {config_path}\n{e}")

        self.validate_config(config)
        return config

    def validate_config(self, config: dict):
        """验证配置结构"""
        required_fields = {
            "root": ["name", "base_url", "encoding"],
            "novel": ["title", "author"],
            "chapters": ["item", "url"],
            "content": ["text"],
        }

        errors = []

        for section, fields in required_fields.items():
            if section == "root":
                for f in fields:
                    if f not in config:
                        errors.append(f"[ROOT] 缺少字段: {f}")
            else:
                if section not in config:
                    errors.append(f"缺少配置段: {section}")
                else:
                    for f in fields:
                        if f not in config[section]:
                            errors.append(f"[{section}] 缺少字段: {f}")

        if errors:
            raise ValueError("配置验证失败:\n" + "\n".join(errors))

        config.setdefault("chapters", {}).setdefault("pagination", False)
        config.setdefault("content", {}).setdefault("pagination", False)