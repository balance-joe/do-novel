# agents/generator_content_agent.py
import os
from pydantic_ai import Agent

from models.data_models import ContentPageConfig


class XPathGeneratorContentAgent:
    
    
    def __init__(self, model_name: str, model_key: str):
        """初始化Agent"""
        # 确保API密钥已设置
        os.environ['DEEPSEEK_API_KEY'] = model_key
        
        # 创建Agent实例
        self.agent = Agent(
            model_name,
            deps_type=int,
            output_type=ContentPageConfig,
            system_prompt=self._get_system_prompt(),
        )

    
    def generate_rules(self, html: str) -> ContentPageConfig:
        """
        从HTML生成章节目录XPath规则
        
        Args:
            html: HTML内容字符串
            
        Returns:
            XPathGeneratorContentAgent: 生成的XPath配置
        """
        # 构建分析提示
        prompt = self._build_prompt(html)
        
        # 使用Agent分析HTML并生成XPath模板
        result = self.agent.run_sync(prompt)
        
        # 返回解析结果
        return result.output


    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return (
            '你是一个专业的XPath分析专家。'
            '请仔细分析用户提供的HTML代码结构，从中识别出小说正文内容部分。'
            '你的任务是生成精确的XPath表达式来定位以下元素：'
            '1. container: 包含整个章节正文的容器元素'
            '2. title: 章节标题'
            '3. text: 正文文本内容'
            '4. next_page: 如果有分页，提供"下一页"链接的XPath，否则为null'
            '5. pagination: 判断正文是否分页（true/false）'
            '请基于HTML的实际结构生成XPath，确保表达式能够准确匹配目标元素。'
            '对于pagination字段，如果发现"下一页"、"下一章"等分页元素，返回true，否则返回false。'
            '请以JSON格式返回结果，包含所有上述字段。'
        )

    
    def _build_prompt(self, html: str) -> str:
        """构建分析提示词"""
        # 简化提示，避免过长内容
        return f"""
请分析以下HTML代码结构，生成小说内容的XPath选择器：

HTML内容开始:
{html}
HTML内容结束

请重点分析：
1. 正文内容的容器（通常是div、article等包含整个章节内容的元素）
2. 章节标题的位置和结构
3. 正文文本的显示方式
4. 是否存在分页导航（如"下一页"按钮）

请基于实际HTML结构生成精确的XPath表达式。
"""