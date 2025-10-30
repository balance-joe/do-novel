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
        
        # 使用Agent分析HTML并生成XPath模板
        result = self.agent.run_sync(prompt)
        
        # 返回解析结果
        return result.output


    def _get_system_prompt(self) -> str:
        """
        优化后的系统提示词 - 更专注于网页结构分析和XPath生成
        """
        return (
            "你是一名专业的网页结构分析专家，专门为小说网站生成XPath提取规则。\n\n"
            
            "## 核心任务\n"
            "分析用户提供的HTML内容，为小说详情页的各个字段生成精确、稳定、通用的XPath表达式。\n\n"
            
            "## 字段分析要点\n"
            "1. **title**: 查找<h1>-<h3>标签，优先选择包含小说名称的标签\n"
            "2. **author**: 查找包含'作者'文本的节点，或class包含'author'的节点\n" 
            "3. **update_time**: 查找包含'更新''最后''时间'等关键词的日期信息\n"
            "4. **status**: 查找包含'状态''连载''完结'等状态信息的节点\n"
            "5. **intro**: 查找简介描述文本，通常在多行<p>标签或特定class的div中\n"
            "6. **cover**: 优先查找og:image元标签，其次查找封面图片的img标签\n"
            "7. **category**: 查找分类信息，通常在面包屑导航或特定分类区域\n\n"
            
            "## XPath生成原则\n"
            "- **稳定性优先**: 使用class、id等稳定属性，避免使用易变的数字索引\n"
            "- **容错性强**: 使用contains()进行模糊匹配，使用normalize-space()处理空白\n"
            "- **备用方案**: 为关键字段提供备选XPath（使用|操作符）\n"
            "- **精确提取**: 文本节点使用text()，属性使用@attr，根据需求选择\n\n"
            
            "## 输出要求\n"
            "直接返回有效的XPath表达式字符串，确保：\n"
            "- 可被lxml库直接使用\n"
            "- 能够准确匹配目标内容\n"
            "- 具备一定的通用性和容错性\n"
            "- 若无对应内容则返回None\n\n"
            
            "请基于HTML的实际结构生成最合理的XPath规则。"
        )

    
    def _build_prompt(self, html: str) -> str:
            """
            优化后的用户提示词 - 提供更清晰的分析指导
            """
            # 提取关键信息帮助分析
            
            return f"""
    ## 网页结构分析任务
    请仔细分析以下小说详情页的HTML结构，为每个字段生成最优的XPath提取规则。
    下面是html内容
        {html}
        上面是html内容
    ## HTML内容概览
    - 总长度: {len(html)} 字符
    
    - 检测到可能包含小说信息的区域

    ## 详细分析指导
    请按以下步骤进行分析：

    1. **整体结构识别**
    - 识别页面布局容器（header、container、footer等）
    - 定位小说信息的主要展示区域
    - 识别章节列表的容器结构

    2. **字段级分析** 
    - 标题：查找最显著的小说名称展示位置
    - 作者：搜索包含作者信息的文本模式
    - 元信息：识别更新时间、状态、分类的信息组织方式
    - 内容：定位简介文本和封面图片

    3. **XPath规则生成**
    - 为每个字段生成1-2个最稳定的XPath方案
    - 确保规则能够应对页面的微小变化
    - 优先使用语义化的class和id选择器

    ## HTML内容

请生成精确的XPath规则，确保能够可靠地提取小说信息。
"""

 