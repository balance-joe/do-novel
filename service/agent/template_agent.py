# agents/template_agent.py  
class RuleTemplateAgent:
    """模板分析智能体 - 配置结构理解"""
    def analyze_template(self, yaml_template: str) -> TemplateAnalysis:
        # 解析YAML模板，提取字段约束
        # 输出必填项、可选项、字段描述