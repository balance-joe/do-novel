# agents/orchestrator_agent.py
class OrchestratorAgent:
    """编排控制智能体 - 流程调度中心"""
    async def process_site(self, site_url: str) -> FinalValidationResult:
        # 1. 调用TemplateAgent分析模板结构
        # 2. 调用GeneratorAgent生成初始规则  
        # 3. 循环: Validator验证 → Improver修正 → 再验证
        # 4. 返回最终可用配置