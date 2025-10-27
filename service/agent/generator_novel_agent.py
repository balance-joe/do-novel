# agents/generator_noval_agent.py
import os
from pydantic_ai import Agent

from models.data_models import NovelInfoConfig


class XPathGeneratorNovelAgent:
    
    
    def __init__(self,model_name: str, model_key: str):
        """初始化Agent"""
        # 确保API密钥已设置
        os.environ['DEEPSEEK_API_KEY'] = model_key
        
        # 创建Agent实例
        self.agent = Agent(
            model_name,
            deps_type=int,
            output_type=NovelInfoConfig,
            system_prompt=self._get_system_prompt(),
        )


    def generate_rules(self, html: str) -> NovelInfoConfig:
        """
        从HTML生成章节目录XPath规则
        
        Args:
            html: HTML内容字符串
            
        Returns:
            ChapterListConfig: 生成的XPath配置
        """
        # 构建分析提示
        prompt = self._build_prompt(html)
        
        print("🔍 开始分析HTML结构并生成XPath模板...")
        
        # 使用Agent分析HTML并生成XPath模板
        result = self.agent.run_sync(prompt)
        
        # 返回解析结果
        return result.output


    def _get_system_prompt(self) -> str:
        """
        获取系统提示词 —— 专为 pydantic_ai 结构化输出设计
        """
        return (
            "你是一名专业的网页结构与 XPath 提取专家。"
            "请分析用户提供的小说详情页 HTML 结构，为以下字段生成精确、稳定的 XPath 表达式。"
            "输出将自动映射到 NovelInfoConfig 模型，因此你只需专注生成 XPath 值本身，而非 JSON。"
            "\n\n"
            "字段含义说明：\n"
            "1. title：小说标题所在节点（如 <h1>、<meta property='og:title'> 等）\n"
            "2. author：作者信息所在节点（通常含有“作者”或类名 'author'）\n"
            "3. update_time：更新时间所在节点（可含“更新”、“最后”或日期格式）\n"
            "4. status：小说连载状态（如 连载中 / 完结）对应节点\n"
            "5. intro：小说简介或概要的文本容器节点（通常是 <div class='intro'>）\n"
            "6. cover：封面图像的 XPath，应指向图片 URL 属性（@src、@data-src 或 meta 标签）\n"
            "7. category：小说所属分类节点（如“玄幻”“都市”等文字）\n"
            "8. author_split：若作者字段存在分隔符（例如“作者：张三”），请返回该分隔符，否则返回 null。\n"
            "9. update_split：若更新时间存在分隔符（例如“更新时间：2024-01-01”），请返回该分隔符，否则返回 null。\n\n"
            "输出要求：\n"
            "- 每个字段的值必须是可直接用于 lxml 的 XPath 表达式字符串。\n"
            "- 优先使用稳定的属性选择（如 contains(@class, 'author')），避免数字索引（如 div[7]）。\n"
            "- 文本节点建议使用 normalize-space() 包裹，以去除多余空白。\n"
            "- 若页面无此字段信息，请输出 None。\n"
            "- cover 优先选择图片 URL 属性，如 //img/@src 或 meta[@property='og:image']/@content。\n"
            "\n"
            "请直接返回各字段对应的 XPath 值，系统会自动封装为 NovelInfoConfig 实例。"
        )

    
    def _build_prompt(self, html: str) -> str:
        """
        构建分析提示词 —— 提供上下文 HTML
        """
        return f"""
    请分析以下小说详情页 HTML 内容，并根据结构提取出每个元信息字段的 XPath。
    重点分析：
    - 小说标题（title）
    - 作者信息（author）
    - 更新时间（update_time）
    - 连载状态（status）
    - 简介内容（intro）
    - 封面图像（cover）
    - 分类信息（category）

    HTML 内容如下：
    {html}

    HTML 总长度：{len(html)} 字符。
    请依据结构生成最合理的 XPath 路径，系统将根据你的回答自动构建 NovelInfoConfig 对象。
    """


