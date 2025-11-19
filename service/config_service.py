# service/config_service.py
import os
import json
from urllib.parse import urlparse
from typing import Dict, Any

from models.data_models import XPathTemplate

class ConfigService:
    def __init__(self, config_dir="./config"):
        self.config_dir = config_dir

    def get_config_path(self, url: str) -> str:
        """根据 URL 获取配置文件路径（仅支持 .json）"""
        domain = urlparse(url).netloc
        
        # 只检查 .json 扩展名
        ext = ".json"
        print(f"尝试加载配置文件: {self.config_dir}/{domain}{ext}")
        candidate = os.path.join(self.config_dir, f"{domain}{ext}")
        
        if os.path.exists(candidate):
            return candidate

        # ⚠️ 确保默认配置也是 .json
        default_path = os.path.join(self.config_dir, "default.json")
        print(f"[⚠] 未找到 {domain} 的配置，使用默认配置 {default_path}")
        return default_path

    def extract_domain_from_url(self, url: str) -> str:
        """返回完整域名"""
        parsed = urlparse(url)
        if not parsed.hostname:
            raise ValueError(f"URL 无效: {url}")
        return parsed.hostname

    def load_config(self, url: str) -> Dict[str, Any]:
        """加载配置（仅使用 JSON 格式）"""
        config_path = self.get_config_path(url)
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        # 检查是否是 .json 文件，防止意外加载其他格式
        if not config_path.lower().endswith('.json'):
             raise ValueError(f"只支持 JSON 配置文件，但尝试加载了: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                # 仅使用内置的 json 库加载
                config = json.load(f)
                    
        except json.JSONDecodeError as e:
            # JSON 解析错误
            raise ValueError(f"配置文件格式错误 (JSON 解析失败): {config_path}\n{e}")
        except Exception as e:
            # 其他文件读取错误
            raise ValueError(f"配置文件加载失败: {config_path}\n{e}")

        return config
    
    # --- JSON 保存函数 ---
    def save_config_to_json(self, config_object: XPathTemplate, config_dir: str = "./config"):
        """将最终的 Pydantic XPathTemplate 对象保存为结构化的 JSON 文件。"""
        
        # 使用 Pydantic 的 model_dump_json 方法直接生成 JSON 字符串
        final_json_string = config_object.model_dump_json(
            by_alias=True,          # 确保字段别名（如 user_agent）正确导出
            indent=4,               # 格式化输出
            exclude_none=True       # 排除值为 None 的可选字段，保持文件简洁
        )
        
        # 确定文件名和路径
        domain = config_object.site.base_url.replace("https://", "").replace("http://", "").split("/")[0]
        filename = f"{domain}.json"
        new_config_path = os.path.join(config_dir, filename)
        
        # 确保保存目录存在
        os.makedirs(config_dir, exist_ok=True)
        
        try:
            with open(new_config_path, 'w', encoding='utf-8') as f:
                # 使用 ensure_ascii=False 确保中文不被转义
                f.write(final_json_string)
            print(f"\n🎉 配置已成功保存到文件: {os.path.abspath(new_config_path)}")
        except Exception as e:
            print(f"\n❌ 保存配置文件失败: {e}")