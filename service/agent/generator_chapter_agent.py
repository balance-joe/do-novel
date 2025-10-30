# agents/generator_chapter_agent.py
import os
from pydantic_ai import Agent

from models.data_models import ChapterListConfig


class XPathGeneratorChapterAgent:
    
    
    def __init__(self,model_name: str, model_key: str):
        """初始化Agent"""
        # 确保API密钥已设置
        os.environ['DEEPSEEK_API_KEY'] = model_key
        
        # 创建Agent实例
        self.agent = Agent(
            model_name,
            deps_type=int,
            output_type=ChapterListConfig,
            system_prompt=self._get_system_prompt(),
        )


    def generate_rules(self, html: str) -> ChapterListConfig:
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
        """优化后的章节列表系统提示词"""
        return (
            "你是一名专业的网页结构分析专家，专门为小说网站的章节列表页面生成XPath提取规则。\n\n"
            
            "## 核心任务\n"
            "分析HTML结构，生成能够准确提取章节列表信息的XPath表达式。\n\n"
            
            "## 字段定义与生成原则\n"
            
            "1. **container（容器）**: 包含所有章节列表的主要容器\n"
            "   - 查找特征：通常是<ul>、<ol>、<div>等包裹整个章节列表的元素\n"
            "   - 生成原则：选择最外层的稳定容器，避免过于具体的层级\n"
            "   - 示例：//div[@class='chapter-list'] 或 //ul[contains(@class, 'list')]\n\n"
            
            "2. **item（章节项）**: 单个章节条目的选择器\n"
            "   - 查找特征：通常是<li>、<tr>或包含链接的<div>\n"
            "   - 生成原则：相对于container的相对路径，使用稳定的class或标签特征\n"
            "   - 示例：.//li 或 .//a[contains(@href, 'chapter')]\n\n"
            
            "3. **title（章节标题）**: 章节标题文本\n"
            "   - 查找特征：通常是<a>标签的文本内容或内部的<span>\n"
            "   - 生成原则：相对于item的路径，提取文本节点\n"
            "   - 示例：./a/text() 或 .//span[@class='title']/text()\n\n"
            
            "4. **url（章节链接）**: 章节内容的URL地址\n"
            "   - 查找特征：<a>标签的href属性\n"
            "   - 生成原则：相对于item的路径，提取href属性\n"
            "   - 示例：./a/@href 或 .//a[1]/@href\n\n"
            
            "5. **pagination（分页标志）**: 判断是否存在分页\n"
            "   - 查找特征：'下一页''更多章节''加载更多'等分页元素\n"
            "   - 生成原则：返回布尔值true/false\n\n"
            
            "6. **more_url（更多链接）**: 下一页或加载更多的URL\n"
            "   - 查找特征：分页按钮的href属性\n"
            "   - 生成原则：存在分页时返回XPath，否则返回null\n"
            "   - 示例：//a[contains(text(), '下一页')]/@href\n\n"
            
            "## XPath生成最佳实践\n"
            "- **稳定性优先**: 使用class、id等稳定属性，避免数字索引\n"
            "- **相对路径**: item内的路径使用相对选择器（以.开头）\n"
            "- **容错处理**: 使用contains()进行模糊匹配，normalize-space()处理空白\n"
            "- **备用方案**: 为关键字段提供备选XPath（使用|操作符）\n"
            "- **精确提取**: 文本用text()，属性用@attr\n\n"
            
            "请基于HTML的实际结构生成最合理的XPath规则。"
        )
        
    def _build_prompt(self, html: str) -> str:
        """构建分析提示词"""
        # 简化提示，避免过长内容
        return f"""
## 章节列表分析任务
请仔细分析以下HTML结构，生成章节列表的XPath提取规则。

## 分析重点
请重点分析以下内容：

1. **章节容器识别**
   - 查找包含多个章节条目的父容器
   - 识别容器的标签类型（ul、div、table等）和特征class
   - 选择最稳定、最具体的容器选择器

2. **章节条目分析**  
   - 分析单个章节的结构模式（通常是列表项或包含链接的块）
   - 识别章节标题和链接的嵌套关系
   - 生成相对容器的item选择器

3. **分页机制判断**
   - 检查是否存在'下一页''更多'等分页元素
   - 分析分页导航的结构和链接模式
   - 判断是否需要分页处理

## HTML内容
HTML内容开始:
{html}
HTML内容结束

[完整HTML共{len(html)}字符]

请重点分析：
1. 章节列表的容器（通常是ul、ol、div等包含多个章节的元素）
2. 单个章节条目的结构
3. 章节标题的显示方式
4. 章节链接的定位
5. 是否存在分页导航

请基于实际HTML结构生成精确的XPath表达式。
"""    
