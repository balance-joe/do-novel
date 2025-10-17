# ===========================================
# File: models/data_models.py
# Description:
#   小说网站抓取配置的结构化数据模型定义。
#   所有智能体（Template / Generator / Validator / Improver / Orchestrator）
#   都依赖这些模型进行输入输出的数据约束。
# ===========================================

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# ===========================================
# 1️⃣ 请求与站点配置层
# ===========================================

class RequestHeaders(BaseModel):
    """请求头配置模型，对应 YAML 中的 headers 节点"""
    User_Agent: Optional[str] = Field(None, alias="User-Agent")
    Accept: Optional[str]
    Accept_Language: Optional[str] = Field(None, alias="Accept-Language")
    Accept_Encoding: Optional[str] = Field(None, alias="Accept-Encoding")
    Connection: Optional[str]
    Upgrade_Insecure_Requests: Optional[str] = Field(None, alias="Upgrade-Insecure-Requests")
    Cookie: Optional[str]


class SiteConfig(BaseModel):
    """站点级配置信息"""
    name: str                                  # 站点代号或文件名
    base_url: str                              # 网站根地址
    encoding: str = "utf-8"                    # 字符集
    user_agent: Optional[str] = None           # 浏览器标识
    delay: float = 1.0                         # 抓取延迟秒数
    headers: Optional[RequestHeaders] = None   # 请求头配置


# ===========================================
# 2️⃣ 小说元信息配置层
# ===========================================

class NovelInfoConfig(BaseModel):
    """小说详情页对应的 XPath 规则"""
    title: str                                 # 小说标题 XPath
    author: str                                # 作者 XPath
    update_time: str                           # 更新时间 XPath
    status: str                                # 状态 XPath（连载/完结等）
    intro: str                                 # 简介 XPath
    cover: str                                 # 封面图 XPath
    category: str                              # 分类 XPath
    author_split: Optional[str] = "："          # 作者字段分隔符
    update_split: Optional[str] = "："          # 更新时间分隔符


# ===========================================
# 3️⃣ 章节目录页配置层
# ===========================================

class ChapterListConfig(BaseModel):
    """章节列表页对应的 XPath 规则"""
    container: str                             # 包裹章节列表的父节点 XPath
    item: str                                  # 单个章节节点 XPath（支持多种结构）
    title: str                                 # 章节标题 XPath
    url: str                                   # 章节链接 XPath
    pagination: bool = False                   # 是否存在分页目录
    more_url: Optional[str] = None             # 目录分页链接或“更多章节”按钮的 XPath


# ===========================================
# 4️⃣ 章节正文页配置层
# ===========================================

class ContentPageConfig(BaseModel):
    """章节正文页对应的 XPath 规则"""
    container: str                             # 章节正文容器 XPath
    title: str                                 # 标题 XPath
    text: str                                  # 正文文本 XPath
    next_page: Optional[str] = None            # 下一页链接 XPath
    pagination: bool = True                    # 是否分页显示正文


# ===========================================
# 5️⃣ 内容过滤规则配置层
# ===========================================

class FilterConfig(BaseModel):
    """内容过滤配置（用于清理广告与无关元素）"""
    remove_html: List[str] = []                # 要删除的 HTML 节点 XPath 列表
    regex: List[str] = []                      # 要过滤的文本正则表达式列表


# ===========================================
# 6️⃣ 顶层配置模板对象
# ===========================================

class XPathTemplate(BaseModel):
    """完整的 XPath 抓取配置模板对象"""
    site: SiteConfig                           # 网站与请求层配置
    novel: NovelInfoConfig                     # 小说详情配置
    chapters: ChapterListConfig                # 章节列表配置
    content: ContentPageConfig                 # 章节正文配置
    filters: FilterConfig                      # 内容过滤规则


# ===========================================
# 7️⃣ 验证与反馈结果结构
# ===========================================

class RuleValidationReport(BaseModel):
    """XPath 规则验证报告"""
    is_valid: bool                             # 是否验证通过
    invalid_fields: List[str] = []             # 验证失败的字段列表
    content_preview: Dict[str, str] = {}       # 抓取的预览内容（片段）
    suggestions: Optional[str] = None          # 针对失败项的改进建议


class TemplateAnalysis(BaseModel):
    """模板结构分析结果（由 TemplateAgent 输出）"""
    required_fields: List[str] = []            # 必填字段
    optional_fields: List[str] = []            # 可选字段
    field_descriptions: Dict[str, str] = {}    # 字段描述（从模板或文档提取）


class ImprovedConfig(BaseModel):
    """规则修正结果（由 ImproverAgent 输出）"""
    updated_config: XPathTemplate              # 修正后的配置对象
    changes: Dict[str, str]                    # 修改说明（字段名 -> 变更理由）


class FinalValidationResult(BaseModel):
    """完整闭环后的最终验证结果"""
    site_name: str                             # 站点名称
    success: bool                              # 最终是否成功
    final_config: XPathTemplate                # 最终可用的 XPath 配置
    report: RuleValidationReport               # 最后一次验证报告
