# agents/generator_agent.py
class XPathGeneratorAgent:
    """生成智能体 - HTML结构分析"""
    async def generate_rules(self, html: str, template: TemplateAnalysis) -> XPathConfig:
        # 基于xpath.md规则分析DOM
        # 生成符合模板的YAML配置